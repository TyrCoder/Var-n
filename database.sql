
CREATE DATABASE IF NOT EXISTS varon CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE varon;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(190) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('buyer', 'seller', 'admin', 'rider') NOT NULL DEFAULT 'buyer',
    phone VARCHAR(20),
    status ENUM('active', 'inactive', 'pending', 'suspended') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_role (role),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    parent_id INT NULL,
    image_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE SET NULL,
    INDEX idx_slug (slug),
    INDEX idx_parent (parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS sellers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    store_name VARCHAR(150) NOT NULL,
    store_slug VARCHAR(150) NOT NULL UNIQUE,
    description TEXT,
    logo_url VARCHAR(500),
    address TEXT,
    city VARCHAR(100),
    province VARCHAR(100),
    postal_code VARCHAR(20),
    business_license VARCHAR(100),
    tax_id VARCHAR(100),
    bank_account VARCHAR(100),
    rating DECIMAL(3,2) DEFAULT 0.00,
    total_sales DECIMAL(15,2) DEFAULT 0.00,
    commission_rate DECIMAL(5,2) DEFAULT 10.00,
    status ENUM('pending', 'approved', 'rejected', 'suspended') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user (user_id),
    INDEX idx_status (status),
    INDEX idx_slug (store_slug)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    seller_id INT NOT NULL,
    category_id INT NOT NULL,
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(200) NOT NULL,
    description TEXT,
    brand VARCHAR(100),
    gender ENUM('men', 'women', 'unisex') DEFAULT 'men',
    price DECIMAL(10,2) NOT NULL,
    sale_price DECIMAL(10,2),
    cost_price DECIMAL(10,2),
    sku VARCHAR(100) UNIQUE,
    weight DECIMAL(8,2),
    dimensions VARCHAR(100),
    material VARCHAR(200),
    care_instructions TEXT,
    is_featured BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    views_count INT DEFAULT 0,
    sales_count INT DEFAULT 0,
    rating DECIMAL(3,2) DEFAULT 0.00,
    review_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (seller_id) REFERENCES sellers(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT,
    INDEX idx_seller (seller_id),
    INDEX idx_category (category_id),
    INDEX idx_active (is_active),
    INDEX idx_featured (is_featured),
    INDEX idx_slug (slug)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS product_images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    image_url VARCHAR(500) NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    INDEX idx_product (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS product_variants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    sku VARCHAR(100) UNIQUE,
    size VARCHAR(20),
    color VARCHAR(50),
    stock_quantity INT DEFAULT 0,
    price_adjustment DECIMAL(10,2) DEFAULT 0.00,
    weight_adjustment DECIMAL(8,2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    INDEX idx_product (product_id),
    INDEX idx_sku (sku)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS inventory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    variant_id INT,
    stock_quantity INT DEFAULT 0,
    reserved_quantity INT DEFAULT 0,
    available_quantity INT GENERATED ALWAYS AS (stock_quantity - reserved_quantity) STORED,
    low_stock_threshold INT DEFAULT 10,
    reorder_point INT DEFAULT 5,
    last_restocked_at TIMESTAMP NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (variant_id) REFERENCES product_variants(id) ON DELETE CASCADE,
    UNIQUE KEY unique_inventory (product_id, variant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS addresses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    address_type ENUM('billing', 'shipping', 'both') DEFAULT 'shipping',
    full_name VARCHAR(150) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    street_address TEXT NOT NULL,
    barangay VARCHAR(100),
    city VARCHAR(100) NOT NULL,
    province VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20),
    country VARCHAR(50) DEFAULT 'Philippines',
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    user_id INT NOT NULL,
    seller_id INT NOT NULL,
    shipping_address_id INT NOT NULL,
    billing_address_id INT,
    subtotal DECIMAL(10,2) NOT NULL,
    shipping_fee DECIMAL(10,2) DEFAULT 0.00,
    tax_amount DECIMAL(10,2) DEFAULT 0.00,
    discount_amount DECIMAL(10,2) DEFAULT 0.00,
    total_amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(50),
    payment_status ENUM('pending', 'paid', 'failed', 'refunded') DEFAULT 'pending',
    order_status ENUM('pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'returned') DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,
    FOREIGN KEY (seller_id) REFERENCES sellers(id) ON DELETE RESTRICT,
    FOREIGN KEY (shipping_address_id) REFERENCES addresses(id) ON DELETE RESTRICT,
    FOREIGN KEY (billing_address_id) REFERENCES addresses(id) ON DELETE RESTRICT,
    INDEX idx_user (user_id),
    INDEX idx_seller (seller_id),
    INDEX idx_status (order_status),
    INDEX idx_order_number (order_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    variant_id INT,
    product_name VARCHAR(200) NOT NULL,
    sku VARCHAR(100),
    size VARCHAR(20),
    color VARCHAR(50),
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT,
    FOREIGN KEY (variant_id) REFERENCES product_variants(id) ON DELETE RESTRICT,
    INDEX idx_order (order_id),
    INDEX idx_product (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS riders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    vehicle_type ENUM('motorcycle', 'bicycle', 'car', 'van', 'truck') NOT NULL,
    license_number VARCHAR(50),
    vehicle_plate VARCHAR(20),
    service_area TEXT,
    max_delivery_distance INT DEFAULT 50,
    current_location_lat DECIMAL(10,8),
    current_location_lng DECIMAL(11,8),
    is_available BOOLEAN DEFAULT TRUE,
    rating DECIMAL(3,2) DEFAULT 0.00,
    total_deliveries INT DEFAULT 0,
    earnings DECIMAL(10,2) DEFAULT 0.00,
    status ENUM('pending', 'approved', 'active', 'inactive', 'suspended') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user (user_id),
    INDEX idx_status (status),
    INDEX idx_available (is_available)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS shipments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL UNIQUE,
    rider_id INT,
    tracking_number VARCHAR(100) UNIQUE,
    carrier VARCHAR(100),
    shipped_at TIMESTAMP NULL,
    estimated_delivery TIMESTAMP NULL,
    delivered_at TIMESTAMP NULL,
    delivery_proof_url VARCHAR(500),
    delivery_notes TEXT,
    status ENUM('pending', 'picked_up', 'in_transit', 'out_for_delivery', 'delivered', 'failed', 'returned') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (rider_id) REFERENCES riders(id) ON DELETE SET NULL,
    INDEX idx_order (order_id),
    INDEX idx_rider (rider_id),
    INDEX idx_tracking (tracking_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS cart (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    variant_id INT,
    quantity INT DEFAULT 1,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (variant_id) REFERENCES product_variants(id) ON DELETE CASCADE,
    UNIQUE KEY unique_cart_item (user_id, product_id, variant_id),
    INDEX idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    user_id INT NOT NULL,
    order_id INT,
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    title VARCHAR(200),
    comment TEXT,
    is_verified_purchase BOOLEAN DEFAULT FALSE,
    is_approved BOOLEAN DEFAULT TRUE,
    helpful_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL,
    INDEX idx_product (product_id),
    INDEX idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    transaction_id VARCHAR(100) UNIQUE,
    payment_gateway VARCHAR(50),
    payment_method VARCHAR(50),
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'PHP',
    status ENUM('pending', 'completed', 'failed', 'refunded') DEFAULT 'pending',
    gateway_response TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    INDEX idx_order (order_id),
    INDEX idx_transaction (transaction_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS activity_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id INT,
    description TEXT,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user (user_id),
    INDEX idx_created (created_at),
    INDEX idx_action (action)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS coupons (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    discount_type ENUM('percentage', 'fixed') NOT NULL,
    discount_value DECIMAL(10,2) NOT NULL,
    min_purchase DECIMAL(10,2) DEFAULT 0.00,
    max_discount DECIMAL(10,2),
    usage_limit INT,
    used_count INT DEFAULT 0,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_code (code),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO users (first_name, last_name, email, password, role, status) 
VALUES ('Admin', 'User', 'admin@varon.com', 'admin123', 'admin', 'active')
ON DUPLICATE KEY UPDATE first_name=first_name;

INSERT INTO categories (name, slug, description, parent_id, is_active) VALUES
('Tops', 'tops', 'All types of tops for men', NULL, TRUE),
('T-Shirts', 't-shirts', 'Casual and formal t-shirts', 1, TRUE),
('Polo Shirts', 'polo-shirts', 'Classic polo shirts', 1, TRUE),
('Dress Shirts', 'dress-shirts', 'Formal dress shirts', 1, TRUE),
('Bottoms', 'bottoms', 'Pants, shorts and more', NULL, TRUE),
('Jeans', 'jeans', 'Denim jeans', 5, TRUE),
('Chinos', 'chinos', 'Chino pants', 5, TRUE),
('Shorts', 'shorts', 'Casual shorts', 5, TRUE),
('Outerwear', 'outerwear', 'Jackets and coats', NULL, TRUE),
('Jackets', 'jackets', 'All types of jackets', 9, TRUE),
('Hoodies', 'hoodies', 'Hooded sweatshirts', 9, TRUE),
('Footwear', 'footwear', 'Shoes and sandals', NULL, TRUE),
('Sneakers', 'sneakers', 'Casual sneakers', 12, TRUE),
('Formal Shoes', 'formal-shoes', 'Dress shoes', 12, TRUE),
('Accessories', 'accessories', 'Belts, watches, bags', NULL, TRUE),
('Belts', 'belts', 'Leather and fabric belts', 15, TRUE),
('Watches', 'watches', 'Wrist watches', 15, TRUE),
('Bags', 'bags', 'Backpacks and messenger bags', 15, TRUE)
ON DUPLICATE KEY UPDATE name=name;

INSERT INTO users (first_name, last_name, email, password, role, phone, status) VALUES
('Maria', 'Santos', 'maria.santos@email.com', 'password123', 'buyer', '+63-912-345-6789', 'active'),
('Juan', 'Reyes', 'juan.reyes@email.com', 'password123', 'buyer', '+63-923-456-7890', 'active'),
('Ana', 'Cruz', 'ana.cruz@email.com', 'password123', 'buyer', '+63-934-567-8901', 'active')
ON DUPLICATE KEY UPDATE first_name=first_name;

SELECT 'Database schema created successfully! 🔥' AS Message;
