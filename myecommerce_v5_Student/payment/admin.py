from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_id', 'order', 'payment_method', 'status', 'amount', 'created_at']
    list_filter = ['payment_method', 'status', 'created_at']
    search_fields = ['payment_id', 'order__order_id', 'transaction_id']
    readonly_fields = ['payment_id', 'created_at', 'updated_at', 'completed_at']
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('payment_id', 'order', 'payment_method', 'status', 'amount')
        }),
        ('Transaction Details', {
            'fields': ('transaction_id', 'gateway_response')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        })
    )
