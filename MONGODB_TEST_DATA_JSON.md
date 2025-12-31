# MongoDB Test Data - Ready to Copy-Paste

## Step 1: Get Your IDs First

Run these queries in MongoDB to get your actual IDs:

```javascript
// Get User ID
db.auth_user.findOne({}, {_id: 1, username: 1})

// Get Customer ID (linked to the user above)
db.TSBv1_customer.findOne({}, {_id: 1, name: 1, user_id: 1})

// Get Service ID (with advance payment enabled)
db.TSBv1_services.findOne({supports_advance_payment: true}, {_id: 1, title: 1})
```

**Copy the `_id` values from the results above.**

---

## Step 2: Payment Document (Copy-Paste This)

Replace `YOUR_USER_ID_HERE` with the actual ObjectId from Step 1:

```json
{
  "user_id": ObjectId("YOUR_USER_ID_HERE"),
  "amount": 1.0,
  "razorpay_order_id": "order_test_1234567890",
  "razorpay_payment_status": "SUCCESS",
  "razorpay_payment_id": "pay_test_1234567890",
  "paid": true,
  "payment_type": "ADVANCE",
  "created_at": ISODate("2025-12-31T18:00:00.000Z")
}
```

**After inserting, copy the returned `_id` - you'll need it for the AdvanceBooking document.**

---

## Step 3: AdvanceBooking Document (Copy-Paste This)

Replace these placeholders:
- `YOUR_USER_ID_HERE` - User ObjectId from Step 1
- `YOUR_CUSTOMER_ID_HERE` - Customer ObjectId from Step 1
- `YOUR_SERVICE_ID_HERE` - Service ObjectId from Step 1
- `YOUR_PAYMENT_ID_HERE` - Payment ObjectId from Step 2

```json
{
  "booking_code": "TEST12345678",
  "qr_code_data": "",
  "qr_hash": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2",
  "user_id": ObjectId("YOUR_USER_ID_HERE"),
  "customer_id": ObjectId("YOUR_CUSTOMER_ID_HERE"),
  "service_id": ObjectId("YOUR_SERVICE_ID_HERE"),
  "quantity": 1,
  "booking_date": ISODate("2026-01-01T00:00:00.000Z"),
  "total_amount": NumberDecimal("500.00"),
  "advance_paid": NumberDecimal("1.00"),
  "remaining_amount": NumberDecimal("499.00"),
  "created_at": ISODate("2025-12-31T18:00:00.000Z"),
  "valid_until": ISODate("2026-01-01T23:59:59.999Z"),
  "verified_at": null,
  "status": "PENDING",
  "advance_payment_id": ObjectId("YOUR_PAYMENT_ID_HERE"),
  "final_payment_id": null,
  "verified_by_staff": "",
  "verification_ip": null,
  "verification_attempts": 0
}
```

---

## Complete MongoDB Shell Script (All-in-One)

Copy and paste this entire script into MongoDB shell. It will automatically get IDs and create both documents:

