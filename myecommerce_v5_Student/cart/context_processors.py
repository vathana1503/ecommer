from .models import Cart


def cart_processor(request):
    """
    Context processor to make cart information available in all templates
    """
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            return {
                'cart_total_items': cart.total_items,
                'cart_total_price': cart.total_price,
            }
        except Cart.DoesNotExist:
            return {
                'cart_total_items': 0,
                'cart_total_price': 0,
            }
    return {
        'cart_total_items': 0,
        'cart_total_price': 0,
    }
