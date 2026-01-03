"""
Utility functions for Advance Booking System
"""
import random
import string
import hashlib
import qrcode
from io import BytesIO
import base64
from django.conf import settings
from .models import AdvanceBooking


def generate_booking_code():
    """
    Generate a unique 6-character booking code.
    Excludes confusing characters (0, O, 1, I, L) for clarity.
    """
    # Remove confusing characters
    chars = ''.join(set(string.ascii_uppercase + string.digits) - set('0O1IL'))
    
    max_attempts = 100
    for _ in range(max_attempts):
        code = ''.join(random.choices(chars, k=6))
        # Check if code is unique
        if not AdvanceBooking.objects.filter(booking_code=code).exists():
            return code
    
    # If still no unique code after max attempts, append timestamp
    import time
    timestamp = str(int(time.time()))[-2:]
    code = ''.join(random.choices(chars, k=4)) + timestamp
    return code


def generate_qr_hash(booking_code, booking_id):
    """
    Generate a SHA-256 hash for QR code validation.
    """
    data = f"{booking_code}{settings.SECRET_KEY}{booking_id}"
    return hashlib.sha256(data.encode()).hexdigest()


def generate_qr_code(booking):
    """
    Generate QR code image for a booking.
    Returns base64 encoded image data URL.
    
    Args:
        booking: AdvanceBooking instance
    
    Returns:
        str: Base64 encoded QR code image (data URL format)
    """
    # Generate hash if not already generated or if it's a temporary hash
    if not booking.qr_hash or str(booking.qr_hash).startswith('temp_'):
        booking.qr_hash = generate_qr_hash(booking.booking_code, booking.id)
        booking.save(update_fields=['qr_hash'])
    
    # QR data format: BOOKING_CODE|HASH_FRAGMENT|BOOKING_ID
    # We only include first 16 chars of hash to keep QR compact
    qr_data = f"{booking.booking_code}|{booking.qr_hash[:16]}|{booking.id}"
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    # Return as data URL
    return f"data:image/png;base64,{img_str}"


def validate_qr_data(qr_data):
    """
    Validate QR code data and extract booking information.
    
    Args:
        qr_data: String scanned from QR code
    
    Returns:
        dict: {'valid': bool, 'booking_code': str, 'error': str}
    """
    try:
        parts = qr_data.split('|')
        if len(parts) != 3:
            return {'valid': False, 'error': 'Invalid QR format'}
        
        booking_code, hash_fragment, booking_id = parts
        
        # Validate booking exists
        try:
            booking = AdvanceBooking.objects.get(
                booking_code=booking_code,
                id=int(booking_id)
            )
        except AdvanceBooking.DoesNotExist:
            return {'valid': False, 'error': 'Booking not found'}
        
        # Validate hash
        if not booking.qr_hash.startswith(hash_fragment):
            return {'valid': False, 'error': 'Invalid QR code - possible tampering'}
        
        return {
            'valid': True,
            'booking_code': booking_code,
            'booking': booking
        }
    
    except Exception as e:
        return {'valid': False, 'error': f'QR validation error: {str(e)}'}


def get_client_ip(request):
    """
    Get client IP address from request.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
