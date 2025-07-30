from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import UserProfile


class UserProfileSignalTest(TestCase):
    """
    Test cases to verify that UserProfile is automatically created
    when a new User is created using Django signals
    """
    
    def test_user_profile_created_on_user_creation(self):
        """
        Test that a UserProfile is automatically created when a User is created
        """
        # Create a new user
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Check that a UserProfile was automatically created
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsInstance(user.profile, UserProfile)
        self.assertEqual(user.profile.user, user)
        self.assertEqual(user.profile.role, 'customer')  # Default role
    
    def test_user_profile_saved_on_user_update(self):
        """
        Test that UserProfile is saved when User is updated
        """
        # Create a user (profile should be auto-created)
        user = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        # Update the user's profile
        user.profile.phone_number = '123-456-7890'
        user.save()  # This should trigger the save signal
        
        # Refresh from database
        user.refresh_from_db()
        
        # Check that the profile was saved
        self.assertEqual(user.profile.phone_number, '123-456-7890')
    
    def test_multiple_users_have_separate_profiles(self):
        """
        Test that multiple users each get their own separate profiles
        """
        # Create multiple users
        user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123'
        )
        
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
        
        # Check that each user has their own profile
        self.assertNotEqual(user1.profile.id, user2.profile.id)
        self.assertEqual(user1.profile.user, user1)
        self.assertEqual(user2.profile.user, user2)
        
        # Check that we have exactly 2 profiles
        self.assertEqual(UserProfile.objects.count(), 2)

    def test_superuser_gets_owner_role(self):
        """
        Test that superusers automatically get 'owner' role
        """
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.assertEqual(user.profile.role, 'owner')
        self.assertTrue(user.profile.is_owner())
        self.assertTrue(user.profile.can_access_admin())

    def test_staff_user_gets_staff_role(self):
        """
        Test that staff users automatically get 'staff' role
        """
        user = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='staffpass123',
            is_staff=True
        )
        
        self.assertEqual(user.profile.role, 'staff')
        self.assertTrue(user.profile.is_staff_member())
        self.assertTrue(user.profile.can_manage_products())


class RoleBasedAccessTest(TestCase):
    """
    Test cases for role-based access control
    """
    
    def setUp(self):
        self.client = Client()
        
        # Create users with different roles
        self.customer = User.objects.create_user(
            username='customer',
            password='testpass123'
        )
        
        self.staff = User.objects.create_user(
            username='staff',
            password='testpass123',
            is_staff=True
        )
        
        self.owner = User.objects.create_superuser(
            username='owner',
            email='owner@example.com',
            password='testpass123'
        )
    
    def test_home_page_accessible_to_all(self):
        """Test that home page is accessible to all users"""
        # Anonymous user
        response = self.client.get(reverse('store:home'))
        self.assertEqual(response.status_code, 200)
        
        # Customer
        self.client.login(username='customer', password='testpass123')
        response = self.client.get(reverse('store:home'))
        self.assertEqual(response.status_code, 200)
        
        # Staff
        self.client.login(username='staff', password='testpass123')
        response = self.client.get(reverse('store:home'))
        self.assertEqual(response.status_code, 200)
        
        # Owner
        self.client.login(username='owner', password='testpass123')
        response = self.client.get(reverse('store:home'))
        self.assertEqual(response.status_code, 200)
    
    def test_dashboard_access_control(self):
        """Test that only staff and owners can access dashboard"""
        # Customer cannot access dashboard
        self.client.login(username='customer', password='testpass123')
        response = self.client.get(reverse('store:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect
        
        # Staff can access dashboard
        self.client.login(username='staff', password='testpass123')
        response = self.client.get(reverse('store:dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Owner can access dashboard
        self.client.login(username='owner', password='testpass123')
        response = self.client.get(reverse('store:dashboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_product_management_access_control(self):
        """Test that only staff and owners can manage products"""
        # Customer cannot add products
        self.client.login(username='customer', password='testpass123')
        response = self.client.get(reverse('products:add_product'))
        self.assertEqual(response.status_code, 302)  # Redirect
        
        # Staff can add products
        self.client.login(username='staff', password='testpass123')
        response = self.client.get(reverse('products:add_product'))
        self.assertEqual(response.status_code, 200)
        
        # Owner can add products
        self.client.login(username='owner', password='testpass123')
        response = self.client.get(reverse('products:add_product'))
        self.assertEqual(response.status_code, 200)
