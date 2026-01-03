"""
Views for Advance Booking System
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views import View
from decimal import Decimal
from datetime import datetime, timedelta
import json

from .models import Services, Customer, AdvanceBooking, Payment
from .booking_utils import (generate_booking_code, generate_qr_code, 
                            validate_qr_data, get_client_ip)


def convert_decimal128_to_float(value):
    """
    Convert Decimal128 (MongoDB), Decimal, or other numeric types to float.
    Handles all MongoDB DecimalField types safely.
    """
    if value is None:
        return 0.0
    
    # Try direct conversion first for standard types
    if isinstance(value, (int, float)):
        return float(value)
    
    # For Decimal128, Decimal, or any other type, convert via string
    try:
        return float(str(value))
    except (ValueError, TypeError):
        # Ultimate fallback: default to 0 if conversion fails
        return 0.0


@login_required
def advance_booking_checkout(request, service_id):
    """
    Advance booking checkout page for waterpark services
    """
    service = get_object_or_404(Services, id=service_id)
    
    # Ensure service supports advance payment
    if not service.supports_advance_payment:
        return redirect('category-detail', service.id)
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        booking_date_str = request.POST.get('booking_date')
        customer_id = request.POST.get('customer')
        
        # Validate booking date
        try:
            booking_date = datetime.strptime(booking_date_str, '%Y-%m-%d').date()
            if booking_date < timezone.now().date():
                return JsonResponse({'error': 'Booking date cannot be in the past'}, status=400)
        except ValueError:
            return JsonResponse({'error': 'Invalid date format'}, status=400)
        
        # Get or validate customer
        if customer_id:
            customer = get_object_or_404(Customer, id=customer_id, user=request.user)
        else:
            # Get first customer or redirect to create one
            customer = Customer.objects.filter(user=request.user).first()
            if not customer:
                return JsonResponse({'error': 'Please add your address first'}, status=400)
        
        # Calculate amounts
        total_amount = Decimal(str(service.discounted_price)) * quantity
        advance_amount = Decimal(str(service.calculate_advance_amount(quantity)))
        remaining_amount = total_amount - advance_amount
        
        # Generate booking code first
        booking_code = generate_booking_code()
        
        # Generate a temporary unique qr_hash (will be replaced with proper hash when QR is generated)
        import uuid
        temp_qr_hash = f"temp_{uuid.uuid4().hex}"
        
        # Create booking (qr_hash will be replaced when QR code is created)
        booking = AdvanceBooking.objects.create(
            booking_code=booking_code,
            user=request.user,
            customer=customer,
            service=service,
            quantity=quantity,
            booking_date=booking_date,
            total_amount=total_amount,
            advance_paid=advance_amount,
            remaining_amount=remaining_amount,
            valid_until=timezone.make_aware(datetime.combine(booking_date, datetime.max.time())),
            status='AWAITING_PAYMENT',  # Will be updated to PENDING after successful payment
            qr_hash=temp_qr_hash,  # Temporary unique hash to avoid duplicate key errors
        )
        
        # Store booking ID in session for payment processing
        request.session['pending_advance_booking_id'] = booking.id
        
        # Return booking details for Razorpay payment
        return JsonResponse({
            'success': True,
            'booking_id': booking.id,
            'booking_code': booking.booking_code,
            'advance_amount': float(advance_amount),
            'redirect_url': f'/checkout/advance-payment/{booking.id}/'
        })
    
    # GET request - show checkout form
    customers = Customer.objects.filter(user=request.user)
    
    # Calculate preview amounts
    preview_quantity = 1
    total_price = service.discounted_price * preview_quantity
    advance_amount = service.calculate_advance_amount(preview_quantity)
    remaining_amount = total_price - advance_amount
    
    context = {
        'service': service,
        'customers': customers,
        'total_price': total_price,
        'advance_amount': advance_amount,
        'remaining_amount': remaining_amount,
        'min_date': timezone.now().date().isoformat(),
    }
    
    return render(request, 'app/advance_checkout.html', context)


@login_required
def advance_payment_process(request, booking_id):
    """
    Process Razorpay payment for advance booking
    """
    booking = get_object_or_404(AdvanceBooking, id=booking_id, user=request.user)
    
    if request.method == 'POST':
        # Handle Razorpay payment callback
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_signature = request.POST.get('razorpay_signature')
        
        # Verify Razorpay signature before confirming payment
        import razorpay
        import hmac
        import hashlib
        from django.conf import settings
        from django.contrib import messages
        
        # All three values are required for verification
        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            messages.error(request, "Payment verification failed: Missing payment details.")
            return redirect('advance-payment', booking_id)
        
        # Verify the signature
        try:
            client = razorpay.Client(auth=(settings.RAZOR_PAY_KEY_ID, settings.RAZOR_PAY_KEY_SECRET))
            
            # Razorpay signature verification
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            
            # This will raise an exception if signature is invalid
            client.utility.verify_payment_signature(params_dict)
            
            # Signature verified - Create payment record with SUCCESS status
            payment = Payment.objects.create(
                user=request.user,
                amount=convert_decimal128_to_float(booking.advance_paid),
                razorpay_order_id=razorpay_order_id,
                razorpay_payment_id=razorpay_payment_id,
                razorpay_payment_status='SUCCESS',
                paid=True,
                payment_type='ADVANCE'
            )
            
            # Link payment to booking and update status to confirm it's paid
            AdvanceBooking.objects.filter(id=booking_id).update(
                advance_payment=payment,
                status='PENDING'  # PENDING means paid but waiting for venue verification
            )
            
            # Generate QR code only after successful payment
            qr_data = generate_qr_code(booking)
            AdvanceBooking.objects.filter(id=booking_id).update(qr_code_data=qr_data)
            
            # Redirect to confirmation page
            return redirect('advance-booking-confirmation', booking.id)
            
        except razorpay.errors.SignatureVerificationError:
            # Payment signature verification failed
            # Create a failed payment record for tracking
            Payment.objects.create(
                user=request.user,
                amount=convert_decimal128_to_float(booking.advance_paid),
                razorpay_order_id=razorpay_order_id,
                razorpay_payment_id=razorpay_payment_id,
                razorpay_payment_status='FAILED',
                paid=False,
                payment_type='ADVANCE'
            )
            messages.error(request, "Payment verification failed. Please try again or contact support.")
            return redirect('advance-payment', booking_id)
            
        except Exception as e:
            # Other errors during verification
            print(f"Payment verification error: {e}")
            messages.error(request, f"Payment processing error. Please try again.")
            return redirect('advance-payment', booking_id)
    
    # GET - show payment page
    import razorpay
    from django.conf import settings
    
    client = razorpay.Client(auth=(settings.RAZOR_PAY_KEY_ID, settings.RAZOR_PAY_KEY_SECRET))
    
    # Create Razorpay order
    # Convert Decimal128 to float first, then to paise (multiply by 100)
    advance_paid_float = convert_decimal128_to_float(booking.advance_paid)
    order_amount = int(advance_paid_float * 100)  # Convert to paise
    order_currency = 'INR'
    order_receipt = f'booking_{booking.booking_code}'
    
    razorpay_order = client.order.create({
        'amount': order_amount,
        'currency': order_currency,
        'receipt': order_receipt,
        'payment_capture': 1
    })
    
    context = {
        'booking': booking,
        'razorpay_order_id': razorpay_order['id'],
        'razorpay_key_id': settings.RAZOR_PAY_KEY_ID,
        'amount': order_amount,
        'currency': order_currency,
    }
    
    return render(request, 'app/advance_payment.html', context)


@login_required
def advance_booking_confirmation(request, booking_id):
    """
    Show booking confirmation with QR code - only for paid bookings
    """
    from django.contrib import messages
    
    booking = get_object_or_404(AdvanceBooking, id=booking_id, user=request.user)
    
    # Only show confirmation if payment is complete (not AWAITING_PAYMENT)
    if booking.status == 'AWAITING_PAYMENT':
        messages.warning(request, "Please complete your payment first.")
        return redirect('advance-payment', booking_id)
    
    # Generate QR code if not already generated
    if not booking.qr_code_data:
        qr_data = generate_qr_code(booking)
        # Save QR code data using update to avoid MongoDB issues
        AdvanceBooking.objects.filter(id=booking_id).update(qr_code_data=qr_data)
        # Refresh the booking object to get the updated data
        booking = AdvanceBooking.objects.get(id=booking_id)
    
    context = {
        'booking': booking,
    }
    
    return render(request, 'app/booking_confirmation.html', context)


@login_required
def my_advance_bookings(request):
    """
    Show user's advance bookings - only those with completed payment
    """
    # Only show bookings that have completed payment (exclude AWAITING_PAYMENT)
    bookings = AdvanceBooking.objects.filter(
        user=request.user
    ).exclude(
        status='AWAITING_PAYMENT'
    ).order_by('-created_at')
    
    context = {
        'bookings': bookings,
    }
    
    return render(request, 'app/my_bookings.html', context)


# Staff Verification Views

STAFF_PIN = "123456"  # TODO: Move to settings or environment variable

def staff_login(request):
    """
    Simple PIN-based staff login
    """
    if request.method == 'POST':
        pin = request.POST.get('pin')
        if pin == STAFF_PIN:
            request.session['staff_authenticated'] = True
            request.session['staff_login_time'] = timezone.now().isoformat()
            return redirect('staff-verify')
        else:
            return render(request, 'app/staff_login.html', {'error': 'Invalid PIN'})
    
    return render(request, 'app/staff_login.html')


def staff_verify(request):
    """
    Staff verification portal - QR scanner and manual entry
    """
    # Check staff authentication
    if not request.session.get('staff_authenticated'):
        return redirect('staff-login')
    
    # Get today's date for reference
    today = timezone.now().date()
    
    # Get ALL pending bookings (not just today's) to avoid MongoDB date comparison issues
    # Filter in Python to separate today's vs other dates
    all_pending = list(AdvanceBooking.objects.filter(
        status='PENDING'
    ).select_related('customer', 'service').order_by('-booking_date', '-created_at')[:50])
    
    # Convert Decimal128 to float for template display and separate by date
    todays_bookings = []
    other_bookings = []
    
    for booking in all_pending:
        booking_data = {
            'booking_code': booking.booking_code,
            'customer_name': booking.customer.name,
            'service_name': booking.service.title,
            'quantity': booking.quantity,
            'booking_date': booking.booking_date,
            'advance_paid': convert_decimal128_to_float(booking.advance_paid),
            'remaining_amount': convert_decimal128_to_float(booking.remaining_amount),
            'created_at': booking.created_at,
        }
        # Compare dates as strings to avoid MongoDB date comparison issues
        if str(booking.booking_date) == str(today):
            todays_bookings.append(booking_data)
        else:
            other_bookings.append(booking_data)
    
    context = {
        'todays_bookings': todays_bookings,
        'other_bookings': other_bookings,
        'pending_bookings': todays_bookings + other_bookings,  # Combined for backward compatibility
        'today': today
    }
    
    return render(request, 'app/staff_verify.html', context)


@csrf_exempt
def verify_booking_api(request):
    """
    API endpoint for booking verification
    Accepts booking_code or qr_data
    """
    if not request.session.get('staff_authenticated'):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        booking_code = data.get('booking_code')
        qr_data = data.get('qr_data')
        
        # Validate QR data if provided
        if qr_data:
            validation_result = validate_qr_data(qr_data)
            if not validation_result['valid']:
                return JsonResponse({'error': validation_result['error']}, status=400)
            booking_code = validation_result['booking_code']
        
        # Get booking
        try:
            booking = AdvanceBooking.objects.select_related('customer', 'service').get(
                booking_code=booking_code
            )
        except AdvanceBooking.DoesNotExist:
            # Track failed attempt
            return JsonResponse({'error': 'Booking not found'}, status=404)
        
        # Update verification attempts
        booking.verification_attempts += 1
        booking.save(update_fields=['verification_attempts'])
        
        # Check if already verified
        if booking.status == 'VERIFIED':
            return JsonResponse({
                'status': 'already_verified',
                'message': 'This booking has already been verified',
                'verified_at': booking.verified_at.isoformat() if booking.verified_at else None,
                'verified_by': booking.verified_by_staff
            })
        
        # Check if used
        if booking.status == 'USED':
            return JsonResponse({
                'status': 'already_used',
                'message': 'This booking has already been used',
                'error': 'Booking already used'
            }, status=400)
        
        # Check if expired
        if not booking.is_valid():
            booking.status = 'EXPIRED'
            booking.save()
            return JsonResponse({
                'status': 'expired',
                'error': 'Booking has expired',
                'valid_until': booking.valid_until.isoformat()
            }, status=400)
        
        # Check if cancelled
        if booking.status == 'CANCELLED':
            return JsonResponse({
                'status': 'cancelled',
                'error': 'Booking has been cancelled'
            }, status=400)
        
        # Booking is valid
        return JsonResponse({
            'status': 'valid',
            'booking': {
                'booking_code': booking.booking_code,
                'customer_name': booking.customer.name,
                'customer_phone': booking.customer.mobile,
                'service_name': booking.service.title,
                'quantity': booking.quantity,
                'booking_date': booking.booking_date.isoformat(),
                'total_amount': convert_decimal128_to_float(booking.total_amount),
                'advance_paid': convert_decimal128_to_float(booking.advance_paid),
                'remaining_amount': convert_decimal128_to_float(booking.remaining_amount),
                'created_at': booking.created_at.isoformat(),
            }
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def mark_booking_verified(request):
    """
    Mark booking as verified and optionally collect remaining payment
    """
    if not request.session.get('staff_authenticated'):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        booking_code = data.get('booking_code')
        payment_collected = data.get('payment_collected', False)
        staff_name = data.get('staff_name', 'Staff')
        
        booking = get_object_or_404(AdvanceBooking, booking_code=booking_code)
        
        # Update booking status - only update specific fields to avoid Decimal128 validation issues
        booking.status = 'VERIFIED'
        booking.verified_at = timezone.now()
        booking.verified_by_staff = staff_name
        booking.verification_ip = get_client_ip(request)
        # Use update_fields to only save the fields we're changing
        booking.save(update_fields=['status', 'verified_at', 'verified_by_staff', 'verification_ip'])
        
        # If payment collected, create payment record
        if payment_collected:
            # Create payment record
            final_payment = Payment.objects.create(
                user=booking.user,
                amount=convert_decimal128_to_float(booking.remaining_amount),
                paid=True,
                payment_type='REMAINING',
                razorpay_payment_status='CASH'
            )
            # Update status to USED
            booking.status = 'USED'
            # Skip final_payment assignment due to Djongo ObjectId ForeignKey limitation
            # The payment is created but not linked via ForeignKey
            booking.save(update_fields=['status'])
        
        return JsonResponse({
            'success': True,
            'message': 'Booking verified successfully',
            'status': booking.status
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def staff_logout(request):
    """
    Staff logout
    """
    request.session.pop('staff_authenticated', None)
    request.session.pop('staff_login_time', None)
    return redirect('staff-login')
