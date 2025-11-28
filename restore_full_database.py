
"""
Restore full database schema from original database.sql structure
"""
import pymysql

print("Connecting to database...")
conn = pymysql.connect(host='localhost', user='root', password='', database='varon')
cursor = conn.cursor()

print("Recreating all tables as MyISAM...\n")


tables_to_drop = [
    'activity_logs', 'addresses', 'admin_settings', 'cart', 'categories', 'inventory'
    'journal_entries', 'order_items', 'orders', 'otp_verifications', 'product_archive_requests'
    'product_edits', 'product_images', 'product_variants', 'products', 'promotions'
    'reviews', 'rider_transactions', 'riders', 'sellers', 'shipments', 'transactions', 'users'
]

for table in tables_to_drop:
    try:
        cursor.execute(f"DROP TABLE IF EXISTS `{table}`")
    except:
        pass

print("Creating tables...\n")


cursor.execute("""
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY
    first_name VARCHAR(100) NOT NULL
    last_name VARCHAR(100) NOT NULL
    email VARCHAR(190) NOT NULL UNIQUE
    password VARCHAR(255) NOT NULL
    role ENUM('buyer', 'seller', 'admin', 'rider') NOT NULL DEFAULT 'buyer'
    phone VARCHAR(20)
    status ENUM('active', 'inactive', 'pending', 'suspended') DEFAULT 'active'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    INDEX idx_email (email)
    INDEX idx_role (role)
    INDEX idx_status (status)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4
""")
print("✅ users")


cursor.execute("""
CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY
    name VARCHAR(100) NOT NULL
    slug VARCHAR(100) NOT NULL UNIQUE
    description TEXT
    parent_id INT NULL
    image_url VARCHAR(500)
    is_active BOOLEAN DEFAULT TRUE
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    INDEX idx_slug (slug)
    INDEX idx_parent (parent_id)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4
""")
print("✅ categories")


cursor.execute("""
CREATE TABLE sellers (
    id INT AUTO_INCREMENT PRIMARY KEY
    user_id INT NOT NULL UNIQUE
    store_name VARCHAR(150) NOT NULL
    store_slug VARCHAR(150) NOT NULL UNIQUE
    description TEXT
    logo_url VARCHAR(500)
    address TEXT
    city VARCHAR(100)
    province VARCHAR(100)
    postal_code VARCHAR(20)
    business_license VARCHAR(100)
    tax_id VARCHAR(100)
    bank_account VARCHAR(100)
    rating DECIMAL(3,2) DEFAULT 0.00
    total_sales DECIMAL(15,2) DEFAULT 0.00
    commission_rate DECIMAL(5,2) DEFAULT 10.00
    status ENUM('pending', 'approved', 'rejected', 'suspended') DEFAULT 'pending'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    INDEX idx_user (user_id)
    INDEX idx_status (status)
    INDEX idx_slug (store_slug)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4
""")
print("✅ sellers")


cursor.execute("""
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY
    seller_id INT NOT NULL
    category_id INT NOT NULL
    name VARCHAR(200) NOT NULL
    slug VARCHAR(200) NOT NULL
    description TEXT
    brand VARCHAR(100)
    gender ENUM('men', 'women', 'unisex') DEFAULT 'men'
    price DECIMAL(10,2) NOT NULL
    sale_price DECIMAL(10,2)
    cost_price DECIMAL(10,2)
    sku VARCHAR(100) UNIQUE
    weight DECIMAL(8,2)
    dimensions VARCHAR(100)
    material VARCHAR(200)
    care_instructions TEXT
    is_featured BOOLEAN DEFAULT FALSE
    is_active BOOLEAN DEFAULT TRUE
    views_count INT DEFAULT 0
    sales_count INT DEFAULT 0
    rating DECIMAL(3,2) DEFAULT 0.00
    review_count INT DEFAULT 0
    edit_status ENUM('none', 'pending', 'approved', 'rejected') DEFAULT 'none'
    archive_status ENUM('active', 'archived', 'pending_recovery') DEFAULT 'active'
    archived_at TIMESTAMP NULL
    archived_by INT NULL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    INDEX idx_seller (seller_id)
    INDEX idx_category (category_id)
    INDEX idx_active (is_active)
    INDEX idx_featured (is_featured)
    INDEX idx_slug (slug)
    INDEX idx_edit_status (edit_status)
    INDEX idx_archive_status (archive_status)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4
""")
print("✅ products")


