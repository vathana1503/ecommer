from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal


class SalesReport(models.Model):
    """
    Model to store generated sales reports for caching and history
    """
    REPORT_TYPE_CHOICES = [
        ('daily', 'Daily Report'),
        ('weekly', 'Weekly Report'),
        ('monthly', 'Monthly Report'),
        ('yearly', 'Yearly Report'),
        ('custom', 'Custom Date Range'),
    ]
    
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Report Data
    total_orders = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_items_sold = models.PositiveIntegerField(default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Status tracking
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generated_reports')
    generated_at = models.DateTimeField(auto_now_add=True)
    is_cached = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-generated_at']
        unique_together = ['report_type', 'start_date', 'end_date']
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.start_date} to {self.end_date}"


class ProductSalesReport(models.Model):
    """
    Model to track product-specific sales data
    """
    sales_report = models.ForeignKey(SalesReport, on_delete=models.CASCADE, related_name='product_sales')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    
    quantity_sold = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    average_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    class Meta:
        unique_together = ['sales_report', 'product']
    
    def __str__(self):
        return f"{self.product.name} - {self.quantity_sold} sold"


class CustomerSalesReport(models.Model):
    """
    Model to track customer-specific sales data
    """
    sales_report = models.ForeignKey(SalesReport, on_delete=models.CASCADE, related_name='customer_sales')
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    
    total_orders = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    class Meta:
        unique_together = ['sales_report', 'customer']
    
    def __str__(self):
        return f"{self.customer.username} - {self.total_orders} orders"
