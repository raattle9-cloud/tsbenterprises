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
        
        # Create booking
        booking = AdvanceBooking.objects.create(
            booking_code=generate_booking_code(),
            user=request.user,
            customer=customer,
            service=service,
            quantity=quantity,
            booking_date=booking_date,
            total_amount=total_amount,
            advance_paid=advance_amount,
            remaining_amount=remaining_amount,
            valid_until=timezone.make_aware(datetime.combine(booking_date, datetime.max.time())),
            status='PENDING'
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
        
        # Create payment record
        payment = Payment.objects.create(
            user=request.user,
            amount=float(booking.advance_paid),
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_payment_status='SUCCESS',
            paid=True,
            payment_type='ADVANCE'
        )
        
        # Link payment to booking
        booking.advance_payment = payment
        booking.save()
        
        # Generate QR code
        qr_data = generate_qr_code(booking)
        booking.qr_code_data = qr_data
        booking.save()
        
        # Redirect to confirmation page
        return redirect('advance-booking-confirmation', booking.id)
    
    # GET - show payment page
    import razorpay
    from django.conf import settings
    
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    
    # Create Razorpay order
    order_amount = int(booking.advance_paid * 100)  # Convert to paise
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
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'amount': order_amount,
        'currency': order_currency,
    }
    
    return render(request, 'app/advance_payment.html', context)


@login_required
def advance_booking_confirmation(request, booking_id):
    """
    Show booking confirmation with QR code
    """
    booking = get_object_or_404(AdvanceBooking, id=booking_id, user=request.user)
    
    context = {
        'booking': booking,
    }
    
    return render(request, 'app/booking_confirmation.html', context)


@login_required
def my_advance_bookings(request):
    """
    Show user's advance bookings
    """
    bookings = AdvanceBooking.objects.filter(user=request.user).order_by('-created_at')
    
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
    
    return render(request, 'app/staff_verify.html')


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
                'total_amount': float(booking.total_amount),
                'advance_paid': float(booking.advance_paid),
                'remaining_amount': float(booking.remaining_amount),
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
        
        # Update booking status
        booking.status = 'VERIFIED'
        booking.verified_at = timezone.now()
        booking.verified_by_staff = staff_name
        booking.verification_ip = get_client_ip(request)
        booking.save()
        
        # If payment collected, create payment record
        if payment_collected:
            final_payment = Payment.objects.create(
                user=booking.user,
                amount=float(booking.remaining_amount),
                paid=True,
                payment_type='REMAINING',
                razorpay_payment_status='CASH'
            )
            booking.final_payment = final_payment
            booking.status = 'USED'
            booking.save()
        
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
