"""
Management command to create a test service for advance booking testing
Usage: python manage.py create_test_service
"""
from django.core.management.base import BaseCommand
from TSBv1.models import Services, ServiceImage


class Command(BaseCommand):
    help = 'Creates a test service with 1 rupee price for advance booking testing'

    def handle(self, *args, **options):
        # Check if test service already exists
        existing = Services.objects.filter(title__icontains='Test Waterpark').first()
        
        if existing:
            self.stdout.write(
                self.style.WARNING(f'Test service already exists: {existing.title} (ID: {existing.id})')
            )
            self.stdout.write(
                self.style.SUCCESS(f'You can use this service at: /category-detail/{existing.id}/')
            )
            return

        # Create test service
        service = Services.objects.create(
            title='Test Waterpark - ₹1',
            selling_price=100.0,
            discounted_price=1.0,  # 1 rupee
            description='This is a test service for advance booking testing. Price is set to ₹1 for easy testing.',
            composition='Test Service',
            servapp='Testing',
            category='WP',  # Waterpark
            supports_advance_payment=True,
            advance_payment_type='FIXED',
            advance_payment_value=1.0,  # 1 rupee advance payment
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created test service: {service.title} (ID: {service.id})'
            )
        )
        self.stdout.write('')
        self.stdout.write('Service Details:')
        self.stdout.write(f'  - Title: {service.title}')
        self.stdout.write(f'  - Price: ₹{service.discounted_price}')
        self.stdout.write(f'  - Advance Payment: ₹{service.advance_payment_value} (Fixed)')
        self.stdout.write(f'  - Category: Waterpark')
        self.stdout.write('')
        self.stdout.write('Next Steps:')
        self.stdout.write(f'  1. Visit: http://127.0.0.1:8000/category-detail/{service.id}/')
        self.stdout.write(f'  2. Click "Book with Advance Payment"')
        self.stdout.write(f'  3. Complete the booking flow')
        self.stdout.write(f'  4. Test payment with Razorpay (use test card: 4111 1111 1111 1111)')
        self.stdout.write(f'  5. Verify QR code generation')
        self.stdout.write(f'  6. Test staff verification at: /staff/login/')
        self.stdout.write('')
        self.stdout.write(
            self.style.WARNING(
                'Note: Make sure you have Razorpay test keys configured for testing!'
            )
        )

