from django.db import models
from django.contrib.auth.models import User
from orders.models import Order
from decimal import Decimal
import uuid
from django.utils import timezone


class Payment(models.Model):
    """
    Payment model to track payment transactions
    """
    PAYMENT_METHOD_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('cash_on_delivery', 'Cash on Delivery'),
        ('aba_pay', 'ABA Pay'),
        ('wing', 'Wing'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    payment_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Payment gateway response data
    gateway_response = models.JSONField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Payment {self.payment_id} - {self.order.order_id}"

    def mark_completed(self):
        """Mark payment as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
        
        # Update order status
        self.order.status = 'confirmed'
        self.order.save()
