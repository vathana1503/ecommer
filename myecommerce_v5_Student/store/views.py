from django.shortcuts import render
from products.models import Product
from accounts.decorators import staff_or_owner_required

def home(request):
    """Store front page displaying products - accessible to everyone"""
    products = Product.objects.all()
    return render(request, 'home.html', {'products': products})

@staff_or_owner_required
def dashboard(request):
    """Dashboard for store management - staff and owner only"""
    products = Product.objects.all()
    return render(request, 'dashboard.html', {'products': products})