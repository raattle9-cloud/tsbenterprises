# Migration Commands Explanation

## What Changed in the Model

I modified the `AdvanceBooking` model's `qr_hash` field from:
```python
qr_hash = models.CharField(max_length=64, unique=True)
```

To:
```python
qr_hash = models.CharField(max_length=64, unique=True, blank=True, null=True)
```

## What the Migration Commands Will Do

### 1. `python manage.py makemigrations`

**Purpose**: Detects changes in your models and creates migration files

**What it will do**:
- Compares your current model definitions with the last migration (0010)
- Detects that `qr_hash` field now has `blank=True, null=True`
- Creates a new migration file (likely `0011_alter_advancebooking_qr_hash.py`)

**The new migration will contain**:
```python
migrations.AlterField(
    model_name='advancebooking',
    name='qr_hash',
    field=models.CharField(blank=True, max_length=64, null=True, unique=True),
)
```

**What this means**:
- The field can now be empty (`blank=True`)
- The field can store NULL values (`null=True`)
- The field still must be unique (when it has a value)

### 2. `python manage.py migrate`

**Purpose**: Applies pending migrations to your database

**What it will do**:
- Reads the new migration file created by `makemigrations`
- Alters the `qr_hash` column in the `AdvanceBooking` collection/table
- Changes the field constraint to allow NULL/empty values

**Database Changes** (MongoDB via djongo):
- Updates the field definition in MongoDB
- Existing records with `qr_hash` values remain unchanged
- New records can now have `qr_hash = None` or empty string

## Why This Change Was Needed

**Before the change**:
- `qr_hash` was required (no `blank=True, null=True`)
- When creating a booking, you had to provide a `qr_hash` immediately
- But the hash is only generated when the QR code is created (after payment)
- This caused issues when creating bookings before payment

**After the change**:
- `qr_hash` can be empty when booking is first created
- Hash is generated later when QR code is created (after payment)
- More flexible workflow: Create booking → Process payment → Generate QR code

## Impact on Existing Data

### Existing Bookings:
- ✅ **No impact** - Existing bookings with `qr_hash` values remain unchanged
- ✅ **No data loss** - All existing data is preserved

### New Bookings:
- ✅ Can be created without `qr_hash` initially
- ✅ `qr_hash` will be set when QR code is generated
- ✅ Works with the current workflow

## Safety Check

**Is it safe to run?**
- ✅ **Yes** - This is a non-destructive change
- ✅ Only adds flexibility (allows NULL/empty)
- ✅ Doesn't remove any data
- ✅ Doesn't change existing constraints (still unique)

**Potential Issues**:
- ⚠️ If you have existing bookings without `qr_hash`, they might need to be updated
- ⚠️ MongoDB (djongo) might handle NULL differently than SQL databases
- ✅ But since we're only making the field more permissive, it should be safe

## Step-by-Step Execution

1. **Run makemigrations**:
   ```bash
   python manage.py makemigrations
   ```
   - Creates migration file
   - Shows what will change
   - **Does NOT modify database yet**

2. **Review the migration** (optional):
   - Check `TSBv1/migrations/0011_*.py` (or next number)
   - Verify it looks correct

3. **Run migrate**:
   ```bash
   python manage.py migrate
   ```
   - Applies the migration
   - **Actually modifies the database**
   - Updates field constraints

## What Happens If You Skip Migrations?

**If you don't run migrations**:
- ❌ Django will complain about model/database mismatch
- ❌ Creating new bookings might fail if `qr_hash` is required
- ❌ You'll see errors when trying to save bookings without `qr_hash`

**So you should run them** to keep your database in sync with your models.

## Summary

| Command | What It Does | Database Changed? |
|---------|-------------|-------------------|
| `makemigrations` | Creates migration file | ❌ No |
| `migrate` | Applies migration to DB | ✅ Yes |

**Result**: The `qr_hash` field can now be empty when bookings are created, and will be populated when QR codes are generated after payment.

