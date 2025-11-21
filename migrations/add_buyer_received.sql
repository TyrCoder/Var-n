-- Migration: Add buyer_received columns to orders table
-- Date: November 20, 2025
-- Purpose: Track when buyer confirms they received their order

USE varon;

-- Add buyer_received columns to orders table
ALTER TABLE orders 
ADD COLUMN IF NOT EXISTS buyer_received BOOLEAN DEFAULT FALSE AFTER order_status,
ADD COLUMN IF NOT EXISTS buyer_received_at DATETIME NULL AFTER buyer_received;

-- Add index for querying received orders
CREATE INDEX IF NOT EXISTS idx_buyer_received ON orders(buyer_received, buyer_received_at);

-- Update description
ALTER TABLE orders COMMENT = 'Orders table with buyer confirmation tracking';

SELECT '✅ Migration complete: buyer_received columns added to orders table' as status;
