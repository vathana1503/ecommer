from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Sales Reports
    path('sales/', views.sales_report, name='sales_report'),
    path('products/', views.product_report, name='product_report'),
    path('customers/', views.customer_report, name='customer_report'),
    
    # Export functionality
    path('export/', views.export_report, name='export_report'),
]
