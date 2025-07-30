from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    # Cart URLs
    path('', views.cart_view, name='cart_view'),
    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('clear/', views.clear_cart, name='clear_cart'),
    
    # Wishlist URLs
    path('wishlist/', views.wishlist_view, name='wishlist_view'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/move-to-cart/<int:product_id>/', views.move_to_cart, name='move_to_cart'),
    
    # AJAX URLs
    path('api/count/', views.cart_count, name='cart_count'),
    path('api/quick-add/', views.quick_add_to_cart, name='quick_add_to_cart'),
]
