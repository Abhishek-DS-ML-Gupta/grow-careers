import hmac
import hashlib
import razorpay
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from plans.models import InvestmentPlan, Investment
from .models import Wallet, Deposit, Purchase, Transaction, Product
from .forms import DepositForm, ProductForm


def is_admin(user):
    return user.is_authenticated and user.is_staff


def get_wallet(user):
    wallet, _ = Wallet.objects.get_or_create(user=user)
    return wallet


def razorpay_client():
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )


@login_required
def deposit_page(request):
    wallet = get_wallet(request.user)
    form = DepositForm()
    preset = [100, 500, 1000, 5000, 10000]

    context = {
        'wallet': wallet,
        'form': form,
        'preset_amounts': preset,
    }
    return render(request, 'wallet/deposit.html', context)


@login_required
def create_order(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request')

    form = DepositForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'error': 'Invalid data'}, status=400)

    amount = form.cleaned_data['amount']
    if amount < 1:
        return JsonResponse({'error': 'Minimum deposit is ₹1'}, status=400)

    upi_id = form.cleaned_data.get('upi_id', '').strip()

    client = razorpay_client()
    order_data = {
        'amount': int(amount * 100),
        'currency': 'INR',
        'payment_capture': 1,
        'notes': {
            'upi_id': upi_id,
        }
    }
    order = client.order.create(data=order_data)

    deposit = Deposit.objects.create(
        user=request.user,
        amount=Decimal(amount),
        razorpay_order_id=order['id'],
        upi_id=upi_id,
        status='pending',
    )

    Transaction.objects.create(
        user=request.user,
        txn_type='DEPOSIT',
        amount=Decimal(amount),
        reference_id=order['id'],
        deposit=deposit,
    )

    return JsonResponse({
        'order_id': order['id'],
        'amount': order['amount'],
        'currency': order['currency'],
        'key': settings.RAZORPAY_KEY_ID,
        'upi_id': upi_id,
    })


@login_required
def wallet_page(request):
    wallet = get_wallet(request.user)
    transactions = Transaction.objects.filter(user=request.user).select_related(
        'deposit', 'purchase'
    )[:100]

    context = {
        'wallet': wallet,
        'transactions': transactions,
    }
    return render(request, 'wallet/wallet.html', context)


@login_required
def transaction_list(request):
    transactions = Transaction.objects.filter(user=request.user).select_related(
        'deposit', 'purchase'
    )
    return render(request, 'wallet/transactions.html', {'transactions': transactions})


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
            amount=-amount,
            reference_id=f"PUR-{purchase.id}",
            purchase=purchase,
        )

        Investment.objects.create(
            user=request.user,
            plan=plan,
            invested_amount=plan.price_inr,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + __import__('datetime').timedelta(days=plan.validity_days),
            status='active',
        )

    return JsonResponse({'success': True, 'redirect': '/dashboard/'})


@login_required
@user_passes_test(is_admin)
def admin_product_list(request):
    products = Product.objects.all().order_by('-created_at')
    return render(request, 'wallet/admin/products.html', {'products': products})


@login_required
@user_passes_test(is_admin)
def admin_add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product created successfully!')
            return redirect('wallet_admin_products')
    else:
        form = ProductForm()
    return render(request, 'wallet/admin/product_form.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def admin_edit_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('wallet_admin_products')
    else:
        form = ProductForm(instance=product)
    return render(request, 'wallet/admin/product_form.html', {'form': form, 'product': product})


@login_required
@user_passes_test(is_admin)
def admin_delete_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
        return redirect('wallet_admin_products')
    return render(request, 'wallet/admin/product_confirm_delete.html', {'product': product})


@login_required
@transaction.atomic
def verify_payment(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid request')

    razorpay_payment_id = request.POST.get('razorpay_payment_id', '')
    razorpay_order_id = request.POST.get('razorpay_order_id', '')
    razorpay_signature = request.POST.get('razorpay_signature', '')

    client = razorpay_client()
    params_dict = {
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': razorpay_payment_id,
    }

    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature,
        })
    except razorpay.errors.SignatureVerificationError:
        deposit = Deposit.objects.filter(razorpay_order_id=razorpay_order_id).first()
        if deposit:
            deposit.status = 'failed'
            deposit.save(update_fields=['status'])
        messages.error(request, 'Payment verification failed. Please contact support.')
        return redirect('wallet_deposit')

    deposit = get_object_or_404(Deposit, razorpay_order_id=razorpay_order_id)
    if deposit.status == 'completed':
        messages.info(request, 'Payment already processed')
        return redirect('wallet_page')

    deposit.status = 'completed'
    deposit.razorpay_payment_id = razorpay_payment_id
    deposit.razorpay_signature = razorpay_signature
    deposit.save(update_fields=['status', 'razorpay_payment_id', 'razorpay_signature', 'updated_at'])

    wallet = get_wallet(deposit.user)
    wallet.balance += deposit.amount
    wallet.total_deposit += deposit.amount
    wallet.save(update_fields=['balance', 'total_deposit', 'updated_at'])

    Transaction.objects.filter(
        user=deposit.user,
        deposit=deposit,
        txn_type='DEPOSIT',
        reference_id=razorpay_order_id,
    ).update(amount=deposit.amount)

    messages.success(request, f'₹{deposit.amount} has been credited to your wallet!')
    return redirect('wallet_page')


@csrf_exempt
def razorpay_webhook(request):
    import json
    if request.method != 'POST':
        return JsonResponse({'status': 'ok'})

    try:
        webhook_body = request.body.decode('utf-8')
        webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', '')
        signature = request.headers.get('X-Razorpay-Signature', '')

        if webhook_secret:
            expected = hmac.new(
                webhook_secret.encode(),
                webhook_body.encode(),
                hashlib.sha256,
            ).hexdigest()
            if not hmac.compare_digest(expected, signature):
                return JsonResponse({'status': 'invalid signature'}, status=400)

        event = json.loads(webhook_body)
        event_type = event.get('event')

        if event_type in ['payment.captured', 'payment.authorized']:
            payment = event.get('payload', {}).get('payment', {}).get('entity', {})
            order_id = payment.get('order_id', '')
            payment_id = payment.get('id', '')
            amount = Decimal(payment.get('amount', 0)) / 100

            deposit = Deposit.objects.filter(razorpay_order_id=order_id).first()
            if deposit:
                if deposit.status != 'completed':
                    deposit.status = 'completed'
                    deposit.razorpay_payment_id = payment_id
                    deposit.save(update_fields=['status', 'razorpay_payment_id', 'updated_at'])

                    wallet = get_wallet(deposit.user)
                    wallet.balance += amount
                    wallet.total_deposit += amount
                    wallet.save(update_fields=['balance', 'total_deposit', 'updated_at'])

                    Transaction.objects.filter(
                        user=deposit.user,
                        deposit=deposit,
                    ).update(amount=amount)

        return JsonResponse({'status': 'ok'})

    except Exception:
        return JsonResponse({'status': 'error'}, status=400)
