-- Add columns for the new order confirmation flow
-- These columns track the multi-step confirmation process

ALTER TABLE orders
ADD COLUMN IF NOT EXISTS rider_id INT NULL AFTER seller_id,
ADD COLUMN IF NOT EXISTS seller_confirmed_rider BOOLEAN DEFAULT FALSE AFTER rider_id,
ADD COLUMN IF NOT EXISTS buyer_approved_rider BOOLEAN DEFAULT FALSE AFTER seller_confirmed_rider,
ADD FOREIGN KEY (rider_id) REFERENCES users(id) ON DELETE SET NULL;

-- Add index for faster queries
ALTER TABLE orders
ADD INDEX idx_rider (rider_id) IF NOT EXISTS;
