-- Create rider_ratings table for buyers to rate riders after delivery

CREATE TABLE IF NOT EXISTS rider_ratings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rider_id INT NOT NULL,
    user_id INT NOT NULL COMMENT 'Buyer who is rating',
    order_id INT NOT NULL,
    shipment_id INT NULL,
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (rider_id) REFERENCES riders(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (shipment_id) REFERENCES shipments(id) ON DELETE SET NULL,
    
    UNIQUE KEY unique_rating (rider_id, user_id, order_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add index for performance
CREATE INDEX idx_rider_ratings_rider ON rider_ratings(rider_id);
CREATE INDEX idx_rider_ratings_user ON rider_ratings(user_id);
CREATE INDEX idx_rider_ratings_order ON rider_ratings(order_id);
