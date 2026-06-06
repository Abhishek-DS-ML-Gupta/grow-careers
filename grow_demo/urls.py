from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render, redirect
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import UserCreationForm
from django import forms
from plans import views as plan_views
from rest_framework import routers


class StyledUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'w-full rounded-lg border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-milky-500 focus:border-transparent',
                'placeholder': field.label
            })


router = routers.DefaultRouter()
router.register(r'plans', plan_views.InvestmentPlanViewSet)
router.register(r'objects', plan_views.TradeObjectViewSet)


def coming_soon(request):
    return render(request, 'plans/coming_soon.html')


def create_superuser(request):
    if request.method == 'POST':
        form = StyledUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = True
            user.is_superuser = True
            user.save()
            return render(request, 'plans/superuser_success.html')
    else:
        form = StyledUserCreationForm()
    return render(request, 'plans/create_superuser.html', {'form': form})



urlpatterns = [
    path('admin/', admin.site.urls),
    path('wallet/', include('wallet.urls')),
    path('', plan_views.plans_grid, name='home'),
    path('plan/', plan_views.plans_grid, name='plans_grid'),
    path('dashboard/', plan_views.dashboard, name='dashboard'),
    path('signup/', plan_views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='plans/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='plans_grid'), name='logout'),
    path('coming-soon/', coming_soon, name='coming_soon'),
    path('invest/<int:plan_id>/', plan_views.invest, name='invest'),
    path('api/', include(router.urls)),
    path('create-superuser/', create_superuser, name='create_superuser'),
    path('admin-dashboard/', plan_views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/objects/', plan_views.admin_objects, name='admin_objects'),
    path('admin-dashboard/objects/add/', plan_views.admin_add_object, name='admin_add_object'),
    path('admin-dashboard/objects/<int:object_id>/edit/', plan_views.admin_edit_object, name='admin_edit_object'),
    path('admin-dashboard/objects/<int:object_id>/delete/', plan_views.admin_delete_object, name='admin_delete_object'),
    path('admin-dashboard/plans/', plan_views.admin_plans, name='admin_plans'),
    path('admin-dashboard/plans/add/', plan_views.admin_add_plan, name='admin_add_plan'),
    path('admin-dashboard/plans/<int:plan_id>/edit/', plan_views.admin_edit_plan, name='admin_edit_plan'),
    path('admin-dashboard/plans/<int:plan_id>/delete/', plan_views.admin_delete_plan, name='admin_delete_plan'),
    path('admin-dashboard/investments/', plan_views.admin_investments, name='admin_investments'),
    path('admin-dashboard/users/', plan_views.admin_users, name='admin_users'),
]
