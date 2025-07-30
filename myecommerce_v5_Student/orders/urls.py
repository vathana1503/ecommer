from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Order management URLs
    path('', views.order_list, name='order_list'),
    path('<uuid:order_id>/', views.order_detail, name='order_detail'),
    path('<uuid:order_id>/mark-delivered/', views.mark_order_delivered, name='mark_order_delivered'),
    path('pending-count/', views.get_pending_orders_count, name='pending_orders_count'),
    
    # Admin URLs
    path('admin/', views.admin_order_list, name='admin_order_list'),
    path('admin/<uuid:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    path('admin/<uuid:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
