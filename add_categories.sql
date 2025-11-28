-- Add new categories
INSERT INTO categories (name, slug, description, is_active) VALUES
('Grooming Products', 'grooming-products', 'Personal grooming and care products', TRUE),
('Activewear & Fitness', 'activewear-fitness', 'Athletic wear and fitness apparel', TRUE),
('Shoes & Accessories', 'shoes-accessories', 'Footwear and fashion accessories', TRUE),
('Outerwear & Jackets', 'outerwear-jackets', 'Jackets, coats, and outer layers', TRUE),
('Casual Shirts & Pants', 'casual-shirts-pants', 'Casual everyday clothing', TRUE),
('Suits & Blazers', 'suits-blazers', 'Formal wear and blazers', TRUE)
ON DUPLICATE KEY UPDATE description = VALUES(description), is_active = TRUE;

-- Verify categories
SELECT id, name, slug FROM categories ORDER BY name;