cursor.execute("""
CREATE TABLE product_images (
    id INT AUTO_INCREMENT PRIMARY KEY
    product_id INT NOT NULL
    image_url VARCHAR(500) NOT NULL
    is_primary BOOLEAN DEFAULT FALSE
    sort_order INT DEFAULT 0
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    INDEX idx_product (product_id)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4
""")
print("✅ product_images")


cursor.execute("""
CREATE TABLE product_variants (
    id INT AUTO_INCREMENT PRIMARY KEY
    product_id INT NOT NULL
    sku VARCHAR(100) UNIQUE
    size VARCHAR(20)
    color VARCHAR(50)
    stock_quantity INT DEFAULT 0
    price_adjustment DECIMAL(10,2) DEFAULT 0.00
    weight_adjustment DECIMAL(8,2) DEFAULT 0.00
    is_active BOOLEAN DEFAULT TRUE
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    INDEX idx_product (product_id)
    INDEX idx_sku (sku)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4
""")
print("✅ product_variants")


cursor.execute("""
CREATE TABLE inventory (
    id INT AUTO_INCREMENT PRIMARY KEY
    product_id INT NOT NULL
    variant_id INT
    stock_quantity INT DEFAULT 0
    reserved_quantity INT DEFAULT 0
    low_stock_threshold INT DEFAULT 10
    reorder_point INT DEFAULT 5
    last_restocked_at TIMESTAMP NULL
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    INDEX idx_product (product_id)
    INDEX idx_variant (variant_id)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4
""")
print("✅ inventory")


cursor.execute("""
CREATE TABLE product_edits (
    id INT AUTO_INCREMENT PRIMARY KEY
    product_id INT NOT NULL
    seller_id INT NOT NULL
    field_name VARCHAR(100) NOT NULL
    old_value TEXT
    new_value TEXT
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending'
    admin_notes TEXT
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    reviewed_at TIMESTAMP NULL
    reviewed_by INT NULL
    INDEX idx_product (product_id)
    INDEX idx_status (status)
    INDEX idx_seller (seller_id)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4
""")
print("✅ product_edits")


cursor.execute("""
CREATE TABLE product_archive_requests (
    id INT AUTO_INCREMENT PRIMARY KEY
    product_id INT NOT NULL
    seller_id INT NOT NULL
    request_type ENUM('archive', 'recover') NOT NULL
    reason TEXT
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending'
    admin_notes TEXT
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    reviewed_at TIMESTAMP NULL
    reviewed_by INT NULL
    INDEX idx_product (product_id)
    INDEX idx_status (status)
    INDEX idx_seller (seller_id)
    INDEX idx_type (request_type)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4
""")
print("✅ product_archive_requests")


cursor.execute("""
CREATE TABLE addresses (
    id INT AUTO_INCREMENT PRIMARY KEY
    user_id INT NOT NULL
    address_type ENUM('billing', 'shipping', 'both') DEFAULT 'shipping'
    full_name VARCHAR(150) NOT NULL
    phone VARCHAR(20) NOT NULL
    street_address TEXT NOT NULL
    barangay VARCHAR(100)
    city VARCHAR(100) NOT NULL
    province VARCHAR(100) NOT NULL
    postal_code VARCHAR(20)
    country VARCHAR(50) DEFAULT 'Philippines'
    is_default BOOLEAN DEFAULT FALSE
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    INDEX idx_user (user_id)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4
""")
print("✅ addresses")


cursor.execute("""
CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY
    order_number VARCHAR(50) UNIQUE NOT NULL
    user_id INT NOT NULL
    seller_id INT NOT NULL
    shipping_address_id INT NOT NULL
    billing_address_id INT
    subtotal DECIMAL(10,2) NOT NULL
    shipping_fee DECIMAL(10,2) DEFAULT 0.00
    tax_amount DECIMAL(10,2) DEFAULT 0.00
    discount_amount DECIMAL(10,2) DEFAULT 0.00
    total_amount DECIMAL(10,2) NOT NULL
    payment_method VARCHAR(50)
    payment_status ENUM('pending', 'paid', 'failed', 'refunded') DEFAULT 'pending'
    order_status ENUM('pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'returned') DEFAULT 'pending'
    notes TEXT
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    INDEX idx_user (user_id)
    INDEX idx_seller (seller_id)
    INDEX idx_status (order_status)
    INDEX idx_order_number (order_number)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4
""")
print("✅ orders")


