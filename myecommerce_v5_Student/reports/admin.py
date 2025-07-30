from django.contrib import admin
from .models import SalesReport, ProductSalesReport, CustomerSalesReport


@admin.register(SalesReport)
class SalesReportAdmin(admin.ModelAdmin):
    list_display = ['report_type', 'start_date', 'end_date', 'total_orders', 'total_revenue', 'generated_by', 'generated_at']
    list_filter = ['report_type', 'generated_at', 'is_cached']
    search_fields = ['generated_by__username']
    readonly_fields = ['generated_at']
    date_hierarchy = 'generated_at'
    
    fieldsets = (
        ('Report Information', {
            'fields': ('report_type', 'start_date', 'end_date')
        }),
        ('Report Data', {
            'fields': ('total_orders', 'total_revenue', 'total_items_sold', 'average_order_value')
        }),
        ('Meta Information', {
            'fields': ('generated_by', 'generated_at', 'is_cached')
        }),
    )


@admin.register(ProductSalesReport)
class ProductSalesReportAdmin(admin.ModelAdmin):
    list_display = ['product', 'sales_report', 'quantity_sold', 'total_revenue', 'average_price']
    list_filter = ['sales_report__report_type', 'sales_report__generated_at']
    search_fields = ['product__name']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'sales_report')


@admin.register(CustomerSalesReport)
class CustomerSalesReportAdmin(admin.ModelAdmin):
    list_display = ['customer', 'sales_report', 'total_orders', 'total_spent', 'average_order_value']
    list_filter = ['sales_report__report_type', 'sales_report__generated_at']
    search_fields = ['customer__username', 'customer__email']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('customer', 'sales_report')