```javascript
// ============================================
// COMPLETE COPY-PASTE SCRIPT
// ============================================

// Get IDs
var user = db.auth_user.findOne({}, {_id: 1, username: 1});
var customer = db.TSBv1_customer.findOne({user_id: user._id}, {_id: 1, name: 1});
var service = db.TSBv1_services.findOne({supports_advance_payment: true}, {_id: 1, title: 1});

if (!user || !customer || !service) {
    print("❌ ERROR: Missing required data!");
    print("User: " + (user ? "Found" : "NOT FOUND"));
    print("Customer: " + (customer ? "Found" : "NOT FOUND"));
    print("Service: " + (service ? "Found" : "NOT FOUND"));
} else {
    print("✅ Found all required data:");
    print("User: " + user.username + " (" + user._id + ")");
    print("Customer: " + customer.name + " (" + customer._id + ")");
    print("Service: " + service.title + " (" + service._id + ")");
    print("\n");
    
    // Create Payment
    var payment = db.TSBv1_payment.insertOne({
        user_id: user._id,
        amount: 1.0,
        razorpay_order_id: "order_test_" + Date.now(),
        razorpay_payment_status: "SUCCESS",
        razorpay_payment_id: "pay_test_" + Date.now(),
        paid: true,
        payment_type: "ADVANCE",
        created_at: new Date()
    });
    
    print("✅ Payment created: " + payment.insertedId);
    
    // Calculate dates
    var bookingDate = new Date();
    bookingDate.setDate(bookingDate.getDate() + 1); // Tomorrow
    var validUntil = new Date(bookingDate);
    validUntil.setHours(23, 59, 59, 999);
    
    // Generate unique booking code
    var chars = "ABCDEFGHJKMNPQRSTUVWXYZ23456789";
    var bookingCode = "";
    for (var i = 0; i < 12; i++) {
        bookingCode += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    
    // Create AdvanceBooking
    var booking = db.TSBv1_advancebooking.insertOne({
        booking_code: bookingCode,
        qr_code_data: "",
        qr_hash: "test_hash_" + Date.now(),
        user_id: user._id,
        customer_id: customer._id,
        service_id: service._id,
        quantity: 1,
        booking_date: bookingDate,
        total_amount: NumberDecimal("500.00"),
        advance_paid: NumberDecimal("1.00"),
        remaining_amount: NumberDecimal("499.00"),
        created_at: new Date(),
        valid_until: validUntil,
        verified_at: null,
        status: "PENDING",
        advance_payment_id: payment.insertedId,
        final_payment_id: null,
        verified_by_staff: "",
        verification_ip: null,
        verification_attempts: 0
    });
    
    print("✅ Booking created: " + booking.insertedId);
    print("\n");
    print("═══════════════════════════════════════");
    print("✅ TEST DATA CREATED SUCCESSFULLY!");
    print("═══════════════════════════════════════");
    print("📋 Booking Code: " + bookingCode);
    print("🔗 Staff Login: http://127.0.0.1:8000/staff/login/");
    print("🔑 PIN: 123456");
    print("═══════════════════════════════════════");
}
```

---

## Quick Manual Insert (If Script Doesn't Work)

### Payment Document:
```json
{
  "user_id": ObjectId("REPLACE_WITH_USER_ID"),
  "amount": 1.0,
  "razorpay_order_id": "order_test_1234567890",
  "razorpay_payment_status": "SUCCESS",
  "razorpay_payment_id": "pay_test_1234567890",
  "paid": true,
  "payment_type": "ADVANCE",
  "created_at": ISODate("2025-12-31T18:00:00.000Z")
}
```

### AdvanceBooking Document:
```json
{
  "booking_code": "TEST12345678",
  "qr_code_data": "",
  "qr_hash": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2",
  "user_id": ObjectId("REPLACE_WITH_USER_ID"),
  "customer_id": ObjectId("REPLACE_WITH_CUSTOMER_ID"),
  "service_id": ObjectId("REPLACE_WITH_SERVICE_ID"),
  "quantity": 1,
  "booking_date": ISODate("2026-01-01T00:00:00.000Z"),
  "total_amount": NumberDecimal("500.00"),
  "advance_paid": NumberDecimal("1.00"),
  "remaining_amount": NumberDecimal("499.00"),
  "created_at": ISODate("2025-12-31T18:00:00.000Z"),
  "valid_until": ISODate("2026-01-01T23:59:59.999Z"),
  "verified_at": null,
  "status": "PENDING",
  "advance_payment_id": ObjectId("REPLACE_WITH_PAYMENT_ID"),
  "final_payment_id": null,
  "verified_by_staff": "",
  "verification_ip": null,
  "verification_attempts": 0
}
```

---

## Notes:

1. **ObjectId()** - Replace with actual ObjectIds from your database
2. **NumberDecimal()** - Required for decimal fields in MongoDB
3. **ISODate()** - For date fields
4. **booking_code** - Must be unique (12 characters, no 0, O, 1, I, L)
5. After inserting Payment, copy its `_id` and use it in `advance_payment_id` field

