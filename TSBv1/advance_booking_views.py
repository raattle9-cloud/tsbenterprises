"""
Views for Advance Booking System
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import messages
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
    Process Razorpay payment for advance booking.
    Set PAYMENT_MODE=testing in .env to bypass Razorpay for development/QA.
    """
    print(f"========== ADVANCE PAYMENT PROCESS CALLED ==========")
    print(f"Booking ID: {booking_id}")
    print(f"Request method: {request.method}")

    from django.conf import settings
    payment_mode = getattr(settings, 'PAYMENT_MODE', 'live')

    booking = get_object_or_404(AdvanceBooking, id=booking_id, user=request.user)

    print(f"Booking found: {booking.booking_code}, Status: {booking.status}, payment_mode={payment_mode}")

    if request.method == 'POST':
        print("POST request received - processing payment callback")
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_signature = request.POST.get('razorpay_signature')

        print(f"Payment IDs received: order={razorpay_order_id}, payment={razorpay_payment_id}")

        # ── TESTING MODE: bypass Razorpay entirely ───────────────────────────
        if payment_mode == 'testing':
            print("[TEST MODE] Bypassing Razorpay signature verification")
            import logging
            logger = logging.getLogger(__name__)
            try:
                import time as _t, random as _r
                _pid = int(_t.time() * 1000) % 2147483647 + _r.randint(1, 999)
                payment = Payment(
                    id=_pid,
                    user=request.user,
                    amount=convert_decimal128_to_float(booking.advance_paid),
                    razorpay_order_id=razorpay_order_id or f'test_order_{booking.booking_code}',
                    razorpay_payment_id=razorpay_payment_id or f'test_pay_{booking.booking_code}',
                    razorpay_payment_status='TEST_SUCCESS',
                    paid=True,
                    payment_type='ADVANCE'
                )
                payment.save()
                payment.id = _pid  # restore integer after djongo ObjectId override
                booking.status = 'PENDING'
                booking.save(update_fields=['status'])
                qr_data = generate_qr_code(booking)
                booking.qr_code_data = qr_data
                booking.save(update_fields=['qr_code_data'])
                try:
                    from .invoice_service import create_and_notify
                    create_and_notify(
                        advance_booking=booking,
                        payment=payment,
                        customer=booking.customer,
                        service=booking.service,
                        amount=convert_decimal128_to_float(booking.advance_paid),
                        quantity=booking.quantity,
                    )
                except Exception as inv_err:
                    logger.error(f"[INVOICE] Failed for advance booking {booking.booking_code}: {inv_err}", exc_info=True)
                return redirect('advance-booking-confirmation', booking.id)
            except Exception as e:
                logger.error(f"[TEST PAYMENT] Error: {e}", exc_info=True)
                messages.error(request, f"Test payment error: {e}")
                return redirect('advance-payment', booking_id)
        # ── END TESTING MODE ─────────────────────────────────────────────────

        # Verify Razorpay signature before confirming payment
        import razorpay
        import hmac
        import hashlib
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
            import time as _t2, random as _r2
            _pid2 = int(_t2.time() * 1000) % 2147483647 + _r2.randint(1, 999)
            payment = Payment(
                id=_pid2,
                user=request.user,
                amount=convert_decimal128_to_float(booking.advance_paid),
                razorpay_order_id=razorpay_order_id,
                razorpay_payment_id=razorpay_payment_id,
                razorpay_payment_status='SUCCESS',
                paid=True,
                payment_type='ADVANCE'
            )
            payment.save()
            payment.id = _pid2  # restore integer after djongo ObjectId override
            
            # Update booking status to PENDING (paid but waiting for venue verification)
            # NOTE: NOT linking payment via ForeignKey due to Djongo bugs
            # Payment record is created above and exists in DB, just not linked
            import logging
            logger = logging.getLogger(__name__)
            
            print(f"[PAYMENT] About to update status for booking {booking.booking_code}")
            print(f"[PAYMENT] Current status: {booking.status}")
            print(f"[PAYMENT] Payment created with ID: {payment.id}")
            
            logger.info(f"[PAYMENT] Processing payment for booking {booking.booking_code}")
            logger.info(f"[PAYMENT] Current status: {booking.status}")
            logger.info(f"[PAYMENT] Payment created: {payment.id}")
            
            # Just update the status - this is all that's needed for tickets to show in profile
            try:
                print("[PAYMENT] Calling booking.save() to update status...")
                booking.status = 'PENDING'
                booking.save(update_fields=['status'])
                print(f"[PAYMENT] SUCCESS! Status updated to: {booking.status}")
                logger.info(f"[PAYMENT] Status updated to PENDING")
            except Exception as save_error:
                print(f"[PAYMENT] ERROR saving status: {save_error}")
                logger.error(f"[PAYMENT] Error saving status: {save_error}", exc_info=True)
                # If even this fails, raise it
                raise
            
            # Generate QR code only after successful payment
            qr_data = generate_qr_code(booking)
            booking.qr_code_data = qr_data
            booking.save(update_fields=['qr_code_data'])
            
            logger.info(f"[PAYMENT] QR code generated and saved")
            logger.info(f"[PAYMENT] Final booking status: {booking.status}")
            
            # Create invoice + notify all three parties (customer, vendor, platform owner)
            try:
                from .invoice_service import create_and_notify
                create_and_notify(
                    advance_booking=booking,
                    payment=payment,
                    customer=booking.customer,
                    service=booking.service,
                    amount=convert_decimal128_to_float(booking.advance_paid),
                    quantity=booking.quantity,
                )
            except Exception as inv_err:
                logger.error(f"[INVOICE] Failed for advance booking {booking.booking_code}: {inv_err}", exc_info=True)
            
            # Redirect to confirmation page
            return redirect('advance-booking-confirmation', booking.id)
            
        except razorpay.errors.SignatureVerificationError:
            # Payment signature verification failed
            # Create a failed payment record for tracking
            import time as _t3, random as _r3
            _pid3 = int(_t3.time() * 1000) % 2147483647 + _r3.randint(1, 999)
            _fp = Payment(id=_pid3, user=request.user, amount=convert_decimal128_to_float(booking.advance_paid),
                razorpay_order_id=razorpay_order_id, razorpay_payment_id=razorpay_payment_id,
                razorpay_payment_status='FAILED', paid=False, payment_type='ADVANCE')
            _fp.save()
            messages.error(request, "Payment verification failed. Please try again or contact support.")
            return redirect('advance-payment', booking_id)
            
        except Exception as e:
            # Other errors during verification
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"[PAYMENT] Payment verification error: {e}", exc_info=True)
            print(f"Payment verification error: {e}")
            messages.error(request, f"Payment processing error. Please try again.")
            return redirect('advance-payment', booking_id)
    
    # GET - show payment page
    import razorpay

    advance_paid_float = convert_decimal128_to_float(booking.advance_paid)
    order_amount = int(advance_paid_float * 100)
    order_currency = 'INR'

    # ── TESTING MODE: skip Razorpay order creation ───────────────────────────
    if payment_mode == 'testing':
        context = {
            'booking': booking,
            'razorpay_order_id': f'test_order_{booking.booking_code}',
            'razorpay_key_id': 'test_key_id',
            'amount': order_amount,
            'currency': order_currency,
            'payment_mode': 'testing',
        }
        return render(request, 'app/advance_payment.html', context)
    # ── END TESTING MODE ─────────────────────────────────────────────────────

    client = razorpay.Client(auth=(settings.RAZOR_PAY_KEY_ID, settings.RAZOR_PAY_KEY_SECRET))
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
        'payment_mode': 'live',
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
    
    # Check and mark expired bookings based on visit date
    today = timezone.now().date()
    for booking in bookings:
        # If booking_date (visit date) has passed and status is still PENDING or VERIFIED, mark as expired
        if booking.booking_date < today and booking.status in ['PENDING', 'VERIFIED']:
            booking.status = 'EXPIRED'
            booking.save(update_fields=['status'])
    
    context = {
        'bookings': bookings,
    }
    
    return render(request, 'app/my_bookings.html', context)


