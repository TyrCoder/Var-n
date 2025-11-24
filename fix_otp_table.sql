-- Fix OTP Verifications Table - Add missing columns
-- Run this script directly in your MySQL database
-- Note: If columns already exist, you'll get an error - that's okay, just ignore it

USE varon;

-- Add phone column (run this - if it exists, you'll get an error which you can ignore)
ALTER TABLE otp_verifications 
ADD COLUMN phone VARCHAR(20) AFTER email;

-- Add used_at column (run this - if it exists, you'll get an error which you can ignore)
ALTER TABLE otp_verifications 
ADD COLUMN used_at TIMESTAMP NULL AFTER expires_at;

-- Add index for phone (run this - if it exists, you'll get an error which you can ignore)
CREATE INDEX idx_phone ON otp_verifications(phone);

-- Verify table structure
DESCRIBE otp_verifications;

