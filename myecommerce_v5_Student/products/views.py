from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Product, Category
from .forms import ProductForm
from accounts.decorators import staff_or_owner_required

def product_list(request):
    """View to display all products - accessible to everyone"""
    products = Product.objects.all()
    categories = Category.objects.all()
    
    # Filter by category if specified
    category_id = request.GET.get('category')
    selected_category = None
    if category_id:
        try:
            selected_category = Category.objects.get(id=category_id)
            products = products.filter(category=selected_category)
        except Category.DoesNotExist:
            pass
    
    context = {
        'products': products,
        'categories': categories,
        'selected_category': selected_category,
    }
    return render(request, 'products/product_list.html', context)

@staff_or_owner_required
def add_product(request):
    """View to add a new product - staff and owner only"""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product added successfully!')
            return redirect('products:product_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductForm()
    return render(request, 'products/add_product.html', {'form': form})

def product_detail(request, product_id):
    """View to display product details - accessible to everyone"""
    product = get_object_or_404(Product, id=product_id)
    
    # Get related products (same category, excluding current product)
    related_products = Product.objects.filter(
        category=product.category
    ).exclude(id=product.id)[:4]  # Limit to 4 related products
    
    # If no related products in same category, get random products
    if not related_products and product.category:
        related_products = Product.objects.exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'related_products': related_products,
    }
    
    return render(request, 'products/product_detail.html', context)

@staff_or_owner_required
def edit_product(request, product_id):
    """View to edit an existing product - staff and owner only"""
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('products:product_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductForm(instance=product)
    return render(request, 'products/edit_product.html', {'form': form, 'product': product})

@staff_or_owner_required
def delete_product(request, product_id):
    """View to delete a product - staff and owner only"""
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
        return redirect('products:product_list')
    return render(request, 'products/delete_product.html', {'product': product})
