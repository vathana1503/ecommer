from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """
    Extended user profile model that automatically gets created
    when a new user registers using Django signals
    """
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('staff', 'Staff'),
        ('owner', 'Owner/Admin'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    
    # Saved billing information
    billing_first_name = models.CharField(max_length=100, blank=True, null=True)
    billing_last_name = models.CharField(max_length=100, blank=True, null=True)
    billing_email = models.EmailField(blank=True, null=True)
    billing_phone = models.CharField(max_length=20, blank=True, null=True)
    billing_address = models.TextField(blank=True, null=True)
    billing_city = models.CharField(max_length=100, blank=True, null=True)
    billing_state = models.CharField(max_length=100, blank=True, null=True)
    billing_postal_code = models.CharField(max_length=20, blank=True, null=True)
    billing_country = models.CharField(max_length=100, blank=True, null=True)
    
    # Saved shipping information
    shipping_first_name = models.CharField(max_length=100, blank=True, null=True)
    shipping_last_name = models.CharField(max_length=100, blank=True, null=True)
    shipping_phone = models.CharField(max_length=20, blank=True, null=True)
    shipping_address = models.TextField(blank=True, null=True)
    shipping_city = models.CharField(max_length=100, blank=True, null=True)
    shipping_state = models.CharField(max_length=100, blank=True, null=True)
    shipping_postal_code = models.CharField(max_length=20, blank=True, null=True)
    shipping_country = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile ({self.get_role_display()})"

    def is_customer(self):
        return self.role == 'customer'
    
    def is_staff_member(self):
        return self.role == 'staff'
    
    def is_owner(self):
        return self.role == 'owner'
    
    def can_access_admin(self):
        """Check if user can access admin panel"""
        return self.role == 'owner' or self.user.is_superuser
    
    def can_manage_products(self):
        """Check if user can manage products"""
        return self.role in ['staff', 'owner'] or self.user.is_superuser
    
    def can_access_dashboard(self):
        """Check if user can access dashboard"""
        return self.role in ['staff', 'owner'] or self.user.is_superuser

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal to automatically create a UserProfile when a new User is created
    """
    if created:
        # Set role based on user properties
        role = 'customer'  # Default role
        if instance.is_superuser:
            role = 'owner'
        elif instance.is_staff:
            role = 'staff'
            
        UserProfile.objects.create(user=instance, role=role)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Signal to automatically save the UserProfile when User is saved
    """
    if hasattr(instance, 'profile'):
        # Update role based on user properties
        if instance.is_superuser and instance.profile.role != 'owner':
            instance.profile.role = 'owner'
            instance.profile.save()
        elif instance.is_staff and instance.profile.role == 'customer':
            instance.profile.role = 'staff'
            instance.profile.save()
        else:
            instance.profile.save()
    else:
        # Create profile if it doesn't exist (backup)
        role = 'customer'
        if instance.is_superuser:
            role = 'owner'
        elif instance.is_staff:
            role = 'staff'
        UserProfile.objects.create(user=instance, role=role)
