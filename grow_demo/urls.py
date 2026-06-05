from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from rest_framework import routers
from django.contrib.auth import views as auth_views
from plans import views as plan_views


router = routers.DefaultRouter()
router.register(r'plans', plan_views.InvestmentPlanViewSet)
router.register(r'objects', plan_views.TradeObjectViewSet)


def coming_soon(request):
    return render(request, 'plans/coming_soon.html')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', plan_views.plans_grid, name='home'),
    path('plan/', plan_views.plans_grid, name='plans_grid'),
    path('dashboard/', plan_views.dashboard, name='dashboard'),
    path('signup/', plan_views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='plans/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='plans_grid'), name='logout'),
    path('coming-soon/', coming_soon, name='coming_soon'),
    path('invest/<int:plan_id>/', plan_views.invest, name='invest'),
    path('api/', include(router.urls)),
]