cursor.execute("""
CREATE TABLE order_items (
    id INT AUTO_INCREMENT PRIMARY KEY
    order_id INT NOT NULL
    product_id INT NOT NULL
    variant_id INT
    product_name VARCHAR(200) NOT NULL
    sku VARCHAR(100)
    size VARCHAR(20)
    color VARCHAR(50)
    quantity INT NOT NULL
    unit_price DECIMAL(10,2) NOT NULL
    subtotal DECIMAL(10,2) NOT NULL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    INDEX idx_order (order_id)
    INDEX idx_product (product_id)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4
""")
print("✅ order_items")


cursor.execute("""
CREATE TABLE riders (
    id INT AUTO_INCREMENT PRIMARY KEY
    user_id INT NOT NULL UNIQUE
    vehicle_type ENUM('motorcycle', 'bicycle', 'car', 'van', 'truck') NOT NULL
    license_number VARCHAR(50)
    vehicle_plate VARCHAR(20)
    service_area TEXT
    profile_image VARCHAR(500)
    max_delivery_distance INT DEFAULT 50
    current_location_lat DECIMAL(10,8)
    current_location_lng DECIMAL(11,8)
    is_available BOOLEAN DEFAULT TRUE
    rating DECIMAL(3,2) DEFAULT 0.00
    total_deliveries INT DEFAULT 0
    earnings DECIMAL(10,2) DEFAULT 0.00
    status ENUM('pending', 'approved', 'active', 'inactive', 'suspended') DEFAULT 'pending'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    INDEX idx_user (user_id)
    INDEX idx_status (status)
    INDEX idx_available (is_available)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4
""")
print("✅ riders")


cursor.execute("""
CREATE TABLE shipments (
    id INT AUTO_INCREMENT PRIMARY KEY
    order_id INT NOT NULL UNIQUE
    rider_id INT
    tracking_number VARCHAR(100) UNIQUE
    carrier VARCHAR(100)
    shipped_at TIMESTAMP NULL
    estimated_delivery TIMESTAMP NULL
    delivered_at TIMESTAMP NULL
    delivery_proof_url VARCHAR(500)
    delivery_notes TEXT
    status ENUM('pending', 'picked_up', 'in_transit', 'out_for_delivery', 'delivered', 'failed', 'returned') DEFAULT 'pending'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    INDEX idx_order (order_id)
    INDEX idx_rider (rider_id)
    INDEX idx_tracking (tracking_number)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4
""")
print("✅ shipments")


cursor.execute("""
CREATE TABLE cart (
    id INT AUTO_INCREMENT PRIMARY KEY
    user_id INT NOT NULL
    product_id INT NOT NULL
    variant_id INT
    quantity INT DEFAULT 1
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    INDEX idx_user (user_id)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4
""")
print("✅ cart")


cursor.execute("""
CREATE TABLE reviews (
    id INT AUTO_INCREMENT PRIMARY KEY
    product_id INT NOT NULL
    user_id INT NOT NULL
    order_id INT
    rating INT NOT NULL
    title VARCHAR(200)
    comment TEXT
    is_verified_purchase BOOLEAN DEFAULT FALSE
    is_approved BOOLEAN DEFAULT TRUE
    helpful_count INT DEFAULT 0
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    INDEX idx_product (product_id)
    INDEX idx_user (user_id)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4
""")
print("✅ reviews")


cursor.execute("""
CREATE TABLE transactions (
    id INT AUTO_INCREMENT PRIMARY KEY
    order_id INT NOT NULL
    transaction_id VARCHAR(100) UNIQUE
    payment_gateway VARCHAR(50)
    payment_method VARCHAR(50)
    amount DECIMAL(10,2) NOT NULL
    currency VARCHAR(10) DEFAULT 'PHP'
    status ENUM('pending', 'completed', 'failed', 'refunded') DEFAULT 'pending'
    gateway_response TEXT
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    INDEX idx_order (order_id)
    INDEX idx_transaction (transaction_id)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4
""")
print("✅ transactions")


