from django.db import models
from django.contrib.auth.models import User


class TradeObject(models.Model):
    CATEGORY_CHOICES = [
        ('vehicle', 'Vehicle'),
        ('property', 'Property'),
        ('electronics', 'Electronics'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True, help_text="URL for object image")
    market_value_inr = models.PositiveIntegerField(help_text="Current market value in INR")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class InvestmentPlan(models.Model):
    object = models.ForeignKey(TradeObject, on_delete=models.CASCADE, related_name='plans')
    name = models.CharField(max_length=100)
    price_inr = models.PositiveIntegerField()
    validity_days = models.PositiveSmallIntegerField()
    total_income_inr = models.PositiveIntegerField()
    daily_income_inr = models.PositiveIntegerField()
    is_limited = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def clean(self):
        from django.core.exceptions import ValidationError
        qs = InvestmentPlan.objects.filter(object=self.object)
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        if qs.count() >= 3:
            raise ValidationError('A TradeObject can have at most 3 investment plans.')

    def __str__(self):
        return f"{self.object.name} - {self.name}"


class Investment(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='investments')
    plan = models.ForeignKey(InvestmentPlan, on_delete=models.PROTECT, related_name='investments')
    invested_amount = models.PositiveIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    total_earned = models.PositiveIntegerField(default=0)
    last_payout_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"
