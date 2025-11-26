# Seller Panel Fixes - Code Changes Reference

## 📁 Files Modified

1. `templates/pages/SellerDashboard.html` - Frontend HTML and JavaScript
2. `app.py` - Backend Python endpoints

---

## 🎨 Frontend Changes: SellerDashboard.html

### 1. Account Section - HTML Template

**Key Changes:**
- Removed password section (Current, New, Confirm Password fields)
- Added email field with verification button
- Added OTP verification section (hidden by default)
- Updated button labels to use new functions

**New Email Field:**
```html
<div style="margin-bottom: 20px;">
  <label style="display: block; margin-bottom: 8px; font-weight: 500;">Email Address *</label>
  <div style="display: flex; gap: 8px;">
    <input type="email" id="email-address" placeholder="Enter email address" 
           style="flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box;">
    <button type="button" id="verify-email-btn" onclick="sendEmailOTP()" 
            class="action-btn" style="background: #3b82f6; color: white; padding: 10px 16px; 
            border: none; border-radius: 6px; cursor: pointer; font-weight: 500; white-space: nowrap;">
      Verify Email
    </button>
  </div>
  <small>Click "Verify Email" to send OTP verification code</small>
</div>
```

**OTP Verification Section:**
```html
<div id="otp-verification-section" style="display: none; margin-top: 12px; 
     padding: 12px; background: #f0f9ff; border: 1px solid #bfdbfe; border-radius: 6px;">
  <input type="text" id="otp-code" placeholder="Enter 6-digit OTP code" 
         style="width: 100%; padding: 10px; border: 1px solid #bfdbfe; 
         border-radius: 6px; margin-bottom: 8px; box-sizing: border-box;">
  <button type="button" id="verify-otp-btn" onclick="verifyEmailOTP()" 
          class="action-btn" style="width: 100%; background: #10b981; color: white; 
          padding: 10px; border: none; border-radius: 6px; cursor: pointer; font-weight: 500;">
    Verify OTP
  </button>
</div>
```

**Success Message:**
```html
<div id="email-verified-message" style="display: none; margin-top: 12px; padding: 12px; 
     background: #dcfce7; border: 1px solid #86efac; border-radius: 6px; 
     color: #15803d; font-weight: 500;">
  ✓ Email verified successfully
</div>
```

---

### 2. Brand Settings Section - HTML Template

**Key Changes:**
- Renamed "Store Name" label to "Brand Name"
- Renamed "Store Description" label to "Brand Description"
- Updated placeholder text
- Added `required` attributes to both fields

**Before:**
```html
<label>Store Name</label>
<input type="text" id="store-name" placeholder="Enter store name">

<label>Store Description</label>
<textarea id="store-description" placeholder="Tell customers about your store">
```

**After:**
```html
<label>Brand Name *</label>
<input type="text" id="store-name" placeholder="Enter brand name" required>

<label>Brand Description *</label>
<textarea id="store-description" placeholder="Tell customers about your brand" required>
```

---

### 3. Inventory Section - HTML Template

**Removed Search Bar:**
```html
<!-- BEFORE -->
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
  <h2 style="margin: 0;">📦 Inventory Management</h2>
  <input type="text" id="inventory-search" placeholder="Search products..." 
         style="padding: 8px 12px; border: 1px solid var(--line); border-radius: 6px; width: 250px;" 
         onkeyup="loadInventory()">
</div>

<!-- AFTER -->
<div style="margin-bottom: 20px;">
  <h2 style="margin: 0;">📦 Inventory Management</h2>
</div>
```

---

### 4. Account Settings JavaScript Functions

**New Function: reloadAccountSettings()**
```javascript
function reloadAccountSettings() {
  loadAccountSettings();
  alert('✅ Account settings reloaded!');
}
```

**New Function: sendEmailOTP()**
```javascript
function sendEmailOTP() {
  const email = document.getElementById('email-address').value.trim();
  if (!email) {
    alert('⚠️ Please enter an email address');
    return;
  }
  
  if (!email.includes('@')) {
    alert('⚠️ Please enter a valid email address');
    return;
  }

  const btn = document.getElementById('verify-email-btn');
  btn.disabled = true;
  btn.textContent = 'Sending...';

  fetch('/send-otp', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      email: email, 
      verification_type: 'email', 
      purpose: 'email_change'
    })
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      alert('✅ OTP code sent to ' + email);
      document.getElementById('otp-verification-section').style.display = 'block';
      document.getElementById('otp-code').focus();
    } else {
      alert('❌ Error: ' + (data.message || data.error || 'Could not send OTP'));
    }
    btn.disabled = false;
    btn.textContent = 'Verify Email';
  })
  .catch(error => {
    alert('❌ Error sending OTP: ' + error.message);
    btn.disabled = false;
    btn.textContent = 'Verify Email';
  });
}
```

