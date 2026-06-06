from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render, redirect
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from plans import views as plan_views
from wallet_app import views as wallet_views
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


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', plan_views.plans_grid, name='home'),
    path('object/<int:pk>/', plan_views.object_detail, name='object_detail'),
    path('plan/', plan_views.plans_grid, name='plans_grid'),
    path('how-it-works/', plan_views.how_it_works, name='how_it_works'),
    path('support/', plan_views.support, name='support'),
    path('dashboard/', plan_views.dashboard, name='dashboard'),
    path('signup/', plan_views.signup, name='signup'),
    path('login/', plan_views.user_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='plans_grid'), name='logout'),
    path('coming-soon/', coming_soon, name='coming_soon'),
    path('create-superuser/', plan_views.create_superuser, name='create_superuser'),
    path('superuser-success/', plan_views.superuser_success, name='superuser_success'),
    path('invest/<int:plan_id>/', plan_views.invest, name='invest'),
    path('api/', include(router.urls)),
    path('', include('wallet_app.urls')),
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
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
