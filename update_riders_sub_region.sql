-- Migration: Add sub_region support to riders table for North/Central/South Luzon subdivision
-- This ensures riders can be matched to orders based on delivery location region

-- Step 1: Add sub_region column if it doesn't exist (already in schema)
-- ALTER TABLE riders ADD COLUMN sub_region ENUM('North Luzon', 'Central Luzon', 'South Luzon', 'Visayas', 'Mindanao', 'All areas') DEFAULT 'All areas';

-- Step 2: Update existing riders based on their current service_area
-- If a rider has "Luzon", subdivide them or set to "All areas"
-- If they have "Visayas", map to "Visayas"
-- If they have "Mindanao", map to "Mindanao"

-- Map generic "Luzon" to "All areas" (they should update their profile to be more specific)
UPDATE riders SET sub_region = 'All areas' WHERE service_area = 'Luzon' AND sub_region IS NULL;

-- Map "Visayas" to "Visayas"
UPDATE riders SET sub_region = 'Visayas' WHERE service_area = 'Visayas' AND sub_region IS NULL;

-- Map "Mindanao" to "Mindanao"
UPDATE riders SET sub_region = 'Mindanao' WHERE service_area = 'Mindanao' AND sub_region IS NULL;

-- Map "All areas" to "All areas"
UPDATE riders SET sub_region = 'All areas' WHERE service_area = 'All areas' AND sub_region IS NULL;

-- Set default for any remaining NULL values
UPDATE riders SET sub_region = 'All areas' WHERE sub_region IS NULL;

-- Verification queries:
-- SELECT COUNT(*) FROM riders WHERE sub_region = 'All areas';
-- SELECT COUNT(*) FROM riders WHERE sub_region = 'Visayas';
-- SELECT COUNT(*) FROM riders WHERE sub_region = 'Mindanao';
-- SELECT id, service_area, sub_region FROM riders LIMIT 10;
