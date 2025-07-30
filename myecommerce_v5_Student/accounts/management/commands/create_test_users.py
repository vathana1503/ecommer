from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Create test users with different roles for testing the role-based access system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing test users before creating new ones',
        )

    def handle(self, *args, **options):
        if options['reset']:
            # Delete existing test users
            test_usernames = ['customer_user', 'staff_user', 'owner_user']
            deleted_count = User.objects.filter(username__in=test_usernames).delete()[0]
            if deleted_count > 0:
                self.stdout.write(
                    self.style.WARNING(f'Deleted {deleted_count} existing test users')
                )

        # Create customer user
        customer_user, created = User.objects.get_or_create(
            username='customer_user',
            defaults={
                'email': 'customer@example.com',
                'first_name': 'John',
                'last_name': 'Customer',
            }
        )
        if created:
            customer_user.set_password('customer123')
            customer_user.save()
            # Profile will be auto-created with 'customer' role
            self.stdout.write(
                self.style.SUCCESS('Created customer user: customer_user (password: customer123)')
            )
        else:
            self.stdout.write('Customer user already exists')

        # Create staff user
        staff_user, created = User.objects.get_or_create(
            username='staff_user',
            defaults={
                'email': 'staff@example.com',
                'first_name': 'Jane',
                'last_name': 'Staff',
                'is_staff': True,
            }
        )
        if created:
            staff_user.set_password('staff123')
            staff_user.save()
            # Profile will be auto-created with 'staff' role
            self.stdout.write(
                self.style.SUCCESS('Created staff user: staff_user (password: staff123)')
            )
        else:
            self.stdout.write('Staff user already exists')

        # Create owner/admin user
        owner_user, created = User.objects.get_or_create(
            username='owner_user',
            defaults={
                'email': 'owner@example.com',
                'first_name': 'Admin',
                'last_name': 'Owner',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            owner_user.set_password('owner123')
            owner_user.save()
            # Profile will be auto-created with 'owner' role
            self.stdout.write(
                self.style.SUCCESS('Created owner user: owner_user (password: owner123)')
            )
        else:
            self.stdout.write('Owner user already exists')

        # Display summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('TEST USERS SUMMARY:'))
        self.stdout.write('='*50)
        
        for username in ['customer_user', 'staff_user', 'owner_user']:
            try:
                user = User.objects.get(username=username)
                role = user.profile.get_role_display()
                self.stdout.write(f'• {username}: {role} (password: {username.split("_")[0]}123)')
            except User.DoesNotExist:
                pass
        
        self.stdout.write('\n' + self.style.WARNING('ROLE PERMISSIONS:'))
        self.stdout.write('• Customer: Can browse home page and products')
        self.stdout.write('• Staff: Can manage products and access dashboard')
        self.stdout.write('• Owner: Can access admin panel and all features')
        self.stdout.write('• Anonymous: Can browse home page and products')
        self.stdout.write('\n' + '='*50)
