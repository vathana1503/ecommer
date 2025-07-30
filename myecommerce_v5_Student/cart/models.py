from django.db import models
from django.contrib.auth.models import User
from products.models import Product
from decimal import Decimal


class Cart(models.Model):
    """
    Shopping cart model for storing user's cart information
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

    @property
    def total_items(self):
        """Calculate total number of items in cart"""
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self):
        """Calculate total price of all items in cart"""
        total = sum(item.total_price for item in self.items.all())
        return Decimal(str(total)) if total else Decimal('0.00')

    def clear(self):
        """Clear all items from cart"""
        self.items.all().delete()


class CartItem(models.Model):
    """
    Individual items in a shopping cart
    """
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def total_price(self):
        """Calculate total price for this cart item"""
        return Decimal(str(self.product.price)) * self.quantity

    def save(self, *args, **kwargs):
        """Override save to ensure quantity doesn't exceed available stock"""
        if self.quantity > self.product.qty:
            raise ValueError(f"Quantity cannot exceed available stock ({self.product.qty})")
        super().save(*args, **kwargs)


class WishList(models.Model):
    """
    Wishlist model for customers to save products for later
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wishlist')
    products = models.ManyToManyField(Product, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Wishlist for {self.user.username}"

    @property
    def total_items(self):
        """Get total number of items in wishlist"""
        return self.products.count()
