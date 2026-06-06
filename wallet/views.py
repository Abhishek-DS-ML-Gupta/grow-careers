from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json, hmac, hashlib

from .models import Wallet, Deposit, Purchase, Product, Transaction
from .forms import DepositForm


def _get_razorpay_client():
    try:
        import razorpay
        key_id = getattr(settings, 'RAZORPAY_KEY_ID', '')
        key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '')
        if key_id and key_secret:
            return razorpay.Client(auth=(key_id, key_secret))
    except Exception:
        pass
    return None


@login_required
def dashboard(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    transactions = Transaction.objects.filter(user=request.user).select_related('deposit', 'purchase')
    return render(request, 'wallet/dashboard.html', {
        'wallet': wallet,
        'transactions': transactions,
    })



@login_required
def deposit(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    form = DepositForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        deposit_obj = form.save(commit=False)
        deposit_obj.user = request.user
        deposit_obj.save()
        messages.success(request, 'Deposit request submitted. Please complete payment.')
        return redirect('wallet_deposit')
    return render(request, 'wallet/deposit.html', {'form': form, 'wallet': wallet})


@login_required
@csrf_exempt
def create_order(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    try:
        amount_val = float(request.POST.get('amount', 0))
        upi_id = request.POST.get('upi_id', '')
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Invalid amount'}, status=400)

    client = _get_razorpay_client()
    if client is None:
        deposit = Deposit.objects.create(
            user=request.user,
            amount=amount_val,
            upi_id=upi_id,
            status='pending',
            razorpay_order_id='SIMULATED',
        )
        return JsonResponse({
            'order_id': deposit.razorpay_order_id,
            'amount': amount_val,
            'currency': 'INR',
            'simulated': True,
        })

    order = client.order.create({
        'amount': int(amount_val * 100),
        'currency': 'INR',
        'payment_capture': 1,
        'notes': {'upi_id': upi_id},
    })
    deposit = Deposit.objects.create(
        user=request.user,
        amount=amount_val,
        upi_id=upi_id,
        status='pending',
        razorpay_order_id=order['id'],
    )
    return JsonResponse({
        'order_id': order['id'],
        'amount': order['amount'],
        'currency': order['currency'],
        'key_id': getattr(settings, 'RAZORPAY_KEY_ID', ''),
        'simulated': False,
    })


@login_required
@csrf_exempt
def verify_payment(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    razorpay_payment_id = data.get('razorpay_payment_id', '')
    razorpay_order_id = data.get('razorpay_order_id', '')
    razorpay_signature = data.get('razorpay_signature', '')

    deposit = get_object_or_404(Deposit, razorpay_order_id=razorpay_order_id, user=request.user)

    client = _get_razorpay_client()
    if client is not None:
        try:
            client.utility.verify_payment_signature({
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_order_id': razorpay_order_id,
                'razorpay_signature': razorpay_signature,
            })
        except Exception as e:
            deposit.status = 'failed'
            deposit.razorpay_payment_id = razorpay_payment_id
            deposit.razorpay_signature = razorpay_signature
            deposit.save(update_fields=['status', 'razorpay_payment_id', 'razorpay_signature', 'updated_at'])
            return JsonResponse({'status': 'failed', 'message': str(e)})

    deposit.status = 'completed'
    deposit.razorpay_payment_id = razorpay_payment_id
    deposit.razorpay_signature = razorpay_signature
    deposit.save(update_fields=['status', 'razorpay_payment_id', 'razorpay_signature', 'updated_at'])

    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    wallet.balance += deposit.amount
    wallet.total_deposit += deposit.amount
    wallet.save(update_fields=['balance', 'total_deposit', 'updated_at'])

    Transaction.objects.create(
        user=request.user,
        txn_type='DEPOSIT',
        amount=deposit.amount,
        reference_id=razorpay_payment_id or deposit.razorpay_order_id,
        deposit=deposit,
    )
    return JsonResponse({'status': 'completed'})


@csrf_exempt
def razorpay_webhook(request):
    if request.method != 'POST':
        return JsonResponse(status=405, data={'error': 'Method not allowed'})
    webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', '')
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(status=400, data={'error': 'Invalid JSON'})

    if webhook_secret:
        signature = request.META.get('HTTP_X_RAZORPAY_SIGNATURE', '')
        expected = hmac.new(
            webhook_secret.encode(),
            request.body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, signature):
            return JsonResponse(status=403, data={'error': 'Invalid signature'})

    event = data.get('event', '')
    payment = data.get('payload', {}).get('payment', {}).get('entity', {})
    order_id = payment.get('order_id', '')
    if event == 'payment.captured' and order_id:
        Deposit.objects.filter(razorpay_order_id=order_id, status='pending').update(status='completed')
    elif event == 'payment.failed' and order_id:
        Deposit.objects.filter(razorpay_order_id=order_id, status='pending').update(status='failed')
    return JsonResponse(status=200, data={'status': 'ok'})


@login_required
def purchase_plan(request, plan_id):
    product = get_object_or_404(Product, pk=plan_id, active=True)
    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    if wallet.balance < product.investment_amount:
        messages.error(request, 'Insufficient Wallet Balance. Please deposit funds first.')
        return redirect('wallet_deposit')

    with transaction.atomic():
        wallet.balance -= product.investment_amount
        wallet.total_withdrawal += product.investment_amount
        wallet.save(update_fields=['balance', 'total_withdrawal', 'updated_at'])

        purchase = Purchase.objects.create(
            user=request.user,
            product=product,
            amount=product.investment_amount,
            status='ACTIVE',
        )
        Transaction.objects.create(
            user=request.user,
            txn_type='PURCHASE',
            amount=-product.investment_amount,
            reference_id=f"PUR-{purchase.id}",
            purchase=purchase,
        )

    return render(request, 'wallet/purchase.html', {
        'product': product,
        'purchase': purchase,
        'wallet': wallet,
    })
