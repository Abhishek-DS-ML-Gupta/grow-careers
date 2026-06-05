from rest_framework import viewsets
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
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
    plan = InvestmentPlan.objects.filter(pk=plan_id, is_active=True).first()
    if not plan:
        messages.error(request, 'Plan not found.')
        return redirect('plans_grid')

    if request.method == 'POST':
        investment = Investment.objects.create(
            user=request.user,
            plan=plan,
            invested_amount=plan.price_inr,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=plan.validity_days),
            status='active',
        )
        messages.success(request, f'Successfully invested in {plan.name}!')
        return redirect('dashboard')

    return render(request, 'plans/invest.html', {'plan': plan})
