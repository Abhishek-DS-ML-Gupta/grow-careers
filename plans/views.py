from rest_framework import viewsets
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Sum, Q
from django.db import transaction
from decimal import Decimal
from wallet.models import Wallet, Purchase, Transaction
from .models import TradeObject, InvestmentPlan, Investment
from .serializers import InvestmentPlanSerializer, TradeObjectSerializer


class InvestmentPlanViewSet(viewsets.ModelViewSet):
    queryset = InvestmentPlan.objects.filter(is_active=True).order_by('order', 'name')
    serializer_class = InvestmentPlanSerializer


class TradeObjectViewSet(viewsets.ModelViewSet):
    queryset = TradeObject.objects.filter(is_active=True)
    serializer_class = TradeObjectSerializer


def plans_grid(request):
    objects = TradeObject.objects.filter(is_active=True).prefetch_related('plans')
    return render(request, 'plans/grid.html', {'objects': objects})


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('plans_grid')
    else:
        form = UserCreationForm()
    return render(request, 'plans/signup.html', {'form': form})


@login_required
def dashboard(request):
    investments = Investment.objects.filter(user=request.user).select_related('plan__object')
    return render(request, 'plans/dashboard.html', {'investments': investments})


@login_required
def invest(request, plan_id):
    plan = get_object_or_404(InvestmentPlan, pk=plan_id, is_active=True)

    if request.method == 'POST':
        wallet = Wallet.objects.filter(user=request.user).first()
        amount = Decimal(plan.price_inr)

        if not wallet or wallet.balance < amount:
            messages.error(request, 'Insufficient Wallet Balance. Please deposit funds first.')
            return redirect('wallet_deposit')

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

            investment = Investment.objects.create(
                user=request.user,
                plan=plan,
                invested_amount=plan.price_inr,
                start_date=timezone.now().date(),
                end_date=timezone.now().date() + timedelta(days=plan.validity_days),
                status='active',
            )

        messages.success(request, f'Successfully invested in {plan.name}!')
        return render(request, 'wallet/purchase.html', {'plan': plan, 'purchase': purchase, 'wallet': wallet})

    return render(request, 'plans/invest.html', {'plan': plan})


