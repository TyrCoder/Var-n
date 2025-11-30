-- Create seller_notifications table for product approval/rejection notifications
CREATE TABLE IF NOT EXISTS seller_notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    seller_id INT NOT NULL,
    product_id INT NULL,
    notification_type ENUM('new_order', 'order_cancelled', 'product_approved', 'product_rejected') NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    read_at DATETIME NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_seller_read (seller_id, is_read),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Show table structure
DESCRIBE seller_notifications;

-- Verify table was created
SHOW TABLES LIKE 'seller_notifications';
