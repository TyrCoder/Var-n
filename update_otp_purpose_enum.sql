-- Update OTP purpose enum to include email_change and phone_verification
-- Run this script to update the database enum values

ALTER TABLE otp_verifications 
MODIFY COLUMN purpose ENUM('registration', 'login', 'password_reset', 'verification', 'email_change', 'phone_verification') 
NOT NULL DEFAULT 'registration';

