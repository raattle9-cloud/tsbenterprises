# Staff Login & Payment Storage Guide

## Staff Login

### How Staff Login Works

1. **URL**: `/staff/login/`
2. **PIN**: `123456` (hardcoded in `TSBv1/advance_booking_views.py` line 226)
3. **Authentication**: Session-based (stores `staff_authenticated` in session)
4. **After Login**: Redirects to `/staff/verify/` (staff verification portal)

### Staff Login Flow

```
User enters PIN → Validates against STAFF_PIN → Sets session → Redirects to verification portal
```

---

## How Payments Are Stored in Database

### 1. Payment Model Structure

**Collection**: `TSBv1_payment`

**Fields**:

```javascript
{
  _id: ObjectId,                    // Auto-generated MongoDB ID
  user_id: ObjectId,                 // Foreign key to auth_user
  amount: Float,                     // Payment amount (e.g., 1.0 for ₹1)
  razorpay_order_id: String,         // Razorpay order ID (nullable)
  razorpay_payment_status: String,   // Payment status (nullable)
  razorpay_payment_id: String,       // Razorpay payment ID (nullable)
  paid: Boolean,                     // Payment status (default: false)
  payment_type: String,              // "FULL" or "ADVANCE" (default: "FULL")
  created_at: ISODate               // Auto-generated timestamp
}
```

### 2. AdvanceBooking Model Structure

**Collection**: `TSBv1_advancebooking`

**Fields**:

```javascript
{
  _id: ObjectId,                     // Auto-generated MongoDB ID
  booking_code: String,              // Unique 12-character code (e.g., "ABC123XYZ456")
  qr_code_data: String,              // Base64 QR code image (optional)
  qr_hash: String,                   // SHA-256 hash for validation (optional, nullable)

  // Foreign Keys
  user_id: ObjectId,                 // Foreign key to auth_user
  customer_id: ObjectId,             // Foreign key to TSBv1_customer
  service_id: ObjectId,              // Foreign key to TSBv1_services

  // Booking Details
  quantity: Integer,                 // Number of tickets/services (default: 1)
  booking_date: ISODate,             // Date for which booking is made
  total_amount: Decimal128,          // Total booking amount (e.g., Decimal128("500.00"))
  advance_paid: Decimal128,          // Advance payment amount (e.g., Decimal128("1.00"))
  remaining_amount: Decimal128,     // Remaining amount to pay (e.g., Decimal128("499.00"))

  // Timestamps
  created_at: ISODate,               // Auto-generated
  valid_until: ISODate,              // Booking expiration time
  verified_at: ISODate,              // When verified by staff (nullable)

  // Status
  status: String,                    // "PENDING", "VERIFIED", "USED", "EXPIRED", "CANCELLED"

  // Payment References
  advance_payment_id: ObjectId,      // Foreign key to TSBv1_payment (nullable)
  final_payment_id: ObjectId,        // Foreign key to TSBv1_payment (nullable)

  // Verification Tracking
  verified_by_staff: String,         // Staff name who verified (nullable)
  verification_ip: String,           // IP address of verification (nullable)
  verification_attempts: Integer     // Number of verification attempts (default: 0)
}
```

---

## Manual Test Data Insertion in MongoDB

### Step 1: Get Required IDs

First, you need to get the ObjectIds for:

- A User (from `auth_user` collection)
- A Customer (from `TSBv1_customer` collection)
- A Service (from `TSBv1_services` collection)

**Example MongoDB Queries**:

```javascript
// Get a user ID
db.auth_user.findOne({}, { _id: 1, username: 1 });

// Get a customer ID
db.TSBv1_customer.findOne({}, { _id: 1, name: 1 });

// Get a service ID (preferably one with advance_payment enabled)
db.TSBv1_services.findOne(
  { supports_advance_payment: true },
  { _id: 1, title: 1 }
);
```

### Step 2: Create a Payment Record

```javascript
db.TSBv1_payment.insertOne({
  user_id: ObjectId("YOUR_USER_ID_HERE"),
  amount: 1.0, // ₹1 for testing
  razorpay_order_id: "order_test_12345",
  razorpay_payment_status: "SUCCESS",
  razorpay_payment_id: "pay_test_12345",
  paid: true,
  payment_type: "ADVANCE",
  created_at: new Date(),
});
```

**Note**: Save the returned `_id` - you'll need it for the AdvanceBooking record.

### Step 3: Generate Booking Code

Booking codes are 12 characters, excluding confusing characters (0, O, 1, I, L).

**Example booking codes**:

- `ABC234DEF567`
- `XYZ789GHI123`
- `MNP456QRS890`

### Step 4: Generate QR Hash (Optional but Recommended)

The QR hash is generated using:

```python
import hashlib
from django.conf import settings

booking_code = "ABC234DEF567"
booking_id = "YOUR_BOOKING_ID"  # Will be generated after insert
secret_key = "YOUR_SECRET_KEY"  # From Django settings

data = f"{booking_code}{secret_key}{booking_id}"
qr_hash = hashlib.sha256(data.encode()).hexdigest()
```

**For testing, you can use a dummy hash**:

```javascript
qr_hash: "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2";
```

### Step 5: Create AdvanceBooking Record

