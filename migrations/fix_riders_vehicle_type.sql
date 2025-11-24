-- Migration: Fix riders table to support multiple vehicle types
-- This migration changes vehicle_type from ENUM to TEXT to support comma-separated values

ALTER TABLE riders 
MODIFY COLUMN vehicle_type TEXT NOT NULL;

-- Update index if needed (optional)
-- This allows storing multiple vehicle types like "motorcycle,truck,van"