**New Function: verifyEmailOTP()**
```javascript
function verifyEmailOTP() {
  const email = document.getElementById('email-address').value.trim();
  const otp = document.getElementById('otp-code').value.trim();
  
  if (!otp || otp.length !== 6) {
    alert('⚠️ Please enter a valid 6-digit OTP code');
    return;
  }

  const btn = document.getElementById('verify-otp-btn');
  btn.disabled = true;
  btn.textContent = 'Verifying...';

  fetch('/verify-otp', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      email: email, 
      otp_code: otp, 
      purpose: 'email_change'
    })
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      alert('✅ Email verified successfully!');
      document.getElementById('otp-verification-section').style.display = 'none';
      document.getElementById('email-verified-message').style.display = 'block';
      document.getElementById('verify-email-btn').disabled = true;
      document.getElementById('verify-email-btn').textContent = '✓ Verified';
    } else {
      alert('❌ Error: ' + (data.message || data.error || 'Invalid OTP code'));
    }
    btn.disabled = false;
    btn.textContent = 'Verify OTP';
  })
  .catch(error => {
    alert('❌ Error verifying OTP: ' + error.message);
    btn.disabled = false;
    btn.textContent = 'Verify OTP';
  });
}
```

---

### 5. Updated loadAccountSettings() Function

**Key Changes:**
- Populate email field from account data
- Reset OTP form elements
- Clear verified state on reload

```javascript
function loadAccountSettings() {
  fetch('/seller/account-settings')
    .then(response => {
      console.log('Account settings response status:', response.status);
      return response.json();
    })
    .then(data => {
      console.log('Account settings data:', data);
      if (data.success) {
        const account = data.account;
        document.getElementById('account-username').textContent = account.username || 'User';
        document.getElementById('account-email').textContent = account.email || '';
        document.getElementById('full-name').value = account.full_name || '';
        document.getElementById('phone-number').value = account.phone_number || '';
        document.getElementById('email-address').value = account.email || '';
        
        // Reset OTP verification UI
        document.getElementById('otp-verification-section').style.display = 'none';
        document.getElementById('email-verified-message').style.display = 'none';
        document.getElementById('otp-code').value = '';
      } else {
        console.error('Account settings error:', data.error);
        document.getElementById('account-username').textContent = 'Error: ' + (data.error || 'Unknown error');
      }
    })
    .catch(error => {
      console.error('Error loading account settings:', error);
      document.getElementById('account-username').textContent = 'Error loading settings';
    });
}
```

---

### 6. Updated Account Form Submission Handler

**Key Changes:**
- Remove password validation
- Add email verification check
- Add confirmation popup
- Pass email to backend

```javascript
const accountForm = document.getElementById('account-settings-form');
if (accountForm) {
  accountForm.addEventListener('submit', (e) => {
    e.preventDefault();
    
    // Show confirmation popup
    if (!confirm('Are you sure you want to save these account settings?')) {
      return;
    }
    
    // Check if email was verified (if it was changed)
    const newEmail = document.getElementById('email-address').value.trim();
    const currentEmail = document.getElementById('account-email').textContent;
    
    if (newEmail && newEmail !== currentEmail) {
      const emailVerified = document.getElementById('email-verified-message').style.display !== 'none';
      if (!emailVerified) {
        alert('⚠️ Please verify the new email address before saving');
        return;
      }
    }
    
    const formData = new FormData();
    formData.append('full_name', document.getElementById('full-name').value);
    formData.append('phone_number', document.getElementById('phone-number').value);
    formData.append('email', newEmail);
    
    fetch('/seller/account-settings', { method: 'POST', body: formData })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          alert('✅ Account settings updated successfully!');
          loadAccountSettings();
        } else {
          alert('❌ Error: ' + (data.error || 'Unknown error'));
        }
      })
      .catch(error => alert('❌ Error saving settings: ' + error.message));
  });
}
```

---

### 7. Updated Brand Settings Form Submission Handler

**Key Changes:**
- Add field validation
- Add confirmation popup
- Validate required fields

```javascript
const brandForm = document.getElementById('brand-settings-form');
if (brandForm) {
  brandForm.addEventListener('submit', (e) => {
    e.preventDefault();
    
    // Validate required fields
    const storeName = document.getElementById('store-name').value.trim();
    const storeDesc = document.getElementById('store-description').value.trim();
    
    if (!storeName) {
      alert('⚠️ Please enter a brand name');
      return;
    }
    
    if (!storeDesc) {
      alert('⚠️ Please enter a brand description');
      return;
    }
    
    // Show confirmation popup
    if (!confirm('Are you sure you want to save these brand settings?')) {
      return;
    }
    
    const formData = new FormData();
    formData.append('store_name', storeName);
    formData.append('description', storeDesc);
    formData.append('contact_email', document.getElementById('contact-email').value);
    formData.append('contact_phone', document.getElementById('contact-phone').value);
    formData.append('address', document.getElementById('store-address').value);
    formData.append('island_group', document.getElementById('island-group').value);
    
    fetch('/seller/brand-settings', { method: 'POST', body: formData })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          alert('✅ Brand settings updated successfully!');
          loadBrandSettings();
        } else {
          alert('❌ Error: ' + (data.error || 'Unknown error'));
        }
      })
      .catch(error => alert('❌ Error saving settings: ' + error.message));
  });
}
```

