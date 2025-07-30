from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.db import transaction
from django.db import models
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from decimal import Decimal
import json
import uuid

from orders.models import Order, OrderItem, ShippingMethod, Coupon, OrderCoupon
from .models import Payment
from .forms import CheckoutForm, PaymentForm, CouponForm
from cart.models import Cart, CartItem
from products.models import Product


@login_required
def checkout(request):
    """
    Checkout page for completing the order
    """
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.select_related('product')
    except Cart.DoesNotExist:
        messages.error(request, "Your cart is empty.")
        return redirect('cart:cart_detail')

    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('cart:cart_detail')

    shipping_methods = ShippingMethod.objects.filter(is_active=True)
    
    if request.method == 'POST':
        checkout_form = CheckoutForm(request.POST)
        payment_form = PaymentForm(request.POST)
        
        if checkout_form.is_valid() and payment_form.is_valid():
            try:
                with transaction.atomic():
                    # Save billing and shipping information if requested
                    if request.POST.get('save_billing_info'):
                        profile = request.user.profile
                        profile.billing_first_name = checkout_form.cleaned_data['first_name']
                        profile.billing_last_name = checkout_form.cleaned_data['last_name']
                        profile.billing_phone = checkout_form.cleaned_data['phone']
                        profile.save()
                    
                    if request.POST.get('save_shipping_info'):
                        profile = request.user.profile
                        profile.shipping_first_name = checkout_form.cleaned_data.get('shipping_first_name', '')
                        profile.shipping_last_name = checkout_form.cleaned_data.get('shipping_last_name', '')
                        profile.shipping_phone = checkout_form.cleaned_data.get('shipping_phone', '')
                        profile.shipping_address = checkout_form.cleaned_data['shipping_address']
                        profile.shipping_city = checkout_form.cleaned_data['shipping_city']
                        profile.shipping_state = checkout_form.cleaned_data['shipping_state']
                        profile.shipping_postal_code = checkout_form.cleaned_data['shipping_postal_code']
                        profile.shipping_country = checkout_form.cleaned_data['shipping_country']
                        profile.save()
                    
                    # Create order
                    order = checkout_form.save(commit=False)
                    order.user = request.user
                    order.total_amount = Decimal(str(cart.total_price))
                    
                    # Get shipping cost
                    shipping_method = checkout_form.cleaned_data['shipping_method']
                    order.shipping_cost = Decimal(str(shipping_method.cost))
                    
                    # Apply coupon if provided
                    coupon_code = checkout_form.cleaned_data.get('coupon_code')
                    discount_amount = Decimal('0.00')
                    
                    if coupon_code:
                        try:
                            coupon = Coupon.objects.get(code=coupon_code)
                            if coupon.is_valid:
                                discount_amount = coupon.calculate_discount(order.total_amount)
                                order.total_amount -= discount_amount
                        except Coupon.DoesNotExist:
                            pass
                    
                    order.save()
                    
                    # Create order items
                    for cart_item in cart_items:
                        OrderItem.objects.create(
                            order=order,
                            product=cart_item.product,
                            quantity=cart_item.quantity,
                            price=cart_item.product.price
                        )
                    
                    # Create coupon usage record if coupon was applied
                    if coupon_code and discount_amount > 0:
                        coupon = Coupon.objects.get(code=coupon_code)
                        OrderCoupon.objects.create(
                            order=order,
                            coupon=coupon,
                            discount_amount=discount_amount
                        )
                        coupon.used_count += 1
                        coupon.save()
                    
                    # Create payment
                    payment = payment_form.save(commit=False)
                    payment.order = order
                    payment.amount = order.grand_total
                    payment.save()
                    
                    # Clear cart
                    cart.clear()
                    
                    # Process payment based on method
                    if payment.payment_method == 'cash_on_delivery':
                        payment.status = 'pending'
                        payment.save()
                        
                        messages.success(request, f"Order placed successfully! Order ID: {order.order_id}")
                        return redirect('payment:order_success', order_id=order.order_id)
                    
                    elif payment.payment_method in ['bank_transfer', 'aba_pay', 'wing']:
                        # For digital payment methods, mark as pending
                        payment.status = 'pending'
                        payment.transaction_id = str(uuid.uuid4())
                        payment.save()
                        
                        messages.success(request, f"Order placed successfully! Order ID: {order.order_id}")
                        messages.info(request, f"Please complete your {payment.get_payment_method_display()} payment.")
                        return redirect('payment:order_success', order_id=order.order_id)
                    
                    else:
                        # Fallback for other payment methods
                        payment.status = 'pending'
                        payment.save()
                        
                        messages.success(request, f"Order placed successfully! Order ID: {order.order_id}")
                        return redirect('payment:order_success', order_id=order.order_id)
                        
            except Exception as e:
                import traceback
                print(f"Checkout error: {e}")
                print(f"Traceback: {traceback.format_exc()}")
                messages.error(request, "An error occurred while processing your order. Please try again.")
    else:
        # Pre-populate form with saved information if available
        initial_data = {}
        profile = request.user.profile
        
        # Pre-populate billing information
        if profile.billing_first_name:
            initial_data.update({
                'first_name': profile.billing_first_name,
                'last_name': profile.billing_last_name,
                'phone': profile.billing_phone,
            })
        
        # Pre-populate shipping information
        if profile.shipping_address:
            initial_data.update({
                'shipping_first_name': profile.shipping_first_name,
                'shipping_last_name': profile.shipping_last_name,
                'shipping_phone': profile.shipping_phone,
                'shipping_address': profile.shipping_address,
                'shipping_city': profile.shipping_city,
                'shipping_state': profile.shipping_state,
                'shipping_postal_code': profile.shipping_postal_code,
                'shipping_country': profile.shipping_country,
            })
        
        checkout_form = CheckoutForm(initial=initial_data)
        payment_form = PaymentForm()

    context = {
        'checkout_form': checkout_form,
        'payment_form': payment_form,
        'cart': cart,
        'cart_items': cart_items,
        'shipping_methods': shipping_methods,
    }
    return render(request, 'payment/checkout.html', context)


