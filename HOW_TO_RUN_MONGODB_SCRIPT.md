# How to Run MongoDB Shell Script

## Option 1: MongoDB Shell (mongosh) - Recommended

### Step 1: Open Terminal/Command Prompt

**Windows:**
- Press `Win + R`, type `cmd` or `powershell`, press Enter
- Or open Git Bash (if you have Git installed)

**Mac/Linux:**
- Open Terminal

### Step 2: Connect to MongoDB

If MongoDB is running locally (default port 27017):

```bash
mongosh
```

Or if you need to specify connection details:

```bash
# Local MongoDB
mongosh mongodb://localhost:27017/

# MongoDB Atlas (Cloud)
mongosh "mongodb+srv://username:password@cluster.mongodb.net/"

# With database name
mongosh mongodb://localhost:27017/tsb_database
```

### Step 3: Select Your Database

Once connected, select your database:

```javascript
use tsb_database
```

### Step 4: Run the Script

Copy and paste the entire script from `MONGODB_TEST_DATA_JSON.md` into the MongoDB shell and press Enter.

---

## Option 2: MongoDB Compass (GUI) - Easiest

### Step 1: Open MongoDB Compass

1. Download MongoDB Compass if you don't have it: https://www.mongodb.com/try/download/compass
2. Connect to your MongoDB instance

### Step 2: Navigate to Your Database

1. Click on `tsb_database` (or your database name)
2. Click on the collection where you want to insert (e.g., `TSBv1_payment`)

### Step 3: Insert Documents

1. Click **"INSERT DOCUMENT"** button
2. Paste the JSON document (remove `ObjectId()`, `ISODate()`, `NumberDecimal()` wrappers - Compass will handle them)
3. Click **"INSERT"**

**Note:** In Compass, you can use plain JSON format:
```json
{
  "user_id": "YOUR_USER_ID_HERE",
  "amount": 1.0,
  "razorpay_order_id": "order_test_1234567890",
  "razorpay_payment_status": "SUCCESS",
  "razorpay_payment_id": "pay_test_1234567890",
  "paid": true,
  "payment_type": "ADVANCE",
  "created_at": "2025-12-31T18:00:00.000Z"
}
```

---

## Option 3: Using Python Script (Alternative)

Create a file `insert_test_data.py`:

```python
import pymongo
from datetime import datetime, timedelta
from decimal import Decimal
from bson import ObjectId, Decimal128

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["tsb_database"]

# Get IDs
user = db.auth_user.find_one({}, {"_id": 1, "username": 1})
customer = db.TSBv1_customer.find_one({"user_id": user["_id"]}, {"_id": 1, "name": 1})
service = db.TSBv1_services.find_one({"supports_advance_payment": True}, {"_id": 1, "title": 1})

# Create Payment
payment = db.TSBv1_payment.insert_one({
    "user_id": user["_id"],
    "amount": 1.0,
    "razorpay_order_id": f"order_test_{int(datetime.now().timestamp())}",
    "razorpay_payment_status": "SUCCESS",
    "razorpay_payment_id": f"pay_test_{int(datetime.now().timestamp())}",
    "paid": True,
    "payment_type": "ADVANCE",
    "created_at": datetime.now()
})

# Create AdvanceBooking
booking_date = datetime.now() + timedelta(days=1)
valid_until = booking_date.replace(hour=23, minute=59, second=59, microsecond=999000)

import random
import string
chars = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
booking_code = ''.join(random.choices(chars, k=12))

booking = db.TSBv1_advancebooking.insert_one({
    "booking_code": booking_code,
    "qr_code_data": "",
    "qr_hash": f"test_hash_{int(datetime.now().timestamp())}",
    "user_id": user["_id"],
    "customer_id": customer["_id"],
    "service_id": service["_id"],
    "quantity": 1,
    "booking_date": booking_date,
    "total_amount": Decimal128("500.00"),
    "advance_paid": Decimal128("1.00"),
    "remaining_amount": Decimal128("499.00"),
    "created_at": datetime.now(),
    "valid_until": valid_until,
    "verified_at": None,
    "status": "PENDING",
    "advance_payment_id": payment.inserted_id,
    "final_payment_id": None,
    "verified_by_staff": "",
    "verification_ip": None,
    "verification_attempts": 0
})

print(f"✅ Booking Code: {booking_code}")
print("🔗 Staff Login: /staff/login/")
print("🔑 PIN: 123456")
```

Run it:
```bash
python insert_test_data.py
```

---

## Quick Check: Is MongoDB Running?

### Windows:
```bash
# Check if MongoDB service is running
sc query MongoDB
```

### Mac/Linux:
```bash
# Check if MongoDB is running
ps aux | grep mongod
```

### Start MongoDB (if not running):

**Windows:**
```bash
net start MongoDB
```

**Mac (Homebrew):**
```bash
brew services start mongodb-community
```

**Linux:**
```bash
sudo systemctl start mongod
```

---

## Common Connection Strings

### Local MongoDB (Default):
```
mongodb://localhost:27017/
```

### MongoDB Atlas (Cloud):
```
mongodb+srv://username:password@cluster.mongodb.net/dbname
```

### With Authentication:
```
mongodb://username:password@localhost:27017/tsb_database
```

---

## Troubleshooting

### "mongosh: command not found"
- Install MongoDB Shell: https://www.mongodb.com/try/download/shell
- Or use `mongo` (older version) if installed

### "Connection refused"
- MongoDB is not running - start it first
- Check if port 27017 is correct

### "Authentication failed"
- Check your username/password
- Check if authentication is required in your MongoDB setup

### "Database not found"
- MongoDB will create the database automatically when you insert data
- Just use `use tsb_database` and it will be created

---

## Recommended: Use MongoDB Compass

**Easiest method for beginners:**
1. Download MongoDB Compass
2. Connect to your database
3. Click on collection
4. Click "INSERT DOCUMENT"
5. Paste JSON and click INSERT

No command line needed! 🎉