```javascript
// Calculate dates
var today = new Date();
var bookingDate = new Date(
  today.getFullYear(),
  today.getMonth(),
  today.getDate() + 1
); // Tomorrow
var validUntil = new Date(bookingDate);
validUntil.setHours(23, 59, 59, 999); // End of booking date

db.TSBv1_advancebooking.insertOne({
  booking_code: "ABC234DEF567", // Unique 12-char code
  qr_code_data: "", // Can be empty for testing
  qr_hash: "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2", // Optional

  // Foreign Keys (replace with actual ObjectIds)
  user_id: ObjectId("YOUR_USER_ID_HERE"),
  customer_id: ObjectId("YOUR_CUSTOMER_ID_HERE"),
  service_id: ObjectId("YOUR_SERVICE_ID_HERE"),

  // Booking Details
  quantity: 1,
  booking_date: bookingDate,
  total_amount: NumberDecimal("500.00"), // Total amount
  advance_paid: NumberDecimal("1.00"), // Advance paid (₹1 for testing)
  remaining_amount: NumberDecimal("499.00"), // Remaining amount

  // Timestamps
  created_at: new Date(),
  valid_until: validUntil,
  verified_at: null, // Will be set when verified

  // Status
  status: "PENDING", // "PENDING", "VERIFIED", "USED", "EXPIRED", "CANCELLED"

  // Payment References
  advance_payment_id: ObjectId("YOUR_PAYMENT_ID_HERE"), // From Step 2
  final_payment_id: null, // For final payment (if any)

  // Verification Tracking
  verified_by_staff: "",
  verification_ip: null,
  verification_attempts: 0,
});
```

---

## Complete Example MongoDB Script

```javascript
// ============================================
// COMPLETE TEST DATA INSERTION SCRIPT
// ============================================

// Step 1: Get IDs (run these first to get actual IDs)
var userId = db.auth_user.findOne({}, { _id: 1 })._id;
var customerId = db.TSBv1_customer.findOne({ user_id: userId }, { _id: 1 })._id;
var serviceId = db.TSBv1_services.findOne(
  { supports_advance_payment: true },
  { _id: 1 }
)._id;

print("User ID: " + userId);
print("Customer ID: " + customerId);
print("Service ID: " + serviceId);

// Step 2: Create Payment
var payment = db.TSBv1_payment.insertOne({
  user_id: userId,
  amount: 1.0,
  razorpay_order_id: "order_test_" + Date.now(),
  razorpay_payment_status: "SUCCESS",
  razorpay_payment_id: "pay_test_" + Date.now(),
  paid: true,
  payment_type: "ADVANCE",
  created_at: new Date(),
});

var paymentId = payment.insertedId;
print("Payment ID: " + paymentId);

// Step 3: Create AdvanceBooking
var bookingDate = new Date();
bookingDate.setDate(bookingDate.getDate() + 1); // Tomorrow
var validUntil = new Date(bookingDate);
validUntil.setHours(23, 59, 59, 999);

var booking = db.TSBv1_advancebooking.insertOne({
  booking_code:
    "TEST" +
    Math.random()
      .toString(36)
      .substring(2, 14)
      .toUpperCase()
      .replace(/[0O1IL]/g, "X"),
  qr_code_data: "",
  qr_hash: "test_hash_" + Date.now(),
  user_id: userId,
  customer_id: customerId,
  service_id: serviceId,
  quantity: 1,
  booking_date: bookingDate,
  total_amount: NumberDecimal("500.00"),
  advance_paid: NumberDecimal("1.00"),
  remaining_amount: NumberDecimal("499.00"),
  created_at: new Date(),
  valid_until: validUntil,
  verified_at: null,
  status: "PENDING",
  advance_payment_id: paymentId,
  final_payment_id: null,
  verified_by_staff: "",
  verification_ip: null,
  verification_attempts: 0,
});

var bookingId = booking.insertedId;
print("Booking ID: " + bookingId);
print(
  "Booking Code: " +
    db.TSBv1_advancebooking.findOne({ _id: bookingId }).booking_code
);
print("\n✅ Test data created successfully!");
print(
  "📋 Booking Code: " +
    db.TSBv1_advancebooking.findOne({ _id: bookingId }).booking_code
);
print("🔗 Access staff login at: /staff/login/");
print("🔑 PIN: 123456");
```

---

## Testing Staff Login

1. **Access**: Navigate to `http://127.0.0.1:8000/staff/login/`
2. **Enter PIN**: `123456`
3. **Verify Booking**:
   - Enter the booking code from your test data
   - Or scan the QR code (if generated)
4. **Mark as Verified**: The booking status will change to "VERIFIED"

---

## Important Notes

1. **Decimal128 Fields**: MongoDB uses `NumberDecimal()` for decimal fields. In the shell, use:

   ```javascript
   NumberDecimal("500.00");
   ```

2. **Foreign Keys**: All `_id` fields must be valid ObjectIds that exist in their respective collections.

3. **Booking Code Uniqueness**: Booking codes must be unique. The system generates 12-character codes excluding confusing characters.

4. **Status Values**: Valid status values are:

   - `"PENDING"` - Awaiting verification
   - `"VERIFIED"` - Verified by staff
   - `"USED"` - Already used
   - `"EXPIRED"` - Booking expired
   - `"CANCELLED"` - Cancelled

5. **QR Hash**: While optional, it's recommended for security. The hash is validated when scanning QR codes.

---

## Quick Reference

### Staff Login

- **URL**: `/staff/login/`
- **PIN**: `123456`
- **Session Key**: `staff_authenticated`

### Collections

- `TSBv1_payment` - Payment records
- `TSBv1_advancebooking` - Advance booking records
- `auth_user` - Django users
- `TSBv1_customer` - Customer profiles
- `TSBv1_services` - Service listings

### Key Fields for Verification

- `booking_code` - Used for manual entry
- `qr_hash` - Used for QR code validation
- `status` - Must be "PENDING" for verification
- `valid_until` - Booking must not be expired
