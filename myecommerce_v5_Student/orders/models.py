from django.db import models
from django.contrib.auth.models import User
from products.models import Product
from decimal import Decimal
import uuid
from django.utils import timezone


class Order(models.Model):
    """
    Order model to store customer orders
    """
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    order_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    
    # Billing Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    
    # Shipping Information
    shipping_first_name = models.CharField(max_length=100, blank=True)
    shipping_last_name = models.CharField(max_length=100, blank=True)
    shipping_phone = models.CharField(max_length=20, blank=True)
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20)
    shipping_country = models.CharField(max_length=100, default='Cambodia')
    
    # Order Details
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Notes
    order_notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_id} - {self.user.username}"

    @property
    def grand_total(self):
        """Calculate grand total including shipping and tax"""
        from decimal import Decimal
        total = Decimal(str(self.total_amount)) if self.total_amount else Decimal('0.00')
        shipping = Decimal(str(self.shipping_cost)) if self.shipping_cost else Decimal('0.00')
        tax = Decimal(str(self.tax_amount)) if self.tax_amount else Decimal('0.00')
        return total + shipping + tax

    @property
    def total_items(self):
        """Calculate total number of items in the order"""
        return sum(item.quantity for item in self.order_items.all())


class OrderItem(models.Model):
    """
    Individual items within an order
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of order
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def total_price(self):
        """Calculate total price for this item"""
        return self.quantity * self.price


class ShippingMethod(models.Model):
    """
    Available shipping methods
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_days = models.PositiveIntegerField(help_text="Estimated delivery days")
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - ${self.cost}"


class Coupon(models.Model):
    """
    Discount coupons
    """
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]

    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    maximum_uses = models.PositiveIntegerField(default=1)
    used_count = models.PositiveIntegerField(default=0)
    
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code

    @property
    def is_valid(self):
        """Check if coupon is valid"""
        now = timezone.now()
        return (
            self.is_active and
            self.valid_from <= now <= self.valid_to and
            self.used_count < self.maximum_uses
        )

    def calculate_discount(self, amount):
        """Calculate discount amount"""
        if not self.is_valid or amount < self.minimum_amount:
            return Decimal('0.00')
        
        if self.discount_type == 'percentage':
            return amount * (self.discount_value / 100)
        else:
            return min(self.discount_value, amount)


class OrderCoupon(models.Model):
    """
    Track coupon usage in orders
    """
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='coupon_usage')
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='orders')
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.order.order_id} - Coupon {self.coupon.code}"
