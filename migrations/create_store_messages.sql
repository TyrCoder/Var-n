-- Create buyer ↔ seller chat table for brand stores
CREATE TABLE IF NOT EXISTS store_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    seller_id INT NOT NULL,
    buyer_id INT NOT NULL,
    sender_id INT NOT NULL,
    sender_role ENUM('buyer', 'seller', 'admin') NOT NULL DEFAULT 'buyer',
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (seller_id) REFERENCES sellers(id) ON DELETE CASCADE,
    FOREIGN KEY (buyer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_seller_buyer (seller_id, buyer_id, created_at),
    INDEX idx_sender (sender_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Confirm table exists
SHOW TABLES LIKE 'store_messages';
DESC store_messages;
