-- Add seller confirmation field to shipments table
-- This tracks whether the seller has confirmed the rider can proceed with delivery

ALTER TABLE shipments 
ADD COLUMN seller_confirmed BOOLEAN DEFAULT FALSE AFTER rider_id,
ADD COLUMN seller_confirmed_at TIMESTAMP NULL AFTER seller_confirmed;

-- Update existing shipments to be confirmed if rider is already assigned
UPDATE shipments 
SET seller_confirmed = TRUE, seller_confirmed_at = NOW() 
WHERE rider_id IS NOT NULL;
