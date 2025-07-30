from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from products.models import Product, Category
from cart.models import Cart, CartItem, WishList


class CartTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create a category and product
        self.category = Category.objects.create(
            name='Test Category',
            description='Test category description'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category,
            description='Test product description',
            price=19.99,
            qty=10
        )

    def test_cart_creation(self):
        """Test that a cart is created when user is authenticated"""
        self.client.login(username='testuser', password='testpass123')
        
        # Access cart view
        response = self.client.get(reverse('cart:cart_view'))
        self.assertEqual(response.status_code, 200)
        
        # Check that cart was created
        self.assertTrue(Cart.objects.filter(user=self.user).exists())

    def test_add_to_cart(self):
        """Test adding a product to cart"""
        self.client.login(username='testuser', password='testpass123')
        
        # Add product to cart
        response = self.client.post(reverse('cart:add_to_cart', args=[self.product.id]), {
            'quantity': 2
        })
        
        # Check redirect
        self.assertEqual(response.status_code, 302)
        
        # Check cart item was created
        cart = Cart.objects.get(user=self.user)
        cart_item = CartItem.objects.get(cart=cart, product=self.product)
        self.assertEqual(cart_item.quantity, 2)

    def test_cart_total_calculation(self):
        """Test cart total price and items calculation"""
        self.client.login(username='testuser', password='testpass123')
        
        # Add product to cart
        self.client.post(reverse('cart:add_to_cart', args=[self.product.id]), {
            'quantity': 3
        })
        
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.total_items, 3)
        self.assertEqual(float(cart.total_price), 59.97)  # 3 * 19.99

    def test_wishlist_functionality(self):
        """Test wishlist add/remove functionality"""
        self.client.login(username='testuser', password='testpass123')
        
        # Add to wishlist
        response = self.client.post(reverse('cart:add_to_wishlist', args=[self.product.id]))
        self.assertEqual(response.status_code, 302)
        
        # Check wishlist
        wishlist = WishList.objects.get(user=self.user)
        self.assertTrue(self.product in wishlist.products.all())
        
        # Remove from wishlist
        response = self.client.post(reverse('cart:remove_from_wishlist', args=[self.product.id]))
        self.assertEqual(response.status_code, 302)
        
        wishlist.refresh_from_db()
        self.assertFalse(self.product in wishlist.products.all())

    def test_stock_validation(self):
        """Test that cart respects product stock limits"""
        self.client.login(username='testuser', password='testpass123')
        
        # Try to add more than available stock
        response = self.client.post(reverse('cart:add_to_cart', args=[self.product.id]), {
            'quantity': 15  # More than the 10 in stock
        })
        
        # Should redirect back with error message
        self.assertEqual(response.status_code, 302)
        
        # Check that cart item wasn't created with invalid quantity
        self.assertFalse(CartItem.objects.filter(cart__user=self.user, product=self.product).exists())
