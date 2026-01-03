"""
Script to manually fix existing bookings stuck in AWAITING_PAYMENT status
Run this with: python manage.py shell < fix_bookings.py
"""

from TSBv1.models import AdvanceBooking, Payment

# Get all bookings in AWAITING_PAYMENT status
stuck_bookings = AdvanceBooking.objects.filter(status='AWAITING_PAYMENT')

print(f"Found {stuck_bookings.count()} bookings in AWAITING_PAYMENT status")

for booking in stuck_bookings:
    print(f"\nBooking: {booking.booking_code}")
    print(f"  Current status: {booking.status}")
    print(f"  Advance paid: {booking.advance_paid}")
    print(f"  Has qr_hash: {booking.qr_hash[:30] if booking.qr_hash else 'None'}")
    
    # Check if there's a payment for this booking
    # Payments might have been created but not linked
    potential_payments = Payment.objects.filter(
        user=booking.user,
        payment_type='ADVANCE',
        paid=True,
        created_at__gte=booking.created_at
    ).order_by('-created_at')
    
    if potential_payments.exists():
        print(f"  Found {potential_payments.count()} potential payments")
        payment = potential_payments.first()
        print(f"  Using payment ID: {payment.id}")
        
        # Try to update status
        try:
            booking.status = 'PENDING'
            booking.save(update_fields=['status'])
            print(f"  ✓ Status updated to PENDING")
        except Exception as e:
            print(f"  ✗ Error updating status: {e}")
            
    else:
        print(f"  No payments found for this booking")

print("\n\nDone!")
