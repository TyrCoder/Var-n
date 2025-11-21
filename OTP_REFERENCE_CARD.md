# 🚀 OTP Quick Reference Card

## ⚡ 30-Second Setup

```bash
# 1. Edit .env file
MAIL_USERNAME=your-gmail@gmail.com
MAIL_PASSWORD=your-16-char-app-password

# 2. Test
python scripts/test_otp.py

# 3. Run
python app.py
```

---

## 📋 Commands

```bash
python scripts/test_otp.py                    # Test OTP
python scripts/run_single_migration.py ...    # Run migration  
python app.py                                  # Start app
pip install python-dotenv requests            # Install deps
```

---

## 🔑 Key Files

```
.env                           # Your credentials HERE
utils/otp_service.py          # OTP logic
templates/auth/verify_otp.html # Verification UI
migrations/add_otp_verification.sql # Database
```

---

## 🌐 URLs

```
http://localhost:5000/login           # Main login page
http://localhost:5000/verify-otp-page # OTP verification
https://myaccount.google.com/apppasswords # Gmail app password
https://semaphore.co/                 # SMS (Philippines)
https://www.twilio.com/try-twilio     # SMS (International)
```

---

## ⚙️ Configuration (.env)

```env
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
SEMAPHORE_API_KEY=your-key (optional)
TWILIO_ACCOUNT_SID=your-sid (optional)
```

---

## 🧪 Testing

```bash
# Email test
python scripts/test_otp.py → Option 1

# SMS test  
python scripts/test_otp.py → Option 2

# Full flow test
python app.py → localhost:5000/login → Sign Up
```

---

## 📊 Database

```sql
mysql -u root -p varon
SHOW TABLES LIKE 'otp%';
SELECT * FROM otp_verifications LIMIT 5;
DESCRIBE users;
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| No email | Check Gmail app password |
| Database error | Re-run migration |
| Module not found | pip install python-dotenv requests |
| OTP expired | Click "Resend OTP" |

---

## 📱 OTP Settings (config.py)

```python
OTP_EXPIRY_MINUTES = 10    # Expiry time
OTP_MAX_ATTEMPTS = 5       # Max attempts
OTP_LENGTH = 6             # Code length
```

---

## 🔒 Security

- ✅ 10-minute expiration
- ✅ 5 attempt limit
- ✅ One-time use
- ✅ IP tracking
- ✅ Session security
- ✅ 60s resend cooldown

---

## 📖 Documentation

```
OTP_QUICKSTART.md           # 5-min setup
docs/OTP_SETUP_GUIDE.md     # Full guide
docs/OTP_FLOW_DIAGRAM.md    # Visual flows
SETUP_CHECKLIST.md          # Checklist
README_OTP.md               # Complete ref
```

---

## ✅ Status Check

```bash
# All should return success
python -c "import dotenv; print('dotenv: OK')"
python -c "import requests; print('requests: OK')"
python -c "from utils.otp_service import OTPService; print('OTP Service: OK')"
```

---

## 🎯 User Flow

```
Sign Up → Enter Details → Submit
→ OTP Sent (Email/SMS)
→ Enter 6-Digit Code → Verify
→ Success → Login
```

---

## 💡 Pro Tips

1. Use Gmail app password (not regular password)
2. Check spam folder for test emails
3. SMS is optional - email works standalone
4. Test before production
5. Never commit .env to Git

---

## 🆘 Quick Help

**Email not working?**
```bash
python scripts/test_otp.py
```

**Need Gmail app password?**
→ https://myaccount.google.com/apppasswords

**Database issues?**
```bash
python scripts/run_single_migration.py migrations/add_otp_verification.sql
```

---

## 📞 Support

Console logs → Check for errors
Test script → `python scripts/test_otp.py`
Documentation → `docs/OTP_SETUP_GUIDE.md`

---

**Status**: ✅ Ready to use! Just add Gmail credentials!

**Setup time**: 5 minutes

**Cost**: FREE (email), Optional (SMS)