@require_POST
@login_required
def apply_coupon(request):
    """
    Apply coupon code via AJAX
    """
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Cart not found'})

    form = CouponForm(request.POST)
    if form.is_valid():
        code = form.cleaned_data['code']
        try:
            coupon = Coupon.objects.get(code=code)
            if coupon.is_valid:
                discount = coupon.calculate_discount(cart.total_price)
                return JsonResponse({
                    'success': True,
                    'discount': float(discount),
                    'new_total': float(cart.total_price - discount),
                    'message': f'Coupon "{code}" applied successfully!'
                })
            else:
                return JsonResponse({'success': False, 'error': 'Coupon is not valid or has expired'})
        except Coupon.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid coupon code'})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid form data'})


def order_success(request, order_id):
    """
    Order success page
    """
    try:
        order = Order.objects.get(order_id=order_id)
        # Allow access to order owner or staff
        if request.user.is_authenticated and (order.user == request.user or request.user.is_staff):
            return render(request, 'payment/order_success.html', {'order': order})
        else:
            raise Http404
    except Order.DoesNotExist:
        raise Http404


@login_required
def order_detail(request, order_id):
    """
    Order detail page
    """
    order = get_object_or_404(Order, order_id=order_id)
    
    # Check if user can access this order
    if order.user != request.user and not request.user.is_staff:
        raise Http404
    
    return render(request, 'payment/order_detail.html', {'order': order})


@login_required
def order_list(request):
    """
    List user's orders
    """
    orders = Order.objects.filter(user=request.user).prefetch_related('order_items__product')
    
    context = {
        'orders': orders,
    }
    return render(request, 'payment/order_list.html', context)


def payment_process(request, order_id):
    """
    Payment processing page for non-card payments
    """
    order = get_object_or_404(Order, order_id=order_id)
    
    # Check if user can access this order
    if request.user.is_authenticated and order.user != request.user:
        raise Http404
    
    try:
        payment = order.payment
    except Payment.DoesNotExist:
        raise Http404
    
    if payment.status == 'completed':
        return redirect('payment:order_success', order_id=order.order_id)
    
    context = {
        'order': order,
        'payment': payment,
    }
    return render(request, 'payment/payment_process.html', context)


