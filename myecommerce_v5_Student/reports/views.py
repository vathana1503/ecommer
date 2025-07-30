from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json

from accounts.decorators import owner_required
from orders.models import Order, OrderItem
from products.models import Product
from .models import SalesReport, ProductSalesReport, CustomerSalesReport
from .forms import ReportFilterForm


@login_required
@owner_required
def dashboard(request):
    """
    Main dashboard view for reports
    """
    # Quick stats for the last 30 days
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    
    recent_stats = {
        'total_orders': Order.objects.filter(created_at__date__gte=thirty_days_ago).count(),
        'total_revenue': Order.objects.filter(
            created_at__date__gte=thirty_days_ago,
            status='delivered'
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00'),
        'average_order_value': Order.objects.filter(
            created_at__date__gte=thirty_days_ago,
            status='delivered'
        ).aggregate(Avg('total_amount'))['total_amount__avg'] or Decimal('0.00'),
        'total_customers': Order.objects.filter(
            created_at__date__gte=thirty_days_ago
        ).values('user').distinct().count(),
    }
    
    # Recent orders
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]
    
    # Top selling products (last 30 days)
    top_products = OrderItem.objects.filter(
        order__created_at__date__gte=thirty_days_ago,
        order__status='delivered'
    ).values('product__name').annotate(
        total_sold=Sum('quantity'),
        total_revenue=Sum('price')
    ).order_by('-total_sold')[:5]
    
    context = {
        'stats': recent_stats,
        'recent_orders': recent_orders,
        'top_products': top_products,
        'thirty_days_ago': thirty_days_ago,
    }
    
    return render(request, 'reports/dashboard.html', context)


@login_required
@owner_required
def sales_report(request):
    """
    Generate and display sales reports
    """
    form = ReportFilterForm(request.GET or None)
    report_data = None
    
    if form.is_valid():
        report_type = form.cleaned_data['report_type']
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
        
        # Generate the report
        report_data = generate_sales_report(report_type, start_date, end_date, request.user)
    
    context = {
        'form': form,
        'report_data': report_data,
    }
    
    return render(request, 'reports/sales_report.html', context)


@login_required
@owner_required
def product_report(request):
    """
    Product-specific sales report
    """
    form = ReportFilterForm(request.GET or None)
    product_data = None
    
    if form.is_valid():
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
        
        # Generate product sales data
        product_data = OrderItem.objects.filter(
            order__created_at__date__range=[start_date, end_date],
            order__status='delivered'
        ).values(
            'product__name',
            'product__id'
        ).annotate(
            total_sold=Sum('quantity'),
            total_revenue=Sum('price'),
            average_price=Avg('price')
        ).order_by('-total_sold')
    
    context = {
        'form': form,
        'product_data': product_data,
    }
    
    return render(request, 'reports/product_report.html', context)


@login_required
@owner_required
def customer_report(request):
    """
    Customer-specific sales report
    """
    form = ReportFilterForm(request.GET or None)
    customer_data = None
    
    if form.is_valid():
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
        
        # Generate customer sales data
        customer_data = Order.objects.filter(
            created_at__date__range=[start_date, end_date],
            status='delivered'
        ).values(
            'user__username',
            'user__email',
            'user__first_name',
            'user__last_name'
        ).annotate(
            total_orders=Count('id'),
            total_spent=Sum('total_amount'),
            average_order_value=Avg('total_amount')
        ).order_by('-total_spent')
    
    context = {
        'form': form,
        'customer_data': customer_data,
    }
    
    return render(request, 'reports/customer_report.html', context)


@login_required
@owner_required
def export_report(request):
    """
    Export reports as CSV or JSON
    """
    if request.method == 'POST':
        data = json.loads(request.body)
        report_type = data.get('report_type')
        export_format = data.get('format', 'csv')
        start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()
        
        if export_format == 'csv':
            return export_csv_report(report_type, start_date, end_date)
        elif export_format == 'json':
            return export_json_report(report_type, start_date, end_date)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


def generate_sales_report(report_type, start_date, end_date, user):
    """
    Generate comprehensive sales report data
    """
    # Filter orders within date range
    orders = Order.objects.filter(
        created_at__date__range=[start_date, end_date],
        status='delivered'
    )
    
    # Calculate metrics
    total_orders = orders.count()
    total_revenue = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    average_order_value = orders.aggregate(Avg('total_amount'))['total_amount__avg'] or Decimal('0.00')
    
    # Total items sold
    total_items_sold = OrderItem.objects.filter(
        order__in=orders
    ).aggregate(Sum('quantity'))['quantity__sum'] or 0
    
    # Order status breakdown (include all statuses for comparison, but only delivered orders contribute to revenue)
    status_breakdown = Order.objects.filter(
        created_at__date__range=[start_date, end_date]
    ).values('status').annotate(
        count=Count('id'),
        revenue=Sum('total_amount', filter=Q(status='delivered'))
    ).order_by('status')
    
    # Daily sales data for charts (only delivered orders for revenue)
    daily_sales = Order.objects.filter(
        created_at__date__range=[start_date, end_date]
    ).extra(
        select={'day': 'date(created_at)'}
    ).values('day').annotate(
        orders_count=Count('id'),
        revenue=Sum('total_amount', filter=Q(status='delivered'))
    ).order_by('day')
    
    return {
        'report_type': report_type,
        'start_date': start_date,
        'end_date': end_date,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'average_order_value': average_order_value,
        'total_items_sold': total_items_sold,
        'status_breakdown': status_breakdown,
        'daily_sales': list(daily_sales),
    }


def export_csv_report(report_type, start_date, end_date):
    """
    Export report data as CSV
    """
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="sales_report_{start_date}_{end_date}.csv"'
    
    writer = csv.writer(response)
    
    if report_type == 'sales':
        # Sales report CSV
        writer.writerow(['Date', 'Orders', 'Revenue', 'Items Sold'])
        
        orders = Order.objects.filter(
            created_at__date__range=[start_date, end_date],
            status='delivered'
        ).extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(
            orders_count=Count('id'),
            revenue=Sum('total_amount'),
            items_sold=Sum('order_items__quantity')
        ).order_by('day')
        
        for order in orders:
            writer.writerow([
                order['day'],
                order['orders_count'],
                order['revenue'],
                order['items_sold'] or 0
            ])
    
    return response


def export_json_report(report_type, start_date, end_date):
    """
    Export report data as JSON
    """
    report_data = generate_sales_report(report_type, start_date, end_date, None)
    
    # Convert Decimal objects to strings for JSON serialization
    def decimal_default(obj):
        if isinstance(obj, Decimal):
            return str(obj)
        raise TypeError
    
    response = HttpResponse(
        json.dumps(report_data, default=decimal_default, indent=2),
        content_type='application/json'
    )
    response['Content-Disposition'] = f'attachment; filename="sales_report_{start_date}_{end_date}.json"'
    
    return response
