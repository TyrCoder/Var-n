-- Migration to update product categories
-- Based on Google Drive folder structure

USE varon;

-- Disable foreign key checks temporarily
SET FOREIGN_KEY_CHECKS = 0;

-- Truncate categories table to start fresh
TRUNCATE TABLE categories;

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- Insert new categories based on Drive structure
INSERT INTO categories (name, slug, description, is_active) VALUES
('Suits & Blazers', 'suits-blazers', 'Formal suits, blazers, and professional attire', TRUE),
('Shoes & Accessories', 'shoes-accessories', 'Footwear and fashion accessories', TRUE),
('Outerwear & Jackets', 'outerwear-jackets', 'Jackets, coats, and outerwear', TRUE),
('Grooming Products', 'grooming', 'Personal care and grooming items', TRUE),
('Casual Shirts & Pants', 'casual-shirts-pants', 'Everyday casual wear', TRUE),
('Activewear & Fitness', 'activewear-fitness', 'Athletic and fitness apparel', TRUE);

-- Verify insertion
SELECT * FROM categories ORDER BY name;