@require_POST
def payment_callback(request):
    """
    Payment gateway callback endpoint
    """
    # This would handle payment gateway callbacks
    # Implementation depends on the payment gateway being used
    return JsonResponse({'status': 'received'})


@login_required
def cancel_order(request, order_id):
    """
    Cancel an order
    """
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    if order.status in ['pending', 'confirmed']:
        order.status = 'cancelled'
        order.save()
        
        # Update payment status
        try:
            payment = order.payment
            payment.status = 'cancelled'
            payment.save()
        except Payment.DoesNotExist:
            pass
        
        messages.success(request, f"Order {order.order_id} has been cancelled.")
    else:
        messages.error(request, "This order cannot be cancelled.")
    
    return redirect('payment:order_detail', order_id=order.order_id)


@login_required
@require_POST
def mark_order_delivered(request, order_id):
    """
    Mark an order as delivered by the customer
    """
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    
    # Only allow marking as delivered if order is shipped
    if order.status == 'shipped':
        order.status = 'delivered'
        order.save()
        
        # Update payment status to completed if not already
        try:
            payment = order.payment
            if payment.status != 'completed':
                payment.status = 'completed'
                payment.save()
        except Payment.DoesNotExist:
            pass
        
        messages.success(request, 
                        f"Order {order.order_id} has been marked as delivered. Thank you for your purchase! "
                        f"We hope you enjoyed your shopping experience.")
    else:
        messages.error(request, "This order cannot be marked as delivered. It must be shipped first.")
    
    return redirect('payment:order_detail', order_id=order.order_id)


def order_tracking(request, order_id):
    """
    Order tracking page
    """
    order = get_object_or_404(Order, order_id=order_id)
    
    # Allow access to order owner or with order ID
    if request.user.is_authenticated and order.user == request.user:
        pass  # User can access their own order
    elif request.user.is_staff:
        pass  # Staff can access any order
    else:
        # For guest checkout, you might want to implement email verification
        pass
    
    context = {
        'order': order,
    }
    return render(request, 'payment/order_tracking.html', context)


# def send_order_confirmation_email(order):
#     """
#     Send order confirmation email - DISABLED since email field was removed
#     """
#     subject = f'Order Confirmation - {order.order_id}'
#     html_message = render_to_string('payment/emails/order_confirmation.html', {
#         'order': order,
#         'site_name': 'MyEcommerce',
#     })
#     
#     try:
#         send_mail(
#             subject=subject,
#             message='',  # Plain text version can be added
#             html_message=html_message,
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             recipient_list=[order.email],
#             fail_silently=False,
#         )
#     except Exception as e:
#         print(f"Failed to send confirmation email: {e}")


# Admin views for managing orders
@login_required
def admin_order_list(request):
    """
    Admin view for managing orders
    """
    if not (request.user.is_staff or hasattr(request.user, 'profile') and request.user.profile.can_access_dashboard()):
        raise Http404
    
    orders = Order.objects.all().select_related('user').prefetch_related('order_items__product')
    
    # Filter by status if provided
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
    
    # Filter by search query
    search = request.GET.get('search')
    if search:
        orders = orders.filter(
            models.Q(order_id__icontains=search) |
            models.Q(user__username__icontains=search) |
            models.Q(user__email__icontains=search) |
            models.Q(first_name__icontains=search) |
            models.Q(last_name__icontains=search)
        )
    
    # Order by most recent first
    orders = orders.order_by('-created_at')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(orders, 20)  # Show 20 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'orders': page_obj,
        'status_choices': Order.ORDER_STATUS_CHOICES,
        'current_status': status,
        'search_query': search,
        'total_orders': orders.count(),
    }
    return render(request, 'payment/admin/order_list.html', context)


