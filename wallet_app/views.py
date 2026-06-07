import hmac
import hashlib
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from io import BytesIO
import base64
import qrcode
from plans.models import InvestmentPlan, Investment, TradeObject
from .models import Wallet, Deposit, Purchase, Transaction, Product
from .forms import DepositForm, ProductForm


def is_admin(user):
    return user.is_authenticated and user.is_staff


def get_wallet(user):
    wallet, _ = Wallet.objects.get_or_create(user=user)
    return wallet


def generate_upi_qr(upi_id, amount, name='ObjectTrade'):
    upi_string = f"upi://pay?pa={upi_id}&pn={name}&am={amount}&cu=INR"
    qr_img = qrcode.make(upi_string)
    buffered = BytesIO()
    qr_img.save(buffered, format='PNG')
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return img_str


@login_required
def wallet_page(request):
    wallet = get_wallet(request.user)
    transactions = Transaction.objects.filter(user=request.user).select_related('deposit', 'purchase')[:100]
    context = {'wallet': wallet, 'transactions': transactions}
    return render(request, 'wallet/wallet.html', context)


@login_required
def dashboard(request):
    investments = Investment.objects.filter(user=request.user).select_related('plan__object')
    wallet = get_wallet(request.user)
    return render(request, 'plans/dashboard.html', {'investments': investments, 'wallet': wallet})


@login_required
def transaction_list(request):
    transactions = Transaction.objects.filter(user=request.user).select_related('deposit', 'purchase')
    return render(request, 'wallet/transactions.html', {'transactions': transactions})


@login_required
def deposit_page(request):
    wallet = get_wallet(request.user)
    form = DepositForm()
    merchant_upi = settings.MERCHANT_UPI_ID

    if request.method == 'POST':
        form = DepositForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            upi_id = form.cleaned_data.get('upi_id', '').strip()
            if amount < 1:
                messages.error(request, 'Minimum deposit is ₹1')
            else:
                deposit = Deposit.objects.create(
                    user=request.user,
                    amount=Decimal(amount),
                    upi_id=upi_id,
                    status='pending',
                )
                qr_data = generate_upi_qr(merchant_upi, amount)
                return render(request, 'wallet/deposit_qr.html', {
                    'deposit': deposit,
                    'qr_data': qr_data,
                    'merchant_upi': merchant_upi,
                    'amount': amount,
                    'upi_id': upi_id,
                })

    preset = [100, 500, 1000, 5000, 10000]
    context = {
        'wallet': wallet,
        'form': form,
        'preset_amounts': preset,
        'merchant_upi': merchant_upi,
    }
    return render(request, 'wallet/deposit.html', context)


@login_required
def select_payment_method(request):
    wallet = get_wallet(request.user)
    merchant_upi = settings.MERCHANT_UPI_ID
    context = {'wallet': wallet, 'merchant_upi': merchant_upi}
    return render(request, 'wallet/payment_method.html', context)


