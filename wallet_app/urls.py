from django.urls import path
from . import views

urlpatterns = [
    path('wallet/', views.wallet_page, name='wallet_page'),
    path('wallet/deposit/', views.deposit_page, name='wallet_deposit'),
    path('wallet/transactions/', views.transaction_list, name='wallet_transactions'),
    path('wallet/purchase/<int:plan_id>/', views.purchase_plan, name='wallet_purchase_plan'),
    path('admin-dashboard/deposits/', views.admin_deposits, name='wallet_admin_deposits'),
    path('admin-dashboard/investments/', views.admin_investments, name='wallet_admin_investments'),
    path('admin-dashboard/investments/<int:inv_id>/payout/', views.admin_manual_payout, name='admin_manual_payout'),
    path('admin-dashboard/run-payouts/', views.run_daily_payouts_view, name='run_daily_payouts'),
]
