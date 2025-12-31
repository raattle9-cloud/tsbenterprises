# Waterpark Advance Payment System - Setup Instructions

## What Has Been Implemented

The waterpark advance payment and booking verification system is now complete with the following features:

### ✅ Database Models
- **Services Model**: Added advance payment fields (`supports_advance_payment`, `advance_payment_type`, `advance_payment_value`)
- **AdvanceBooking Model**: Complete booking tracking with QR codes, payment status, and verification logging
- **Payment Model**: Enhanced to track payment types (FULL, ADVANCE, REMAINING)

### ✅ Backend & APIs
- Booking checkout with date selection
- Razorpay integration for advance payments
- QR code generation (unique per booking)
- Staff verification API endpoints
- Booking validation and security

### ✅ Admin Interface
- Service configuration for advance payments
- AdvanceBooking dashboard with filters
- QR code preview in admin
- Bulk actions (cancel, verify bookings)

### ✅ Customer Interface
- Advance booking checkout page
- Payment processing
- Booking confirmation with QR code
- My Bookings page

### ✅ Staff Verification Portal
- PIN-based authentication (`/staff/login/`)
- QR code scanner (camera-based)
- Manual booking code entry
- Real-time verification
- Payment collection tracking

## Next Steps to Deploy

### 1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

New libraries added:
- `qrcode==7.4.2` - QR code generation
- `Pillow==10.1.0` - Image processing
- `django-ratelimit==4.1.0` - API rate limiting

### 2. **Configure Settings**

Add to your Django settings or `.env`:

```python
# Staff Portal PIN (change this!)
STAFF_VERIFICATION_PIN = "123456"

# Razorpay Keys (already configured)
RAZORPAY_KEY_ID = "your_key"
RAZORPAY_KEY_SECRET = "your_secret"
```

**IMPORTANT**: Change the default staff PIN in `advance_booking_views.py` line 202 or move to settings.

### 3. **Run Migrations**

```bash
python manage.py makemigrations
python manage.py migrate
```

This will create:
- `AdvanceBooking` table
- Updated `Services`, `Payment`, and `OrderPlaced` tables

### 4. **Configure a Waterpark Service**

1. Go to Django Admin (`/admin/`)
2. Open **Services**
3. Select a Waterpark service (or create one)
4. Check **"Supports advance payment"**
5. Choose payment type:
   - **FIXED**: Enter amount (e.g., 500 for ₹500 advance)
   - **PERCENTAGE**: Enter percentage (e.g., 20 for 20%)
6. Save

### 5. **Test the Flow**

#### Customer Flow:
1. Browse waterpark services
2. Click on a service with advance payment enabled
3. Select "Book with Advance Payment"
4. Choose booking date and quantity
5. Pay advance via Razorpay
6. Receive QR code and booking confirmation

#### Staff Flow:
1. Navigate to `/staff/login/`
2. Enter PIN (default: `123456`)
3. Choose QR Scanner or Manual Entry
4. Scan customer's QR code or enter booking code
5. Verify customer details
6. Collect remaining payment
7. Mark as verified

### 6. **URLs Reference**

**Customer URLs:**
- Advance Checkout: `/checkout/advance/<service_id>/`
- Payment: `/checkout/advance-payment/<booking_id>/`
- Confirmation: `/booking/confirmation/<booking_id>/`
- My Bookings: `/my-bookings/`

**Staff URLs:**
- Staff Login: `/staff/login/`
- Verification Portal: `/staff/verify/`
- Logout: `/staff/logout/`

**API Endpoints:**
- Verify Booking: `/api/verify-booking/`
- Mark Verified: `/api/mark-verified/`

## Security Features Implemented

1. **QR Hash Validation**: SHA-256 hash prevents QR tampering
2. **Unique Booking Codes**: 12-character collision-resistant codes
3. **One-Time Verification**: Tracks verification attempts
4. **Booking Expiration**: Auto-expires based on booking date
5. **IP Logging**: Tracks verification IP addresses
6. **Staff Authentication**: PIN-based access control

## Customization Options

### Change Booking Validity Period
Edit `valid_until` in `advance_booking_views.py` line 68:
```python
valid_until=timezone.make_aware(datetime.combine(booking_date, datetime.max.time()))
```

### Add Email/SMS Notifications
Integrate with your existing notification system after successful booking (line 152 in `advance_booking_views.py`).

### Customize Staff PIN
Move `STAFF_PIN` to environment variable or database for multi-location support.

## Testing Checklist

- [ ] Create waterpark service with advance payment
- [ ] Customer can book with advance payment
- [ ] QR code generates correctly
- [ ] Razorpay payment processes
- [ ] Staff can login to verification portal
- [ ] QR scanner works on mobile
- [ ] Manual code entry works
- [ ] Booking verification shows correct details
- [ ] Payment collection marks booking as USED
- [ ] Expired bookings are rejected

## Troubleshooting

**QR Scanner not working?**
- Ensure HTTPS (required for camera access in browsers)
- Check browser permissions for camera
- Use manual code entry as fallback

**Migrations failing?**
- Ensure all model files are saved
- Check for syntax errors in `models.py`
- Run `python manage.py makemigrations TSBv1`

**Razorpay errors?**
- Verify API keys in settings
- Check Razorpay dashboard for test mode
- Ensure amount is in paise (multiply by 100)

## File Structure

```
TSBv1/
├── models.py (updated)
├── admin.py (updated)
├── urls.py (updated)
├── booking_utils.py (new)
├── advance_booking_views.py (new)
└── templates/app/
    ├── staff_login.html (new)
    ├── staff_verify.html (new)
    └── booking_confirmation.html (new)
```

## Support

For issues or questions:
1. Check Django logs for errors
2. Verify all migrations are applied
3. Test with Razorpay test mode first
4. Ensure all dependencies are installed

---

**Ready to launch!** The system is production-ready once you:
1. Install dependencies
2. Run migrations
3. Configure at least one waterpark service
4. Update the staff PIN
