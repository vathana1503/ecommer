from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from functools import wraps


def role_required(allowed_roles):
    """
    Decorator to restrict access based on user roles
    allowed_roles: list of roles that can access the view
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            # Ensure user has a profile
            if not hasattr(request.user, 'profile'):
                messages.error(request, 'Profile not found. Please contact administrator.')
                return redirect('accounts:profile')
            
            user_role = request.user.profile.role
            
            if user_role in allowed_roles or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, f'Access denied. This page requires {" or ".join(allowed_roles)} role.')
                return redirect('store:home')
        
        return wrapped_view
    return decorator


def customer_required(view_func):
    """Decorator for customer-only views"""
    return role_required(['customer'])(view_func)


def staff_required(view_func):
    """Decorator for staff-only views"""
    return role_required(['staff', 'owner'])(view_func)


def owner_required(view_func):
    """Decorator for owner-only views"""
    return role_required(['owner'])(view_func)


def staff_or_owner_required(view_func):
    """Decorator for staff or owner views"""
    return role_required(['staff', 'owner'])(view_func)


def check_user_role_access(user, required_roles):
    """
    Helper function to check if user has required role access
    """
    if not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
        
    if not hasattr(user, 'profile'):
        return False
    
    return user.profile.role in required_roles


def can_access_product_management(user):
    """Check if user can access product management"""
    return check_user_role_access(user, ['staff', 'owner'])


def can_access_admin_panel(user):
    """Check if user can access admin panel"""
    return check_user_role_access(user, ['owner']) or user.is_superuser


def can_access_dashboard(user):
    """Check if user can access dashboard"""
    return check_user_role_access(user, ['staff', 'owner'])
