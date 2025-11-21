# OTP Authentication Flow

## Registration Flow with OTP

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER REGISTRATION FLOW                       │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │    User      │
    │  Opens App   │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Login Page   │
    │ /login       │
    └──────┬───────┘
           │
           │ Clicks "Sign Up"
           ▼
    ┌──────────────────────┐
    │  Registration Form   │
    │                      │
    │  • First Name        │
    │  • Last Name         │
    │  • Email             │
    │  • Phone             │
    │  • Password          │
    │  • Terms Checkbox    │
    └──────┬───────────────┘
           │
           │ Submit Form
           ▼
    ┌──────────────────────┐
    │   Backend Process    │
    │   (app.py)           │
    │                      │
    │  1. Validate Data    │
    │  2. Check Duplicates │
    │  3. Create User      │────────┐
    │  4. Generate OTP     │        │
    └──────┬───────────────┘        │
           │                         │
           │                    ┌────▼─────────┐
           │                    │   Database   │
           │                    │   users      │
           │                    │   table      │
           │                    └────┬─────────┘
           │                         │
           │                    user_id = 123
           │                    email_verified = FALSE
           │                         │
           ├─────────────────────────┘
           │
           ▼
    ┌──────────────────────┐
    │  OTP Service         │
    │  (otp_service.py)    │
    │                      │
    │  1. Generate Code    │───► "123456"
    │  2. Save to DB       │
    │  3. Send Email/SMS   │
    └──────┬───────────────┘
           │
           │
    ┌──────┴───────┐
    │              │
    ▼              ▼
┌────────┐    ┌─────────┐
│ Email  │    │   SMS   │
│ (Gmail)│    │(Twilio/ │
│        │    │Semaphre)│
└───┬────┘    └────┬────┘
    │              │
    │              │
    ▼              ▼
┌────────────────────────┐
│   User's Inbox/Phone   │
│                        │
│   "Your code: 123456"  │
└───┬────────────────────┘
    │
    │ User receives OTP
    ▼
┌──────────────────────┐
│  OTP Verify Page     │
│  /verify-otp-page    │
│                      │
│  ┌──┐┌──┐┌──┐       │
│  │1 ││2 ││3 │       │
│  └──┘└──┘└──┘       │
│  ┌──┐┌──┐┌──┐       │
│  │4 ││5 ││6 │       │
│  └──┘└──┘└──┘       │
│                      │
│  [Verify Button]     │
│  [Resend OTP]        │
└───┬──────────────────┘
    │
    │ User enters code
    ▼
┌──────────────────────┐
│  Backend Verify      │
│  POST /verify-otp    │
│                      │
│  1. Check code       │
│  2. Check expiry     │
│  3. Check attempts   │
│  4. Update user      │
└───┬──────────────────┘
    │
    │
┌───┴───────────────────────────────────┐
│                                       │
│  ✓ Valid?                             │
│                                       │
└───┬────────────────────┬──────────────┘
    │                    │
    │ YES                │ NO
    ▼                    ▼
┌─────────────┐      ┌──────────────┐
│  Success    │      │   Error      │
│             │      │              │
│ • Set       │      │ • Increment  │
│   verified  │      │   attempts   │
│   = TRUE    │      │ • Show error │
│ • Clear     │      │ • Try again  │
│   session   │      └──────────────┘
│ • Redirect  │
│   to login  │
└─────┬───────┘
      │
      ▼
┌─────────────┐
│ Login Page  │
│             │
│ "Success!   │
│  Please     │
│  log in"    │
└─────────────┘


═══════════════════════════════════════════════════════════════

## Database Tables

┌─────────────────────────────────────────────────────────┐
│                    users                                │
├─────────────────────────────────────────────────────────┤
│ id                  INT PRIMARY KEY                     │
│ email               VARCHAR(190) UNIQUE                 │
│ password            VARCHAR(255)                        │
│ first_name          VARCHAR(100)                        │
│ last_name           VARCHAR(100)                        │
│ phone               VARCHAR(20)                         │
│ role                ENUM(buyer, seller, admin, rider)   │
│ email_verified      BOOLEAN DEFAULT FALSE        ◄──┐   │
│ phone_verified      BOOLEAN DEFAULT FALSE           │   │
│ email_verified_at   TIMESTAMP NULL                  │   │
│ phone_verified_at   TIMESTAMP NULL                  │   │
│ created_at          TIMESTAMP                       │   │
└─────────────────────────────────────────────────────┼───┘
                                                      │
                                                      │
┌─────────────────────────────────────────────────────┼───┐
│                otp_verifications                    │   │
├─────────────────────────────────────────────────────┼───┤
│ id                  INT PRIMARY KEY                 │   │
│ user_id             INT FOREIGN KEY ───────────────►│   │
│ email               VARCHAR(190)                        │
│ phone               VARCHAR(20)                         │
│ otp_code            VARCHAR(10)                         │
│ otp_type            ENUM(email, sms, both)              │
│ purpose             ENUM(registration, login, etc)      │
│ attempts            INT DEFAULT 0                       │
│ is_verified         BOOLEAN DEFAULT FALSE               │
│ expires_at          TIMESTAMP                           │
│ created_at          TIMESTAMP                           │
│ verified_at         TIMESTAMP NULL                      │
│ ip_address          VARCHAR(45)                         │
└─────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════

