# TSB Enterprises - Staff Verification Portal & Advance Booking

This document outlines the features and setup instructions for the Staff Verification Portal and the Advance Booking system.

## Features

### 1. Conditional Service Buttons
- Services that support advance booking (e.g., Waterparks) will display an orange **"Book Now"** button.
- Services that do not support advance booking will display a green **"Buy Now"** button.
- This ensures users are directed to the correct checkout flow depending on the service type.

### 2. Secure Staff Portal
- **Unified Login**: Staff members use the standard Django login system.
- **Auto-Redirect**: Users in the `StaffMembers` group are automatically redirected to the `/staff/verify/` portal upon login.
- **QR Code Scanner**: Integrated camera-based QR scanner for quick booking verification.
- **Manual Entry**: Fallback option to manually enter 6-character booking codes.
- **Anti-Fraud**: Each booking can only be verified **once**. Subsequent scans will show an "Already Used" or "Already Verified" error.

---

## Setup Instructions

### 1. Create Staff Group
Due to technical limitations with certain database drivers, follow these steps in the Django Admin:
1. Go to `/admin/auth/group/`.
2. Click **Add Group**.
3. Name the group exactly: `StaffMembers`.
4. Click **Save**.

### 2. Create Staff User
1. Go to `/admin/auth/user/`.
2. Click **Add User**.
3. Enter desired credentials (e.g., Username: `staff1`, Password: `staff123`).
4. In the user edit screen, scroll to **Groups**.
5. Move `StaffMembers` from "Available groups" to "Chosen groups".
6. Click **Save**.

### 3. Test the Portal
1. Login at `/accounts/login/` with your staff credentials.
2. You should be redirected to `/staff/verify/`.
3. Toggle between **Manual Entry** and **QR Scanner** using the buttons in the portal.

---

## Technical Details

- **Auth View**: Uses a custom `StaffAwareLoginView` to handle group-based redirection.
- **Verification API**: 
  - `POST /api/verify-booking/`: Checks booking code validty and status.
  - `POST /api/mark-verified/`: Updates booking status to `USED` and logs the verifying staff member.
- **QR Library**: Uses `html5-qrcode` for client-side scanning.

---

## Troubleshooting

- **"Access Denied"**: Ensure the user is assigned to the `StaffMembers` group (not `Staff`, which may be corrupted in the DB).
- **Scanner Not Opening**: Ensure the site is running on `https` or `localhost`, as browsers require a secure context for camera access.
- **QR Code Not Recognized**: Ensure the QR code is generated from the `/my-bookings/` section of the user profile.