# Staff Verification Views

@login_required
def staff_verify(request):
    """
    Staff verification portal - manual code entry and QR scanning
    Requires Django authentication and Staff group membership
    """
    # Check if user is in Staff group
    if not request.user.groups.filter(name='StaffMembers').exists():
        messages.error(request, "Access denied. Staff credentials required.")
        return redirect('home')
    
    context = {
        'today': timezone.now().date(),
        'staff_name': request.user.get_full_name() or request.user.username,
    }
    
    return render(request, 'app/staff_verify.html', context)


@login_required
@csrf_exempt
def verify_booking_api(request):
    """
    API endpoint for booking verification
    Accepts booking_code or qr_data
    """
    # Check if user is in Staff group
    if not request.user.groups.filter(name='StaffMembers').exists():
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
        
        # Check if expired - either by valid_until time or if visit date has passed
        today = timezone.now().date()
        if not booking.is_valid() or booking.booking_date < today:
            booking.status = 'EXPIRED'
            booking.save(update_fields=['status'])
            return JsonResponse({
                'status': 'expired',
                'error': 'Booking has expired',
                'valid_until': booking.valid_until.isoformat(),
                'booking_date': booking.booking_date.isoformat()
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


@login_required
@csrf_exempt
def mark_booking_verified(request):
    """
    Mark booking as verified and optionally collect remaining payment
    """
    # Check if user is in Staff group
    if not request.user.groups.filter(name='StaffMembers').exists():
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
