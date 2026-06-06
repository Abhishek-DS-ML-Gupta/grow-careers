from django.urls import path
from . import views

urlpatterns = [
    path('wallet/', views.wallet_page, name='wallet_page'),
    path('wallet/deposit/', views.deposit_page, name='wallet_deposit'),
    path('wallet/deposit/create-order/', views.create_order, name='wallet_create_order'),
    path('wallet/deposit/verify-payment/', views.verify_payment, name='wallet_verify_payment'),
    path('wallet/transactions/', views.transaction_list, name='wallet_transactions'),
    path('wallet/purchase/<int:plan_id>/', views.purchase_plan, name='wallet_purchase_plan'),
    path('razorpay/webhook/', views.razorpay_webhook, name='razorpay_webhook'),
    path('admin-dashboard/products/', views.admin_product_list, name='wallet_admin_products'),
    path('admin-dashboard/products/add/', views.admin_add_product, name='wallet_admin_add_product'),
    path('admin-dashboard/products/<int:product_id>/edit/', views.admin_edit_product, name='wallet_admin_edit_product'),
    path('admin-dashboard/products/<int:product_id>/delete/', views.admin_delete_product, name='wallet_admin_delete_product'),
]