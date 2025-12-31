# Test Workflow Guide - Advance Booking System

## Overview
This guide helps you test the complete advance booking workflow with a ₹1 test service.

## Step 1: Create Test Service

Run the management command to create a test service:

```bash
python manage.py create_test_service
```

This creates:
- **Service Name**: "Test Waterpark - ₹1"
- **Price**: ₹1.00
- **Advance Payment**: ₹1.00 (Fixed)
- **Category**: Waterpark

## Step 2: Complete Customer Flow

### 2.1 Browse and Select Service
1. Visit: `http://127.0.0.1:8000/services/`
2. Find "Test Waterpark - ₹1" or visit directly: `/category-detail/<service_id>/`
3. Click "Book with Advance Payment" button

### 2.2 Advance Checkout
1. Select booking date (must be today or future)
2. Select quantity (default: 1)
3. Choose customer profile
4. Review price summary:
   - Total Price: ₹1.00
   - Pay Online Now: ₹1.00
   - Pay at Venue: ₹0.00

### 2.3 Payment
1. Click "Pay Advance & Book"
2. Razorpay payment window opens
3. **For Testing**: Use Razorpay test card:
   - Card Number: `4111 1111 1111 1111`
   - CVV: Any 3 digits (e.g., `123`)
   - Expiry: Any future date (e.g., `12/25`)
   - Name: Any name

### 2.4 Confirmation & Receipt
After successful payment, you'll see:
- ✅ **QR Code**: Scannable QR code for entry
- ✅ **Booking Code**: 12-character code (e.g., `ABC123XYZ456`)
- ✅ **Booking Details**: Service, date, quantity
- ✅ **Payment Summary**: Total, paid, remaining amounts
- ✅ **Print Button**: Print-friendly receipt

**Important**: Take a screenshot or print this page - you'll need the QR code or booking code for staff verification!

## Step 3: Staff Verification Flow

### 3.1 Staff Login
1. Visit: `http://127.0.0.1:8000/staff/login/`
2. Enter PIN: `123456` (default)
3. Click "Login"

### 3.2 Verify Booking

**Option A: QR Code Scanner**
1. Click "Scan QR Code" button
2. Allow camera access
3. Scan the QR code from customer's confirmation page
4. Booking details will appear automatically

**Option B: Manual Entry**
1. Click "Manual Entry" tab
2. Enter the 12-character booking code
3. Click "Verify Booking"
4. Booking details will appear

### 3.3 Verify Details
The system will show:
- ✅ Booking Code
- ✅ Customer Name & Phone
- ✅ Service Name
- ✅ Quantity
- ✅ Booking Date
- ✅ Total Amount: ₹1.00
- ✅ Advance Paid: ₹1.00
- ✅ Remaining Amount: ₹0.00

### 3.4 Mark as Verified
1. Review all details
2. If payment collected, check "Payment Collected" (if remaining amount > 0)
3. Enter staff name (optional)
4. Click "Mark as Verified"
5. Booking status changes to "VERIFIED"

## Step 4: Verify Receipt Generation

### Check Receipt Contains:
- ✅ QR Code (base64 encoded image)
- ✅ Booking Code (12 characters)
- ✅ Service Details
- ✅ Booking Date
- ✅ Quantity
- ✅ Payment Breakdown:
  - Total Amount
  - Advance Paid
  - Remaining Amount
- ✅ Valid Until Date
- ✅ Print-friendly format

### Test Print Functionality
1. On confirmation page, click "Print Confirmation"
2. Verify print preview shows:
   - QR code
   - All booking details
   - Payment summary
   - No navigation/buttons (hidden in print)

## Step 5: Test Edge Cases

### 5.1 Already Verified Booking
- Try verifying the same booking twice
- Should show "Already Verified" message

### 5.2 Expired Booking
- Create booking with past date
- Try to verify
- Should show "Booking Expired" message

### 5.3 Invalid QR Code
- Try scanning a fake/modified QR code
- Should show "Invalid QR code" error

### 5.4 Missing Customer Profile
- Try booking without customer profile
- Should redirect to profile creation

## Step 6: Check Database Records

### Verify in Django Admin (`/admin/`)

**AdvanceBooking Model:**
- ✅ Booking created with correct details
- ✅ `booking_code` is unique 12-character code
- ✅ `qr_code_data` contains base64 image
- ✅ `qr_hash` is SHA-256 hash
- ✅ `advance_paid` = ₹1.00
- ✅ `total_amount` = ₹1.00
- ✅ `remaining_amount` = ₹0.00
- ✅ `status` = "PENDING" (before verification)

**Payment Model:**
- ✅ Payment record created
- ✅ `amount` = ₹1.00
- ✅ `payment_type` = "ADVANCE"
- ✅ `paid` = True
- ✅ Razorpay IDs stored

## Troubleshooting

### QR Code Not Generating
- Check if `qrcode` package is installed: `pip install qrcode[pil]`
- Verify booking has `qr_hash` set
- Check browser console for errors

### Payment Not Processing
- Verify Razorpay keys in settings
- Check Razorpay dashboard for test mode
- Ensure amount is in paise (₹1 = 100 paise)

### Staff Verification Not Working
- Check staff is logged in (session)
- Verify booking exists in database
- Check QR hash validation

### Decimal128 Errors
- All Decimal128 conversions are handled
- If errors occur, check `convert_decimal128_to_float()` function

## Test Checklist

- [ ] Test service created successfully
- [ ] Customer can browse and select service
- [ ] Advance checkout page loads correctly
- [ ] Price calculations are correct
- [ ] Razorpay payment processes
- [ ] QR code generates and displays
- [ ] Booking confirmation page shows all details
- [ ] Receipt is print-friendly
- [ ] Staff can login
- [ ] Staff can scan QR code
- [ ] Staff can manually enter booking code
- [ ] Staff can verify booking
- [ ] Booking status updates correctly
- [ ] Database records are correct
- [ ] Edge cases handled properly

## URLs Reference

**Customer URLs:**
- Services: `/services/`
- Service Detail: `/category-detail/<id>/`
- Advance Checkout: `/checkout/advance/<service_id>/`
- Payment: `/checkout/advance-payment/<booking_id>/`
- Confirmation: `/booking/confirmation/<booking_id>/`
- My Bookings: `/my-bookings/`

**Staff URLs:**
- Staff Login: `/staff/login/`
- Verification Portal: `/staff/verify/`
- Staff Logout: `/staff/logout/`

**API Endpoints:**
- Verify Booking: `/api/verify-booking/` (POST)
- Mark Verified: `/api/mark-verified/` (POST)

## Notes

- Default staff PIN: `123456` (change in `advance_booking_views.py`)
- Test service price: ₹1.00 (easy for testing)
- QR codes are base64 encoded images
- Booking codes exclude confusing characters (0, O, 1, I, L)
- All Decimal128 conversions are handled automatically