@login_required
def purchase_plan(request, plan_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    plan = get_object_or_404(InvestmentPlan, pk=plan_id, is_active=True)
    wallet = get_wallet(request.user)
    amount = Decimal(plan.price_inr)

    if wallet.balance < amount:
        return JsonResponse({'error': 'Insufficient Wallet Balance', 'balance': str(wallet.balance)}, status=400)

    with transaction.atomic():
        wallet.balance -= amount
        wallet.total_withdrawal += amount
        wallet.save(update_fields=['balance', 'total_withdrawal', 'updated_at'])

        purchase = Purchase.objects.create(
            user=request.user,
            product=plan,
            amount=amount,
            status='ACTIVE',
        )

        Transaction.objects.create(
            user=request.user,
            txn_type='PURCHASE',
            amount=amount,
            reference_id=f"PUR-{purchase.id}",
            purchase=purchase,
        )

        Investment.objects.create(
            user=request.user,
            plan=plan,
            invested_amount=plan.price_inr,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + __import__('datetime').timedelta(days=plan.validity_days),
            status='pending',
        )

    return JsonResponse({'success': True, 'redirect': '/dashboard/'})


def execute_daily_payouts():
    today = timezone.now().date()
    active_investments = Investment.objects.filter(
        status='active',
        start_date__lte=today,
        end_date__gte=today,
    ).exclude(last_payout_date=today)

    updated_count = 0
    for inv in active_investments:
        wallet = inv.user.wallet
        wallet.balance = F('balance') + Decimal(inv.plan.daily_income_inr)
        wallet.total_earned = F('total_earned') + Decimal(inv.plan.daily_income_inr)
        wallet.save(update_fields=['balance', 'total_earned', 'updated_at'])

        inv.total_earned = F('total_earned') + inv.plan.daily_income_inr
        inv.last_payout_date = today
        if inv.total_earned >= inv.plan.total_income_inr:
            inv.status = 'completed'
            inv.end_date = today
        inv.save(update_fields=['total_earned', 'last_payout_date', 'status', 'end_date'])

        Transaction.objects.create(
            user=inv.user,
            txn_type='PURCHASE',
            amount=Decimal(inv.plan.daily_income_inr),
            reference_id=f"PAYOUT-{inv.id}-{today}",
        )
        updated_count += 1

    return updated_count


@csrf_exempt
def razorpay_webhook(request):
    return JsonResponse({'status': 'ok'})


@login_required
@user_passes_test(is_admin)
def run_daily_payouts_view(request):
    count = execute_daily_payouts()
    messages.success(request, f'Daily payout executed for {count} investments.')
    return redirect('run_daily_payouts')


@login_required
@user_passes_test(is_admin)
def run_daily_payouts(request):
    count = execute_daily_payouts()
    context = {'count': count}
    return render(request, 'wallet/admin/payouts.html', context)


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    from django.contrib.auth.models import User
    from django.db.models import Sum
    total_users = User.objects.count()
    total_admins = User.objects.filter(is_staff=True).count()
    total_objects = TradeObject.objects.count()
    total_plans = InvestmentPlan.objects.count()
    total_investments = Investment.objects.count()
    active_investments = Investment.objects.filter(status='active').count()
    total_invested = Investment.objects.aggregate(total=Sum('invested_amount'))['total'] or 0
    total_earned_all = Investment.objects.aggregate(total=Sum('total_earned'))['total'] or 0
    pending_deposits = Deposit.objects.filter(status='pending').count()
    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_investments = Investment.objects.select_related('user', 'plan', 'plan__object').order_by('-created_at')[:5]
    pending_deposit_list = Deposit.objects.filter(status='pending').select_related('user').order_by('-created_at')[:10]

    context = {
        'total_users': total_users,
        'total_admins': total_admins,
        'total_objects': total_objects,
        'total_plans': total_plans,
        'total_investments': total_investments,
        'active_investments': active_investments,
        'total_invested': total_invested,
        'total_earned': total_earned_all,
        'recent_users': recent_users,
        'recent_investments': recent_investments,
        'pending_deposits': pending_deposits,
        'pending_deposit_list': pending_deposit_list,
    }
    return render(request, 'plans/admin/dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def admin_deposits(request):
    deposits = Deposit.objects.select_related('user', 'verified_by').all()
    if request.method == 'POST':
        deposit_id = request.POST.get('deposit_id')
        action = request.POST.get('action')
        deposit = get_object_or_404(Deposit, pk=deposit_id)

        if action == 'approve':
            if deposit.status != 'pending':
                messages.warning(request, 'Only pending deposits can be approved.')
                return redirect('wallet_admin_deposits')

            with transaction.atomic():
                deposit.status = 'completed'
                deposit.is_verified = True
                deposit.verified_by = request.user
                deposit.verified_at = timezone.now()
                deposit.save(update_fields=['status', 'is_verified', 'verified_by', 'verified_at', 'updated_at'])

                wallet = deposit.user.wallet
                wallet.balance += deposit.amount
                wallet.total_deposit += deposit.amount
                wallet.save(update_fields=['balance', 'total_deposit', 'updated_at'])

                Transaction.objects.create(
                    user=deposit.user,
                    txn_type='DEPOSIT',
                    amount=deposit.amount,
                    reference_id=f"DEP-{deposit.id}",
                    deposit=deposit,
                )

            messages.success(request, f'Deposit of ₹{deposit.amount} approved for {deposit.user.username}.')
            return redirect('wallet_admin_deposits')

        if action == 'reject':
            if deposit.status != 'pending':
                messages.warning(request, 'Only pending deposits can be rejected.')
                return redirect('wallet_admin_deposits')

            deposit.status = 'cancelled'
            deposit.save(update_fields=['status', 'updated_at'])
            messages.info(request, f'Deposit of ₹{deposit.amount} rejected.')
            return redirect('wallet_admin_deposits')

    return render(request, 'wallet/admin/deposits.html', {'deposits': deposits})


@login_required
@user_passes_test(is_admin)
def admin_investments(request):
    investments = Investment.objects.all().select_related('user', 'plan', 'plan__object').order_by('-created_at')
    if request.method == 'POST':
        investment_id = request.POST.get('investment_id')
        action = request.POST.get('action')
        upi_ref = request.POST.get('upi_reference', '').strip()
        investment = get_object_or_404(Investment, pk=investment_id)

        if action == 'approve':
            if investment.status != 'pending':
                messages.warning(request, 'Only pending investments can be approved.')
                return redirect('wallet_admin_investments')

            investment.status = 'active'
            investment.start_date = timezone.now().date()
            investment.end_date = timezone.now().date() + __import__('datetime').timedelta(days=investment.plan.validity_days)
            investment.save(update_fields=['status', 'start_date', 'end_date'])

            transaction_record = Transaction.objects.filter(
                user=investment.user,
                txn_type='PURCHASE',
                amount=-investment.invested_amount,
                reference_id__startswith=f"PUR-",
            ).order_by('-created_at').first()

            if transaction_record:
                transaction_record.reference_id = f"UTR-{upi_ref}" if upi_ref else transaction_record.reference_id
                transaction_record.save(update_fields=['reference_id'])

            messages.success(request, f'Investment for {investment.user.username} in {investment.plan.name} approved and activated.')
            return redirect('wallet_admin_investments')

        if action == 'cancel':
            if investment.status != 'pending':
                messages.warning(request, 'Only pending investments can be cancelled.')
                return redirect('wallet_admin_investments')

            wallet = investment.user.wallet
            with transaction.atomic():
                investment.status = 'cancelled'
                investment.save(update_fields=['status'])
                wallet.balance += investment.invested_amount
                wallet.total_withdrawal -= investment.invested_amount
                wallet.save(update_fields=['balance', 'total_withdrawal', 'updated_at'])

                Transaction.objects.create(
                    user=investment.user,
                    txn_type='REFUND',
                    amount=investment.invested_amount,
                    reference_id=f"REF-{investment.id}",
                )

            messages.info(request, f'Investment for {investment.user.username} cancelled and amount refunded.')
            return redirect('wallet_admin_investments')

    return render(request, 'wallet/admin/investments.html', {'investments': investments})


@login_required
@user_passes_test(is_admin)
def admin_manual_payout(request, inv_id):
    investment = get_object_or_404(Investment, pk=inv_id, status='active')
    if request.method == 'POST':
        amount = request.POST.get('amount')
        if amount:
            try:
                amount = Decimal(amount)
            except Exception:
                messages.error(request, 'Invalid amount.')
                return redirect('wallet_admin_investments')
        else:
            amount = Decimal(investment.plan.daily_income_inr)

        with transaction.atomic():
            wallet = investment.user.wallet
            wallet.balance = F('balance') + amount
            wallet.total_earned = F('total_earned') + amount
            wallet.refresh_from_db(fields=['balance', 'total_earned'])
            wallet.save(update_fields=['balance', 'total_earned', 'updated_at'])

            investment.total_earned = models.ExpressionWrapper(
                models.F('total_earned') + amount, output_field=models.DecimalField()
            )
            investment.last_payout_date = timezone.now().date()
            if investment.total_earned >= investment.plan.total_income_inr:
                investment.status = 'completed'
                investment.end_date = timezone.now().date()
            investment.save(update_fields=['total_earned', 'last_payout_date', 'status', 'end_date'])

            Transaction.objects.create(
                user=investment.user,
                txn_type='PURCHASE',
                amount=amount,
                reference_id=f"PAYOUT-{investment.id}-{timezone.now().date()}",
            )

        messages.success(request, f'Daily income of ₹{amount} credited to {investment.user.username}.')
    return redirect('wallet_admin_investments')
