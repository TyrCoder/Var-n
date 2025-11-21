# OTP Authentication - Quick Start

## Setup (5 minutes)

### 1. Install packages
```bash
pip install python-dotenv requests
```

### 2. Configure Email (Gmail)
Edit `.env` file:
```env
MAIL_USERNAME=sedocode7@gmail.com
MAIL_PASSWORD=fbio jkvd alpk hopn
```

To get Gmail app password:
- Visit: https://myaccount.google.com/apppasswords
- Enable 2FA first if not enabled
- Generate app password for "Mail" → "Other (Varon)"
- Copy 16-character password

### 3. Run Migration
```bash
python scripts/run_single_migration.py migrations/add_otp_verification.sql
```

### 4. Test
```bash
python app.py
```

Open http://localhost:5000/login → Sign up → Enter email → Receive OTP!

## SMS (Optional)

### Semaphore (Philippines - FREE credits)
1. Sign up: https://semaphore.co/
2. Get API key from dashboard
3. Add to `.env`:
```env
SEMAPHORE_API_KEY=your-api-key
```

### Twilio (International - $15 free trial)
1. Sign up: https://www.twilio.com/try-twilio
2. Get credentials from console
3. Add to `.env`:
```env
TWILIO_ACCOUNT_SID=your-sid
TWILIO_AUTH_TOKEN=your-token
TWILIO_PHONE_NUMBER=your-number
```

## Features
- ✅ Email OTP on registration
- ✅ SMS OTP for riders (optional)
- ✅ 6-digit codes
- ✅ 10-minute expiry
- ✅ Resend with cooldown
- ✅ Rate limiting (5 attempts)

## Files Changed
- `app.py` - Added OTP routes & signup integration
- `utils/otp_service.py` - OTP generation & sending
- `config.py` - Configuration settings
- `templates/auth/verify_otp.html` - Verification page
- `migrations/add_otp_verification.sql` - Database changes

## Troubleshooting
- **Email not sending**: Check Gmail app password is correct (16 chars, no spaces)
- **Database error**: Run migration script again
- **Module not found**: Run `pip install python-dotenv requests`

Full guide: `docs/OTP_SETUP_GUIDE.md`
