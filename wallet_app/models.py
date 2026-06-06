from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_deposit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_withdrawal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - ₹{self.balance}"

    class Meta:
        ordering = ['-created_at']


class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    investment_amount = models.DecimalField(max_digits=12, decimal_places=2)
    daily_return = models.DecimalField(max_digits=12, decimal_places=2)
    duration_days = models.PositiveIntegerField()
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']


class Deposit(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deposits')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    razorpay_order_id = models.CharField(max_length=255, blank=True, db_index=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True, db_index=True)
    razorpay_signature = models.CharField(max_length=500, blank=True)
    upi_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - ₹{self.amount} ({self.status})"

    class Meta:
        ordering = ['-created_at']


class Purchase(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='purchases')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    purchase_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')

    def __str__(self):
        return f"{self.user.username} - {self.product.name} - ₹{self.amount}"

    class Meta:
        ordering = ['-purchase_date']


class Transaction(models.Model):
    TYPE_CHOICES = [
        ('DEPOSIT', 'Deposit'),
        ('PURCHASE', 'Purchase'),
        ('REFUND', 'Refund'),
        ('WITHDRAWAL', 'Withdrawal'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    txn_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reference_id = models.CharField(max_length=255, blank=True)
    deposit = models.ForeignKey(Deposit, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    purchase = models.ForeignKey(Purchase, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.txn_type} - ₹{self.amount}"

    class Meta:
        ordering = ['-created_at']
