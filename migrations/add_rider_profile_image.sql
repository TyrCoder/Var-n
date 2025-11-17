-- Migration: Add profile_image column to riders table
-- Date: November 17, 2025
-- Description: Adds profile image support for riders

-- Add profile_image column to riders table if it doesn't exist
ALTER TABLE riders 
ADD COLUMN IF NOT EXISTS profile_image VARCHAR(500) AFTER service_area;

-- Optional: Update existing riders with a default placeholder
-- UPDATE riders SET profile_image = '/static/images/default-avatar.png' WHERE profile_image IS NULL;

-- Verify the change
SELECT 'Migration completed successfully: profile_image column added to riders table' AS status;
