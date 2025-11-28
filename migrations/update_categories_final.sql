-- ============================================
-- FINAL MEN'S APPAREL CATEGORY STRUCTURE
-- ============================================
-- This updates the categories table to match the finalized hierarchy:
-- - TOPS (parent) with 6 subcategories
-- - BOTTOMS (parent) with 3 subcategories
-- - FOOTWEAR (standalone)
-- - ACCESSORIES (standalone)
-- - GROOMING PRODUCTS (standalone)

-- Add category_type column if it doesn't exist
ALTER TABLE categories ADD COLUMN category_type VARCHAR(50) DEFAULT 'general';

-- First, clear existing categories to avoid conflicts  
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE categories;
SET FOREIGN_KEY_CHECKS = 1;

-- Insert parent categories
INSERT INTO categories (id, name, slug, description, parent_id, category_type, is_active, created_at) VALUES
(1, 'TOPS', 'tops', 'All top wear for men', NULL, 'tops', TRUE, NOW()),
(2, 'BOTTOMS', 'bottoms', 'All bottom wear for men', NULL, 'bottoms', TRUE, NOW()),
(3, 'FOOTWEAR', 'footwear', 'All types of men''s shoes', NULL, 'footwear', TRUE, NOW()),
(4, 'ACCESSORIES', 'accessories', 'Belts, wallets, hats, bags, watches, eyewear, etc.', NULL, 'accessories', TRUE, NOW()),
(5, 'GROOMING PRODUCTS', 'grooming-products', 'Skincare, haircare, fragrances, etc.', NULL, 'grooming', TRUE, NOW());

-- Insert TOPS subcategories
INSERT INTO categories (id, name, slug, description, parent_id, category_type, is_active, created_at) VALUES
(11, 'Barong', 'barong', 'Traditional Filipino formal shirt', 1, 'tops', TRUE, NOW()),
(12, 'Suits & Blazers', 'suits-blazers', 'Formal suits and blazer jackets', 1, 'tops', TRUE, NOW()),
(13, 'Casual Shirts', 'casual-shirts', 'Everyday casual shirts', 1, 'tops', TRUE, NOW()),
(14, 'Polo Shirt', 'polo-shirt', 'Classic polo shirts', 1, 'tops', TRUE, NOW()),
(15, 'Outerwear & Jackets', 'outerwear-jackets', 'Jackets, coats, and outerwear', 1, 'tops', TRUE, NOW()),
(16, 'Activewear & Fitness Tops', 'activewear-fitness-tops', 'Athletic and fitness tops', 1, 'tops', TRUE, NOW());

-- Insert BOTTOMS subcategories
INSERT INTO categories (id, name, slug, description, parent_id, category_type, is_active, created_at) VALUES
(21, 'Pants', 'pants', 'All types of pants and trousers', 2, 'bottoms', TRUE, NOW()),
(22, 'Shorts', 'shorts', 'Casual and athletic shorts', 2, 'bottoms', TRUE, NOW()),
(23, 'Activewear & Fitness Bottoms', 'activewear-fitness-bottoms', 'Athletic and fitness bottoms', 2, 'bottoms', TRUE, NOW());

-- Verify the structure
SELECT 
    c1.id,
    c1.name as category,
    c1.category_type,
    c1.parent_id,
    c2.name as parent_name
FROM categories c1
LEFT JOIN categories c2 ON c1.parent_id = c2.id
ORDER BY 
    COALESCE(c1.parent_id, c1.id),
    c1.id;
