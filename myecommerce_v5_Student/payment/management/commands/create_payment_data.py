from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from payment.models import ShippingMethod, Coupon


class Command(BaseCommand):
    help = 'Create initial payment and shipping data'

    def handle(self, *args, **options):
        # Create shipping methods
        shipping_methods = [
            {
                'name': 'Standard Shipping',
                'description': 'Delivery within 5-7 business days',
                'cost': 5.99,
                'estimated_days': 7,
            },
            {
                'name': 'Express Shipping',
                'description': 'Delivery within 2-3 business days',
                'cost': 12.99,
                'estimated_days': 3,
            },
            {
                'name': 'Overnight Shipping',
                'description': 'Next business day delivery',
                'cost': 24.99,
                'estimated_days': 1,
            },
            {
                'name': 'Free Shipping',
                'description': 'Free delivery within 7-10 business days (orders over $50)',
                'cost': 0.00,
                'estimated_days': 10,
            },
        ]

        for method_data in shipping_methods:
            shipping_method, created = ShippingMethod.objects.get_or_create(
                name=method_data['name'],
                defaults=method_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created shipping method: {shipping_method.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Shipping method already exists: {shipping_method.name}')
                )

        # Create sample coupons
        now = timezone.now()
        coupons = [
            {
                'code': 'WELCOME10',
                'discount_type': 'percentage',
                'discount_value': 10.00,
                'minimum_amount': 0.00,
                'maximum_uses': 100,
                'valid_from': now,
                'valid_to': now + timedelta(days=365),
                'is_active': True,
            },
            {
                'code': 'SAVE20',
                'discount_type': 'fixed',
                'discount_value': 20.00,
                'minimum_amount': 100.00,
                'maximum_uses': 50,
                'valid_from': now,
                'valid_to': now + timedelta(days=30),
                'is_active': True,
            },
            {
                'code': 'FREESHIP',
                'discount_type': 'fixed',
                'discount_value': 15.00,
                'minimum_amount': 75.00,
                'maximum_uses': 200,
                'valid_from': now,
                'valid_to': now + timedelta(days=60),
                'is_active': True,
            },
        ]

        for coupon_data in coupons:
            coupon, created = Coupon.objects.get_or_create(
                code=coupon_data['code'],
                defaults=coupon_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created coupon: {coupon.code}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Coupon already exists: {coupon.code}')
                )

        self.stdout.write(
            self.style.SUCCESS('Successfully created initial payment data!')
        )