---

### 8. Updated Inventory Function

**Removed search filtering:**
```javascript
function loadInventory() {
  fetch('/seller/inventory')
    .then(response => response.json())
    .then(data => {
      if (data.success && data.inventory) {
        const inventory = data.inventory;
        displayInventory(inventory);
      } else {
        document.getElementById('inventory-list').innerHTML = '<p style="color:#999;padding:40px;">No inventory items found</p>';
      }
    })
    .catch(error => {
      document.getElementById('inventory-list').innerHTML = '<p style="color:#d32f2f;padding:40px;">Error loading inventory</p>';
    });
}
```

---

## 🐍 Backend Changes: app.py

### 1. Updated /seller/account-settings Endpoint

**Key Changes:**
- Remove password handling code
- Add email field handling
- Add email uniqueness check
- Update user profile with email

**Updated Code:**
```python
@app.route('/seller/account-settings', methods=['GET', 'POST'])
def seller_account_settings():
    """Get or update seller account settings"""
    # ... (connection and auth code same as before) ...
    
    if request.method == 'GET':
        # Return current account settings (unchanged)
        # ...
    
    else:  # POST - Update account settings
        full_name = request.form.get('full_name', '').strip()
        phone_number = request.form.get('phone_number', '').strip()
        new_email = request.form.get('email', '').strip()
        
        # Split full name into first and last
        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0] if len(name_parts) > 0 else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # If email is being changed, verify it's unique
        if new_email and new_email != user['email']:
            cursor.execute('SELECT id FROM users WHERE email = %s AND id != %s', (new_email, user_id))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'error': 'Email already in use'}), 400
            
            # Update email
            cursor.execute('UPDATE users SET email = %s WHERE id = %s', (new_email, user_id))
        
        # Update user profile
        cursor.execute('''
            UPDATE users
            SET first_name = %s, last_name = %s, phone = %s
            WHERE id = %s
        ''', (first_name, last_name, phone_number, user_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Account settings updated'}), 200
```

---

### 2. Database Schema Enhancement

**Added is_verified Column to otp_verifications Table:**
```python
# In init_db() function:
try:
    cursor.execute("SHOW COLUMNS FROM otp_verifications LIKE 'is_verified'")
    if not cursor.fetchone():
        cursor.execute("ALTER TABLE otp_verifications ADD COLUMN is_verified BOOLEAN DEFAULT FALSE AFTER used_at")
        print("[DB INIT] Added missing 'is_verified' column to otp_verifications table")
except Exception as e:
    print(f"[DB INIT] Error checking/adding is_verified column: {e}")
```

---

## 🔄 API Flow Diagram

```
FRONTEND                          BACKEND

Account Settings Form
    ↓
Enter Email + Click "Verify Email"
    ↓
POST /send-otp ────────────────→ Generate OTP code
                                ↓
                            Store in DB
                                ↓
                            Send via Email
                                ↓
                            Return {success: true}
    ←──────────────────────────
Show OTP Input Section
    ↓
Enter OTP + Click "Verify OTP"
    ↓
POST /verify-otp ──────────────→ Check OTP validity
                                ↓
                            Check expiration
                                ↓
                            Mark as verified
                                ↓
                            Return {success: true}
    ←──────────────────────────
Show "Email verified" Message
    ↓
Click "Save Changes"
    ↓
Show confirmation popup
    ↓
POST /seller/account-settings ─→ Check email unique
                                ↓
                            Update user profile
                                ↓
                            Return {success: true}
    ←──────────────────────────
Show success message
```

---

## 📊 Database Changes

### otp_verifications Table

**New Column Added:**
```sql
ALTER TABLE otp_verifications ADD COLUMN is_verified BOOLEAN DEFAULT FALSE AFTER used_at;
```

**Complete Table Structure:**
```sql
CREATE TABLE IF NOT EXISTS otp_verifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(190),
    phone VARCHAR(20),
    otp_code VARCHAR(10) NOT NULL,
    otp_type ENUM('email', 'sms') NOT NULL DEFAULT 'email',
    purpose ENUM(..., 'email_change', ...) NOT NULL DEFAULT 'registration',
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP NULL,
    is_verified BOOLEAN DEFAULT FALSE,  ← NEW COLUMN
    attempts INT DEFAULT 0,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_phone (phone),
    INDEX idx_code (otp_code),
    INDEX idx_expires (expires_at),
    INDEX idx_purpose (purpose)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## ✅ Testing Verification

All changes have been:
- ✅ Implemented
- ✅ Tested
- ✅ Verified working
- ✅ Deployed to server

Server Status: **RUNNING AT 192.168.123.57:5000**

---

*Last Updated: 2025-11-26*
*All code changes documented and tested*
