from django import forms
from django.contrib.auth.models import User
from orders.models import Order, ShippingMethod, Coupon
from .models import Payment
from decimal import Decimal


class CheckoutForm(forms.ModelForm):
    """
    Form for checkout information
    """
    shipping_method = forms.ModelChoiceField(
        queryset=ShippingMethod.objects.filter(is_active=True),
        empty_label="Select shipping method",
        widget=forms.RadioSelect,
        required=True
    )
    
    coupon_code = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter coupon code',
            'class': 'form-control'
        })
    )

    class Meta:
        model = Order
        fields = [
            'first_name', 'last_name', 'phone',
            'shipping_first_name', 'shipping_last_name', 'shipping_phone',
            'shipping_address', 'shipping_city', 'shipping_state',
            'shipping_postal_code', 'shipping_country', 'order_notes'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'shipping_first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'shipping_last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'shipping_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'shipping_address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Street Address',
                'rows': 3
            }),
            'shipping_city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'shipping_state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State/Province'}),
            'shipping_postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Postal Code'}),
            'shipping_country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),
            'order_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Order notes (optional)',
                'rows': 3
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Pre-fill form with user data if available
        if user and user.is_authenticated:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            
            # Try to get user profile data if available
            if hasattr(user, 'userprofile'):
                profile = user.userprofile
                self.fields['phone'].initial = getattr(profile, 'phone', '')

    def clean_coupon_code(self):
        """Validate coupon code"""
        code = self.cleaned_data.get('coupon_code')
        if code:
            try:
                coupon = Coupon.objects.get(code=code.upper())
                if not coupon.is_valid:
                    raise forms.ValidationError("This coupon is not valid or has expired.")
                return code.upper()
            except Coupon.DoesNotExist:
                raise forms.ValidationError("Invalid coupon code.")
        return code


class PaymentForm(forms.ModelForm):
    """
    Form for payment information
    """
    class Meta:
        model = Payment
        fields = ['payment_method']
        widgets = {
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial payment method to the first available option
        self.fields['payment_method'].initial = 'bank_transfer'

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        
        # All current payment methods are valid without additional validation
        return cleaned_data


class CouponForm(forms.Form):
    """
    Form for applying coupon codes
    """
    code = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter coupon code'
        })
    )

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code:
            code = code.upper()
            try:
                coupon = Coupon.objects.get(code=code)
                if not coupon.is_valid:
                    raise forms.ValidationError("This coupon is not valid or has expired.")
                return code
            except Coupon.DoesNotExist:
                raise forms.ValidationError("Invalid coupon code.")
        return code


class OrderSearchForm(forms.Form):
    """
    Form for searching orders
    """
    order_id = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Order ID'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + Order.ORDER_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class ShippingMethodForm(forms.ModelForm):
    """
    Form for managing shipping methods (admin)
    """
    class Meta:
        model = ShippingMethod
        fields = ['name', 'description', 'cost', 'estimated_days', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'estimated_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CouponAdminForm(forms.ModelForm):
    """
    Form for managing coupons (admin)
    """
    class Meta:
        model = Coupon
        fields = [
            'code', 'discount_type', 'discount_value', 'minimum_amount',
            'maximum_uses', 'valid_from', 'valid_to', 'is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'discount_type': forms.Select(attrs={'class': 'form-control'}),
            'discount_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'minimum_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'maximum_uses': forms.NumberInput(attrs={'class': 'form-control'}),
            'valid_from': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'valid_to': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_code(self):
        return self.cleaned_data.get('code', '').upper()

    def clean(self):
        cleaned_data = super().clean()
        valid_from = cleaned_data.get('valid_from')
        valid_to = cleaned_data.get('valid_to')
        
        if valid_from and valid_to and valid_from >= valid_to:
            raise forms.ValidationError("Valid from date must be before valid to date.")
        
        return cleaned_data
