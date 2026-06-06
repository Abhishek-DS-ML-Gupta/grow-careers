
from django.contrib import admin
from .models import Wallet, Product, Deposit, Purchase, Transaction


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'total_deposit', 'total_withdrawal', 'created_at']
    search_fields = ['user__username', 'user__email']
    list_filter = ['created_at']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'investment_amount', 'daily_return', 'duration_days', 'active', 'created_at']
    list_filter = ['active']
    search_fields = ['name']
    ordering = ['-created_at']


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'status', 'upi_id', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'upi_id', 'razorpay_order_id']


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'amount', 'status', 'purchase_date']
    list_filter = ['status', 'purchase_date']
    search_fields = ['user__username', 'product__name']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'txn_type', 'amount', 'reference_id', 'created_at']
    list_filter = ['txn_type', 'created_at']
    search_fields = ['user__username', 'reference_id']
