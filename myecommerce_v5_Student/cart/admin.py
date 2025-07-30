from django.contrib import admin
from .models import Cart, CartItem, WishList


class CartItemInline(admin.TabularInline):
    """Inline admin for cart items"""
    model = CartItem
    extra = 0
    readonly_fields = ('total_price', 'added_at')

    def total_price(self, obj):
        return f"${obj.total_price:.2f}" if obj.id else "-"
    total_price.short_description = "Total Price"


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Admin interface for Cart model"""
    list_display = ('user', 'total_items', 'total_price_display', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'total_items', 'total_price_display')
    inlines = [CartItemInline]

    def total_price_display(self, obj):
        return f"${obj.total_price:.2f}"
    total_price_display.short_description = "Total Price"


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """Admin interface for CartItem model"""
    list_display = ('cart', 'product', 'quantity', 'total_price_display', 'added_at')
    list_filter = ('added_at', 'product__category')
    search_fields = ('cart__user__username', 'product__name')
    readonly_fields = ('total_price_display', 'added_at')

    def total_price_display(self, obj):
        return f"${obj.total_price:.2f}"
    total_price_display.short_description = "Total Price"


@admin.register(WishList)
class WishListAdmin(admin.ModelAdmin):
    """Admin interface for WishList model"""
    list_display = ('user', 'total_items_display', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__email')
    filter_horizontal = ('products',)
    readonly_fields = ('created_at', 'total_items_display')

    def total_items_display(self, obj):
        return obj.total_items
    total_items_display.short_description = "Total Items"