@login_required
@require_POST
def admin_update_order_status(request, order_id):
    """
    Update order status (admin only)
    """
    if not (request.user.is_staff or hasattr(request.user, 'profile') and request.user.profile.can_access_dashboard()):
        raise Http404
    
    order = get_object_or_404(Order, order_id=order_id)
    new_status = request.POST.get('status')
    
    if new_status in dict(Order.ORDER_STATUS_CHOICES):
        old_status = order.status
        order.status = new_status
        order.save()
        
        # Update payment status based on order status
        try:
            payment = order.payment
            if new_status == 'cancelled':
                payment.status = 'cancelled'
            elif new_status == 'delivered':
                payment.status = 'completed'
            elif new_status in ['confirmed', 'processing', 'shipped']:
                payment.status = 'processing'
            payment.save()
        except Payment.DoesNotExist:
            pass
        
        messages.success(request, f"Order {order.order_id} status updated from {old_status} to {new_status}.")
    else:
        messages.error(request, "Invalid status.")
    
    return redirect('payment:admin_order_list')


@login_required
def admin_order_detail(request, order_id):
    """
    Admin view for order details
    """
    if not (request.user.is_staff or hasattr(request.user, 'profile') and request.user.profile.can_access_dashboard()):
        raise Http404
    
    order = get_object_or_404(
        Order.objects.select_related('user', 'payment').prefetch_related('order_items__product'), 
        order_id=order_id
    )
    
    context = {
        'order': order,
        'status_choices': Order.ORDER_STATUS_CHOICES,
    }
    return render(request, 'payment/admin/order_detail.html', context)


@login_required
def admin_dashboard(request):
    """
    Admin dashboard with order statistics
    """
    if not (request.user.is_staff or hasattr(request.user, 'profile') and request.user.profile.can_access_dashboard()):
        raise Http404
    
    from django.db.models import Count, Sum
    from datetime import datetime, timedelta
    
    # Order statistics
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    processing_orders = Order.objects.filter(status__in=['confirmed', 'processing']).count()
    shipped_orders = Order.objects.filter(status='shipped').count()
    delivered_orders = Order.objects.filter(status='delivered').count()
    cancelled_orders = Order.objects.filter(status='cancelled').count()
    
    # Revenue statistics
    total_revenue = Order.objects.filter(status='delivered').aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0.00')
    
    # Recent orders (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_orders = Order.objects.filter(created_at__gte=thirty_days_ago).count()
    
    # Orders by status for chart
    orders_by_status = Order.objects.values('status').annotate(count=Count('id'))
    
    # Recent orders list
    latest_orders = Order.objects.select_related('user').order_by('-created_at')[:10]
    
    context = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'shipped_orders': shipped_orders,
        'delivered_orders': delivered_orders,
        'cancelled_orders': cancelled_orders,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'latest_orders': latest_orders,
        'orders_by_status': orders_by_status,
    }
    return render(request, 'payment/admin/dashboard.html', context)


@login_required
@require_POST
def admin_bulk_update_orders(request):
    """
    Bulk update order statuses
    """
    if not (request.user.is_staff or hasattr(request.user, 'profile') and request.user.profile.can_access_dashboard()):
        raise Http404
    
    order_ids = request.POST.getlist('order_ids')
    new_status = request.POST.get('bulk_status')
    
    if not order_ids:
        messages.error(request, "No orders selected.")
        return redirect('payment:admin_order_list')
    
    if new_status not in dict(Order.ORDER_STATUS_CHOICES):
        messages.error(request, "Invalid status.")
        return redirect('payment:admin_order_list')
    
    # Update orders
    updated_count = Order.objects.filter(order_id__in=order_ids).update(status=new_status)
    
    # Update corresponding payments
    for order_id in order_ids:
        try:
            order = Order.objects.get(order_id=order_id)
            payment = order.payment
            if new_status == 'cancelled':
                payment.status = 'cancelled'
            elif new_status == 'delivered':
                payment.status = 'completed'
            elif new_status in ['confirmed', 'processing', 'shipped']:
                payment.status = 'processing'
            payment.save()
        except (Order.DoesNotExist, Payment.DoesNotExist):
            continue
    
    messages.success(request, f"Updated {updated_count} orders to {new_status}.")
    return redirect('payment:admin_order_list')
