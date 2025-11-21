# OTP Authentication Setup Guide

## Overview
This system implements **FREE** OTP (One-Time Password) authentication for email and SMS verification during user registration and account confirmation.

## Features
- ✅ **Email OTP** using Gmail SMTP (FREE)
- ✅ **SMS OTP** using Semaphore API (Philippines) or Twilio (with free trial)
- ✅ **Database migration** for OTP verification tracking
- ✅ **Automatic verification** on registration
- ✅ **Resend OTP** functionality with cooldown
- ✅ **OTP expiration** (10 minutes default)
- ✅ **Rate limiting** (max 5 attempts)

---

## Installation

### 1. Install Required Packages
```bash
pip install python-dotenv requests twilio
```

Or use the requirements file:
```bash
pip install -r requirements_otp.txt
```

### 2. Run Database Migration
```bash
python scripts/run_migration.py migrations/add_otp_verification.sql
```

Or manually run the SQL in your MySQL:
```sql
mysql -u root -p varon < migrations/add_otp_verification.sql
```

---

## Configuration

### 1. Copy Environment File
```bash
copy .env.example .env
```

### 2. Configure Email (Gmail - FREE)

#### Get Gmail App Password:
1. Go to https://myaccount.google.com/security
2. Enable **2-Step Verification**
3. Go to **App passwords** (https://myaccount.google.com/apppasswords)
4. Select app: **Mail**, Select device: **Other (Custom name)** → "Varon App"
5. Click **Generate** and copy the 16-character password

#### Update `.env`:
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-16-char-app-password
MAIL_DEFAULT_SENDER=Varón <noreply@varon.com>
```

### 3. Configure SMS (Choose One Provider)

#### Option A: Semaphore (Philippines - FREE Credits)
1. Sign up at https://semaphore.co/
2. Get FREE credits for testing (₱20-50 initial credits)
3. Get API key from dashboard

Update `.env`:
```env
SEMAPHORE_API_KEY=your-api-key-here
SEMAPHORE_SENDER_NAME=VARON
```

#### Option B: Twilio (International - FREE Trial)
1. Sign up at https://www.twilio.com/try-twilio
2. Get FREE $15.50 trial credit
3. Get credentials from console

Update `.env`:
```env
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=your-twilio-number
```

---

## Usage

### Registration Flow

1. **User signs up** → Email/Phone/Password
2. **OTP sent** → Via email or SMS
3. **User enters OTP** → 6-digit code
4. **Verification** → Account activated
5. **Redirect** → Login page

### API Endpoints

#### Send OTP
```http
POST /send-otp
Content-Type: application/json

{
  "email": "user@example.com",
  "phone": "+639123456789",
  "verification_type": "email",  # or "sms"
  "purpose": "registration"
}
```

#### Verify OTP
```http
POST /verify-otp
Content-Type: application/json

{
  "otp_code": "123456",
  "email": "user@example.com",
  "purpose": "registration"
}
```

#### Resend OTP
```http
POST /resend-otp
Content-Type: application/json

{
  "email": "user@example.com",
  "verification_type": "email",
  "purpose": "registration"
}
```

---

## Testing

### 1. Test Email OTP
```bash
python -c "from utils.otp_service import OTPService; print('Email sent:', OTPService.send_email_otp('test@example.com', '123456', 'registration'))"
```

### 2. Test SMS OTP (Semaphore)
```bash
python -c "from utils.otp_service import OTPService; print('SMS sent:', OTPService.send_sms_otp('+639123456789', '123456', 'registration'))"
```

### 3. Full Registration Test
1. Open http://localhost:5000/login
2. Click "Sign Up" tab
3. Fill in details
4. Submit → Check email/phone for OTP
5. Enter OTP → Should verify and redirect to login

---

## Customization

### OTP Settings (config.py)
```python
OTP_EXPIRY_MINUTES = 10    # OTP expires in 10 minutes
OTP_MAX_ATTEMPTS = 5       # Maximum 5 verification attempts
OTP_LENGTH = 6             # 6-digit OTP code
```

### Email Template
Edit `utils/otp_service.py` → `send_email_otp()` method to customize email HTML.

### SMS Message
Edit `utils/otp_service.py` → `send_sms_otp_*()` methods to customize SMS text.

---

## Database Schema

### otp_verifications Table
```sql
- id: Primary key
- user_id: Foreign key to users table
- email: Email address (nullable)
- phone: Phone number (nullable)
- otp_code: 6-digit verification code
- otp_type: 'email', 'sms', or 'both'
- purpose: 'registration', 'login', 'password_reset', 'phone_verify'
- attempts: Number of verification attempts
- is_verified: Verification status
- expires_at: Expiration timestamp
- created_at: Creation timestamp
- verified_at: Verification timestamp
- ip_address: User's IP address
```

### users Table (Added Columns)
```sql
- email_verified: BOOLEAN (default FALSE)
- phone_verified: BOOLEAN (default FALSE)
- email_verified_at: TIMESTAMP (nullable)
- phone_verified_at: TIMESTAMP (nullable)
- verification_token: VARCHAR(255) (nullable)
```

---

## Troubleshooting

### Email Not Sending
1. Check Gmail app password is correct (16 characters, no spaces)
2. Ensure 2FA is enabled on Gmail account
3. Check firewall/antivirus not blocking port 587
4. Try with different Gmail account

### SMS Not Sending
1. **Semaphore**: Check API key and credits balance
2. **Twilio**: Verify trial account is active and has credits
3. Ensure phone number format is correct (+63 for Philippines)
4. Check console for error messages

### OTP Expired
- Default expiry is 10 minutes
- User can click "Resend OTP" (60-second cooldown)
- Old OTPs are automatically cleaned up

### Database Errors
```bash
# Check if migration ran successfully
mysql -u root -p varon -e "SHOW TABLES LIKE 'otp_verifications';"

# Check table structure
mysql -u root -p varon -e "DESCRIBE otp_verifications;"
```

---

## Security Features

1. **Rate Limiting**: Max 5 OTP attempts per code
2. **Expiration**: OTPs expire after 10 minutes
3. **IP Tracking**: Logs user IP for audit trails
4. **One-Time Use**: OTPs marked as used after verification
5. **Secure Storage**: OTP codes stored in database (consider hashing in production)

---

## Production Recommendations

1. **Environment Variables**: Never commit `.env` file
2. **HTTPS Only**: Use SSL/TLS in production
3. **Rate Limiting**: Implement API rate limiting
4. **Hash OTP Codes**: Hash OTP codes before storing in database
5. **Monitor Usage**: Track email/SMS usage and costs
6. **Backup Codes**: Implement backup verification methods
7. **Logging**: Add comprehensive logging for security audits

---

## Cost Estimates

### Email (Gmail)
- **FREE** - No cost for SMTP usage
- Limit: ~500 emails/day per account

### SMS Options

#### Semaphore (Philippines)
- Initial FREE credits: ₱20-50
- Cost per SMS: ₱0.50-1.00 (~$0.01-0.02 USD)
- 1000 SMS ≈ ₱500-1000 (~$10-20 USD)

#### Twilio (International)
- Free trial: $15.50 credit
- Cost per SMS: $0.0075-0.10 USD depending on country
- 1000 SMS ≈ $7.50-100 USD

---

## Support

For issues or questions:
1. Check console logs for error messages
2. Verify all environment variables are set correctly
3. Test with a different email/phone number
4. Check provider documentation (Gmail, Semaphore, Twilio)

---

## License
MIT License - Feel free to modify and use as needed.
