from django import forms
from .models import CartItem


class AddToCartForm(forms.Form):
    """Form for adding products to cart"""
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'style': 'width: 80px;'
        })
    )

    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)
        
        if self.product:
            self.fields['quantity'].widget.attrs['max'] = str(self.product.qty)

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if self.product and quantity > self.product.qty:
            raise forms.ValidationError(f"Only {self.product.qty} items available in stock.")
        return quantity


class UpdateCartItemForm(forms.ModelForm):
    """Form for updating cart item quantities"""
    
    class Meta:
        model = CartItem
        fields = ['quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'min': '1',
                'style': 'width: 70px;'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.product:
            self.fields['quantity'].widget.attrs['max'] = str(self.instance.product.qty)

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if self.instance and self.instance.product:
            if quantity > self.instance.product.qty:
                raise forms.ValidationError(
                    f"Only {self.instance.product.qty} items available in stock."
                )
        return quantity
