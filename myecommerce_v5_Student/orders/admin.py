from django.contrib import admin
from .models import Order, OrderItem, ShippingMethod, Coupon, OrderCoupon


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['total_price']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'user', 'status', 'grand_total', 'created_at']
    list_filter = ['status', 'created_at', 'shipping_country']
    search_fields = ['order_id', 'user__username', 'user__email', 'first_name', 'last_name', 'email']
    readonly_fields = ['order_id', 'created_at', 'updated_at', 'grand_total', 'total_items']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_id', 'user', 'status', 'order_notes')
        }),
        ('Customer Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('Shipping Information', {
            'fields': ('shipping_address', 'shipping_city', 'shipping_state', 'shipping_postal_code', 'shipping_country')
        }),
        ('Order Totals', {
            'fields': ('total_amount', 'shipping_cost', 'tax_amount', 'grand_total', 'total_items')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price', 'total_price']
    list_filter = ['created_at']
    search_fields = ['order__order_id', 'product__name']
    readonly_fields = ['total_price']


@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'cost', 'estimated_days', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'discount_value', 'used_count', 'maximum_uses', 'is_active']
    list_filter = ['discount_type', 'is_active', 'valid_from', 'valid_to']
    search_fields = ['code']
    readonly_fields = ['used_count']


@admin.register(OrderCoupon)
class OrderCouponAdmin(admin.ModelAdmin):
    list_display = ['order', 'coupon', 'discount_amount', 'created_at']
    list_filter = ['created_at']
    search_fields = ['order__order_id', 'coupon__code']
