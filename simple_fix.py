"""
Simple script to fix booking statuses - no complex queries
Run this with: python manage.py shell < simple_fix.py
"""

from TSBv1.models import AdvanceBooking

# Get all bookings in AWAITING_PAYMENT status
stuck_bookings = AdvanceBooking.objects.filter(status='AWAITING_PAYMENT')

print(f"Found {stuck_bookings.count()} bookings in AWAITING_PAYMENT status\n")

fixed_count = 0
error_count = 0

for booking in stuck_bookings:
    print(f"Booking: {booking.booking_code}")
    try:
        # Just update the status field, nothing else
        booking.status = 'PENDING'
        booking.save(update_fields=['status'])
        print(f"  ✓ Status updated to PENDING")
        fixed_count += 1
    except Exception as e:
        print(f"  ✗ Error: {e}")
        error_count += 1

print(f"\n\nResults:")
print(f"  Fixed: {fixed_count}")
print(f"  Errors: {error_count}")
