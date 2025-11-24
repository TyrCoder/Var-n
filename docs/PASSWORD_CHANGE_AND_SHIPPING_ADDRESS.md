# Password Change & Shipping Address Management - Implementation Guide

## Overview
Added comprehensive password change functionality and shipping address management features to the Account Details page. Users can now securely change their password with OTP verification (SMS or Email) and manage multiple shipping addresses.

---

## Features Implemented

### 1. **Password Change Functionality**

#### Frontend (accountDetails.html)
- **Password & Security Section**: New section in account details page
- **4-Step Modal Flow**:
  1. **Step 1**: Verify current password
  2. **Step 2**: Choose OTP method (SMS or Email)
  3. **Step 3**: Enter and confirm new password
  4. **Step 4**: Verify OTP code

#### Password Validation
- Minimum 6 characters
- Must contain both letters and numbers
- Password strength verified before OTP step

#### OTP Features
- User selects delivery method: SMS or Email
- 6-digit OTP code
- 10-minute timer with countdown
- Resend OTP button
- Auto-focus between OTP input fields
- Backspace navigation support

#### Backend Routes (app.py)
- `POST /initiate-password-change`: Send OTP via selected method
- `POST /confirm-password-change`: Verify OTP and update password

---

### 2. **Shipping Address Management**

#### Frontend (accountDetails.html)
- **Shipping Addresses Section**: New section to manage saved addresses
- **Address Card Display**:
  - Shows full name, phone, street address, barangay, city, province, postal code
  - Displays address type badge (Shipping, Billing, or Both)
  - Shows "Default" badge for default address
  - Edit, Delete, and Set as Default buttons

#### Address Form Modal
- **Fields**:
  - Full Name (required)
  - Phone Number (required, +63 prefix enforced)
  - Street Address (required)
  - Barangay (required)
  - City (required)
  - Province (required)
  - Postal Code (optional)
  - Address Type (Shipping, Billing, or Both)
  - Set as Default checkbox

- **Features**:
  - Add new address
  - Edit existing address
  - Delete address with confirmation
  - Set default address
  - Empty state when no addresses saved

#### Backend Routes (app.py)
- `GET /get-shipping-addresses`: Fetch all addresses for user
- `GET /get-address/<id>`: Fetch specific address
- `POST /save-shipping-address`: Create new address
- `PUT /update-shipping-address/<id>`: Update existing address
- `DELETE /delete-shipping-address/<id>`: Delete address
- `PUT /set-default-address/<id>`: Set address as default

---

## User Flow

### Password Change Flow
1. User clicks "Change Password" button
2. Enters current password to verify identity
3. Selects OTP delivery method (SMS or Email)
4. System sends 6-digit OTP code
5. Enters new password (minimum 6 chars with letters + numbers)
6. Confirms new password
7. Enters OTP code from SMS/Email
8. Password successfully changed
9. Page reloads to confirm changes

### Shipping Address Flow
1. User views all saved shipping addresses
2. Can perform the following actions:
   - **Add New**: Fills form and saves address
   - **Edit**: Clicks edit, modifies fields, saves changes
   - **Delete**: Confirms deletion
   - **Set Default**: Sets address as default for future orders

---

## Database Integration

### Existing Tables Used
- `users`: User account information
- `addresses`: Customer shipping addresses (already exists)

### Address Table Structure
```sql
addresses (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  address_type ENUM('billing', 'shipping', 'both'),
  full_name VARCHAR(150) NOT NULL,
  phone VARCHAR(20) NOT NULL,
  street_address TEXT NOT NULL,
  barangay VARCHAR(100),
  city VARCHAR(100) NOT NULL,
  province VARCHAR(100) NOT NULL,
  postal_code VARCHAR(20),
  country VARCHAR(50) DEFAULT 'Philippines',
  is_default BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
)
```

---

## Security Features

### Password Change
- Requires current password verification
- OTP verification via SMS or Email
- Prevents unauthorized password changes
- Session-based state management

### Shipping Addresses
- User can only view/edit/delete their own addresses
- Phone number validation with +63 prefix
- Default address management prevents multiple defaults

---

## OTP Integration

Uses existing `OTPService` utility for:
- **Email OTP**: Via email notification
- **SMS OTP**: Via SMS notification (console output for testing)
- 6-digit code generation
- Configurable OTP purpose tracking
- IP address logging
- Session-based OTP state

### OTP Features
- **Email Option**: Sends OTP to user's email
- **SMS Option**: Sends OTP to user's phone (dev: console output)
- **10-Minute Timer**: OTP expires after 10 minutes
- **Resend Option**: Request new code with timer
- **Console Display**: For testing/development

---

## Styling & UX

### CSS Classes
- `.address-card`: Address display card
- `.address-card-header`: Card header with name and type
- `.address-card-actions`: Edit, Delete, Set Default buttons
- `.otp-method-selector`: SMS/Email selection buttons
- `.password-change-modal`: Password change modal styling
- `.address-form-modal`: Address form modal styling

### Visual Feedback
- Hover effects on buttons and cards
- Loading states on buttons
- Alert messages (success/error)
- Modal step indicators
- Timer countdown display
- Default address badge

---

## Testing Checklist

- [ ] Password Change
  - [ ] Current password validation
  - [ ] SMS OTP delivery
  - [ ] Email OTP delivery
  - [ ] OTP timer and countdown
  - [ ] OTP resend functionality
  - [ ] Password validation (length, characters)
  - [ ] Successful password update
  - [ ] Page reload after change

- [ ] Shipping Addresses
  - [ ] Add new address
  - [ ] View all addresses
  - [ ] Edit existing address
  - [ ] Delete address with confirmation
  - [ ] Set default address
  - [ ] Phone number formatting (+63)
  - [ ] Empty state display
  - [ ] Form validation

- [ ] Security
  - [ ] Users can only access own data
  - [ ] OTP verification required
  - [ ] Session management
  - [ ] Error handling

---

## Files Modified

1. **templates/pages/accountDetails.html**
   - Added Password & Security section
   - Added Shipping Addresses section
   - Added password change modal (4 steps)
   - Added address form modal
   - Added CSS styles
   - Added JavaScript functionality

2. **app.py**
   - Added `/initiate-password-change` route
   - Added `/confirm-password-change` route
   - Added `/get-shipping-addresses` route
   - Added `/get-address/<id>` route
   - Added `/save-shipping-address` route
   - Added `/update-shipping-address/<id>` route
   - Added `/delete-shipping-address/<id>` route
   - Added `/set-default-address/<id>` route

---

## Future Enhancements

1. Address autocomplete using geolocation API
2. Multiple address types per user
3. Address book search/filter
4. Address templates for quick entry
5. Biometric authentication option for password change
6. Two-factor authentication (2FA)
7. Password strength meter
8. Activity log for account changes
9. Email notification for password changes
10. Address delivery preferences (default for orders)

---

## Notes

- All routes are protected with role-based access control (buyer only)
- OTP codes are printed to console for testing/development
- Email sending uses existing OTPService
- Phone numbers use +63 prefix for Philippines
- Default address automatically set when deleting current default
- Session-based OTP tracking for security
