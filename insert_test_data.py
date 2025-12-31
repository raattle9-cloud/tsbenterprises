"""
MongoDB Test Data Insertion Script
Run this script to insert test data for staff login verification
"""
import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TSB.settings')
django.setup()

from django.contrib.auth.models import User
from TSBv1.models import Customer, Services, Payment, AdvanceBooking
from django.utils import timezone
from bson import Decimal128
import random
import string

def insert_test_data():
    """Insert test payment and booking data"""
    
    print("=" * 50)
    print("MongoDB Test Data Insertion")
    print("=" * 50)
    
    # Step 1: Get or create required data
    print("\n📋 Step 1: Getting required data...")
    
    # Get a user
    user = User.objects.first()
    if not user:
        print("❌ ERROR: No users found in database!")
        print("   Please create a user first through Django admin or registration.")
        return
    
    print(f"✅ Found user: {user.username} (ID: {user.id})")
    
    # Get or create customer
    customer, created = Customer.objects.get_or_create(
        user=user,
        defaults={
            'name': user.username,
            'locality': 'Test Locality',
            'city': 'Test City',
            'mobile': '1234567890',
            'zipcode': 123456,
            'state': 'MH'
        }
    )
    if created:
        print(f"✅ Created customer: {customer.name}")
    else:
        print(f"✅ Found customer: {customer.name}")
    
    # Get a service with advance payment enabled
    # Use list() to avoid Djongo ordering issues
    services = list(Services.objects.all())
    service = None
    for s in services:
        if s.supports_advance_payment:
            service = s
            break
    
    if not service:
        print("❌ ERROR: No services with advance payment enabled!")
        print("   Please create a service with 'supports_advance_payment=True' first.")
        return
    
    print(f"✅ Found service: {service.title} (ID: {service.id})")
    
    # Step 2: Create Payment
    print("\n💰 Step 2: Creating payment...")
    
    payment = Payment.objects.create(
        user=user,
        amount=1.0,
        razorpay_order_id=f"order_test_{int(datetime.now().timestamp())}",
        razorpay_payment_status="SUCCESS",
        razorpay_payment_id=f"pay_test_{int(datetime.now().timestamp())}",
        paid=True,
        payment_type="ADVANCE"
    )
    
    print(f"✅ Payment created: ID {payment.id}")
    
    # Step 3: Generate booking code
    print("\n🎫 Step 3: Creating advance booking...")
    
    # Generate unique booking code (12 chars, excluding confusing chars)
    chars = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
    max_attempts = 100
    booking_code = None
    
    for _ in range(max_attempts):
        code = ''.join(random.choices(chars, k=12))
        if not AdvanceBooking.objects.filter(booking_code=code).exists():
            booking_code = code
            break
    
    if not booking_code:
        # Fallback: use timestamp
        booking_code = "TEST" + str(int(datetime.now().timestamp()))[-8:]
    
    # Calculate dates (with timezone awareness)
    booking_date = timezone.now().date() + timedelta(days=1)  # Tomorrow
    valid_until = timezone.make_aware(
        datetime.combine(booking_date, datetime.max.time())
    )
    
    # Create AdvanceBooking
    # Note: advance_payment is set to None due to Djongo ObjectId ForeignKey limitations
    # The booking will still work for staff verification testing
    booking = AdvanceBooking.objects.create(
        booking_code=booking_code,
        qr_code_data="",
        qr_hash=f"test_hash_{int(datetime.now().timestamp())}",
        user=user,
        customer=customer,
        service=service,
        quantity=1,
        booking_date=booking_date,
        total_amount=Decimal("500.00"),
        advance_paid=Decimal("1.00"),
        remaining_amount=Decimal("499.00"),
        valid_until=valid_until,
        status="PENDING",
        advance_payment=None,  # Skipped due to Djongo ObjectId ForeignKey issue
        verified_by_staff="",
        verification_attempts=0
    )
    
    print(f"   Note: Payment link skipped (Djongo limitation)")
    print(f"   Payment was created separately: {payment.id}")
    
    print(f"✅ Booking created: ID {booking.id}")
    
    # Step 4: Summary
    print("\n" + "=" * 50)
    print("✅ TEST DATA CREATED SUCCESSFULLY!")
    print("=" * 50)
    print(f"📋 Booking Code: {booking_code}")
    print(f"👤 Customer: {customer.name}")
    print(f"🎯 Service: {service.title}")
    print(f"💰 Advance Paid: ₹{booking.advance_paid}")
    print(f"📅 Booking Date: {booking_date}")
    print(f"📊 Status: {booking.status}")
    print("\n" + "=" * 50)
    print("🔗 Staff Login: http://127.0.0.1:8000/staff/login/")
    print("🔑 PIN: 123456")
    print("=" * 50)
    print("\n💡 Use the booking code above to test staff verification!")

if __name__ == "__main__":
    try:
        insert_test_data()
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\nPlease make sure:")
        print("1. Django is properly configured")
        print("2. MongoDB is running and connected")
        print("3. You have at least one user in the database")
        import traceback
        traceback.print_exc()