def is_admin(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(is_admin)
def admin_dashboard(request):
    total_users = User.objects.count()
    total_admins = User.objects.filter(is_staff=True).count()
    total_objects = TradeObject.objects.count()
    total_plans = InvestmentPlan.objects.count()
    total_investments = Investment.objects.count()
    active_investments = Investment.objects.filter(status='active').count()
    total_invested = Investment.objects.aggregate(total=Sum('invested_amount'))['total'] or 0
    total_earned = Investment.objects.aggregate(total=Sum('total_earned'))['total'] or 0
    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_investments = Investment.objects.select_related('user', 'plan', 'plan__object').order_by('-created_at')[:5]

    context = {
        'total_users': total_users,
        'total_admins': total_admins,
        'total_objects': total_objects,
        'total_plans': total_plans,
        'total_investments': total_investments,
        'active_investments': active_investments,
        'total_invested': total_invested,
        'total_earned': total_earned,
        'recent_users': recent_users,
        'recent_investments': recent_investments,
    }
    return render(request, 'plans/admin/dashboard.html', context)


@user_passes_test(is_admin)
def admin_objects(request):
    objects_list = TradeObject.objects.all().prefetch_related('plans')
    context = {'objects': objects_list}
    return render(request, 'plans/admin/objects.html', context)


@user_passes_test(is_admin)
def admin_add_object(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        category = request.POST.get('category', 'other')
        description = request.POST.get('description', '')
        image_url = request.POST.get('image_url', '')
        market_value_inr = request.POST.get('market_value_inr', 0)
        is_active = request.POST.get('is_active') == 'on'
        obj = TradeObject.objects.create(
            name=name,
            category=category,
            description=description,
            image_url=image_url,
            market_value_inr=market_value_inr,
            is_active=is_active,
        )
        messages.success(request, f'Object "{name}" created successfully!')
        return redirect('admin_objects')
    return render(request, 'plans/admin/object_form.html')


@user_passes_test(is_admin)
def admin_edit_object(request, object_id):
    obj = get_object_or_404(TradeObject, pk=object_id)
    if request.method == 'POST':
        obj.name = request.POST.get('name')
        obj.category = request.POST.get('category', 'other')
        obj.description = request.POST.get('description', '')
        obj.image_url = request.POST.get('image_url', '')
        obj.market_value_inr = request.POST.get('market_value_inr', 0)
        obj.is_active = request.POST.get('is_active') == 'on'
        obj.save()
        messages.success(request, f'Object "{obj.name}" updated successfully!')
        return redirect('admin_objects')
    return render(request, 'plans/admin/object_form.html', {'object': obj})


@user_passes_test(is_admin)
def admin_delete_object(request, object_id):
    obj = get_object_or_404(TradeObject, pk=object_id)
    if request.method == 'POST':
        name = obj.name
        obj.delete()
        messages.success(request, f'Object "{name}" deleted successfully!')
        return redirect('admin_objects')
    return render(request, 'plans/admin/object_confirm_delete.html', {'object': obj})


@user_passes_test(is_admin)
def admin_plans(request):
    plans_list = InvestmentPlan.objects.all().select_related('object').order_by('order', 'name')
    context = {'plans': plans_list}
    return render(request, 'plans/admin/plans.html', context)


@user_passes_test(is_admin)
def admin_add_plan(request):
    objects = TradeObject.objects.filter(is_active=True)
    if request.method == 'POST':
        obj_id = request.POST.get('object')
        obj = get_object_or_404(TradeObject, pk=obj_id)
        plan = InvestmentPlan.objects.create(
            object=obj,
            name=request.POST.get('name'),
            price_inr=request.POST.get('price_inr', 0),
            validity_days=request.POST.get('validity_days', 30),
            total_income_inr=request.POST.get('total_income_inr', 0),
            daily_income_inr=request.POST.get('daily_income_inr', 0),
            is_limited=request.POST.get('is_limited') == 'on',
            is_active=request.POST.get('is_active') == 'on',
            order=request.POST.get('order', 0),
        )
        messages.success(request, f'Plan "{plan.name}" created successfully!')
        return redirect('admin_plans')
    return render(request, 'plans/admin/plan_form.html', {'objects': objects})


@user_passes_test(is_admin)
def admin_edit_plan(request, plan_id):
    plan = get_object_or_404(InvestmentPlan, pk=plan_id)
    objects = TradeObject.objects.filter(is_active=True)
    if request.method == 'POST':
        plan.object = get_object_or_404(TradeObject, pk=request.POST.get('object'))
        plan.name = request.POST.get('name')
        plan.price_inr = request.POST.get('price_inr', 0)
        plan.validity_days = request.POST.get('validity_days', 30)
        plan.total_income_inr = request.POST.get('total_income_inr', 0)
        plan.daily_income_inr = request.POST.get('daily_income_inr', 0)
        plan.is_limited = request.POST.get('is_limited') == 'on'
        plan.is_active = request.POST.get('is_active') == 'on'
        plan.order = request.POST.get('order', 0)
        plan.save()
        messages.success(request, f'Plan "{plan.name}" updated successfully!')
        return redirect('admin_plans')
    return render(request, 'plans/admin/plan_form.html', {'plan': plan, 'objects': objects})


@user_passes_test(is_admin)
def admin_delete_plan(request, plan_id):
    plan = get_object_or_404(InvestmentPlan, pk=plan_id)
    if request.method == 'POST':
        name = plan.name
        plan.delete()
        messages.success(request, f'Plan "{name}" deleted successfully!')
        return redirect('admin_plans')
    return render(request, 'plans/admin/plan_confirm_delete.html', {'plan': plan})


@user_passes_test(is_admin)
def admin_investments(request):
    investments = Investment.objects.all().select_related('user', 'plan', 'plan__object').order_by('-created_at')
    context = {'investments': investments}
    return render(request, 'plans/admin/investments.html', context)


@user_passes_test(is_admin)
def admin_users(request):
    users = User.objects.all().order_by('-date_joined')
    context = {'users': users}
    return render(request, 'plans/admin/users.html', context)


