
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='wallet_dashboard'),
    path('deposit/', views.deposit, name='wallet_deposit'),
    path('deposit/create-order/', views.create_order, name='wallet_create_order'),
    path('deposit/verify-payment/', views.verify_payment, name='wallet_verify_payment'),
    path('purchase/<int:plan_id>/', views.purchase_plan, name='wallet_purchase_plan'),
    path('razorpay/webhook/', views.razorpay_webhook, name='razorpay_webhook'),
]
