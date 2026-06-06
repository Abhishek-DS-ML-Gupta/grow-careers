from django.contrib import admin
from .models import Wallet, Product, Deposit, Purchase, Transaction


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'total_deposit', 'total_withdrawal', 'updated_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'investment_amount', 'daily_return', 'duration_days', 'active', 'created_at']
    list_filter = ['active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'status', 'razorpay_order_id', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'razorpay_order_id', 'razorpay_payment_id']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'amount', 'status', 'purchase_date']
    list_filter = ['status', 'purchase_date']
    search_fields = ['user__username', 'product__name']
    readonly_fields = ['purchase_date']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'txn_type', 'amount', 'reference_id', 'created_at']
    list_filter = ['txn_type', 'created_at']
    search_fields = ['user__username', 'reference_id']
    readonly_fields = ['created_at']
