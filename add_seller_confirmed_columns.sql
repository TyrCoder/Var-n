-- Add seller_confirmed columns to shipments table
-- Run this to fix the "Unknown column 'seller_confirmed'" error

USE varon;

-- Add seller_confirmed column if it doesn't exist
ALTER TABLE shipments 
ADD COLUMN IF NOT EXISTS seller_confirmed BOOLEAN DEFAULT FALSE AFTER status;

-- Add seller_confirmed_at column if it doesn't exist
ALTER TABLE shipments 
ADD COLUMN IF NOT EXISTS seller_confirmed_at TIMESTAMP NULL AFTER seller_confirmed;

-- Verify the columns were added
DESCRIBE shipments;

SELECT 'Migration completed successfully!' AS status;
