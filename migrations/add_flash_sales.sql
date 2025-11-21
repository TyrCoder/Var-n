-- Migration: Add Flash Sales System
-- Created: November 21, 2025
-- Description: Add tables for flash sales and promotional discounts

-- Flash sales table
CREATE TABLE IF NOT EXISTS flash_sales (
    id INT PRIMARY KEY AUTO_INCREMENT,
    seller_id INT NOT NULL,
    sale_name VARCHAR(255) NOT NULL,
    description TEXT,
    discount_percentage DECIMAL(5,2) NOT NULL CHECK (discount_percentage >= 5 AND discount_percentage <= 90),
    start_date DATETIME NOT NULL,
    end_date DATETIME NOT NULL,
    status ENUM('upcoming', 'active', 'ended') DEFAULT 'upcoming',
    total_orders INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (seller_id) REFERENCES sellers(id) ON DELETE CASCADE,
    INDEX idx_seller (seller_id),
    INDEX idx_status (status),
    INDEX idx_dates (start_date, end_date)
);

-- Flash sale products (which products are in which sale)
CREATE TABLE IF NOT EXISTS flash_sale_products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    flash_sale_id INT NOT NULL,
    product_id INT NOT NULL,
    original_price DECIMAL(10,2) NOT NULL,
    sale_price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (flash_sale_id) REFERENCES flash_sales(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE KEY unique_sale_product (flash_sale_id, product_id),
    INDEX idx_flash_sale (flash_sale_id),
    INDEX idx_product (product_id)
);

-- Add sale_id to orders to track which orders used flash sales
ALTER TABLE orders ADD COLUMN flash_sale_id INT DEFAULT NULL AFTER seller_id;
ALTER TABLE orders ADD FOREIGN KEY (flash_sale_id) REFERENCES flash_sales(id) ON DELETE SET NULL;
ALTER TABLE orders ADD INDEX idx_flash_sale (flash_sale_id);