## OTP Lifecycle

┌─────────────┐
│   Created   │  ◄─── Generate 6-digit code
└──────┬──────┘       Save to database
       │              expires_at = now + 10 minutes
       │
       ▼
┌─────────────┐
│    Sent     │  ◄─── Email/SMS delivered
└──────┬──────┘       User receives code
       │
       │
       ▼
┌─────────────┐
│   Pending   │  ◄─── Waiting for user input
└──────┬──────┘       attempts = 0
       │
       │
┌──────┴────────────────────────┐
│                               │
│  User enters code?            │
│                               │
└──────┬────────────┬───────────┘
       │            │
  Invalid      Valid
       │            │
       ▼            ▼
┌─────────────┐  ┌─────────────┐
│  Increment  │  │  Verified   │
│  attempts   │  │             │
└──────┬──────┘  │ is_verified │
       │         │   = TRUE    │
       │         └──────┬──────┘
       │                │
       │                ▼
       │         ┌─────────────┐
       │         │   Update    │
       │         │    User     │
       │         │             │
       │         │ email_verified │
       │         │    = TRUE   │
       │         └─────────────┘
       │
       ▼
┌─────────────┐
│ attempts > 5│
│   OR        │
│  expired?   │
└──────┬──────┘
       │
       │ YES
       ▼
┌─────────────┐
│   Failed    │
│             │
│ Must resend │
└─────────────┘


═══════════════════════════════════════════════════════════════

## Email Template Structure

┌───────────────────────────────────────────────┐
│                                               │
│              Varón                            │
│                                               │
│         Verification Code                     │
│                                               │
│  Use this code to complete your              │
│  registration:                                │
│                                               │
│  ┌─────────────────────────────────┐         │
│  │                                 │         │
│  │          1 2 3 4 5 6            │         │
│  │                                 │         │
│  └─────────────────────────────────┘         │
│                                               │
│  This code will expire in 10 minutes.        │
│  For your security, do not share this        │
│  code with anyone.                            │
│                                               │
│  If you didn't request this code,            │
│  please ignore this email.                    │
│                                               │
│  ─────────────────────────────────            │
│  © 2025 Varón. All rights reserved.          │
│                                               │
└───────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════

## SMS Message Format

┌───────────────────────────────────────────┐
│  From: VARON                              │
│                                           │
│  Your Varon registration code is:        │
│  123456                                   │
│                                           │
│  Valid for 10 minutes. Do not share      │
│  this code.                               │
└───────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════

## Security Features

┌─────────────────────────────────────────────────────────┐
│                   Security Layers                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. Rate Limiting                                       │
│     └── Max 5 attempts per OTP code                     │
│                                                         │
│  2. Time Expiration                                     │
│     └── OTP expires after 10 minutes                    │
│                                                         │
│  3. One-Time Use                                        │
│     └── Code marked as used after verification          │
│                                                         │
│  4. IP Tracking                                         │
│     └── Logs requesting IP for audit                    │
│                                                         │
│  5. Session Security                                    │
│     └── Verification state stored in session            │
│                                                         │
│  6. Resend Cooldown                                     │
│     └── 60-second wait before resending                 │
│                                                         │
└─────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════

## Error Handling

┌─────────────────────────┐
│   Possible Errors       │
├─────────────────────────┤
│                         │
│  ✗ Invalid OTP code     │
│    ↳ Show error         │
│    ↳ Allow retry       │
│                         │
│  ✗ OTP expired          │
│    ↳ Offer resend       │
│                         │
│  ✗ Max attempts         │
│    ↳ Must resend        │
│                         │
│  ✗ Email failed         │
│    ↳ Log error          │
│    ↳ Try SMS fallback   │
│                         │
│  ✗ Database error       │
│    ↳ Show generic error │
│    ↳ Log details        │
│                         │
└─────────────────────────┘


═══════════════════════════════════════════════════════════════

## Provider Integration

Email (Gmail SMTP)
┌─────────────────────────────┐
│   app.py                    │
│     ↓                       │
│   otp_service.py            │
│     ↓                       │
│   send_email_otp()          │
│     ↓                       │
│   smtplib.SMTP()            │
│     ↓                       │
│   smtp.gmail.com:587        │
│     ↓                       │
│   Gmail Server              │
│     ↓                       │
│   User's Inbox              │
└─────────────────────────────┘

SMS (Semaphore/Twilio)
┌─────────────────────────────┐
│   app.py                    │
│     ↓                       │
│   otp_service.py            │
│     ↓                       │
│   send_sms_otp()            │
│     ↓                       │
│   requests.post()           │
│     ↓                       │
│   Semaphore/Twilio API      │
│     ↓                       │
│   SMS Gateway               │
│     ↓                       │
│   User's Phone              │
└─────────────────────────────┘
```

This visual guide shows the complete flow of the OTP authentication system implemented in your Varón e-commerce platform!
