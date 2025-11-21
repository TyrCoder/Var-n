# 📋 OTP Setup Checklist

## ✅ Pre-Setup (Completed)
- [x] Database migration executed
- [x] Python packages installed (python-dotenv, requests)
- [x] Files created and integrated
- [x] No errors in code

## 🔧 Configuration Required (Your Action)

### 1. Gmail Setup for Email OTP (REQUIRED)

**Steps:**

1. **Enable 2-Factor Authentication on Gmail**
   - Visit: https://myaccount.google.com/security
   - Enable "2-Step Verification"

2. **Generate App Password**
   - Visit: https://myaccount.google.com/apppasswords
   - Select App: **Mail**
   - Select Device: **Other (Custom name)** → Type "Varon"
   - Click **Generate**
   - Copy the 16-character password (no spaces)

3. **Update .env File**
   ```env
   MAIL_USERNAME=your-actual-email@gmail.com
   MAIL_PASSWORD=your-16-character-app-password
   ```

4. **Test Email**
   ```bash
   python scripts/test_otp.py
   ```
   Select option 1 and enter your email

**Status:** ⏳ **WAITING** - Configure Gmail credentials

---

### 2. SMS Setup (OPTIONAL)

#### Option A: Semaphore (Philippines - FREE Credits)

1. **Sign Up**
   - Visit: https://semaphore.co/
   - Register for free account
   - Get FREE ₱20-50 credits

2. **Get API Key**
   - Login to dashboard
   - Navigate to "API" section
   - Copy your API key

3. **Update .env File**
   ```env
   SEMAPHORE_API_KEY=your-api-key-here
   SEMAPHORE_SENDER_NAME=VARON
   ```

4. **Test SMS**
   ```bash
   python scripts/test_otp.py
   ```
   Select option 2 and enter phone number

**Status:** ⏳ **OPTIONAL** - Add if you want SMS verification

#### Option B: Twilio (International - $15 Trial)

1. **Sign Up**
   - Visit: https://www.twilio.com/try-twilio
   - Register and verify phone
   - Get $15.50 free trial credit

2. **Get Credentials**
   - From Twilio Console:
     - Account SID
     - Auth Token
     - Phone Number

3. **Update .env File**
   ```env
   TWILIO_ACCOUNT_SID=your-account-sid
   TWILIO_AUTH_TOKEN=your-auth-token
   TWILIO_PHONE_NUMBER=+1234567890
   ```

4. **Test SMS**
   ```bash
   python scripts/test_otp.py
   ```

**Status:** ⏳ **OPTIONAL** - Alternative SMS provider

---

## 🧪 Testing Checklist

### After Gmail Configuration:

- [ ] Run test script: `python scripts/test_otp.py`
- [ ] Test email OTP (option 1)
- [ ] Receive email with OTP code
- [ ] Verify email looks good

### Full System Test:

- [ ] Start app: `python app.py`
- [ ] Open: http://localhost:5000/login
- [ ] Click "Sign Up" tab
- [ ] Fill in registration form
- [ ] Submit form
- [ ] Check email for OTP
- [ ] Enter OTP on verification page
- [ ] Verify redirect to login
- [ ] Login with new account
- [ ] Check user dashboard

### SMS Test (If Configured):

- [ ] Sign up as Rider
- [ ] Check both email and phone
- [ ] Receive OTP via SMS
- [ ] Verify SMS format is correct

---

## 📊 Verification Status

### Email OTP Status:
```
[  ] Not Configured
[  ] Configured - Not Tested
[  ] Tested - Working
[  ] Tested - Has Issues
```

### SMS OTP Status:
```
[  ] Not Needed (Email Only)
[  ] Not Configured
[  ] Configured - Not Tested  
[  ] Tested - Working
[  ] Tested - Has Issues
```

### Database Status:
```
[x] Migration Executed Successfully
[x] Tables Created
[x] Columns Added to Users Table
```

### Code Status:
```
[x] OTP Service Implemented
[x] Routes Added to app.py
[x] Signup Routes Updated
[x] UI Templates Created
[x] No Syntax Errors
```

---

## 🚨 Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'dotenv'"
**Solution:**
```bash
pip install python-dotenv
```

### Issue: Email not sending
**Checklist:**
- [ ] Using Gmail app password (not regular password)
- [ ] 2FA enabled on Gmail account
- [ ] App password is 16 characters
- [ ] No spaces in app password
- [ ] MAIL_USERNAME is correct email
- [ ] MAIL_PASSWORD is correct app password

**Test:**
```bash
python -c "from utils.otp_service import OTPService; print(OTPService.send_email_otp('test@example.com', '123456', 'registration'))"
```

### Issue: "SMTPAuthenticationError"
**Solution:** Regenerate Gmail app password

### Issue: Can't connect to database
**Solution:** Check MySQL is running and credentials are correct

### Issue: OTP page not showing
**Solution:** Check session is working and redirect is correct

---

## 🎯 Next Steps After Setup

1. **Test thoroughly** - Try all signup flows
2. **Customize email** - Edit `utils/otp_service.py` for branding
3. **Set up monitoring** - Track OTP success rates
4. **Configure production** - Use HTTPS, secure secrets
5. **Add logging** - Monitor OTP failures
6. **Set up backup** - Alternative verification methods

---

## 📞 Getting Help

### Quick Diagnostics:
```bash
python scripts/test_otp.py
```

### Check Logs:
```bash
python app.py
```
Look for error messages in console

### Verify Database:
```bash
mysql -u root -p varon -e "SELECT * FROM otp_verifications LIMIT 5;"
```

### Test Email Service:
```bash
python -c "from utils.otp_service import OTPService; print(OTPService.send_email_otp('your-email@gmail.com', '123456', 'registration'))"
```

---

## 📝 Configuration Summary

### Required:
- [x] Database migration ✓
- [x] Python packages ✓
- [ ] Gmail app password ⏳
- [x] .env file created ✓

### Optional:
- [ ] SMS provider (Semaphore/Twilio)
- [ ] Custom email templates
- [ ] Custom SMS messages
- [ ] Advanced security settings

---

## 🎉 When Everything Works

You'll see:
1. User signs up
2. Redirects to OTP verification page
3. Email arrives within seconds
4. User enters 6-digit code
5. Verification succeeds
6. Redirects to login
7. User can log in successfully

---

**Current Status:** 🟡 **90% Complete** - Just add Gmail credentials!

**Next Step:** Configure Gmail app password in `.env` file

**Then:** Run `python scripts/test_otp.py` to verify email works

---

Need help? Check:
- `OTP_QUICKSTART.md` - Quick setup guide
- `docs/OTP_SETUP_GUIDE.md` - Detailed documentation
- `OTP_IMPLEMENTATION_SUMMARY.md` - What was built

**All set! Configure Gmail and you're ready to go! 🚀**
