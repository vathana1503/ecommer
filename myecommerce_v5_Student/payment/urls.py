from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    # Checkout and payment
    path('checkout/', views.checkout, name='checkout'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('payment/process/<uuid:order_id>/', views.payment_process, name='payment_process'),
    path('payment/callback/', views.payment_callback, name='payment_callback'),
    
    # Orders
    path('order/success/<uuid:order_id>/', views.order_success, name='order_success'),
    path('order/<uuid:order_id>/', views.order_detail, name='order_detail'),
    path('orders/', views.order_list, name='order_list'),
    path('order/<uuid:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('order/<uuid:order_id>/mark-delivered/', views.mark_order_delivered, name='mark_order_delivered'),
    path('order/<uuid:order_id>/track/', views.order_tracking, name='order_tracking'),
    
    # Admin views
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/orders/', views.admin_order_list, name='admin_order_list'),
    path('admin/order/<uuid:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    path('admin/order/<uuid:order_id>/update-status/', views.admin_update_order_status, name='admin_update_order_status'),
    path('admin/orders/bulk-update/', views.admin_bulk_update_orders, name='admin_bulk_update_orders'),
]
