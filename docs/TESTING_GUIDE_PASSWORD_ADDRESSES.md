# Quick Test Guide - Password Change & Shipping Address

## Testing Password Change Feature

### Test Case 1: Change Password via Email OTP
1. Go to Account Details page
2. Scroll to "Password & Security" section
3. Click "Change Password" button
4. Modal opens at Step 1: Password Confirmation
5. Enter your current password
6. Click "Continue" → Moves to Step 2
7. Click "Email" option button
8. Click "Send Code" → Check console for OTP
9. Click "Continue" → Step 3: New Password
10. Enter new password (must be 6+ chars with letters + numbers)
11. Confirm new password
12. Click "Continue" → Step 4: OTP Verification
13. Enter the 6-digit code from console
14. Click "Verify & Change"
15. Success message → Page reloads

### Test Case 2: Change Password via SMS OTP
- Same as above but select "SMS" option
- OTP will be printed to console (no actual SMS sent)

### Test Case 3: Password Validation
- Try password < 6 characters: Should fail
- Try password without numbers: Should fail
- Try password without letters: Should fail
- Try mismatched passwords: Should fail

### Test Case 4: Incorrect OTP
- Enter wrong 6-digit code
- Should show error message
- Can retry or resend

### Test Case 5: OTP Timeout
- Send OTP, wait 10 minutes
- OTP expires, resend button becomes active
- Click "Resend" to get new code

---

## Testing Shipping Address Feature

### Test Case 1: Add New Address
1. Go to Account Details page
2. Scroll to "Shipping Addresses" section
3. If no addresses: See empty state message
4. Click "+ Add New Address" button
5. Modal opens with form fields:
   - Full Name: Enter name
   - Phone: Automatically has +63 prefix
   - Street Address: Enter address
   - Barangay: Enter barangay
   - City: Enter city
   - Province: Enter province
   - Postal Code: Optional
   - Address Type: Select Shipping/Billing/Both
   - Set as Default: Check if desired
6. Click "Save Address"
7. Success message
8. Address card appears in list

### Test Case 2: Add Multiple Addresses
1. Repeat Test Case 1 multiple times
2. Verify all addresses display in list
3. Each with own Edit/Delete/Set Default buttons

### Test Case 3: Edit Address
1. Click "Edit" button on any address
2. Modal opens with form populated
3. Title shows "Edit Address"
4. Modify any fields
5. Click "Save Address"
6. Address updated in list

### Test Case 4: Set Default Address
1. Click "Set Default" button on address without default badge
2. Address gets "Default" badge
3. Previous default loses badge
4. Check database: Only one address has is_default = TRUE

### Test Case 5: Delete Address
1. Click "Delete" button
2. Confirmation dialog appears
3. Confirm deletion
4. Address removed from list
5. If deleted address was default:
   - Another address automatically becomes default

### Test Case 6: Phone Number Formatting
1. Try entering phone without +63: Should auto-format to +63
2. Try entering with country code: Should maintain +63
3. Cursor can't go before +63 (protected)

### Test Case 7: Form Validation
1. Try submitting empty form: Should show validation errors
2. Fill only some fields: Should show missing field errors
3. All required fields must be filled

---

## Database Verification

### Check Password Change
```sql
-- Verify password was updated (shows as plain text)
SELECT id, email, password FROM users WHERE id = [YOUR_USER_ID];
```

### Check Addresses
```sql
-- View all addresses for user
SELECT * FROM addresses WHERE user_id = [YOUR_USER_ID] ORDER BY is_default DESC;

-- Check default address
SELECT * FROM addresses WHERE user_id = [YOUR_USER_ID] AND is_default = TRUE;

-- Count addresses
SELECT COUNT(*) FROM addresses WHERE user_id = [YOUR_USER_ID];
```

---

## Console Output Examples

### Password Change OTP (Email)
```
============================================================
📧 PASSWORD CHANGE OTP FOR user@example.com
OTP CODE: 123456
============================================================
```

### Password Change OTP (SMS)
```
============================================================
📱 PASSWORD CHANGE OTP FOR +639123456789
OTP CODE: 123456
============================================================
```

---

## Common Issues & Solutions

### Issue: Phone number not formatting correctly
- **Solution**: Phone input has auto-formatting. Should always show +63 prefix

### Issue: Can't delete default address
- **Solution**: Should work - another address auto-becomes default
- Check database to verify

### Issue: OTP not appearing in console
- **Solution**: Check if using Email or SMS option
- Ensure backend is running in debug mode
- Check terminal where Flask is running

### Issue: Password change modal stuck on Step 1
- **Solution**: Make sure current password is correct
- Check user is logged in
- Verify session is active

### Issue: Address form not submitting
- **Solution**: Fill all required fields (marked with *)
- Check phone number format
- Ensure city and province are filled

---

## Frontend Elements to Check

### Password Change Modal
- [ ] All 4 steps render correctly
- [ ] Buttons are clickable
- [ ] Password visibility toggles work
- [ ] OTP inputs auto-focus
- [ ] Timer countdown works
- [ ] Resend button disabled during timer

### Address Management
- [ ] Address cards display all information
- [ ] Edit/Delete/Set Default buttons work
- [ ] Form modal opens for add/edit
- [ ] Phone field shows +63 prefix
- [ ] All form fields render
- [ ] Validation messages appear
- [ ] Success/error alerts display

### Styling
- [ ] No layout breaks
- [ ] Modal centers properly
- [ ] Buttons have hover effects
- [ ] Cards have proper spacing
- [ ] Responsive on different screen sizes

---

## API Endpoints to Test

### Password Change
- POST `/initiate-password-change`
  - Payload: `{ "otp_method": "email" or "sms" }`
  - Response: `{ "success": true, "otp_id": "...", "message": "..." }`

- POST `/confirm-password-change`
  - Payload: `{ "otp": "123456", "otp_id": "...", "new_password": "..." }`
  - Response: `{ "success": true, "message": "Password changed successfully" }`

### Shipping Addresses
- GET `/get-shipping-addresses`
  - Response: `{ "success": true, "addresses": [...] }`

- POST `/save-shipping-address`
  - Payload: Address object with all fields
  - Response: `{ "success": true, "message": "..." }`

- PUT `/update-shipping-address/<id>`
  - Payload: Updated address object
  - Response: `{ "success": true, "message": "..." }`

- DELETE `/delete-shipping-address/<id>`
  - Response: `{ "success": true, "message": "..." }`

- PUT `/set-default-address/<id>`
  - Response: `{ "success": true, "message": "..." }`

---

## Success Indicators

✅ **Password Change Success**
- User receives OTP via email or console
- New password meets requirements
- OTP verification succeeds
- Password updated in database
- User can login with new password

✅ **Shipping Address Success**
- Address saved with all fields
- Default address auto-set for first address
- Can edit without losing other data
- Can delete with proper cascade
- Can retrieve all user addresses

✅ **Security Success**
- Only logged-in buyers can access
- Users can only modify own data
- OTP prevents unauthorized changes
- Session properly managed
