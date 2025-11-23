# Varón OTP System Documentation

## Overview
The Varón OTP (One-Time Password) system provides secure email-based verification for user registration, login, and password reset functionality.

## Features
- ✅ Email OTP verification
- ✅ SMS OTP support (Semaphore API)
- ✅ Automatic OTP expiration (10 minutes)
- ✅ Attempt limiting (max 3 attempts)
- ✅ IP address tracking
- ✅ Multiple purposes (registration, login, password reset)

## Configuration

### Environment Variables (.env)
```env
# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=Varón Apparel <noreply@varon.com>

# SMS Configuration (Optional)
SEMAPHORE_API_KEY=your-semaphore-api-key
SEMAPHORE_SENDER_NAME=VARON
```

### Database Table
The system uses the existing `otp_verifications` table with the following structure:
- `id` - Primary key
- `email` - User's email address
- `phone` - User's phone number
- `otp_code` - 6-digit OTP code
- `otp_type` - 'email' or 'sms'
- `purpose` - 'registration', 'login', or 'password_reset'
- `expires_at` - Expiration timestamp
- `attempts` - Number of verification attempts
- `is_verified` - Verification status
- `verified_at` - Verification timestamp
- `ip_address` - Request IP address

## Usage Examples

### 1. Send OTP for Registration
```python
from utils.otp_service import OTPService

# Generate and send OTP
otp_code, otp_id = OTPService.create_otp_record(
    conn=conn,  # Database connection
    email="user@example.com",
    otp_type="email",
    purpose="registration"
)

# Send email
success = OTPService.send_email_otp(
    "user@example.com",
    otp_code,
    "registration"
)
```

### 2. Verify OTP
```python
from utils.otp_service import OTPService

# Verify the OTP code
is_valid, message = OTPService.verify_otp(
    conn=conn,
    otp_code="123456",
    email="user@example.com",
    purpose="registration"
)

if is_valid:
    # OTP is valid, proceed with registration
    print("Verification successful!")
else:
    # OTP is invalid or expired
    print(f"Verification failed: {message}")
```

### 3. Flask Route Integration
```python
@app.route('/send-otp', methods=['POST'])
def send_otp():
    data = request.get_json()
    email = data.get('email')

    conn = get_db()
    otp_code, otp_id = OTPService.create_otp_record(
        conn, email=email, purpose='registration'
    )

    if otp_code:
        success = OTPService.send_email_otp(email, otp_code, 'registration')
        if success:
            return jsonify({'success': True, 'message': 'OTP sent'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send email'})

    return jsonify({'success': False, 'message': 'Failed to generate OTP'})

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    otp_code = data.get('otp_code')
    email = data.get('email')

    conn = get_db()
    is_valid, message = OTPService.verify_otp(conn, otp_code, email=email)

    return jsonify({'success': is_valid, 'message': message})
```

## API Endpoints

### POST /send-otp
Send OTP to user's email
```json
{
  "email": "user@example.com",
  "purpose": "registration"
}
```

### POST /verify-otp
Verify OTP code
```json
{
  "otp_code": "123456",
  "email": "user@example.com",
  "purpose": "registration"
}
```

### POST /resend-otp
Resend OTP code
```json
{
  "email": "user@example.com",
  "purpose": "registration"
}
```

## Security Features

1. **Expiration**: OTP codes expire after 10 minutes
2. **Attempt Limiting**: Maximum 3 verification attempts per code
3. **IP Tracking**: Records IP address for security monitoring
4. **Single Use**: Each OTP can only be used once
5. **Purpose Validation**: OTPs are validated by purpose and recipient

## Email Template

The system sends professional HTML emails with:
- Company branding (Varón Apparel)
- Clear OTP display
- Security instructions
- Expiration warnings
- Responsive design

## Testing

Run the test script to verify the system:
```bash
python test_otp.py
```

## Error Handling

The system provides detailed error messages:
- "Invalid or expired OTP code"
- "Too many failed attempts. Please request a new OTP"
- "Verification failed"
- "OTP verified successfully"

## Maintenance

The system includes a cleanup function to remove expired OTPs:
```python
OTPService.cleanup_expired_otps(conn)
```

This should be called periodically to maintain database performance.