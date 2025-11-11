-- Migration script to update existing Varon database with product edit and archive features
-- Run this if you already have an existing database

USE varon;

-- Add new columns to products table
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS edit_status ENUM('none', 'pending', 'approved', 'rejected') DEFAULT 'none',
ADD COLUMN IF NOT EXISTS archive_status ENUM('active', 'archived', 'pending_recovery') DEFAULT 'active',
ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP NULL,
ADD COLUMN IF NOT EXISTS archived_by INT NULL;

-- Add indexes
ALTER TABLE products ADD INDEX IF NOT EXISTS idx_edit_status (edit_status);
ALTER TABLE products ADD INDEX IF NOT EXISTS idx_archive_status (archive_status);

-- Create product_edits table
CREATE TABLE IF NOT EXISTS product_edits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    seller_id INT NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    admin_notes TEXT,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP NULL,
    reviewed_by INT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (seller_id) REFERENCES sellers(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_product (product_id),
    INDEX idx_status (status),
    INDEX idx_seller (seller_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create product_archive_requests table
CREATE TABLE IF NOT EXISTS product_archive_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    seller_id INT NOT NULL,
    request_type ENUM('archive', 'recover') NOT NULL,
    reason TEXT,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    admin_notes TEXT,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP NULL,
    reviewed_by INT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (seller_id) REFERENCES sellers(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_product (product_id),
    INDEX idx_status (status),
    INDEX idx_seller (seller_id),
    INDEX idx_type (request_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Update existing products to have default values
UPDATE products 
SET edit_status = 'none', archive_status = 'active'
WHERE edit_status IS NULL OR archive_status IS NULL;

SELECT 'Migration completed successfully!' as message;
