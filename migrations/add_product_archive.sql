-- Add archive functionality for products
USE varon;

-- Add archive status to products table
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS archive_status ENUM('active', 'archived', 'pending_recovery') DEFAULT 'active',
ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP NULL,
ADD COLUMN IF NOT EXISTS archived_by INT NULL,
ADD INDEX idx_archive_status (archive_status);

-- Create product_archive_requests table for tracking recovery requests
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
