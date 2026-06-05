from django.contrib import admin
from .models import TradeObject, InvestmentPlan, Investment


@admin.register(TradeObject)
class TradeObjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'market_value_inr', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description')


@admin.register(InvestmentPlan)
class InvestmentPlanAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'object',
        'price_inr',
        'validity_days',
        'daily_income_inr',
        'total_income_inr',
        'is_limited',
        'is_active',
        'order',
    )
    list_filter = ('is_limited', 'is_active', 'object__category')
    search_fields = ('name', 'object__name')
    ordering = ['order', 'name']
    fields = (
        'object',
        'name',
        'price_inr',
        'validity_days',
        'total_income_inr',
        'daily_income_inr',
        'is_limited',
        'is_active',
        'order',
    )


@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'plan',
        'invested_amount',
        'start_date',
        'end_date',
        'status',
        'total_earned',
        'last_payout_date',
    )
    list_filter = ('status', 'start_date')
    search_fields = ('user__username', 'plan__name')
    readonly_fields = ('total_earned', 'last_payout_date', 'start_date', 'end_date')
    fields = (
        'user',
        'plan',
        'invested_amount',
        'start_date',
        'end_date',
        'status',
        'total_earned',
        'last_payout_date',
    )