cursor.execute("""
CREATE TABLE rider_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY
    rider_id INT NOT NULL
    order_id INT NOT NULL
    shipment_id INT NOT NULL
    earning_amount DECIMAL(10,2) NOT NULL
    commission_rate DECIMAL(5,2) DEFAULT 15.00
    status ENUM('pending', 'completed', 'cancelled') DEFAULT 'pending'
    completed_at TIMESTAMP NULL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    INDEX idx_rider (rider_id)
    INDEX idx_order (order_id)
    INDEX idx_status (status)
    INDEX idx_created (created_at)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4
""")
print("✅ rider_transactions")


cursor.execute("""
CREATE TABLE activity_logs (
    id INT AUTO_INCREMENT PRIMARY KEY
    user_id INT
    action VARCHAR(100) NOT NULL
    entity_type VARCHAR(50)
    entity_id INT
    description TEXT
    ip_address VARCHAR(45)
    user_agent VARCHAR(500)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    INDEX idx_user (user_id)
    INDEX idx_created (created_at)
    INDEX idx_action (action)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4
""")
print("✅ activity_logs")


cursor.execute("""
CREATE TABLE otp_verifications (
    id INT AUTO_INCREMENT PRIMARY KEY
    email VARCHAR(190)
    phone VARCHAR(20)
    otp_code VARCHAR(10) NOT NULL
    otp_type ENUM('email', 'sms') NOT NULL DEFAULT 'email'
    purpose ENUM('registration', 'login', 'password_reset', 'verification', 'email_change', 'phone_verification') NOT NULL DEFAULT 'registration'
    expires_at TIMESTAMP NOT NULL
    used_at TIMESTAMP NULL
    is_verified BOOLEAN DEFAULT FALSE
    attempts INT DEFAULT 0
    ip_address VARCHAR(45)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    INDEX idx_email (email)
    INDEX idx_phone (phone)
    INDEX idx_code (otp_code)
    INDEX idx_expires (expires_at)
    INDEX idx_purpose (purpose)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4
""")
print("✅ otp_verifications")


cursor.execute("""
CREATE TABLE journal_entries (
    id INT AUTO_INCREMENT PRIMARY KEY
    title VARCHAR(200) NOT NULL
    description TEXT
    image_url VARCHAR(500)
    is_active BOOLEAN DEFAULT TRUE
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    created_by INT
    INDEX idx_active (is_active)
    INDEX idx_created (created_at)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4
""")
print("✅ journal_entries")


cursor.execute("""
CREATE TABLE promotions (
    id INT AUTO_INCREMENT PRIMARY KEY
    code VARCHAR(50) NOT NULL UNIQUE
    product_id INT
    discount_type ENUM('percentage', 'fixed') NOT NULL DEFAULT 'percentage'
    discount_value DECIMAL(10,2) NOT NULL
    start_date DATE NOT NULL
    end_date DATE NOT NULL
    description TEXT
    is_active BOOLEAN DEFAULT TRUE
    is_approved BOOLEAN DEFAULT FALSE
    min_purchase DECIMAL(10,2) DEFAULT 0
    usage_limit INT DEFAULT 999999
    usage_count INT DEFAULT 0
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    INDEX idx_code (code)
    INDEX idx_active (is_active)
    INDEX idx_approved (is_approved)
    INDEX idx_dates (start_date, end_date)
    INDEX idx_product (product_id)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4
""")
print("✅ promotions")


cursor.execute("""
CREATE TABLE admin_settings (
    id INT AUTO_INCREMENT PRIMARY KEY
    system_name VARCHAR(200) DEFAULT 'Var-n E-Commerce'
    support_email VARCHAR(190) DEFAULT 'support@varon.com'
    support_phone VARCHAR(20) DEFAULT '+63 977 XXX XXXX'
    maintenance_mode BOOLEAN DEFAULT FALSE
    email_notifications BOOLEAN DEFAULT TRUE
    order_alerts BOOLEAN DEFAULT TRUE
    seller_alerts BOOLEAN DEFAULT TRUE
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4
""")
print("✅ admin_settings")

conn.commit()
cursor.close()
conn.close()

print("\n" + "="*60)
print("✅ DATABASE FULLY RESTORED!")
print("="*60)
print("All 23 tables have been recreated as MyISAM.")
print("Database is ready for use!")
