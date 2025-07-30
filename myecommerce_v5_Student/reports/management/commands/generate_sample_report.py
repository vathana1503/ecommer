from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from reports.views import generate_sales_report
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Generate a sample sales report for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to include in the report (default: 30)'
        )
        parser.add_argument(
            '--report-type',
            type=str,
            default='monthly',
            choices=['daily', 'weekly', 'monthly', 'yearly', 'custom'],
            help='Type of report to generate'
        )

    def handle(self, *args, **options):
        days = options['days']
        report_type = options['report_type']
        
        # Calculate date range
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        try:
            # Get the first owner/admin user to generate the report
            owner_user = User.objects.filter(
                profile__role='owner'
            ).first()
            
            if not owner_user:
                # If no owner, try to get a superuser
                owner_user = User.objects.filter(is_superuser=True).first()
                
            if not owner_user:
                self.stdout.write(
                    self.style.ERROR('No owner or superuser found. Please create an owner user first.')
                )
                return
            
            self.stdout.write(f'Generating {report_type} sales report...')
            self.stdout.write(f'Date range: {start_date} to {end_date}')
            
            # Generate the report
            report_data = generate_sales_report(
                report_type=report_type,
                start_date=start_date,
                end_date=end_date,
                user=owner_user
            )
            
            # Display results
            self.stdout.write(
                self.style.SUCCESS(f'\nReport generated successfully!')
            )
            self.stdout.write(f'Total Orders: {report_data["total_orders"]}')
            self.stdout.write(f'Total Revenue: ${report_data["total_revenue"]}')
            self.stdout.write(f'Average Order Value: ${report_data["average_order_value"]}')
            self.stdout.write(f'Total Items Sold: {report_data["total_items_sold"]}')
            
            if report_data['daily_sales']:
                self.stdout.write('\nDaily Sales Breakdown:')
                for day_data in report_data['daily_sales']:
                    self.stdout.write(
                        f'  {day_data["day"]}: {day_data["orders_count"]} orders, '
                        f'${day_data["revenue"]} revenue'
                    )
            
            if report_data['status_breakdown']:
                self.stdout.write('\nOrder Status Breakdown:')
                for status_data in report_data['status_breakdown']:
                    self.stdout.write(
                        f'  {status_data["status"].title()}: {status_data["count"]} orders, '
                        f'${status_data["revenue"]} revenue'
                    )
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error generating report: {str(e)}')
            )
