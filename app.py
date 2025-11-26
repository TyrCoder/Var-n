from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, jsonify
import os
import mysql.connector
import time
from dotenv import load_dotenv
from decimal import Decimal
from utils.otp_service import OTPService
import json

# Load environment variables
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder='templates', static_folder='static', static_url_path='/static')
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production-please')

# Custom JSON encoder to handle Decimal types
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

app.json_encoder = DecimalEncoder

# Database configuration from environment
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'varon')
}

def get_db():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Exception as err:
        print(f"[DB ERROR] {err}")
        return None

def convert_decimals_to_float(obj):
    """Recursively convert Decimal objects to float in dicts and lists"""
    if isinstance(obj, dict):
        return {k: convert_decimals_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_decimals_to_float(item) for item in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj

def get_delivery_region(city, province):
    """
    Map Philippine city/province to delivery region for rider matching.
    Returns one of: 'North Luzon', 'Central Luzon', 'South Luzon', 'Visayas', 'Mindanao', 'Unknown'
    """
    # Normalize input
    city = str(city).lower().strip() if city else ''
    province = str(province).lower().strip() if province else ''
    
    # North Luzon: Nueva Ecija, Bulacan, Nueva Vizcaya, Quirino, Tarlac, Pangasinan, La Union, Isabela, Ifugao, Kalinga, Mountain Province, Benguet
    north_luzon = {
        'nueva ecija', 'bulacan', 'nueva vizcaya', 'quirino', 'tarlac', 'pangasinan', 
        'la union', 'isabela', 'ifugao', 'kalinga', 'mountain province', 'benguet'
    }
    
    # Central Luzon: Pampanga, Batangas, Cavite, Laguna, Quezon, Marinduque, Palawan
    central_luzon = {
        'pampanga', 'batangas', 'cavite', 'laguna', 'quezon', 'marinduque', 'palawan',
        'quezon city', 'metro manila', 'manila', 'pasig', 'makati', 'taguig', 'caloocan',
        'manila city', 'ncr'  # National Capital Region (Metro Manila)
    }
    
    # South Luzon: Camarines Norte, Camarines Sur, Albay, Sorsogon, Masbate
    south_luzon = {
        'camarines norte', 'camarines sur', 'albay', 'sorsogon', 'masbate'
    }
    
    # Visayas: Cebu, Iloilo, Bohol, Negros Occidental, Negros Oriental, Aklan, Capiz, Antique, Guimaras
    visayas = {
        'cebu', 'iloilo', 'bohol', 'negros occidental', 'negros oriental', 'aklan',
        'capiz', 'antique', 'guimaras', 'siquijor'
    }
    
    # Mindanao: Davao, Cagayan de Oro, Zamboanga, Butuan, Cotabato, Surigao, Lanao, Misamis, Maguindanao, Sarangani, South Cotabato
    mindanao = {
        'davao', 'cagayan de oro', 'zamboanga', 'butuan', 'cotabato', 'surigao', 'lanao',
        'misamis', 'maguindanao', 'sarangani', 'south cotabato', 'davao del norte',
        'davao del sur', 'davao occidental', 'davao oriental', 'misamis oriental',
        'misamis occidental', 'lanao del norte', 'lanao del sur', 'basilan'
    }
    
    # Check province first (more reliable)
    if province in north_luzon:
        return 'North Luzon'
    elif province in central_luzon:
        return 'Central Luzon'
    elif province in south_luzon:
        return 'South Luzon'
    elif province in visayas:
        return 'Visayas'
    elif province in mindanao:
        return 'Mindanao'
    
    # Fallback: check city/municipality names that can help identify region
    # Metro Manila cities belong to Central Luzon region
    metro_manila_cities = {
        'quezon city', 'manila', 'pasig', 'makati', 'taguig', 'caloocan', 'parañaque',
        'las piñas', 'cavite city', 'mandaluyong', 'marikina', 'san juan', 'muntinlupa'
    }
    
    if city in metro_manila_cities:
        return 'Central Luzon'
    
    return 'Unknown'

def init_db():
    try:
        conn = mysql.connector.connect(host=DB_CONFIG['host'], user=DB_CONFIG['user'], password=DB_CONFIG['password'])
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        conn.database = DB_CONFIG['database']
        
        # Users table (customers, sellers, admins, riders)
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            email VARCHAR(190) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            phone VARCHAR(20) NOT NULL,
            role ENUM('buyer', 'seller', 'admin', 'rider') NOT NULL DEFAULT 'buyer',
            status ENUM('active', 'inactive', 'pending', 'suspended') DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        
        # Categories table for men's apparel
        cursor.execute('''CREATE TABLE IF NOT EXISTS categories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            slug VARCHAR(100) NOT NULL UNIQUE,
            description TEXT,
            parent_id INT NULL,
            image_url VARCHAR(500),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        
        # Sellers profile table
        cursor.execute('''CREATE TABLE IF NOT EXISTS sellers (
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
            island_group ENUM('Luzon', 'Visayas', 'Mindanao') DEFAULT 'Luzon',
            status ENUM('pending', 'approved', 'rejected', 'suspended') DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        
        # Products table for men's apparel
        cursor.execute('''CREATE TABLE IF NOT EXISTS products (
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
            sku VARCHAR(100),
            weight DECIMAL(8,2),
            dimensions VARCHAR(100),
            material VARCHAR(200),
            care_instructions TEXT,
            is_featured BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            archive_status VARCHAR(50) DEFAULT 'active',
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
            INDEX idx_active (is_active)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        
        # Product images table
        cursor.execute('''CREATE TABLE IF NOT EXISTS product_images (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id INT NOT NULL,
            image_url VARCHAR(500) NOT NULL,
            is_primary BOOLEAN DEFAULT FALSE,
            sort_order INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        
        # Product variants (size, color combinations)
        cursor.execute('''CREATE TABLE IF NOT EXISTS product_variants (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id INT NOT NULL,
            sku VARCHAR(100),
            size VARCHAR(20),
            color VARCHAR(50),
            stock_quantity INT DEFAULT 0,
            price_adjustment DECIMAL(10,2) DEFAULT 0.00,
            weight_adjustment DECIMAL(8,2) DEFAULT 0.00,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
            INDEX idx_product (product_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        
        # Inventory/Stock tracking
        cursor.execute('''CREATE TABLE IF NOT EXISTS inventory (
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
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        
        # Customer addresses
        cursor.execute('''CREATE TABLE IF NOT EXISTS addresses (
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
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        
        # Orders table
        cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            order_number VARCHAR(50) UNIQUE NOT NULL,
            user_id INT NOT NULL,
            seller_id INT NOT NULL,
            rider_id INT NULL,
            shipping_address_id INT NOT NULL,
            billing_address_id INT,
            seller_confirmed_rider BOOLEAN DEFAULT FALSE,
            buyer_approved_rider BOOLEAN DEFAULT FALSE,
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
            FOREIGN KEY (rider_id) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY (shipping_address_id) REFERENCES addresses(id) ON DELETE RESTRICT,
            FOREIGN KEY (billing_address_id) REFERENCES addresses(id) ON DELETE RESTRICT,
            INDEX idx_user (user_id),
            INDEX idx_seller (seller_id),
            INDEX idx_rider (rider_id),
            INDEX idx_status (order_status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        
        # Order items table
        cursor.execute('''CREATE TABLE IF NOT EXISTS order_items (
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
            FOREIGN KEY (variant_id) REFERENCES product_variants(id) ON DELETE RESTRICT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        
        # Riders table
        cursor.execute('''CREATE TABLE IF NOT EXISTS riders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL UNIQUE,
            vehicle_type ENUM('motorcycle', 'bicycle', 'car', 'van', 'truck') NOT NULL,
            license_number VARCHAR(50),
            vehicle_plate VARCHAR(20),
            service_area TEXT,
            sub_region ENUM('North Luzon', 'Central Luzon', 'South Luzon', 'Visayas', 'Mindanao', 'All areas') DEFAULT 'All areas',
            max_delivery_distance INT DEFAULT 50,
            current_location_lat DECIMAL(10,8),
            current_location_lng DECIMAL(11,8),
            is_available BOOLEAN DEFAULT TRUE,
            rating DECIMAL(3,2) DEFAULT 0.00,
            total_deliveries INT DEFAULT 0,
            earnings DECIMAL(10,2) DEFAULT 0.00,
            status ENUM('pending', 'approved', 'active', 'inactive', 'suspended') DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        
        # Shipments/Deliveries table
        cursor.execute('''CREATE TABLE IF NOT EXISTS shipments (
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
            seller_confirmed BOOLEAN DEFAULT FALSE,
            seller_confirmed_at TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
            FOREIGN KEY (rider_id) REFERENCES riders(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        
        # Add seller_confirmed column if it doesn't exist (for existing databases)
        try:
            cursor.execute('ALTER TABLE shipments ADD COLUMN seller_confirmed BOOLEAN DEFAULT FALSE')
            print("[INFO] Added seller_confirmed column to shipments table")
        except Exception as e:
            if 'Duplicate column name' in str(e) or '1060' in str(e):
                pass  # Column already exists
            else:
                print(f"[WARNING] Could not add seller_confirmed column: {e}")
        
        # Add seller_confirmed_at column if it doesn't exist
        try:
            cursor.execute('ALTER TABLE shipments ADD COLUMN seller_confirmed_at TIMESTAMP NULL')
            print("[INFO] Added seller_confirmed_at column to shipments table")
        except Exception as e:
            if 'Duplicate column name' in str(e) or '1060' in str(e):
                pass  # Column already exists
            else:
                print(f"[WARNING] Could not add seller_confirmed_at column: {e}")
        
        # Add sub_region column to riders table if it doesn't exist
        try:
            cursor.execute('''ALTER TABLE riders ADD COLUMN sub_region ENUM('North Luzon', 'Central Luzon', 'South Luzon', 'Visayas', 'Mindanao', 'All areas') DEFAULT 'All areas' ''')
            print("[INFO] Added sub_region column to riders table")
        except Exception as e:
            if 'Duplicate column name' in str(e) or '1060' in str(e):
                pass  # Column already exists
            else:
                print(f"[WARNING] Could not add sub_region column to riders table: {e}")
        
        # Shopping cart
        cursor.execute('''CREATE TABLE IF NOT EXISTS cart (
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
            UNIQUE KEY unique_cart_item (user_id, product_id, variant_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        
        # Reviews table
        cursor.execute('''CREATE TABLE IF NOT EXISTS reviews (
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
            INDEX idx_product (product_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        
        # Transactions/Payments table
        cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
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
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        
        # Rider Transactions table - Individual transaction record per rider per order
        cursor.execute('''CREATE TABLE IF NOT EXISTS rider_transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            rider_id INT NOT NULL,
            order_id INT NOT NULL,
            shipment_id INT NOT NULL,
            earning_amount DECIMAL(10,2) NOT NULL,
            commission_rate DECIMAL(5,2) DEFAULT 15.00,
            status ENUM('pending', 'completed', 'cancelled') DEFAULT 'pending',
            completed_at TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (rider_id) REFERENCES riders(id) ON DELETE CASCADE,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
            FOREIGN KEY (shipment_id) REFERENCES shipments(id) ON DELETE CASCADE,
            INDEX idx_rider (rider_id),
            INDEX idx_order (order_id),
            INDEX idx_status (status),
            INDEX idx_created (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        
        # Activity log
        cursor.execute('''CREATE TABLE IF NOT EXISTS activity_logs (
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
            INDEX idx_created (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        
        # Add island_group field to sellers table if it doesn't exist
        try:
            cursor.execute("SHOW COLUMNS FROM sellers LIKE 'island_group'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE sellers ADD COLUMN island_group ENUM('Luzon', 'Visayas', 'Mindanao') DEFAULT 'Luzon' AFTER commission_rate")
                print("[DB INIT] Added 'island_group' column to sellers table")
        except Exception as e:
            print(f"[DB INIT] Error checking/adding island_group column: {e}")
        
        # Coupons/Discounts
        
        # OTP Verifications table
        cursor.execute('''CREATE TABLE IF NOT EXISTS otp_verifications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(190),
            phone VARCHAR(20),
            otp_code VARCHAR(10) NOT NULL,
            otp_type ENUM('email', 'sms') NOT NULL DEFAULT 'email',
            purpose ENUM('registration', 'login', 'password_reset', 'verification', 'email_change', 'phone_verification') NOT NULL DEFAULT 'registration',
            expires_at TIMESTAMP NOT NULL,
            used_at TIMESTAMP NULL,
            is_verified BOOLEAN DEFAULT FALSE,
            attempts INT DEFAULT 0,
            ip_address VARCHAR(45),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_email (email),
            INDEX idx_phone (phone),
            INDEX idx_code (otp_code),
            INDEX idx_expires (expires_at),
            INDEX idx_purpose (purpose)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        
        # Update purpose enum if needed (add new purposes)
        try:
            cursor.execute("ALTER TABLE otp_verifications MODIFY COLUMN purpose ENUM('registration', 'login', 'password_reset', 'verification', 'email_change', 'phone_verification') NOT NULL DEFAULT 'registration'")
            print("[DB INIT] Updated purpose enum to include email_change and phone_verification")
        except Exception as e:
            # Enum might already be updated or table doesn't exist yet
            print(f"[DB INIT] Purpose enum check: {str(e)}")
        
        # Check and add missing columns if table exists but is missing columns
        try:
            cursor.execute("SHOW COLUMNS FROM otp_verifications LIKE 'phone'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE otp_verifications ADD COLUMN phone VARCHAR(20) AFTER email")
                print("[DB INIT] Added missing 'phone' column to otp_verifications table")
        except Exception as e:
            print(f"[DB INIT] Error checking/adding phone column: {e}")
        
        try:
            cursor.execute("SHOW COLUMNS FROM otp_verifications LIKE 'used_at'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE otp_verifications ADD COLUMN used_at TIMESTAMP NULL AFTER expires_at")
                print("[DB INIT] Added missing 'used_at' column to otp_verifications table")
        except Exception as e:
            print(f"[DB INIT] Error checking/adding used_at column: {e}")
        
        try:
            cursor.execute("SHOW COLUMNS FROM otp_verifications LIKE 'is_verified'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE otp_verifications ADD COLUMN is_verified BOOLEAN DEFAULT FALSE AFTER used_at")
                print("[DB INIT] Added missing 'is_verified' column to otp_verifications table")
        except Exception as e:
            print(f"[DB INIT] Error checking/adding is_verified column: {e}")
        
        # Add indexes if they don't exist
        try:
            cursor.execute("SHOW INDEX FROM otp_verifications WHERE Key_name = 'idx_phone'")
            if not cursor.fetchone():
                cursor.execute("CREATE INDEX idx_phone ON otp_verifications(phone)")
                print("[DB INIT] Added missing 'idx_phone' index")
        except Exception as e:
            print(f"[DB INIT] Error checking/adding idx_phone index: {e}")
        
        # Journal entries table
        cursor.execute('''CREATE TABLE IF NOT EXISTS journal_entries (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            image_url VARCHAR(500),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            created_by INT,
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
            INDEX idx_active (is_active),
            INDEX idx_created (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        
        # Promotions table
        cursor.execute('''CREATE TABLE IF NOT EXISTS promotions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            code VARCHAR(50) NOT NULL UNIQUE,
            product_id INT,
            discount_type ENUM('percentage', 'fixed') NOT NULL DEFAULT 'percentage',
            discount_value DECIMAL(10, 2) NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            description TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            is_approved BOOLEAN DEFAULT FALSE,
            min_purchase DECIMAL(10, 2) DEFAULT 0,
            usage_limit INT DEFAULT 999999,
            usage_count INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL,
            INDEX idx_code (code),
            INDEX idx_active (is_active),
            INDEX idx_approved (is_approved),
            INDEX idx_dates (start_date, end_date),
            INDEX idx_product (product_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        
        # Admin settings table
        cursor.execute('''CREATE TABLE IF NOT EXISTS admin_settings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            system_name VARCHAR(200) DEFAULT 'Var-n E-Commerce',
            support_email VARCHAR(190) DEFAULT 'support@varn.com',
            support_phone VARCHAR(20) DEFAULT '+63 977 XXX XXXX',
            maintenance_mode BOOLEAN DEFAULT FALSE,
            email_notifications BOOLEAN DEFAULT TRUE,
            order_alerts BOOLEAN DEFAULT TRUE,
            seller_alerts BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        
        # Migration: Rename coupons table to promotions if it exists
        try:
            cursor.execute("SHOW TABLES LIKE 'coupons'")
            if cursor.fetchone():
                try:
                    cursor.execute('ALTER TABLE coupons RENAME TO promotions')
                    print("[DB MIGRATION] Successfully renamed coupons table to promotions")
                except Exception as e:
                    if 'already exists' in str(e) or 'Duplicate' in str(e):
                        print("[DB MIGRATION] promotions table already exists, dropping old coupons table")
                        try:
                            cursor.execute('DROP TABLE IF EXISTS coupons')
                            print("[DB MIGRATION] Dropped old coupons table")
                        except Exception as drop_err:
                            print(f"[DB MIGRATION] Could not drop coupons table: {drop_err}")
                    else:
                        print(f"[DB MIGRATION] Table rename failed: {e}")
        except Exception as e:
            print(f"[DB MIGRATION] Error during rename: {e}")
        
        # Migration: Add is_approved column to promotions table if it doesn't exist
        try:
            cursor.execute("SHOW COLUMNS FROM promotions LIKE 'is_approved'")
            if not cursor.fetchone():
                cursor.execute('ALTER TABLE promotions ADD COLUMN is_approved BOOLEAN DEFAULT FALSE AFTER is_active')
                print("[DB MIGRATION] Added is_approved column to promotions table")
        except Exception as e:
            if 'Duplicate' not in str(e) and 'already exists' not in str(e):
                print(f"[DB MIGRATION] Could not add is_approved column: {e}")
        
        # Migration: Add index on is_approved if it doesn't exist
        try:
            cursor.execute("SHOW INDEX FROM promotions WHERE Key_name = 'idx_approved'")
            if not cursor.fetchone():
                cursor.execute('CREATE INDEX idx_approved ON promotions(is_approved)')
                print("[DB MIGRATION] Added idx_approved index to promotions table")
        except Exception as e:
            print(f"[DB MIGRATION] Index creation failed: {e}")
        
        conn.commit()
        print("[DB] All tables created successfully!")
        cursor.close()
        conn.close()
    except Exception as err:
        print(f"[DB INIT ERROR] {err}")

init_db()

@app.route('/admin/create-tables', methods=['POST'])
def admin_create_tables():
    """Manually create missing tables and fix existing ones (for admin use)"""
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor()
        messages = []
        
        # Create OTP Verifications table
        cursor.execute('''CREATE TABLE IF NOT EXISTS otp_verifications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(190),
            phone VARCHAR(20),
            otp_code VARCHAR(10) NOT NULL,
            otp_type ENUM('email', 'sms') NOT NULL DEFAULT 'email',
            purpose ENUM('registration', 'login', 'password_reset', 'verification', 'email_change', 'phone_verification') NOT NULL DEFAULT 'registration',
            expires_at TIMESTAMP NOT NULL,
            used_at TIMESTAMP NULL,
            attempts INT DEFAULT 0,
            ip_address VARCHAR(45),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_email (email),
            INDEX idx_phone (phone),
            INDEX idx_code (otp_code),
            INDEX idx_expires (expires_at),
            INDEX idx_purpose (purpose)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        messages.append("OTP verifications table created/verified")
        
        # Check and add missing columns
        try:
            cursor.execute("SHOW COLUMNS FROM otp_verifications LIKE 'phone'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE otp_verifications ADD COLUMN phone VARCHAR(20) AFTER email")
                messages.append("Added missing 'phone' column")
        except Exception as e:
            messages.append(f"Phone column check: {str(e)}")
        
        try:
            cursor.execute("SHOW COLUMNS FROM otp_verifications LIKE 'used_at'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE otp_verifications ADD COLUMN used_at TIMESTAMP NULL AFTER expires_at")
                messages.append("Added missing 'used_at' column")
        except Exception as e:
            messages.append(f"Used_at column check: {str(e)}")
        
        # Add indexes if they don't exist
        try:
            cursor.execute("SHOW INDEX FROM otp_verifications WHERE Key_name = 'idx_phone'")
            if not cursor.fetchone():
                cursor.execute("CREATE INDEX idx_phone ON otp_verifications(phone)")
                messages.append("Added missing 'idx_phone' index")
        except Exception as e:
            messages.append(f"Index check: {str(e)}")
        
        # Create Journal entries table
        cursor.execute('''CREATE TABLE IF NOT EXISTS journal_entries (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            image_url VARCHAR(500),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            created_by INT,
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
            INDEX idx_active (is_active),
            INDEX idx_created (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        messages.append("Journal entries table created/verified")
        
        # Migration: Remove link_url column if it exists
        try:
            cursor.execute("SHOW COLUMNS FROM journal_entries LIKE 'link_url'")
            if cursor.fetchone():
                cursor.execute('ALTER TABLE journal_entries DROP COLUMN link_url')
                messages.append("Removed legacy link_url column from journal_entries")
        except Exception as e:
            if 'Unknown column' not in str(e):
                messages.append(f"link_url column check: {str(e)}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Tables created/fixed successfully', 'details': messages}), 200
    except Exception as err:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(err)}), 500

@app.route('/')
def index():
    conn = get_db()
    products = []
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            # Fetch approved products with their images
            cursor.execute('''
                SELECT 
                    p.id,
                    p.name,
                    p.price,
                    p.slug,
                    c.name as category_name,
                    c.slug as category_slug,
                    pi.image_url
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                LEFT JOIN product_images pi ON p.id = pi.product_id AND pi.is_primary = 1
                WHERE p.is_active = 1
                ORDER BY p.created_at DESC
                LIMIT 20
            ''')
            products = cursor.fetchall()
            
            # Fetch all images for each product
            for product in products:
                cursor.execute('''
                    SELECT image_url, is_primary, sort_order
                    FROM product_images
                    WHERE product_id = %s
                    ORDER BY is_primary DESC, sort_order ASC
                ''', (product['id'],))
                product['all_images'] = cursor.fetchall()
            
            cursor.close()
            conn.close()
        except Exception as err:
            print(f"Error fetching products: {err}")
            if conn:
                conn.close()
    
    return render_template('pages/index.html', products=products)

@app.route('/product/<int:product_id>')
def product_page(product_id):
    # Get user's first name if logged in
    user_first_name = None
    if session.get('logged_in') and session.get('user_id'):
        conn_user = get_db()
        if conn_user:
            try:
                cursor_user = conn_user.cursor(dictionary=True)
                cursor_user.execute('SELECT first_name FROM users WHERE id = %s', (session.get('user_id'),))
                user_data = cursor_user.fetchone()
                if user_data:
                    user_first_name = user_data['first_name']
                cursor_user.close()
                conn_user.close()
            except:
                pass
    
    conn = get_db()
    product = None
    sizes = []
    colors = []
    images = []
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Get product details with primary image
            cursor.execute('''
                SELECT 
                    p.id,
                    p.name,
                    p.description,
                    p.price,
                    p.brand,
                    p.sku,
                    c.name as category_name,
                    pi.image_url
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                LEFT JOIN product_images pi ON p.id = pi.product_id AND pi.is_primary = 1
                WHERE p.id = %s AND p.is_active = 1
            ''', (product_id,))
            
            product = cursor.fetchone()
            
            if product:
                # Get ALL product images (primary first, then others)
                cursor.execute('''
                    SELECT image_url, is_primary
                    FROM product_images
                    WHERE product_id = %s
                    ORDER BY is_primary DESC, id ASC
                ''', (product_id,))
                
                images = cursor.fetchall()
                
                # Get available sizes and colors from variants with stock info
                cursor.execute('''
                    SELECT size, color, stock_quantity
                    FROM product_variants
                    WHERE product_id = %s AND stock_quantity > 0
                    ORDER BY size, color
                ''', (product_id,))
                
                variants = cursor.fetchall()
                
                # Extract unique sizes and colors
                sizes = sorted(list(set([v['size'] for v in variants if v['size']])))
                colors = sorted(list(set([v['color'] for v in variants if v['color']])))
                
                # Create a stock map for quick lookup
                stock_map = {}
                for v in variants:
                    key = f"{v['size']}_{v['color']}"
                    stock_map[key] = v['stock_quantity']
            
            cursor.close()
            conn.close()
        except Exception as err:
            print(f"Error fetching product: {err}")
            if conn:
                conn.close()
    
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('index'))
    
    return render_template('pages/product.html', 
                         product=product, 
                         sizes=sizes, 
                         colors=colors, 
                         images=images,
                         stock_map=stock_map,
                         user_first_name=user_first_name)

@app.route('/api/product/<int:product_id>')
def get_product_detail(product_id):
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'})
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get product details
        cursor.execute('''
            SELECT 
                p.id,
                p.name,
                p.description,
                p.price,
                p.brand,
                p.sku,
                c.name as category_name,
                pi.image_url
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN product_images pi ON p.id = pi.product_id AND pi.is_primary = 1
            WHERE p.id = %s AND p.is_active = 1
        ''', (product_id,))
        
        product = cursor.fetchone()
        
        if not product:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Product not found'})
        
        # Get available sizes and colors from variants
        cursor.execute('''
            SELECT DISTINCT size, color
            FROM product_variants
            WHERE product_id = %s AND stock_quantity > 0
        ''', (product_id,))
        
        variants = cursor.fetchall()
        
        # Extract unique sizes and colors
        sizes = sorted(list(set([v['size'] for v in variants if v['size']])))
        colors = sorted(list(set([v['color'] for v in variants if v['color']])))
        
        product['sizes'] = sizes
        product['colors'] = colors
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'product': product})
        
    except Exception as err:
        print(f"Error fetching product detail: {err}")
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': str(err)})

# Remove static route as Flask will handle static files automatically

# ============ PRODUCT REVIEWS ENDPOINTS ============

@app.route('/api/product-reviews/<int:product_id>', methods=['GET'])
def get_product_reviews(product_id):
    """Get all approved reviews for a product"""
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get product reviews with buyer info
        cursor.execute('''
            SELECT r.id, r.rating, r.title, r.comment, r.helpful_count,
                   r.created_at, r.is_verified_purchase,
                   u.first_name, u.last_name
            FROM reviews r
            JOIN users u ON r.user_id = u.id
            WHERE r.product_id = %s AND r.is_approved = 1
            ORDER BY r.created_at DESC
        ''', (product_id,))
        
        reviews = cursor.fetchall()
        
        # Format dates
        for review in reviews:
            if review.get('created_at'):
                review['created_at'] = review['created_at'].isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'reviews': reviews,
            'count': len(reviews)
        }), 200
        
    except Exception as e:
        print(f"[ERROR] get_product_reviews: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/submit-review', methods=['POST'])
def submit_review():
    """Submit a product review (only for buyers with verified purchase)"""
    if not session.get('logged_in') or session.get('role') != 'buyer':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        order_id = data.get('order_id')
        rating = data.get('rating')
        title = data.get('title', '')
        comment = data.get('comment', '')
        user_id = session.get('user_id')
        
        # Validate input
        if not product_id or not order_id or not rating:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                return jsonify({'success': False, 'error': 'Rating must be between 1 and 5'}), 400
        except:
            return jsonify({'success': False, 'error': 'Invalid rating'}), 400
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Verify the order belongs to the user and is completed
        cursor.execute('''
            SELECT o.id, o.order_status
            FROM orders o
            WHERE o.id = %s AND o.user_id = %s AND o.order_status = 'delivered'
        ''', (order_id, user_id))
        
        order = cursor.fetchone()
        if not order:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Order not found or not delivered'}), 403
        
        # Check if product is in the order
        cursor.execute('''
            SELECT oi.id FROM order_items oi
            WHERE oi.order_id = %s AND oi.product_id = %s
        ''', (order_id, product_id))
        
        order_item = cursor.fetchone()
        if not order_item:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Product not in this order'}), 403
        
        # Check if user already reviewed this product from this order
        cursor.execute('''
            SELECT r.id FROM reviews r
            WHERE r.product_id = %s AND r.user_id = %s AND r.order_id = %s
        ''', (product_id, user_id, order_id))
        
        existing_review = cursor.fetchone()
        if existing_review:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'You have already reviewed this product from this order'}), 409
        
        # Insert review
        cursor.execute('''
            INSERT INTO reviews (product_id, user_id, order_id, rating, title, comment, is_verified_purchase)
            VALUES (%s, %s, %s, %s, %s, %s, 1)
        ''', (product_id, user_id, order_id, rating, title, comment))
        
        review_id = cursor.lastrowid
        
        # Update product rating and review count
        cursor.execute('''
            SELECT AVG(rating) as avg_rating, COUNT(*) as count
            FROM reviews
            WHERE product_id = %s AND is_approved = 1
        ''', (product_id,))
        
        stats = cursor.fetchone()
        avg_rating = float(stats['avg_rating']) if stats['avg_rating'] else 0
        review_count = stats['count'] if stats['count'] else 0
        
        cursor.execute('''
            UPDATE products
            SET rating = %s, review_count = %s
            WHERE id = %s
        ''', (round(avg_rating, 2), review_count, product_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Review submitted successfully',
            'review_id': review_id
        }), 201
        
    except Exception as e:
        print(f"[ERROR] submit_review: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/check-can-review/<int:product_id>', methods=['GET'])
def check_can_review(product_id):
    """Check if buyer can review a product (has completed order)"""
    if not session.get('logged_in') or session.get('role') != 'buyer':
        return jsonify({'success': False, 'can_review': False}), 401
    
    try:
        user_id = session.get('user_id')
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Check if user has a delivered order containing this product
        cursor.execute('''
            SELECT o.id as order_id
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            WHERE o.user_id = %s AND oi.product_id = %s AND o.order_status = 'delivered'
            LIMIT 1
        ''', (user_id, product_id))
        
        order = cursor.fetchone()
        
        # Check if already reviewed
        if order:
            cursor.execute('''
                SELECT r.id FROM reviews r
                WHERE r.product_id = %s AND r.user_id = %s AND r.order_id = %s
            ''', (product_id, user_id, order['order_id']))
            
            existing_review = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'can_review': existing_review is None,
                'order_id': order['order_id'] if not existing_review else None,
                'already_reviewed': existing_review is not None
            }), 200
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'can_review': False,
            'order_id': None,
            'already_reviewed': False
        }), 200
        
    except Exception as e:
        print(f"[ERROR] check_can_review: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ END PRODUCT REVIEWS ============

@app.route('/shop')
def shop():
    return render_template('pages/shop.html')

@app.route('/browse')
def browse():
    return render_template('pages/browse.html')

@app.route('/checkout')
def checkout():
    # Check if user is logged in
    if not session.get('logged_in'):
        flash('Please log in to checkout', 'error')
        return redirect(url_for('login'))
    
    return render_template('pages/checkout.html')

@app.route('/api/validate-cart', methods=['POST'])
def validate_cart():
    """API endpoint to validate cart items and fetch current prices from database"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    try:
        data = request.get_json()
        cart_items = data.get('items', [])
        
        if not cart_items:
            return jsonify({'success': False, 'error': 'Cart is empty'}), 400
        
        cursor = conn.cursor(dictionary=True)
        validated_items = []
        
        # Fetch product details from database
        for item in cart_items:
            product_id = item.get('id')
            if not product_id:
                continue
            
            cursor.execute('''
                SELECT 
                    p.id,
                    p.name,
                    p.price,
                    p.is_active,
                    pi.image_url,
                    i.stock_quantity,
                    s.store_name as seller_name,
                    s.id as seller_id
                FROM products p
                LEFT JOIN product_images pi ON p.id = pi.product_id AND pi.is_primary = 1
                LEFT JOIN inventory i ON p.id = i.product_id
                JOIN sellers s ON p.seller_id = s.id
                WHERE p.id = %s AND p.is_active = 1
            ''', (product_id,))
            
            product = cursor.fetchone()
            
            if product:
                # Check stock
                requested_qty = int(item.get('quantity', 1))
                available_stock = product['stock_quantity'] or 0
                
                validated_items.append({
                    'id': product['id'],
                    'name': product['name'],
                    'price': float(product['price']),
                    'quantity': min(requested_qty, available_stock) if available_stock > 0 else requested_qty,
                    'image_url': product['image_url'] or '/static/images/placeholder.jpg',
                    'seller_id': product['seller_id'],
                    'seller_name': product['seller_name'],
                    'stock_available': available_stock,
                    'size': item.get('size', ''),
                    'color': item.get('color', '')
                })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'items': validated_items
        })
        
    except Exception as err:
        print(f"Error validating cart: {err}")
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': 'Failed to validate cart'}), 500

@app.route('/api/place-order', methods=['POST'])
def place_order():
    # Check if user is logged in
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'Please log in to place an order'})
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'})
    
    try:
        data = request.json
        cursor = conn.cursor(dictionary=True)
        user_id = session.get('user_id')
        
        # Generate unique order number
        import random
        import string
        import time
        order_number = f"ORD-{int(time.time())}-{''.join(random.choices(string.digits, k=4))}"
        
        # Get shipping information
        shipping = data.get('shipping', {})
        payment_method = data.get('payment_method', 'cod')
        payment_provider = data.get('payment_provider', None)
        items = data.get('items', [])
        subtotal = float(data.get('subtotal', 0))
        shipping_fee = float(data.get('shipping_fee', 0))
        total_amount = float(data.get('total', 0))
        notes = shipping.get('notes', '')
        save_address = data.get('save_address', False)
        
        # Create shipping address for this order (always needed for order)
        cursor.execute('''
            INSERT INTO addresses (
                user_id, full_name, phone, street_address, 
                barangay, city, province, postal_code, country,
                address_type, is_default
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'shipping', 0)
        ''', (
            user_id,
            f"{shipping.get('firstName', '')} {shipping.get('lastName', '')}".strip(),
            shipping.get('phone', ''),
            shipping.get('address', ''),
            shipping.get('barangay', ''),
            shipping.get('city', ''),
            shipping.get('province', ''),
            shipping.get('postalCode', ''),
            shipping.get('country', 'Philippines')
        ))
        
        shipping_address_id = cursor.lastrowid
        billing_address_id = shipping_address_id  # Using same address for billing
        
        # If user wants to save the address for future use, update it
        if save_address:
            # Check if user wants this as default address
            cursor.execute('SELECT COUNT(*) as count FROM addresses WHERE user_id = %s AND is_default = TRUE', (user_id,))
            result = cursor.fetchone()
            has_default = result['count'] > 0 if result else False
            is_default = not has_default  # Set as default if no default exists
            
            if is_default:
                # Unset other defaults
                cursor.execute('UPDATE addresses SET is_default = FALSE WHERE user_id = %s', (user_id,))
            
            # Update the address to be saved (set is_default if needed)
            cursor.execute('''
                UPDATE addresses 
                SET is_default = %s
                WHERE id = %s
            ''', (is_default, shipping_address_id))
        
        # Get first product's seller_id (assuming all items from same seller for now)
        # In a multi-vendor system, you'd create separate orders per seller
        seller_id = 1  # Default seller
        if items and len(items) > 0:
            # Try to get actual seller_id from product
            cursor.execute('SELECT seller_id FROM products WHERE id = %s', (items[0].get('id'),))
            product_result = cursor.fetchone()
            if product_result and product_result.get('seller_id'):
                seller_id = product_result['seller_id']
        
        # Determine payment status based on method
        if payment_method == 'cod':
            payment_status = 'pending'
            payment_method_text = 'Cash on Delivery'
        else:
            payment_status = 'pending'  # Would be 'paid' after gateway confirmation
            if payment_method == 'gcash':
                payment_method_text = 'GCash'
            elif payment_method == 'paymaya':
                payment_method_text = 'PayMaya'
            elif payment_method == 'card':
                payment_method_text = 'Credit/Debit Card'
            else:
                payment_method_text = 'Online Payment'
        
        # Insert order
        cursor.execute('''
            INSERT INTO orders (
                order_number, user_id, seller_id, 
                shipping_address_id, billing_address_id,
                subtotal, shipping_fee, total_amount,
                payment_method, payment_status, order_status,
                notes, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        ''', (
            order_number,
            user_id,
            seller_id,
            shipping_address_id,
            billing_address_id,
            subtotal,
            shipping_fee,
            total_amount,
            payment_method_text,
            payment_status,
            'pending',
            notes
        ))
        
        order_id = cursor.lastrowid
        
        # Insert order items
        for item in items:
            product_id = item.get('id')
            product_name = item.get('name', 'Product')
            quantity = int(item.get('quantity', 1))
            unit_price = float(item.get('price', 0))
            item_subtotal = unit_price * quantity
            size = item.get('size', '')
            color = item.get('color', '')
            
            # Get product SKU if available
            sku = ''
            cursor.execute('SELECT sku FROM products WHERE id = %s', (product_id,))
            sku_result = cursor.fetchone()
            if sku_result:
                sku = sku_result.get('sku', '')
            
            # Insert order item
            cursor.execute('''
                INSERT INTO order_items (
                    order_id, product_id, product_name, sku,
                    size, color, quantity, unit_price, subtotal
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                order_id,
                product_id,
                product_name,
                sku,
                size,
                color,
                quantity,
                unit_price,
                item_subtotal
            ))
            
            # Update product sales count
            cursor.execute('''
                UPDATE products 
                SET sales_count = sales_count + %s 
                WHERE id = %s
            ''', (quantity, product_id))
            
            # Decrease inventory if available
            cursor.execute('''
                UPDATE inventory 
                SET stock_quantity = GREATEST(0, stock_quantity - %s),
                    reserved_quantity = reserved_quantity + %s
                WHERE product_id = %s
            ''', (quantity, quantity, product_id))
        
        # Create transaction record
        cursor.execute('''
            INSERT INTO transactions (
                order_id, payment_method, payment_gateway,
                amount, currency, status
            ) VALUES (%s, %s, %s, %s, %s, %s)
        ''', (
            order_id,
            payment_method_text,
            payment_provider,
            total_amount,
            'PHP',
            'pending'
        ))
        
        # Create shipment record
        cursor.execute('''
            INSERT INTO shipments (
                order_id, status, created_at
            ) VALUES (%s, 'pending', NOW())
        ''', (order_id,))
        
        # Log activity
        cursor.execute('''
            INSERT INTO activity_logs (
                user_id, action, entity_type, entity_id, description
            ) VALUES (%s, %s, %s, %s, %s)
        ''', (
            user_id,
            'order_placed',
            'order',
            order_id,
            f'Order {order_number} placed with {len(items)} items'
        ))
        
        # Commit all database changes
        conn.commit()
        
        # Get buyer email for order confirmation
        buyer_email = shipping.get('email', '')
        if not buyer_email:
            # Try to get email from user account
            cursor.execute('SELECT email FROM users WHERE id = %s', (user_id,))
            user_result = cursor.fetchone()
            if user_result:
                buyer_email = user_result.get('email', '')
        
        # Send order confirmation email
        if buyer_email:
            try:
                from utils.otp_service import OTPService
                order_email_data = {
                    'items': items,
                    'subtotal': subtotal,
                    'shipping_fee': shipping_fee,
                    'total': total_amount,
                    'shipping': shipping,
                    'payment_method': payment_method_text
                }
                OTPService.send_order_confirmation_email(buyer_email, order_number, order_email_data)
            except Exception as email_error:
                print(f"Warning: Could not send order confirmation email: {email_error}")
                # Don't fail the order if email fails
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Order placed successfully',
            'order_number': order_number,
            'order_id': order_id
        })
        
    except Exception as e:
        print(f"Error placing order: {str(e)}")
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/order/<int:order_id>')
def order_details(order_id):
    """View order details by order ID"""
    # Check if user is logged in
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db()
    if not conn:
        flash('Database connection failed', 'error')
        return redirect('/indexLoggedIn.html#myOrders')
    
    try:
        cursor = conn.cursor(dictionary=True)
        user_id = session.get('user_id')
        
        # Debug logging
        print(f"[ORDER DETAILS] Fetching order {order_id} (type: {type(order_id)}) for user {user_id}")
        
        # Get order details with addresses
        cursor.execute('''
            SELECT o.*, 
                   CONCAT(a.street_address, ', ', COALESCE(a.barangay, ''), ', ', 
                          a.city, ', ', a.province, ' ', COALESCE(a.postal_code, ''), ', ', 
                          a.country) as shipping_address,
                   a.full_name, a.phone as shipping_phone,
                   s.store_name
            FROM orders o
            LEFT JOIN addresses a ON o.shipping_address_id = a.id
            LEFT JOIN sellers s ON o.seller_id = s.id
            WHERE o.id = %s AND o.user_id = %s
        ''', (order_id, user_id))
        
        order = cursor.fetchone()
        
        print(f"[ORDER DETAILS] Order found: {order is not None}")
        
        if not order:
            cursor.close()
            conn.close()
            print(f"[ORDER DETAILS] Order {order_id} not found for user {user_id}")
            flash('Order not found', 'error')
            return redirect('/indexLoggedIn.html#myOrders')
        
        # Get order items with product images
        cursor.execute('''
            SELECT oi.*, p.name as product_name,
                   COALESCE(pi_primary.image_url, pi_any.image_url) as image_url
            FROM order_items oi
            LEFT JOIN products p ON oi.product_id = p.id
            LEFT JOIN product_images pi_primary ON p.id = pi_primary.product_id AND pi_primary.is_primary = 1
            LEFT JOIN product_images pi_any ON p.id = pi_any.product_id
            WHERE oi.order_id = %s
            GROUP BY oi.id, oi.product_id
        ''', (order_id,))
        
        items = cursor.fetchall()
        
        # Get shipment details for order tracking
        cursor.execute('''
            SELECT id, status, tracking_number, seller_confirmed, seller_confirmed_at,
                   shipped_at, delivered_at, estimated_delivery, delivery_notes, rider_id
            FROM shipments
            WHERE order_id = %s
            LIMIT 1
        ''', (order_id,))
        
        shipment = cursor.fetchone()
        
        # Convert Decimal to float for template
        if order.get('total_amount'):
            order['total_amount'] = float(order['total_amount'])
        if order.get('subtotal'):
            order['subtotal'] = float(order['subtotal'])
        if order.get('shipping_fee'):
            order['shipping_fee'] = float(order['shipping_fee'])
        
        for item in items:
            if item.get('unit_price'):
                item['unit_price'] = float(item['unit_price'])
            if item.get('subtotal'):
                item['subtotal'] = float(item['subtotal'])
        
        # Status colors and emojis
        status_colors = {
            'pending': {'bg': '#fef3c7', 'color': '#92400e', 'emoji': '⏳'},
            'confirmed': {'bg': '#dbeafe', 'color': '#1e40af', 'emoji': '✔️'},
            'processing': {'bg': '#fed7aa', 'color': '#9a3412', 'emoji': '🔄'},
            'shipped': {'bg': '#e9d5ff', 'color': '#6b21a8', 'emoji': '📦'},
            'delivered': {'bg': '#d1fae5', 'color': '#065f46', 'emoji': '✅'},
            'cancelled': {'bg': '#fee2e2', 'color': '#991b1b', 'emoji': '❌'},
            'returned': {'bg': '#f3e8ff', 'color': '#6b21a8', 'emoji': '↩️'}
        }
        
        # Ensure order_status exists and has a default value
        if not order.get('order_status'):
            order['order_status'] = 'pending'
        
        cursor.close()
        conn.close()
        
        return render_template('pages/order_details.html', 
                             order=order, 
                             items=items,
                             shipment=shipment,
                             status_colors=status_colors)
        
    except Exception as e:
        print(f"[ORDER DETAILS] Error loading order details: {str(e)}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.close()
        flash('Error loading order', 'error')
        return redirect('/indexLoggedIn.html#myOrders')

@app.route('/order-confirmation/<order_number>')
def order_confirmation(order_number):
    # Check if user is logged in
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db()
    if not conn:
        flash('Database connection failed', 'error')
        return redirect(url_for('buyer_dashboard'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get order details with addresses
        cursor.execute('''
            SELECT o.*, 
                   CONCAT(a.street_address, ', ', COALESCE(a.barangay, ''), ', ', 
                          a.city, ', ', a.province, ' ', COALESCE(a.postal_code, ''), ', ', 
                          a.country) as shipping_address,
                   a.full_name, a.phone
            FROM orders o
            LEFT JOIN addresses a ON o.shipping_address_id = a.id
            WHERE o.order_number = %s AND o.user_id = %s
        ''', (order_number, session.get('user_id')))
        
        order = cursor.fetchone()
        
        if not order:
            cursor.close()
            conn.close()
            flash('Order not found', 'error')
            return redirect(url_for('buyer_dashboard'))
        
        # Get order items with product images
        cursor.execute('''
            SELECT oi.*, p.name as product_name,
                   COALESCE(pi_primary.image_url, pi_any.image_url) as image_url
            FROM order_items oi
            LEFT JOIN products p ON oi.product_id = p.id
            LEFT JOIN product_images pi_primary ON p.id = pi_primary.product_id AND pi_primary.is_primary = 1
            LEFT JOIN product_images pi_any ON p.id = pi_any.product_id
            WHERE oi.order_id = %s
            GROUP BY oi.id, oi.product_id
        ''', (order['id'],))
        
        items = cursor.fetchall()
        
        # Convert Decimal to float for template
        if order.get('total_amount'):
            order['total_amount'] = float(order['total_amount'])
        if order.get('subtotal'):
            order['subtotal'] = float(order['subtotal'])
        if order.get('shipping_fee'):
            order['shipping_fee'] = float(order['shipping_fee'])
        
        for item in items:
            if item.get('unit_price'):
                item['unit_price'] = float(item['unit_price'])
            if item.get('subtotal'):
                item['subtotal'] = float(item['subtotal'])
        
        cursor.close()
        conn.close()
        
        return render_template('pages/order_confirmation.html', order=order, items=items)
        
    except Exception as e:
        print(f"Error loading order confirmation: {str(e)}")
        if conn:
            conn.close()
        flash('Error loading order', 'error')
        return redirect(url_for('buyer_dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('auth/login.html')
            
        conn = get_db()
        if not conn:
            flash('Database connection failed', 'error')
            return render_template('auth/login.html')
            
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user and password == user['password']:
                session.clear()
                session['logged_in'] = True
                session['user_id'] = user['id']
                session['email'] = user['email']
                session['role'] = user['role']
                
                # Redirect based on role
                if user['role'] == 'admin':
                    return redirect(url_for('dashboard'))
                elif user['role'] == 'seller':
                    return redirect(url_for('seller_dashboard'))
                elif user['role'] == 'rider':
                    return redirect(url_for('rider_dashboard'))
                elif user['role'] == 'buyer':
                    return redirect(url_for('buyer_dashboard'))
                else:
                    return redirect(url_for('index'))
            
            flash('Invalid email or password', 'error')
            return render_template('auth/login.html')
            
        except Exception as err:
            flash(f'Login error: {str(err)}', 'error')
            return render_template('auth/login.html')
            
    return render_template('auth/login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        phone = request.form.get('phone')
        role = request.form.get('role', 'buyer')
        terms = request.form.get('terms')
        
        if not all([email, password, first_name, last_name, phone, terms]):
            return jsonify({'success': False, 'message': 'All fields are required, including terms acceptance'}), 400
            
        # Validate email format
        if '@' not in email or '.' not in email:
            return jsonify({'success': False, 'message': 'Please enter a valid email address'}), 400
            
        # Validate phone number format
        if not phone.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            return jsonify({'success': False, 'message': 'Please enter a valid phone number'}), 400
        
        # Validate password strength (minimum 6 characters with letters and numbers)
        import re
        if not re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{6,}$', password):
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters and contain both letters and numbers'}), 400
            
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
        try:
            cursor = conn.cursor()
            
            # Check if email already exists (prevent duplicates)
            cursor.execute('SELECT id FROM users WHERE email = %s', (email,))
            if cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'message': 'This email is already registered. Please use a different email or try logging in.'}), 400
            
            # Store signup data in session for later use
            session['pending_signup'] = {
                'email': email,
                'password': password,
                'first_name': first_name,
                'last_name': last_name,
                'phone': phone,
                'role': role
            }
            
            # Send OTP
            ip_address = request.remote_addr
            otp_code, otp_id = OTPService.create_otp_record(
                conn, 
                email=email,
                otp_type='email',
                purpose='registration',
                ip_address=ip_address
            )
            
            if not otp_code:
                # Check if table exists
                try:
                    cursor_check = conn.cursor()
                    cursor_check.execute("SHOW TABLES LIKE 'otp_verifications'")
                    table_exists = cursor_check.fetchone()
                    cursor_check.close()
                    
                    if not table_exists:
                        conn.close()
                        return jsonify({'success': False, 'message': 'OTP table does not exist. Please run the migration: python migrations/add_otp_verification.py'}), 500
                except:
                    pass
                
                conn.close()
                return jsonify({'success': False, 'message': 'Failed to generate OTP. Please check database connection and ensure otp_verifications table exists. Check server logs for details.'}), 500
            
            success = OTPService.send_email_otp(email, otp_code, 'registration')
            
            conn.close()
            
            if success:
                session['pending_otp_verification'] = {
                    'email': email,
                    'phone': phone,
                    'verification_type': 'email',
                    'purpose': 'registration'
                }
                return jsonify({'success': True, 'message': 'OTP sent successfully', 'redirect': url_for('verify_otp_page')})
            else:
                return jsonify({'success': False, 'message': 'Failed to send OTP email. Please check email configuration (MAIL_USERNAME and MAIL_PASSWORD in .env file).'}), 500
                
        except Exception as err:
            return jsonify({'success': False, 'message': f'Registration failed: {str(err)}'}), 500
            
    return render_template('auth/signup.html')

@app.route('/signup/rider', methods=['GET', 'POST'])
def signup_rider():
    if request.method == 'POST':
        # Get form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        vehicle_types = request.form.getlist('vehicle_type')  # Get multiple vehicle types
        region = request.form.get('region')
        service_area = request.form.get('service_area')
        tnc = request.form.get('tnc')
        
        # If service_area is empty but region is provided, use region as service_area
        if not service_area or service_area.strip() == '':
            if region and region.strip():
                service_area = region
                print(f"DEBUG: service_area was empty, using region: {service_area}")
            else:
                print(f"DEBUG: Both service_area and region are empty")
        
        # Collect vehicle plates for each vehicle type
        vehicle_plates = []
        for vtype in vehicle_types:
            plate = request.form.get(f'vehicle_plate_{vtype}')
            if plate:
                vehicle_plates.append(f"{vtype}:{plate}")
        
        # Get single driver's license (not per vehicle)
        license_number = request.form.get('license_number')
        
        # Join vehicle types and plates with delimiters for storage
        vehicle_type = ','.join(vehicle_types) if vehicle_types else None
        vehicle_plate = '|'.join(vehicle_plates) if vehicle_plates else None

        # Validate required fields
        required_fields = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone': phone,
            'password': password,
            'vehicle_type': vehicle_type,
            'service_area': service_area,
            'tnc': tnc
        }

        # Check required fields (handle empty strings as missing)
        missing_fields = [field for field, value in required_fields.items() if not value or (isinstance(value, str) and value.strip() == '')]
        if missing_fields:
            # Debug logging
            print(f"DEBUG: Missing fields: {missing_fields}")
            print(f"DEBUG: service_area value: {repr(service_area)}")
            print(f"DEBUG: All form data: {dict(request.form)}")
            print(f"DEBUG: Form keys: {list(request.form.keys())}")
            return jsonify({'success': False, 'message': f'Missing required fields: {", ".join(missing_fields)}'}), 400
        
        # Validate that each vehicle type has plate number
        if not vehicle_plate:
            return jsonify({'success': False, 'message': 'Please provide plate number for all selected vehicles'}), 400
        
        # Validate driver's license
        if not license_number:
            return jsonify({'success': False, 'message': 'Please provide your driver\'s license number'}), 400
        
        # Validate password strength (minimum 6 characters with letters and numbers)
        import re
        if not re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{6,}$', password):
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters and contain both letters and numbers'}), 400

        # Validate email format
        if '@' not in email or '.' not in email:
            return jsonify({'success': False, 'message': 'Please enter a valid email address'}), 400

        # Validate phone number format
        if not phone.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            return jsonify({'success': False, 'message': 'Please enter a valid phone number'}), 400

        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500

        try:
            cursor = conn.cursor(dictionary=True)

            # Check if email already exists (prevent duplicates)
            cursor.execute('SELECT id FROM users WHERE email = %s', (email,))
            if cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'message': 'This email is already registered. Please use a different email or try logging in.'}), 400

            # Store rider signup data in session for later use
            session['pending_rider_signup'] = {
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'phone': phone,
                'password': password,
                'vehicle_type': vehicle_type,
                'vehicle_plate': vehicle_plate,
                'license_number': license_number,
                'service_area': service_area
            }
            
            # Send OTP
            ip_address = request.remote_addr
            otp_code, otp_id = OTPService.create_otp_record(
                conn, 
                email=email,
                otp_type='email',
                purpose='registration',
                ip_address=ip_address
            )
            
            if not otp_code:
                # Check if table exists
                try:
                    cursor_check = conn.cursor()
                    cursor_check.execute("SHOW TABLES LIKE 'otp_verifications'")
                    table_exists = cursor_check.fetchone()
                    cursor_check.close()
                    
                    if not table_exists:
                        conn.close()
                        return jsonify({'success': False, 'message': 'OTP table does not exist. Please run the migration: python migrations/add_otp_verification.py'}), 500
                except:
                    pass
                
                conn.close()
                return jsonify({'success': False, 'message': 'Failed to generate OTP. Please check database connection and ensure otp_verifications table exists. Check server logs for details.'}), 500
            
            success = OTPService.send_email_otp(email, otp_code, 'registration')
            
            conn.close()
            
            if success:
                session['pending_otp_verification'] = {
                    'email': email,
                    'phone': phone,
                    'verification_type': 'email',
                    'purpose': 'registration'
                }
                return jsonify({'success': True, 'message': 'OTP sent successfully', 'redirect': url_for('verify_otp_page')})
            else:
                return jsonify({'success': False, 'message': 'Failed to send OTP email. Please check email configuration (MAIL_USERNAME and MAIL_PASSWORD in .env file).'}), 500
                
        except Exception as err:
            return jsonify({'success': False, 'message': f'Registration failed: {str(err)}'}), 500

    return render_template('auth/signupRider.html')

@app.route('/signup/seller', methods=['GET', 'POST'])
@app.route('/signupSeller', methods=['GET', 'POST'])
def signup_seller():
    if request.method == 'POST':
        # Get form data
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        shop_name = request.form.get('shop_name')
        tnc = request.form.get('tnc')

        # Validate required fields
        if not all([email, password, phone, shop_name, tnc]):
            return jsonify({'success': False, 'message': 'All fields are required, including terms acceptance'}), 400

        # Validate email format
        if '@' not in email or '.' not in email:
            return jsonify({'success': False, 'message': 'Please enter a valid email address'}), 400

        # Validate phone number
        if not phone.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            return jsonify({'success': False, 'message': 'Please enter a valid phone number'}), 400
        
        # Validate password strength (minimum 6 characters with letters and numbers)
        import re
        if not re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{6,}$', password):
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters and contain both letters and numbers'}), 400

        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500

        try:
            cursor = conn.cursor(dictionary=True)
            
            # Check if email already exists in the system (strict one-email-per-account policy)
            cursor.execute('SELECT id, email, role FROM users WHERE email = %s', (email,))
            existing_user = cursor.fetchone()
            
            # No account can use an email that's already registered
            if existing_user:
                conn.close()
                return jsonify({'success': False, 'message': 'This email is already registered in the system. Please use a different email address.'}), 400

            # Check if phone number already exists
            cursor.execute('SELECT id FROM users WHERE phone = %s', (phone,))
            existing_phone_user = cursor.fetchone()
            if existing_phone_user:
                conn.close()
                return jsonify({'success': False, 'message': 'This phone number is already registered. Please use a different number.'}), 400

            # Check if shop name exists
            cursor.execute('SELECT id FROM sellers WHERE store_name = %s', (shop_name,))
            if cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'message': 'Shop name already taken'}), 400

            # Store seller signup data in session for later use (always create new account)
            session['pending_seller_signup'] = {
                'email': email,
                'password': password,
                'phone': phone,
                'shop_name': shop_name,
                'is_existing_user': False,
                'existing_user_id': None
            }
            
            print(f"[SELLER SIGNUP] Stored in session - Email: {email}, Shop: {shop_name}, Creating new seller account")
            print(f"[SELLER SIGNUP] Session keys: {list(session.keys())}")
            
            # Send OTP
            ip_address = request.remote_addr
            otp_code, otp_id = OTPService.create_otp_record(
                conn, 
                email=email,
                otp_type='email',
                purpose='registration',
                ip_address=ip_address
            )
            
            if not otp_code:
                # Check if table exists
                try:
                    cursor_check = conn.cursor()
                    cursor_check.execute("SHOW TABLES LIKE 'otp_verifications'")
                    table_exists = cursor_check.fetchone()
                    cursor_check.close()
                    
                    if not table_exists:
                        conn.close()
                        return jsonify({'success': False, 'message': 'OTP table does not exist. Please run the migration: python migrations/add_otp_verification.py'}), 500
                except:
                    pass
                
                conn.close()
                return jsonify({'success': False, 'message': 'Failed to generate OTP. Please check database connection and ensure otp_verifications table exists. Check server logs for details.'}), 500
            
            success = OTPService.send_email_otp(email, otp_code, 'registration')
            
            conn.close()
            
            if success:
                session['pending_otp_verification'] = {
                    'email': email,
                    'phone': phone,
                    'verification_type': 'email',
                    'purpose': 'registration'
                }
                # Ensure session is saved
                session.permanent = True
                print(f"[SELLER SIGNUP] OTP sent successfully. Session saved. Redirecting to verify page.")
                print(f"[SELLER SIGNUP] Pending seller signup still in session: {session.get('pending_seller_signup') is not None}")
                return jsonify({'success': True, 'message': 'OTP sent successfully', 'redirect': url_for('verify_otp_page')})
            else:
                return jsonify({'success': False, 'message': 'Failed to send OTP email. Please check email configuration (MAIL_USERNAME and MAIL_PASSWORD in .env file).'}), 500
                
        except Exception as err:
            return jsonify({'success': False, 'message': f'Registration failed: {str(err)}'}), 500

    # Do not pre-fill email anymore - users must enter their own
    return render_template('auth/signupSeller.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in') or session.get('role') != 'admin':
        flash('Access denied. Please log in as admin.', 'error')
        return redirect(url_for('login'))
    
    conn = get_db()
    if not conn:
        flash('Database error', 'error')
        return redirect(url_for('login'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get pending products count
        cursor.execute('SELECT COUNT(*) as count FROM products WHERE is_active = 0')
        result = cursor.fetchone()
        pending_products = result['count'] if result else 0
        
        # Get pending sellers count
        cursor.execute("SELECT COUNT(*) as count FROM sellers WHERE status = 'pending'")
        result = cursor.fetchone()
        pending_sellers = result['count'] if result else 0
        
        # Get pending riders count
        cursor.execute("SELECT COUNT(*) as count FROM riders WHERE status = 'pending'")
        result = cursor.fetchone()
        pending_riders = result['count'] if result else 0
        
        # Get total orders
        cursor.execute('SELECT COUNT(*) as count FROM orders')
        result = cursor.fetchone()
        total_orders = result['count'] if result else 0
        
        # Get total users
        cursor.execute('SELECT COUNT(*) as count FROM users')
        result = cursor.fetchone()
        total_users = result['count'] if result else 0
        
        # Get weekly revenue (last 7 days)
        cursor.execute('''
            SELECT 
                DAYNAME(created_at) as day_name,
                DAYOFWEEK(created_at) as day_num,
                COALESCE(SUM(total_amount), 0) as daily_revenue
            FROM orders
            WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)
            AND payment_status = 'paid'
            GROUP BY DATE(created_at), DAYNAME(created_at), DAYOFWEEK(created_at)
            ORDER BY DATE(created_at)
        ''')
        weekly_revenue_raw = cursor.fetchall()
        
        # Create a dictionary for all days of the week with default 0
        days_order = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        weekly_revenue = {day: 0 for day in days_order}
        
        # Fill in actual revenue data
        for row in weekly_revenue_raw:
            weekly_revenue[row['day_name']] = float(row['daily_revenue'])
        
        # Get max revenue for percentage calculation
        max_weekly_revenue = max(weekly_revenue.values()) if max(weekly_revenue.values()) > 0 else 1
        
        cursor.close()
        conn.close()
        
        return render_template('pages/dashboard.html',
                             pending_products=pending_products,
                             pending_sellers=pending_sellers,
                             pending_riders=pending_riders,
                             total_orders=total_orders,
                             total_users=total_users,
                             weekly_revenue=weekly_revenue,
                             max_weekly_revenue=max_weekly_revenue)
        
    except Exception as err:
        flash(f'Error loading dashboard: {str(err)}', 'error')
        return redirect(url_for('login'))

@app.route('/admin/pending-products', methods=['GET'])
def admin_pending_products():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get all pending products (is_active = 0) regardless of stock
        # These are products waiting for admin approval - show even with zero stock
        cursor.execute('''
            SELECT p.*, s.store_name, u.email as seller_email,
                   u.first_name, u.last_name,
                   COALESCE(SUM(pv.stock_quantity), 0) as total_stock,
                   COALESCE(COUNT(DISTINCT pv.id), 0) as variant_count,
                   COALESCE(COUNT(DISTINCT pi.id), 0) as image_count
            FROM products p
            JOIN sellers s ON p.seller_id = s.id
            JOIN users u ON s.user_id = u.id
            LEFT JOIN product_variants pv ON p.id = pv.product_id
            LEFT JOIN product_images pi ON p.id = pi.product_id
            WHERE p.is_active = 0
            GROUP BY p.id
            ORDER BY p.created_at DESC
        ''')
        pending_products = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({'products': pending_products}), 200
        
    except Exception as err:
        print(f"[ERROR] admin_pending_products: {err}")
        return jsonify({'error': str(err)}), 500

@app.route('/admin/product-details/<int:product_id>', methods=['GET'])
def admin_product_details(product_id):
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get product details
        cursor.execute('''
            SELECT p.*, s.store_name, u.email as seller_email,
                   c.name as category,
                   COALESCE(SUM(pv.stock_quantity), 0) as stock
            FROM products p
            JOIN sellers s ON p.seller_id = s.id
            JOIN users u ON s.user_id = u.id
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN product_variants pv ON p.id = pv.product_id
            WHERE p.id = %s
            GROUP BY p.id
        ''', (product_id,))
        product = cursor.fetchone()
        
        if not product:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        # Get product variants (sizes and colors) - show ALL variants including zero stock
        cursor.execute('''
            SELECT size, color, stock_quantity
            FROM product_variants
            WHERE product_id = %s
            ORDER BY size, color
        ''', (product_id,))
        variants = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'product': product,
            'variants': variants
        }), 200
        
    except Exception as err:
        return jsonify({'success': False, 'error': str(err)}), 500

@app.route('/admin/approve-product/<int:product_id>', methods=['POST'])
def admin_approve_product(product_id):
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Approve product
        cursor.execute('UPDATE products SET is_active = 1 WHERE id = %s', (product_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Product approved successfully'}), 200
        
    except Exception as err:
        return jsonify({'error': str(err)}), 500

@app.route('/admin/reject-product/<int:product_id>', methods=['POST'])
def admin_reject_product(product_id):
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get rejection reason from request
        rejection_reason = request.form.get('reason', '') or (request.json.get('reason', '') if request.is_json else '')
        if not rejection_reason:
            rejection_reason = 'No reason provided'
        
        # Add rejection_reason and rejection_status columns if they don't exist
        try:
            cursor.execute('ALTER TABLE products ADD COLUMN rejection_reason TEXT DEFAULT NULL')
            conn.commit()
        except:
            pass  # Column already exists
        
        try:
            cursor.execute('ALTER TABLE products ADD COLUMN rejection_status VARCHAR(50) DEFAULT NULL')
            conn.commit()
        except:
            pass  # Column already exists
        
        # Mark product as rejected (set is_active = 0) and store rejection reason
        cursor.execute('''
            UPDATE products 
            SET is_active = 0, rejection_status = 'rejected', rejection_reason = %s
            WHERE id = %s
        ''', (rejection_reason, product_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': 'Product rejected',
            'rejection_reason': rejection_reason
        }), 200
        
    except Exception as err:
        print(f"[ERROR] admin_reject_product: {err}")
        if conn:
            conn.rollback()
        return jsonify({'error': str(err)}), 500

@app.route('/admin/pending-sellers', methods=['GET'])
def admin_pending_sellers():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get all pending sellers
        cursor.execute('''
            SELECT s.*, u.first_name, u.last_name, u.email, u.phone
            FROM sellers s
            JOIN users u ON s.user_id = u.id
            WHERE s.status = 'pending'
            ORDER BY s.created_at DESC
        ''')
        pending_sellers = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({'sellers': pending_sellers}), 200
        
    except Exception as err:
        return jsonify({'error': str(err)}), 500

@app.route('/admin/approve-seller/<int:seller_id>', methods=['POST'])
def admin_approve_seller(seller_id):
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Approve seller
        cursor.execute("UPDATE sellers SET status = 'approved' WHERE id = %s", (seller_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Seller approved successfully'}), 200
        
    except Exception as err:
        return jsonify({'error': str(err)}), 500

@app.route('/admin/reject-seller/<int:seller_id>', methods=['POST'])
def admin_reject_seller(seller_id):
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get user_id before deleting seller
        cursor.execute('SELECT user_id FROM sellers WHERE id = %s', (seller_id,))
        seller = cursor.fetchone()
        
        if seller:
            user_id = seller['user_id']
            # Delete seller record
            cursor.execute('DELETE FROM sellers WHERE id = %s', (seller_id,))
            # Optionally update user role back to buyer or delete user
            cursor.execute("UPDATE users SET role = 'buyer' WHERE id = %s", (user_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Seller rejected'}), 200
        
    except Exception as err:
        return jsonify({'error': str(err)}), 500

@app.route('/admin/pending-riders', methods=['GET'])
def admin_pending_riders():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get all pending riders from riders table
        cursor.execute('''
            SELECT r.*, u.first_name, u.last_name, u.email, u.phone
            FROM riders r
            JOIN users u ON r.user_id = u.id
            WHERE r.status = 'pending'
            ORDER BY r.created_at DESC
        ''')
        pending_riders = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({'riders': pending_riders}), 200
        
    except Exception as err:
        return jsonify({'error': str(err)}), 500

@app.route('/admin/approve-rider/<int:rider_id>', methods=['POST'])
def admin_approve_rider(rider_id):
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Approve rider by updating status
        cursor.execute("UPDATE riders SET status = 'approved' WHERE id = %s", (rider_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Rider approved successfully'}), 200
        
    except Exception as err:
        return jsonify({'error': str(err)}), 500

@app.route('/admin/reject-rider/<int:rider_id>', methods=['POST'])
def admin_reject_rider(rider_id):
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get user_id before deleting rider
        cursor.execute('SELECT user_id FROM riders WHERE id = %s', (rider_id,))
        rider = cursor.fetchone()
        
        if rider:
            user_id = rider['user_id']
            # Delete rider record
            cursor.execute('DELETE FROM riders WHERE id = %s', (rider_id,))
            # Update user role back to buyer
            cursor.execute("UPDATE users SET role = 'buyer' WHERE id = %s", (user_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Rider application rejected'}), 200
        
    except Exception as err:
        return jsonify({'error': str(err)}), 500

@app.route('/admin/pending-edits', methods=['GET'])
def admin_pending_edits():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get all pending product edits grouped by product
        cursor.execute('''
            SELECT 
                pe.product_id,
                p.name as product_name,
                p.seller_id,
                s.store_name,
                COUNT(pe.id) as edit_count,
                MIN(pe.requested_at) as first_request
            FROM product_edits pe
            JOIN products p ON pe.product_id = p.id
            JOIN sellers s ON p.seller_id = s.id
            WHERE pe.status = 'pending'
            GROUP BY pe.product_id, p.name, p.seller_id, s.store_name
            ORDER BY first_request ASC
        ''')
        pending_products = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({'pending_edits': pending_products}), 200
        
    except Exception as err:
        return jsonify({'error': str(err)}), 500

@app.route('/admin/product-edit-details/<int:product_id>', methods=['GET'])
def admin_product_edit_details(product_id):
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get product details
        cursor.execute('''
            SELECT p.*, s.store_name, c.name as category_name
            FROM products p
            JOIN sellers s ON p.seller_id = s.id
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.id = %s
        ''', (product_id,))
        product = cursor.fetchone()
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Get all pending edits for this product
        cursor.execute('''
            SELECT * FROM product_edits
            WHERE product_id = %s AND status = 'pending'
            ORDER BY requested_at ASC
        ''', (product_id,))
        edits = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'product': product,
            'edits': edits
        }), 200
        
    except Exception as err:
        return jsonify({'error': str(err)}), 500

@app.route('/admin/approve-edit/<int:edit_id>', methods=['POST'])
def admin_approve_edit(edit_id):
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        user_id = session.get('user_id')
        
        # Get edit details
        cursor.execute('SELECT * FROM product_edits WHERE id = %s', (edit_id,))
        edit = cursor.fetchone()
        
        if not edit:
            return jsonify({'error': 'Edit not found'}), 404
        
        # Apply the edit to the product
        field_name = edit['field_name']
        new_value = edit['new_value']
        product_id = edit['product_id']
        
        # Update the product
        update_query = f"UPDATE products SET {field_name} = %s WHERE id = %s"
        cursor.execute(update_query, (new_value, product_id))
        
        # Mark edit as approved
        cursor.execute('''
            UPDATE product_edits 
            SET status = 'approved', reviewed_at = NOW(), reviewed_by = %s
            WHERE id = %s
        ''', (user_id, edit_id))
        
        # Check if there are any more pending edits for this product
        cursor.execute('''
            SELECT COUNT(*) as count 
            FROM product_edits 
            WHERE product_id = %s AND status = 'pending'
        ''', (product_id,))
        
        result = cursor.fetchone()
        pending_count = result['count'] if result else 0
        
        # If no more pending edits, update product edit_status
        if pending_count == 0:
            cursor.execute('''
                UPDATE products 
                SET edit_status = 'approved'
                WHERE id = %s
            ''', (product_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Edit approved successfully'}), 200
        
    except Exception as err:
        if conn:
            conn.rollback()
        return jsonify({'error': str(err)}), 500

@app.route('/admin/reject-edit/<int:edit_id>', methods=['POST'])
def admin_reject_edit(edit_id):
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        user_id = session.get('user_id')
        admin_notes = request.form.get('notes', '')
        
        # Get edit details
        cursor.execute('SELECT product_id FROM product_edits WHERE id = %s', (edit_id,))
        edit = cursor.fetchone()
        
        if not edit:
            return jsonify({'error': 'Edit not found'}), 404
        
        product_id = edit['product_id']
        
        # Mark edit as rejected
        cursor.execute('''
            UPDATE product_edits 
            SET status = 'rejected', reviewed_at = NOW(), reviewed_by = %s, admin_notes = %s
            WHERE id = %s
        ''', (user_id, admin_notes, edit_id))
        
        # Check if there are any more pending edits for this product
        cursor.execute('''
            SELECT COUNT(*) as count 
            FROM product_edits 
            WHERE product_id = %s AND status = 'pending'
        ''', (product_id,))
        
        result = cursor.fetchone()
        pending_count = result['count'] if result else 0
        
        # If no more pending edits, update product edit_status
        if pending_count == 0:
            cursor.execute('''
                UPDATE products 
                SET edit_status = 'rejected'
                WHERE id = %s
            ''', (product_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Edit rejected'}), 200
        
    except Exception as err:
        if conn:
            conn.rollback()
        return jsonify({'error': str(err)}), 500

@app.route('/admin/pending-recoveries', methods=['GET'])
def admin_pending_recoveries():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get all pending recovery requests
        cursor.execute('''
            SELECT 
                par.id as request_id,
                par.product_id,
                p.name as product_name,
                p.sku,
                p.price,
                s.store_name,
                par.reason,
                par.requested_at,
                u.email as seller_email
            FROM product_archive_requests par
            JOIN products p ON par.product_id = p.id
            JOIN sellers s ON par.seller_id = s.id
            JOIN users u ON s.user_id = u.id
            WHERE par.request_type = 'recover' AND par.status = 'pending'
            ORDER BY par.requested_at ASC
        ''')
        pending_recoveries = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({'pending_recoveries': pending_recoveries}), 200
        
    except Exception as err:
        return jsonify({'error': str(err)}), 500

@app.route('/admin/approve-recovery/<int:request_id>', methods=['POST'])
def admin_approve_recovery(request_id):
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        user_id = session.get('user_id')
        
        # Get request details
        cursor.execute('''
            SELECT product_id FROM product_archive_requests 
            WHERE id = %s AND request_type = 'recover'
        ''', (request_id,))
        request_data = cursor.fetchone()
        
        if not request_data:
            return jsonify({'error': 'Request not found'}), 404
        
        product_id = request_data['product_id']
        
        # Recover the product (set status back to active)
        cursor.execute('''
            UPDATE products 
            SET archive_status = 'active', archived_at = NULL, archived_by = NULL
            WHERE id = %s
        ''', (product_id,))
        
        # Mark request as approved
        cursor.execute('''
            UPDATE product_archive_requests 
            SET status = 'approved', reviewed_at = NOW(), reviewed_by = %s
            WHERE id = %s
        ''', (user_id, request_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Recovery approved'}), 200
        
    except Exception as err:
        if conn:
            conn.rollback()
        return jsonify({'error': str(err)}), 500

@app.route('/admin/reject-recovery/<int:request_id>', methods=['POST'])
def admin_reject_recovery(request_id):
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        user_id = session.get('user_id')
        admin_notes = request.form.get('notes', '')
        
        # Get request details
        cursor.execute('''
            SELECT product_id FROM product_archive_requests 
            WHERE id = %s AND request_type = 'recover'
        ''', (request_id,))
        request_data = cursor.fetchone()
        
        if not request_data:
            return jsonify({'error': 'Request not found'}), 404
        
        product_id = request_data['product_id']
        
        # Set product back to archived status
        cursor.execute('''
            UPDATE products 
            SET archive_status = 'archived'
            WHERE id = %s
        ''', (product_id,))
        
        # Mark request as rejected
        cursor.execute('''
            UPDATE product_archive_requests 
            SET status = 'rejected', reviewed_at = NOW(), reviewed_by = %s, admin_notes = %s
            WHERE id = %s
        ''', (user_id, admin_notes, request_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Recovery rejected'}), 200
        
    except Exception as err:
        if conn:
            conn.rollback()
        return jsonify({'error': str(err)}), 500

# Journal Management Routes
@app.route('/admin/journal-entries', methods=['GET'])
def admin_journal_entries():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT id, title, description, image_url, link_url, is_active, created_at, updated_at
            FROM journal_entries
            ORDER BY created_at DESC
        ''')
        entries = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'entries': entries}), 200
    except Exception as err:
        return jsonify({'success': False, 'error': str(err)}), 500

@app.route('/admin/journal-entry', methods=['POST'])
def admin_create_journal_entry():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        user_id = session.get('user_id')
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        is_active = request.form.get('is_active', '1') == '1'
        image_url = ''
        
        if not title:
            return jsonify({'success': False, 'error': 'Title is required'}), 400
        
        # Handle image file upload
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and image_file.filename:
                try:
                    # Create upload folder
                    upload_folder = os.path.join('static', 'images', 'journal')
                    os.makedirs(upload_folder, exist_ok=True)
                    
                    # Generate unique filename
                    timestamp = int(time.time())
                    unique_filename = f"journal_{user_id}_{timestamp}_{os.urandom(4).hex()}.png"
                    filepath = os.path.join(upload_folder, unique_filename)
                    
                    # Save image
                    image_file.save(filepath)
                    image_url = f"/static/images/journal/{unique_filename}"
                    print(f"[JOURNAL] Image uploaded: {image_url}")
                except Exception as img_err:
                    print(f"[JOURNAL] Error uploading image: {img_err}")
                    return jsonify({'success': False, 'error': f'Error uploading image: {img_err}'}), 500
        
        cursor.execute('''
            INSERT INTO journal_entries (title, description, image_url, is_active, created_by)
            VALUES (%s, %s, %s, %s, %s)
        ''', (title, description, image_url, is_active, user_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Journal entry created'}), 200
    except Exception as err:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(err)}), 500

@app.route('/admin/journal-entry/<int:entry_id>', methods=['GET'])
def admin_get_journal_entry(entry_id):
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM journal_entries WHERE id = %s', (entry_id,))
        entry = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if entry:
            return jsonify({'success': True, 'entry': entry}), 200
        else:
            return jsonify({'success': False, 'error': 'Entry not found'}), 404
    except Exception as err:
        return jsonify({'success': False, 'error': str(err)}), 500

@app.route('/admin/journal-entry/<int:entry_id>', methods=['PUT'])
def admin_update_journal_entry(entry_id):
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        user_id = session.get('user_id')
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        is_active = request.form.get('is_active', '1') == '1'
        
        if not title:
            return jsonify({'success': False, 'error': 'Title is required'}), 400
        
        # Get current entry to preserve existing image if new one not provided
        cursor.execute('SELECT image_url FROM journal_entries WHERE id = %s', (entry_id,))
        current_entry = cursor.fetchone()
        image_url = current_entry['image_url'] if current_entry else ''
        
        # Handle image file upload
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and image_file.filename:
                try:
                    # Create upload folder
                    upload_folder = os.path.join('static', 'images', 'journal')
                    os.makedirs(upload_folder, exist_ok=True)
                    
                    # Generate unique filename
                    timestamp = int(time.time())
                    unique_filename = f"journal_{user_id}_{timestamp}_{os.urandom(4).hex()}.png"
                    filepath = os.path.join(upload_folder, unique_filename)
                    
                    # Save image
                    image_file.save(filepath)
                    image_url = f"/static/images/journal/{unique_filename}"
                    print(f"[JOURNAL] Image updated: {image_url}")
                except Exception as img_err:
                    print(f"[JOURNAL] Error uploading image: {img_err}")
                    return jsonify({'success': False, 'error': f'Error uploading image: {img_err}'}), 500
        
        cursor.execute('''
            UPDATE journal_entries 
            SET title = %s, description = %s, image_url = %s, is_active = %s, updated_at = NOW()
            WHERE id = %s
        ''', (title, description, image_url, is_active, entry_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Journal entry updated'}), 200
    except Exception as err:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(err)}), 500

@app.route('/admin/journal-entry/<int:entry_id>', methods=['DELETE'])
def admin_delete_journal_entry(entry_id):
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM journal_entries WHERE id = %s', (entry_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Journal entry deleted'}), 200
    except Exception as err:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(err)}), 500

@app.route('/api/journal-entries', methods=['GET'])
def api_journal_entries():
    """Public API to get active journal entries for homepage"""
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT id, title, description, image_url, created_at
            FROM journal_entries
            WHERE is_active = TRUE
            ORDER BY created_at DESC
            LIMIT 6
        ''')
        entries = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'entries': entries}), 200
    except Exception as err:
        return jsonify({'success': False, 'error': str(err)}), 500

@app.route('/admin/all-products', methods=['GET'])
def admin_all_products():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT p.id, p.name, p.price, s.store_name, 
                   COALESCE(SUM(pv.stock_quantity), 0) as stock,
                   CASE WHEN p.is_active = 1 THEN 'Active' ELSE 'Inactive' END as status
            FROM products p
            JOIN sellers s ON p.seller_id = s.id
            LEFT JOIN product_variants pv ON p.id = pv.product_id
            GROUP BY p.id
            ORDER BY p.created_at DESC
            LIMIT 100
        ''')
        products = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'products': products or []}), 200
    except Exception as err:
        return jsonify({'error': str(err)}), 500

@app.route('/admin/all-customers', methods=['GET'])
def admin_all_customers():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT u.id, u.first_name, u.last_name, u.email, u.phone, u.created_at,
                   COUNT(o.id) as order_count
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id
            WHERE u.role = 'buyer'
            GROUP BY u.id
            ORDER BY u.created_at DESC
            LIMIT 100
        ''')
        customers = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'customers': customers or []}), 200
    except Exception as err:
        return jsonify({'error': str(err)}), 500

@app.route('/admin/all-transactions', methods=['GET'])
def admin_all_transactions():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT o.id, o.order_number, o.total_amount as amount, o.order_status as status,
                   o.created_at, u.first_name, u.last_name,
                   CONCAT(u.first_name, ' ', u.last_name) as customer_name
            FROM orders o
            JOIN users u ON o.user_id = u.id
            ORDER BY o.created_at DESC
            LIMIT 100
        ''')
        transactions = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'transactions': transactions or []}), 200
    except Exception as err:
        return jsonify({'error': str(err)}), 500

@app.route('/admin/statistics', methods=['GET'])
def admin_statistics():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Total revenue
        cursor.execute('SELECT SUM(total_amount) as total_revenue FROM orders WHERE order_status = "delivered"')
        revenue_result = cursor.fetchone()
        total_revenue = revenue_result['total_revenue'] or 0 if revenue_result else 0
        
        # Total orders
        cursor.execute('SELECT COUNT(*) as total FROM orders')
        result = cursor.fetchone()
        total_orders = result['total'] if result else 0
        
        # Active users
        cursor.execute('SELECT COUNT(*) as total FROM users WHERE role = "buyer"')
        result = cursor.fetchone()
        active_users = result['total'] if result else 0
        
        # Active products
        cursor.execute('SELECT COUNT(*) as total FROM products WHERE is_active = 1')
        result = cursor.fetchone()
        active_products = result['total'] if result else 0
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'total_revenue': float(total_revenue),
            'total_orders': total_orders,
            'active_users': active_users,
            'active_products': active_products
        }), 200
    except Exception as err:
        return jsonify({'success': False, 'error': str(err)}), 500

@app.route('/admin/active-sellers', methods=['GET'])
def admin_active_sellers():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT s.id, s.store_name, s.user_id, u.first_name, u.last_name, u.email, u.phone, s.created_at,
                   COUNT(p.id) as product_count
            FROM sellers s
            JOIN users u ON s.user_id = u.id
            LEFT JOIN products p ON s.id = p.seller_id AND p.is_active = 1
            GROUP BY s.id
            ORDER BY s.created_at DESC
            LIMIT 100
        ''')
        sellers = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'sellers': sellers or []}), 200
    except Exception as err:
        return jsonify({'error': str(err)}), 500

@app.route('/admin/active-riders', methods=['GET'])
def admin_active_riders():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT r.id, u.first_name, u.last_name, u.email, u.phone, r.vehicle_type,
                   r.license_number, r.service_area, r.status, r.is_available, r.rating, r.created_at
            FROM riders r
            JOIN users u ON r.user_id = u.id
            ORDER BY r.created_at DESC
            LIMIT 100
        ''')
        riders = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'riders': riders or []}), 200
    except Exception as err:
        print(f"[ERROR] admin_active_riders: {str(err)}")
        return jsonify({'error': str(err)}), 500

@app.route('/admin/customer-growth-by-region', methods=['GET'])
def admin_customer_growth_by_region():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get customer count by region (from addresses)
        cursor.execute('''
            SELECT a.province as region, COUNT(DISTINCT u.id) as count
            FROM users u
            LEFT JOIN addresses a ON u.id = a.user_id AND a.is_default = 1
            WHERE u.role = 'buyer'
            GROUP BY a.province
            HAVING a.province IS NOT NULL
            ORDER BY count DESC
        ''')
        regions = cursor.fetchall()
        
        # If no province data, try to get from cities
        if not regions:
            cursor.execute('''
                SELECT a.city as region, COUNT(DISTINCT u.id) as count
                FROM users u
                LEFT JOIN addresses a ON u.id = a.user_id AND a.is_default = 1
                WHERE u.role = 'buyer'
                GROUP BY a.city
                HAVING a.city IS NOT NULL
                ORDER BY count DESC
            ''')
            regions = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'regions': regions or []
        }), 200
    except Exception as err:
        return jsonify({'success': False, 'error': str(err)}), 500

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        if request.method == 'GET':
            # Fetch current settings
            cursor.execute('SELECT * FROM admin_settings LIMIT 1')
            settings = cursor.fetchone()
            
            if not settings:
                # Return defaults if no settings exist
                settings = {
                    'system_name': 'Var-n E-Commerce',
                    'support_email': 'support@varn.com',
                    'support_phone': '+63 977 XXX XXXX',
                    'maintenance_mode': 0,
                    'email_notifications': 1,
                    'order_alerts': 1,
                    'seller_alerts': 1
                }
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'settings': settings
            }), 200
        
        elif request.method == 'POST':
            # Update or create settings
            system_name = request.form.get('system_name', 'Var-n E-Commerce')
            support_email = request.form.get('support_email', 'support@varn.com')
            support_phone = request.form.get('support_phone', '+63 977 XXX XXXX')
            maintenance_mode = int(request.form.get('maintenance_mode', 0))
            email_notifications = int(request.form.get('email_notifications', 1))
            order_alerts = int(request.form.get('order_alerts', 1))
            seller_alerts = int(request.form.get('seller_alerts', 1))
            
            # Check if settings exist
            cursor.execute('SELECT id FROM admin_settings LIMIT 1')
            existing = cursor.fetchone()
            
            if existing:
                # Update existing settings
                cursor.execute('''
                    UPDATE admin_settings 
                    SET system_name = %s, support_email = %s, support_phone = %s,
                        maintenance_mode = %s, email_notifications = %s, 
                        order_alerts = %s, seller_alerts = %s, updated_at = NOW()
                    WHERE id = %s
                ''', (system_name, support_email, support_phone, maintenance_mode,
                      email_notifications, order_alerts, seller_alerts, existing['id']))
            else:
                # Create new settings
                cursor.execute('''
                    INSERT INTO admin_settings 
                    (system_name, support_email, support_phone, maintenance_mode, 
                     email_notifications, order_alerts, seller_alerts, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                ''', (system_name, support_email, support_phone, maintenance_mode,
                      email_notifications, order_alerts, seller_alerts))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': 'Settings saved successfully'
            }), 200
    
    except Exception as err:
        return jsonify({'success': False, 'error': str(err)}), 500

@app.route('/seller-dashboard')
def seller_dashboard():
    print("[DEBUG] seller_dashboard: Starting...")
    if not session.get('logged_in') or session.get('role') != 'seller':
        print("[DEBUG] seller_dashboard: Access denied - not logged in as seller")
        flash('Access denied. Please log in as a seller.', 'error')
        return redirect(url_for('login'))
    
    conn = get_db()
    if not conn:
        print("[DEBUG] seller_dashboard: Database connection failed")
        flash('Database error', 'error')
        return redirect(url_for('login'))
    
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        user_id = session.get('user_id')
        print(f"[DEBUG] seller_dashboard: user_id={user_id}")
        
        # Get seller info
        print("[DEBUG] seller_dashboard: Fetching seller info...")
        cursor.execute('''
            SELECT s.*, u.first_name, u.last_name, u.email 
            FROM sellers s 
            JOIN users u ON s.user_id = u.id 
            WHERE s.user_id = %s
        ''', (user_id,))
        seller = cursor.fetchone()
        print(f"[DEBUG] seller_dashboard: seller={seller}")
        
        if not seller:
            print("[DEBUG] seller_dashboard: Seller profile not found")
            cursor.close()
            conn.close()
            flash('Seller profile not found. Please complete your seller registration.', 'error')
            return redirect(url_for('login'))
        
        seller_id = seller['id']
        print(f"[DEBUG] seller_dashboard: seller_id={seller_id}")
        
        # Get product count
        print("[DEBUG] seller_dashboard: Fetching product count...")
        cursor.execute('SELECT COUNT(*) as count FROM products WHERE seller_id = %s', (seller_id,))
        result = cursor.fetchone()
        product_count = result['count'] if result else 0
        print(f"[DEBUG] seller_dashboard: product_count={product_count}")
        
        # Get low stock products
        print("[DEBUG] seller_dashboard: Fetching low stock products...")
        cursor.execute('''
            SELECT p.name, p.id, i.stock_quantity, i.low_stock_threshold
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            WHERE p.seller_id = %s AND i.stock_quantity <= i.low_stock_threshold
            ORDER BY i.stock_quantity ASC
            LIMIT 5
        ''', (seller_id,))
        low_stock = cursor.fetchall()
        print(f"[DEBUG] seller_dashboard: low_stock count={len(low_stock) if low_stock else 0}")
        
        # Get recent orders
        print("[DEBUG] seller_dashboard: Fetching recent orders...")
        cursor.execute('''
            SELECT o.order_number, o.total_amount, o.order_status, o.created_at,
                   u.first_name, u.last_name,
                   (SELECT GROUP_CONCAT(oi.product_name SEPARATOR ', ')
                    FROM order_items oi WHERE oi.order_id = o.id) as products
            FROM orders o
            JOIN users u ON o.user_id = u.id
            WHERE o.seller_id = %s
            ORDER BY o.created_at DESC
            LIMIT 5
        ''', (seller_id,))
        recent_orders = cursor.fetchall()
        print(f"[DEBUG] seller_dashboard: recent_orders count={len(recent_orders) if recent_orders else 0}")
        
        # Get today's sales
        print("[DEBUG] seller_dashboard: Fetching today's sales...")
        cursor.execute('''
            SELECT COALESCE(SUM(total_amount), 0) as today_sales
            FROM orders
            WHERE seller_id = %s AND DATE(created_at) = CURDATE()
            AND order_status != 'cancelled'
        ''', (seller_id,))
        result = cursor.fetchone()
        today_sales = result['today_sales'] if result else 0
        print(f"[DEBUG] seller_dashboard: today_sales={today_sales}")
        
        # Get pending orders count
        print("[DEBUG] seller_dashboard: Fetching pending orders count...")
        cursor.execute('''
            SELECT COUNT(*) as pending_count
            FROM orders
            WHERE seller_id = %s AND order_status = 'pending'
        ''', (seller_id,))
        result = cursor.fetchone()
        pending_orders = result['pending_count'] if result else 0
        print(f"[DEBUG] seller_dashboard: pending_orders={pending_orders}")
        
        # Get top performing products
        print("[DEBUG] seller_dashboard: Fetching top products...")
        cursor.execute('''
            SELECT p.id, p.name, p.sales_count
            FROM products p
            WHERE p.seller_id = %s AND p.is_active = 1
            ORDER BY p.sales_count DESC
            LIMIT 3
        ''', (seller_id,))
        top_products = cursor.fetchall()
        print(f"[DEBUG] seller_dashboard: top_products count={len(top_products) if top_products else 0}")
        
        # Get weekly sales (last 7 days)
        print("[DEBUG] seller_dashboard: Fetching weekly sales...")
        cursor.execute('''
            SELECT 
                DAYNAME(created_at) as day_name,
                DAYOFWEEK(created_at) as day_num,
                COALESCE(SUM(total_amount), 0) as daily_sales
            FROM orders
            WHERE seller_id = %s 
            AND created_at >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)
            AND order_status != 'cancelled'
            GROUP BY DATE(created_at), DAYNAME(created_at), DAYOFWEEK(created_at)
            ORDER BY DATE(created_at)
        ''', (seller_id,))
        weekly_sales_raw = cursor.fetchall()
        print(f"[DEBUG] seller_dashboard: weekly_sales_raw count={len(weekly_sales_raw) if weekly_sales_raw else 0}")
        
        # Create a dictionary for all days of the week with default 0
        days_order = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        weekly_sales = {day: 0 for day in days_order}
        
        # Fill in actual sales data
        for row in weekly_sales_raw:
            if row and row.get('day_name'):
                weekly_sales[row['day_name']] = float(row['daily_sales']) if row['daily_sales'] else 0
        
        print(f"[DEBUG] seller_dashboard: weekly_sales={weekly_sales}")
        
        # Get max sales for percentage calculation (ensure it's never 0 to prevent division by zero)
        max_value = max(weekly_sales.values()) if weekly_sales.values() else 0
        max_weekly_sales = max_value if max_value > 0 else 1
        print(f"[DEBUG] seller_dashboard: max_weekly_sales={max_weekly_sales}")
        
        # Get all active categories for the dropdown
        print("[DEBUG] seller_dashboard: Fetching categories...")
        cursor.execute('SELECT id, name, slug FROM categories WHERE is_active = TRUE ORDER BY name')
        categories = cursor.fetchall()
        print(f"[DEBUG] seller_dashboard: categories count={len(categories) if categories else 0}")
        
        cursor.close()
        conn.close()
        
        print("[DEBUG] seller_dashboard: Rendering template...")
        return render_template('pages/SellerDashboard.html',
                             seller=seller,
                             product_count=product_count,
                             low_stock=low_stock,
                             recent_orders=recent_orders,
                             today_sales=today_sales,
                             categories=categories,
                             pending_orders=pending_orders,
                             top_products=top_products,
                             weekly_sales=weekly_sales,
                             max_weekly_sales=max_weekly_sales)
        
    except Exception as err:
        print(f"[ERROR] seller_dashboard: {str(err)}")
        print(f"[ERROR] seller_dashboard: Exception type: {type(err)}")
        import traceback
        traceback.print_exc()
        try:
            if cursor:
                cursor.close()
        except:
            pass
        try:
            conn.close()
        except:
            pass
        flash(f'Error loading dashboard: {str(err)}', 'error')
        return redirect(url_for('login'))

@app.route('/rider-dashboard')
def rider_dashboard():
    if not session.get('logged_in') or session.get('role') != 'rider':
        flash('Access denied. Please log in as a rider.', 'error')
        return redirect(url_for('login'))
    
    conn = get_db()
    if not conn:
        flash('Database error', 'error')
        return redirect(url_for('login'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        user_id = session.get('user_id')
        
        # Get user and rider info
        cursor.execute('SELECT first_name, last_name, email, phone FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return redirect(url_for('login'))
        
        # Get rider profile
        cursor.execute('SELECT * FROM riders WHERE user_id = %s', (user_id,))
        rider = cursor.fetchone()
        
        # Get today's earnings (from shipments where rider delivered)
        cursor.execute('''
            SELECT COALESCE(COUNT(*), 0) as deliveries_today,
                   COALESCE(SUM(CAST(o.total_amount AS DECIMAL(10,2)) * 0.15), 0) as earnings_today
            FROM shipments s
            JOIN orders o ON s.order_id = o.id
            WHERE s.rider_id = %s 
            AND s.status = 'delivered'
            AND DATE(s.delivered_at) = CURDATE()
        ''', (rider['id'] if rider else None,))
        today_stats = cursor.fetchone()
        
        # Get rider rating
        rating = rider['rating'] if rider and rider['rating'] else 4.5
        total_deliveries = rider['total_deliveries'] if rider and rider['total_deliveries'] else 0
        
        # Calculate acceptance rate (mock for now)
        acceptance_rate = 95
        
        # Get recent deliveries (last 5)
        cursor.execute('''
            SELECT s.*, o.order_number, o.total_amount,
                   CONCAT(a1.city, ', ', a1.barangay) as pickup_location,
                   CONCAT(a2.city, ', ', a2.barangay) as delivery_location
            FROM shipments s
            JOIN orders o ON s.order_id = o.id
            LEFT JOIN addresses a1 ON o.billing_address_id = a1.id
            LEFT JOIN addresses a2 ON o.shipping_address_id = a2.id
            WHERE s.rider_id = %s
            ORDER BY s.created_at DESC
            LIMIT 5
        ''', (rider['id'] if rider else None,))
        recent_deliveries = cursor.fetchall()
        
        # Convert Decimal to float for template rendering
        for delivery in recent_deliveries:
            if delivery.get('total_amount'):
                delivery['total_amount'] = float(delivery['total_amount'])
        
        # Get active deliveries
        cursor.execute('''
            SELECT s.*, o.order_number, o.total_amount,
                   CONCAT(a1.city, ', ', a1.barangay) as pickup_location,
                   CONCAT(a2.city, ', ', a2.barangay) as delivery_location
            FROM shipments s
            JOIN orders o ON s.order_id = o.id
            LEFT JOIN addresses a1 ON o.billing_address_id = a1.id
            LEFT JOIN addresses a2 ON o.shipping_address_id = a2.id
            WHERE s.rider_id = %s
            AND s.status IN ('picked_up', 'in_transit', 'out_for_delivery')
            ORDER BY s.created_at DESC
        ''', (rider['id'] if rider else None,))
        active_deliveries = cursor.fetchall()
        
        # Convert Decimal to float for template rendering
        for delivery in active_deliveries:
            if delivery.get('total_amount'):
                delivery['total_amount'] = float(delivery['total_amount'])
        
        # Convert earnings_today to float
        if today_stats.get('earnings_today'):
            today_stats['earnings_today'] = float(today_stats['earnings_today'])
        
        cursor.close()
        conn.close()
        
        return render_template('pages/RiderDashboard.html',
                             rider_name=user['first_name'],
                             rider=rider,
                             user=user,
                             deliveries_today=today_stats['deliveries_today'],
                             earnings_today=today_stats['earnings_today'],
                             rating=rating,
                             acceptance_rate=acceptance_rate,
                             total_deliveries=total_deliveries,
                             recent_deliveries=recent_deliveries,
                             active_deliveries=active_deliveries)
        
    except Exception as err:
        flash(f'Error: {str(err)}', 'error')
        return redirect(url_for('login'))

@app.route('/seller/products', methods=['GET'])
def seller_products():
    if not session.get('logged_in') or session.get('role') != 'seller':
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        user_id = session.get('user_id')
        
        # Get seller ID
        cursor.execute('SELECT id FROM sellers WHERE user_id = %s', (user_id,))
        seller = cursor.fetchone()
        
        if not seller:
            return jsonify({'error': 'Seller not found'}), 404
        
        seller_id = seller['id']
        
        # First, check if products exist for this seller
        cursor.execute('SELECT COUNT(*) as total FROM products WHERE seller_id = %s', (seller_id,))
        count_result = cursor.fetchone()
        total_count = count_result['total'] if count_result else 0
        
        # Get all products for this seller with edit status (excluding archived)
        cursor.execute('''
            SELECT p.id, p.name, p.description, p.price, p.sku, p.brand,
                   p.is_active, p.seller_id, p.created_at,
                   c.name as category_name,
                   COALESCE(SUM(pv.stock_quantity), 0) as stock,
                   'active' as archive_status
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN product_variants pv ON p.id = pv.product_id
            WHERE p.seller_id = %s AND p.is_active = TRUE
            GROUP BY p.id, p.name, p.description, p.price, p.sku, p.brand,
                     p.is_active, p.seller_id, p.created_at, c.name
            ORDER BY p.created_at DESC
        ''', (seller_id,))
        products = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Debug logging
        print(f"DEBUG: User {user_id}, Seller {seller_id}, Total products in DB: {total_count}, Returned: {len(products) if products else 0}")
        
        return jsonify({'products': products if products else [], 'debug': {'seller_id': seller_id, 'total_count': total_count}}), 200
        
    except Exception as err:
        print(f"ERROR in seller_products: {str(err)}")
        return jsonify({'error': str(err)}), 500

# ============ INVENTORY MANAGEMENT ============
@app.route('/seller/inventory', methods=['GET'])
def seller_inventory():
    """Get inventory for seller's products"""
    if not session.get('logged_in') or session.get('role') != 'seller':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        user_id = session.get('user_id')
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get seller ID
        cursor.execute('SELECT id FROM sellers WHERE user_id = %s', (user_id,))
        seller = cursor.fetchone()
        if not seller:
            return jsonify({'success': False, 'error': 'Seller not found'}), 404
        
        # Get inventory for all seller's products with images and variants
        cursor.execute('''
            SELECT 
                i.id,
                i.product_id,
                i.variant_id,
                i.stock_quantity,
                i.reserved_quantity,
                i.available_quantity,
                i.low_stock_threshold,
                p.name as product_name,
                p.sku,
                p.price,
                pv.id as variant_id_full,
                pv.size,
                pv.color,
                pi.image_url
            FROM inventory i
            JOIN products p ON i.product_id = p.id
            LEFT JOIN product_variants pv ON i.variant_id = pv.id
            LEFT JOIN (
                SELECT product_id, image_url FROM product_images 
                WHERE is_primary = TRUE OR (is_primary IS NULL)
                GROUP BY product_id
                LIMIT 1
            ) pi ON p.id = pi.product_id
            WHERE p.seller_id = %s
            ORDER BY p.name, pv.size, pv.color
        ''', (seller['id'],))
        
        inventory = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'inventory': inventory or []}), 200
    except Exception as err:
        return jsonify({'success': False, 'error': str(err)}), 500

# ============ REVIEWS MANAGEMENT ============
@app.route('/seller/reviews', methods=['GET'])
def seller_reviews():
    """Get reviews for seller's products"""
    if not session.get('logged_in') or session.get('role') != 'seller':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        user_id = session.get('user_id')
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get seller ID
        cursor.execute('SELECT id FROM sellers WHERE user_id = %s', (user_id,))
        seller = cursor.fetchone()
        if not seller:
            return jsonify({'success': False, 'error': 'Seller not found'}), 404
        
        # Get reviews for seller's products
        cursor.execute('''
            SELECT 
                r.id,
                r.product_id,
                r.rating,
                r.title,
                r.comment,
                r.is_approved,
                r.created_at,
                p.name as product_name,
                u.first_name,
                u.last_name,
                CONCAT(u.first_name, ' ', u.last_name) as buyer_name
            FROM reviews r
            JOIN products p ON r.product_id = p.id
            JOIN users u ON r.user_id = u.id
            WHERE p.seller_id = %s
            ORDER BY r.created_at DESC
        ''', (seller['id'],))
        
        reviews = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'reviews': reviews or []}), 200
    except Exception as err:
        return jsonify({'success': False, 'error': str(err)}), 500

@app.route('/seller/review/<int:review_id>/approve', methods=['POST'])
def approve_review(review_id):
    """Approve a review"""
    if not session.get('logged_in') or session.get('role') != 'seller':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('UPDATE reviews SET is_approved = TRUE WHERE id = %s', (review_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Review approved'}), 200
    except Exception as err:
        return jsonify({'success': False, 'error': str(err)}), 500

@app.route('/seller/review/<int:review_id>/reject', methods=['POST'])
def reject_review(review_id):
    """Reject a review"""
    if not session.get('logged_in') or session.get('role') != 'seller':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('DELETE FROM reviews WHERE id = %s', (review_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Review rejected'}), 200
    except Exception as err:
        return jsonify({'success': False, 'error': str(err)}), 500

@app.route('/seller/restock', methods=['POST'])
def seller_restock():
    """Update inventory for a product or variant"""
    if not session.get('logged_in') or session.get('role') != 'seller':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        product_id = request.form.get('product_id')
        variant_id = request.form.get('variant_id')
        quantity = int(request.form.get('quantity', 0))
        
        if quantity <= 0:
            return jsonify({'success': False, 'error': 'Quantity must be greater than 0'}), 400
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Verify seller owns this product
        cursor.execute('''
            SELECT id FROM products p
            JOIN sellers s ON p.seller_id = s.id
            WHERE p.id = %s AND s.user_id = %s
        ''', (product_id, session.get('user_id')))
        
        product = cursor.fetchone()
        if not product:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        # Get or create inventory record
        cursor.execute('''
            SELECT id, stock_quantity FROM inventory
            WHERE product_id = %s AND (variant_id = %s OR (variant_id IS NULL AND %s IS NULL))
        ''', (product_id, variant_id, variant_id))
        
        inventory = cursor.fetchone()
        
        if inventory:
            # Update existing inventory
            new_stock = inventory['stock_quantity'] + quantity
            cursor.execute('''
                UPDATE inventory 
                SET stock_quantity = stock_quantity + %s,
                    available_quantity = available_quantity + %s,
                    last_restocked_at = NOW()
                WHERE id = %s
            ''', (quantity, quantity, inventory['id']))
        else:
            # Create new inventory record
            cursor.execute('''
                INSERT INTO inventory (product_id, variant_id, stock_quantity, available_quantity, low_stock_threshold, last_restocked_at)
                VALUES (%s, %s, %s, %s, 10, NOW())
            ''', (product_id, variant_id, quantity, quantity))
            new_stock = quantity
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': f'Restocked with {quantity} units', 'new_stock': new_stock}), 200
    except Exception as err:
        return jsonify({'success': False, 'error': str(err)}), 500

@app.route('/seller/variant/<int:variant_id>', methods=['GET'])
def get_variant_details(variant_id):
    """Get variant details including size and color"""
    if not session.get('logged_in') or session.get('role') != 'seller':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get variant details with product and inventory info
        cursor.execute('''
            SELECT 
                pv.id,
                pv.size,
                pv.color,
                p.name as product_name,
                i.stock_quantity,
                i.reserved_quantity,
                i.available_quantity,
                i.low_stock_threshold
            FROM product_variants pv
            JOIN products p ON pv.product_id = p.id
            JOIN sellers s ON p.seller_id = s.id
            LEFT JOIN inventory i ON pv.id = i.variant_id
            WHERE pv.id = %s AND s.user_id = %s
        ''', (variant_id, session.get('user_id')))
        
        variant = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not variant:
            return jsonify({'success': False, 'error': 'Variant not found'}), 404
        
        return jsonify({'success': True, 'variant': variant}), 200
    except Exception as err:
        return jsonify({'success': False, 'error': str(err)}), 500

# ============ PROMOTIONS MANAGEMENT ============
@app.route('/seller/promotions', methods=['GET'])
def seller_promotions():
    """Get active promotions for seller's products"""
    if not session.get('logged_in') or session.get('role') != 'seller':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        user_id = session.get('user_id')
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get seller ID
        cursor.execute('SELECT id FROM sellers WHERE user_id = %s', (user_id,))
        seller = cursor.fetchone()
        if not seller:
            return jsonify({'success': False, 'error': 'Seller not found'}), 404
        
        # Get promotions for seller's products
        cursor.execute('''
            SELECT 
                c.id,
                c.product_id,
                c.discount_type,
                c.discount_value,
                c.start_date,
                c.end_date,
                c.description,
                c.is_approved,
                c.is_active,
                p.name as product_name,
                p.price
            FROM promotions c
            JOIN products p ON c.product_id = p.id
            WHERE p.seller_id = %s
            ORDER BY c.created_at DESC
        ''', (seller['id'],))
        
        promotions = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'promotions': promotions or []}), 200
    except Exception as err:
        return jsonify({'success': False, 'error': str(err)}), 500

# ============ EMAIL HELPER FUNCTION ============
def send_email(to_email, subject, html_body):
    """Send email notification (using simple SMTP or print for development)"""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # For development, just log the email
        # In production, configure SMTP settings from environment
        smtp_server = os.getenv('SMTP_SERVER', 'localhost')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        sender_email = os.getenv('SENDER_EMAIL', 'noreply@varon.com')
        sender_password = os.getenv('SENDER_PASSWORD', '')
        
        # If no real SMTP configured, just log it
        if not sender_email or sender_email == 'noreply@varon.com':
            print(f"[📧 EMAIL LOG] To: {to_email}")
            print(f"[📧 EMAIL LOG] Subject: {subject}")
            print(f"[📧 EMAIL LOG] Body: {html_body[:200]}...")
            return True
        
        # Send real email
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = sender_email
        message['To'] = to_email
        
        part = MIMEText(html_body, 'html')
        message.attach(part)
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if sender_password:
                server.starttls()
                server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, message.as_string())
        
        return True
    except Exception as e:
        print(f"[⚠️] Email send error: {e}")
        return False

@app.route('/seller/promotion/create', methods=['POST'])
def create_promotion():
    """Create a new promotion and notify interested buyers"""
    if not session.get('logged_in') or session.get('role') != 'seller':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        user_id = session.get('user_id')
        product_id = request.form.get('product_id')
        discount_type = request.form.get('discount_type')
        discount_value = request.form.get('discount_value')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        description = request.form.get('description', '')
        
        # Debug logging
        print(f"[PROMO CREATE] Received data:")
        print(f"  product_id: {product_id}")
        print(f"  discount_type: {discount_type}")
        print(f"  discount_value: {discount_value}")
        print(f"  start_date: {start_date}")
        print(f"  end_date: {end_date}")
        print(f"  description: {description}")
        
        # Validate required fields
        if not product_id or not discount_type or not discount_value or not start_date or not end_date:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        try:
            discount_value = float(discount_value)
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid discount value'}), 400
        
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        # Get seller ID and verify ownership
        cursor.execute('SELECT id FROM sellers WHERE user_id = %s', (user_id,))
        seller = cursor.fetchone()
        if not seller:
            return jsonify({'success': False, 'error': 'Seller not found'}), 404
        
        # Verify seller owns this product and get product details
        cursor.execute('SELECT id, name, price, brand FROM products WHERE id = %s AND seller_id = %s', (product_id, seller['id']))
        product = cursor.fetchone()
        if not product:
            return jsonify({'success': False, 'error': 'Product not found or not owned by seller'}), 404
        
        # Calculate discounted price
        discounted_price = product['price']
        discount_display = f"{discount_value}%"
        if discount_type == 'percentage':
            discounted_price = float(product['price']) * (1 - discount_value / 100)
        else:
            discounted_price = float(product['price']) - discount_value
            discount_display = f"₱{discount_value}"
        
        # Convert datetime-local format (2025-11-25T14:30) to separate date/time
        # Extract just the date part if it contains time
        if 'T' in start_date:
            start_date = start_date.split('T')[0]
        if 'T' in end_date:
            end_date = end_date.split('T')[0]
        
        # Generate auto promotion code: BRAND_PRODUCTID_TIMESTAMP
        brand = (product['brand'] or 'BRAND').upper().replace(' ', '')
        promo_code = f"{brand}_{product_id}_{int(time.time())}"
        print(f"[PROMO CREATE] Inserting promotion with code: {promo_code}")
        
        cursor.execute('''
            INSERT INTO promotions (
                code, product_id, discount_type, discount_value, 
                start_date, end_date, description, is_active, is_approved, created_at,
                min_purchase, usage_limit
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE, FALSE, NOW(), 0, 999999)
        ''', (
            promo_code,
            product_id,
            discount_type,
            discount_value,
            start_date,
            end_date,
            description
        ))
        
        conn.commit()
        promotion_id = cursor.lastrowid
        print(f"[PROMO CREATE] Promotion created with ID: {promotion_id}")
        
        # Get buyers who have purchased this product (for email notification)
        cursor.execute('''
            SELECT DISTINCT u.email, u.first_name
            FROM users u
            JOIN order_items oi ON u.id = oi.user_id
            WHERE oi.product_id = %s AND u.email IS NOT NULL
            LIMIT 100
        ''', (product_id,))
        
        buyers = cursor.fetchall()
        emails_sent = 0
        
        print(f"[PROMO CREATE] Found {len(buyers)} buyers to notify")
        
        # Send email notifications to buyers
        if buyers:
            for buyer in buyers:
                try:
                    email_subject = f"🎉 Special Discount on {product['name']}!"
                    email_body = f"""
                    <html>
                        <body style="font-family: Arial, sans-serif; color: #333;">
                            <h2 style="color: #10b981;">🎉 Great News, {buyer['first_name']}!</h2>
                            <p>We have a special promotion on a product you've purchased before:</p>
                            
                            <div style="background: #f0fdf4; border-left: 4px solid #10b981; padding: 16px; margin: 20px 0;">
                                <h3 style="margin: 0; color: #0a0a0a;">{product['name']}</h3>
                                <p style="margin: 8px 0;">
                                    <strong>Original Price:</strong> <span style="text-decoration: line-through;">₱{float(product['price']):.2f}</span>
                                </p>
                                <p style="margin: 8px 0; font-size: 18px;">
                                    <strong style="color: #10b981;">Discount Price: ₱{discounted_price:.2f}</strong>
                                </p>
                                <p style="margin: 8px 0; color: #f59e0b;">
                                    <strong>Save: {discount_display}</strong>
                                </p>
                                {f'<p style="color: #666; font-size: 14px;">{description}</p>' if description else ''}
                            </div>
                            
                            <p>This promotion is valid from {start_date} to {end_date}.</p>
                            <p style="margin-top: 20px; color: #666; font-size: 12px;">Use promo code: <strong>{promo_code}</strong></p>
                        </body>
                    </html>
                    """
                    
                    if send_email(buyer['email'], email_subject, email_body):
                        emails_sent += 1
                except Exception as email_err:
                    print(f"[PROMO CREATE] Error sending email to {buyer['email']}: {email_err}")
        
        cursor.close()
        conn.close()
        
        print(f"[PROMO CREATE] Success! Emails sent: {emails_sent}")
        
        return jsonify({
            'success': True,
            'message': 'Promotion submitted for admin approval',
            'promotion_id': promotion_id,
            'code': promo_code,
            'emails_sent': emails_sent,
            'status': 'pending_approval'
        }), 201
        
    except Exception as err:
        print(f"[PROMO CREATE] Error: {str(err)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(err)}), 500

@app.route('/seller/promotion/<int:promo_id>/delete', methods=['POST'])
def delete_promotion(promo_id):
    """Delete a promotion"""
    if not session.get('logged_in') or session.get('role') != 'seller':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('UPDATE promotions SET is_active = FALSE WHERE id = %s', (promo_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Promotion deleted'}), 200
    except Exception as err:
        return jsonify({'success': False, 'error': str(err)}), 500

@app.route('/admin/pending-promotions', methods=['GET'])
def admin_pending_promotions():
    """Get all pending promotions waiting for admin approval"""
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get pending promotions with product and brand details
        cursor.execute('''
            SELECT 
                p.id,
                p.code,
                p.product_id,
                p.discount_type,
                p.discount_value,
                p.start_date,
                p.end_date,
                p.description,
                p.created_at,
                pr.name as product_name,
                pr.price as product_price,
                pr.brand,
                s.store_name,
                u.first_name,
                u.last_name
            FROM promotions p
            JOIN products pr ON p.product_id = pr.id
            JOIN sellers s ON pr.seller_id = s.id
            JOIN users u ON s.user_id = u.id
            WHERE p.is_approved = FALSE
            ORDER BY p.created_at ASC
        ''')
        
        promotions = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'promotions': promotions,
            'count': len(promotions)
        }), 200
        
    except Exception as err:
        print(f"[ERROR] admin_pending_promotions: {str(err)}")
        return jsonify({'success': False, 'error': str(err)}), 500

@app.route('/admin/promotion/<int:promo_id>/approve', methods=['POST'])
def admin_approve_promotion(promo_id):
    """Admin approves a promotion"""
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get complete promotion details with dates
        cursor.execute('''
            SELECT p.id, p.code, p.product_id, p.discount_type, p.discount_value,
                   p.start_date, p.end_date, p.description,
                   pr.name as product_name, pr.price, s.user_id, s.store_name
            FROM promotions p
            JOIN products pr ON p.product_id = pr.id
            JOIN sellers s ON pr.seller_id = s.id
            WHERE p.id = %s
        ''', (promo_id,))
        
        promo = cursor.fetchone()
        if not promo:
            return jsonify({'success': False, 'error': 'Promotion not found'}), 404
        
        # Get seller email and details
        cursor.execute('SELECT email, first_name, last_name FROM users WHERE id = %s', (promo['user_id'],))
        seller = cursor.fetchone()
        
        # Update promotion to approved
        cursor.execute('''
            UPDATE promotions SET is_approved = TRUE, updated_at = NOW()
            WHERE id = %s
        ''', (promo_id,))
        
        conn.commit()
        
        # Get buyers who viewed or have interest in this product (from cart or reviews)
        cursor.execute('''
            SELECT DISTINCT u.id, u.email, u.first_name
            FROM users u
            LEFT JOIN cart c ON u.id = c.user_id AND c.product_id = %s
            LEFT JOIN reviews r ON u.id = r.user_id AND r.product_id = %s
            WHERE u.role = 'buyer' AND (c.id IS NOT NULL OR r.id IS NOT NULL)
            LIMIT 100
        ''', (promo['product_id'], promo['product_id']))
        
        interested_buyers = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Format dates for display
        start_date = promo['start_date'].strftime('%B %d, %Y') if promo['start_date'] else 'TBD'
        end_date = promo['end_date'].strftime('%B %d, %Y') if promo['end_date'] else 'TBD'
        
        # Calculate discount display
        if promo['discount_type'] == 'percentage':
            discount_text = f"{promo['discount_value']}% OFF"
            discount_color = "#10b981"
        else:
            discount_text = f"₱{promo['discount_value']:.2f} OFF"
            discount_color = "#8b5cf6"
        
        # Send approval email to seller
        if seller and seller.get('email'):
            try:
                email_subject = f"🎉 Your Promotion Has Been Approved! - {promo['product_name']}"
                email_body = f"""
                <html>
                    <body style="font-family: Arial, sans-serif; color: #333;">
                        <h2 style="color: #10b981;">✓ Promotion Approved!</h2>
                        <p>Hi {seller.get('first_name', 'Seller')},</p>
                        <p>Your promotion for <strong>{promo['product_name']}</strong> has been approved by our admin team and is now <strong>ACTIVE</strong>!</p>
                        
                        <div style="background: #f0fdf4; border-left: 4px solid #10b981; padding: 16px; margin: 20px 0; border-radius: 4px;">
                            <p><strong>📦 Product:</strong> {promo['product_name']}</p>
                            <p><strong>💰 Discount:</strong> <span style="color: {discount_color}; font-weight: bold; font-size: 16px;">{discount_text}</span></p>
                            <p><strong>🎟️ Promo Code:</strong> <span style="background: #e0e7ff; padding: 4px 8px; font-family: monospace; font-weight: bold;">{promo['code']}</span></p>
                            <p><strong>📅 Valid From:</strong> {start_date}</p>
                            <p><strong>📅 Valid Until:</strong> {end_date}</p>
                        </div>
                        
                        <p>Your promotion is now <strong>live and visible to customers</strong> on the product page. Buyers can use the promo code to get the discount at checkout.</p>
                        <p style="color: #666; font-size: 14px; margin-top: 20px;">Store: {promo['store_name']}</p>
                        <p>Thank you for using Varón!</p>
                    </body>
                </html>
                """
                send_email(seller['email'], email_subject, email_body)
                print(f"[PROMO APPROVE] Seller approval email sent to {seller['email']}")
            except Exception as email_err:
                print(f"[PROMO APPROVE] Error sending seller email: {email_err}")
        
        # Send discount notification emails to interested buyers
        if interested_buyers:
            for buyer in interested_buyers:
                if buyer.get('email'):
                    try:
                        email_subject = f"🤑 Special Discount on {promo['product_name']}!"
                        email_body = f"""
                        <html>
                            <body style="font-family: Arial, sans-serif; color: #333;">
                                <h2 style="color: #8b5cf6;">Great News! There's a New Discount!</h2>
                                <p>Hi {buyer.get('first_name', 'Valued Customer')},</p>
                                <p>A product you've shown interest in has a <strong>special promotion</strong> now available!</p>
                                
                                <div style="background: #faf5ff; border-left: 4px solid #8b5cf6; padding: 16px; margin: 20px 0; border-radius: 4px;">
                                    <p style="margin: 0; font-size: 18px; font-weight: bold; color: #333;"><strong>📦 {promo['product_name']}</strong></p>
                                    <p style="margin: 8px 0; font-size: 14px; color: #666;">Original Price: <strong>₱{promo['price']:.2f}</strong></p>
                                    <p style="margin: 8px 0; font-size: 20px; color: {discount_color}; font-weight: bold;">Get <strong>{discount_text}</strong>!</p>
                                    <p style="margin: 12px 0; background: #fff; padding: 8px 12px; border-radius: 4px; font-family: monospace; font-weight: bold; display: inline-block;">Use Code: <span style="color: #8b5cf6;">{promo['code']}</span></p>
                                </div>
                                
                                <div style="background: #fffbeb; border-left: 4px solid #f59e0b; padding: 12px 16px; margin: 16px 0; border-radius: 4px;">
                                    <p style="margin: 0;"><strong>⏰ Limited Time Offer!</strong></p>
                                    <p style="margin: 4px 0; font-size: 14px;">Valid: <strong>{start_date} to {end_date}</strong></p>
                                </div>
                                
                                <p><strong>How to use:</strong></p>
                                <ol>
                                    <li>Go to the product page</li>
                                    <li>Add the item to your cart</li>
                                    <li>Enter the code at checkout: <span style="background: #e0e7ff; padding: 2px 6px; font-family: monospace; font-weight: bold;">{promo['code']}</span></li>
                                    <li>Enjoy your discount! 🎉</li>
                                </ol>
                                
                                <p style="color: #666; font-size: 12px; margin-top: 20px;">Happy shopping!</p>
                            </body>
                        </html>
                        """
                        send_email(buyer['email'], email_subject, email_body)
                        print(f"[PROMO APPROVE] Buyer notification sent to {buyer['email']}")
                    except Exception as email_err:
                        print(f"[PROMO APPROVE] Error sending buyer email: {email_err}")
        
        return jsonify({
            'success': True,
            'message': f'Promotion approved successfully! Emails sent to seller and {len(interested_buyers)} interested buyers.'
        }), 200
        
    except Exception as err:
        print(f"[ERROR] admin_approve_promotion: {str(err)}")
        return jsonify({'success': False, 'error': str(err)}), 500

@app.route('/admin/promotion/<int:promo_id>/reject', methods=['POST'])
def admin_reject_promotion(promo_id):
    """Admin rejects a promotion"""
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        data = request.get_json() or {}
        reason = data.get('reason', 'No reason provided')
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get promotion and seller email
        cursor.execute('''
            SELECT p.id, p.code, pr.name as product_name, s.user_id
            FROM promotions p
            JOIN products pr ON p.product_id = pr.id
            JOIN sellers s ON pr.seller_id = s.id
            WHERE p.id = %s
        ''', (promo_id,))
        
        promo = cursor.fetchone()
        if not promo:
            return jsonify({'success': False, 'error': 'Promotion not found'}), 404
        
        # Get seller email
        cursor.execute('SELECT email, first_name FROM users WHERE id = %s', (promo['user_id'],))
        seller = cursor.fetchone()
        
        # Delete the promotion
        cursor.execute('DELETE FROM promotions WHERE id = %s', (promo_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        # Send rejection email to seller
        if seller and seller.get('email'):
            try:
                email_subject = f"Promotion Rejected: {promo['product_name']}"
                email_body = f"""
                <html>
                    <body style="font-family: Arial, sans-serif; color: #333;">
                        <h2 style="color: #ef4444;">Promotion Rejected</h2>
                        <p>Hi {seller.get('first_name', 'Seller')},</p>
                        <p>Your promotion has been rejected.</p>
                        
                        <div style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 16px; margin: 20px 0;">
                            <p><strong>Product:</strong> {promo['product_name']}</p>
                            <p><strong>Reason:</strong> {reason}</p>
                        </div>
                        
                        <p>Please review the reason and feel free to submit another promotion if needed.</p>
                        <p>Thank you!</p>
                    </body>
                </html>
                """
                send_email(seller['email'], email_subject, email_body)
                print(f"[PROMO REJECT] Rejection email sent to {seller['email']}")
            except Exception as email_err:
                print(f"[PROMO REJECT] Error sending email: {email_err}")
        
        return jsonify({
            'success': True,
            'message': 'Promotion rejected successfully'
        }), 200
        
    except Exception as err:
        print(f"[ERROR] admin_reject_promotion: {str(err)}")
        return jsonify({'success': False, 'error': str(err)}), 500

@app.route('/seller/sales-analytics', methods=['GET'])
def seller_sales_analytics():
    """Get sales analytics for seller - revenue, orders, and top products (last 30 days)"""
    if not session.get('logged_in') or session.get('role') != 'seller':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        user_id = session.get('user_id')
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get seller ID
        cursor.execute('SELECT id FROM sellers WHERE user_id = %s', (user_id,))
        seller = cursor.fetchone()
        if not seller:
            return jsonify({'success': False, 'error': 'Seller not found'}), 404
        
        # Get overall sales metrics for last 30 days
        cursor.execute('''
            SELECT 
                COALESCE(SUM(o.total_amount), 0) as total_revenue,
                COUNT(DISTINCT o.id) as total_orders,
                COALESCE(AVG(o.total_amount), 0) as avg_order_value
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN products p ON oi.product_id = p.id
            WHERE p.seller_id = %s 
            AND o.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            AND o.order_status NOT IN ('cancelled', 'failed')
        ''', (seller['id'],))
        
        analytics = cursor.fetchone()
        
        # Get top 10 products by sales (last 30 days)
        cursor.execute('''
            SELECT 
                p.id,
                p.name as product_name,
                SUM(oi.quantity) as quantity_sold,
                COALESCE(SUM(oi.quantity * oi.unit_price), 0) as product_revenue
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            JOIN orders o ON oi.order_id = o.id
            WHERE p.seller_id = %s 
            AND o.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            AND o.order_status NOT IN ('cancelled', 'failed')
            GROUP BY p.id, p.name
            ORDER BY quantity_sold DESC
            LIMIT 10
        ''', (seller['id'],))
        
        top_products = cursor.fetchall()
        
        # Convert Decimal to float for top products
        for product in top_products:
            if product.get('product_revenue'):
                product['product_revenue'] = float(product['product_revenue'])
            if product.get('quantity_sold'):
                product['quantity_sold'] = int(product['quantity_sold'])
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'analytics': {
                'total_revenue': float(analytics['total_revenue']) if analytics else 0,
                'total_orders': int(analytics['total_orders']) if analytics else 0,
                'avg_order_value': float(analytics['avg_order_value']) if analytics else 0,
                'top_products': top_products or []
            }
        }), 200
    except Exception as err:
        return jsonify({'success': False, 'error': str(err)}), 500

@app.route('/seller/performance', methods=['GET'])
def seller_performance():
    """Get seller performance metrics - ratings, repeat customers, reviews"""
    if not session.get('logged_in') or session.get('role') != 'seller':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        user_id = session.get('user_id')
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get seller ID
        cursor.execute('SELECT id FROM sellers WHERE user_id = %s', (user_id,))
        seller = cursor.fetchone()
        if not seller:
            return jsonify({'success': False, 'error': 'Seller not found'}), 404
        
        # Get average rating and total reviews
        cursor.execute('''
            SELECT 
                COALESCE(AVG(r.rating), 0) as avg_rating,
                COUNT(r.id) as total_reviews
            FROM reviews r
            JOIN products p ON r.product_id = p.id
            WHERE p.seller_id = %s
        ''', (seller['id'],))
        
        rating_data = cursor.fetchone()
        
        # Get repeat customers count
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) as repeat_customers
            FROM (
                SELECT o.user_id, COUNT(DISTINCT o.id) as order_count
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                JOIN products p ON oi.product_id = p.id
                WHERE p.seller_id = %s AND o.order_status NOT IN ('cancelled', 'failed')
                GROUP BY o.user_id
                HAVING order_count > 1
            ) repeat_stats
        ''', (seller['id'],))
        
        repeat_data = cursor.fetchone()
        
        # Get top rated products
        cursor.execute('''
            SELECT 
                p.id,
                p.name as product_name,
                COALESCE(AVG(r.rating), 0) as avg_rating,
                COUNT(r.id) as review_count
            FROM products p
            LEFT JOIN reviews r ON p.id = r.product_id
            WHERE p.seller_id = %s
            GROUP BY p.id, p.name
            HAVING review_count > 0
            ORDER BY avg_rating DESC, review_count DESC
            LIMIT 10
        ''', (seller['id'],))
        
        top_rated = cursor.fetchall()
        
        # Convert Decimal to float for top_rated
        for product in top_rated:
            if product.get('avg_rating'):
                product['avg_rating'] = float(product['avg_rating'])
            if product.get('review_count'):
                product['review_count'] = int(product['review_count'])
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'performance': {
                'avg_rating': float(rating_data['avg_rating']) if rating_data else 0,
                'total_reviews': int(rating_data['total_reviews']) if rating_data else 0,
                'repeat_customers': int(repeat_data['repeat_customers']) if repeat_data else 0,
                'top_rated_products': top_rated or []
            }
        }), 200
    except Exception as err:
        return jsonify({'success': False, 'error': str(err)}), 500

@app.route('/seller/brand-settings', methods=['GET', 'POST'])
def seller_brand_settings():
    """Get or update seller brand settings"""
    if not session.get('logged_in') or session.get('role') != 'seller':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        user_id = session.get('user_id')
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get seller ID
        cursor.execute('SELECT id FROM sellers WHERE user_id = %s', (user_id,))
        seller = cursor.fetchone()
        if not seller:
            return jsonify({'success': False, 'error': 'Seller not found'}), 404
        
        if request.method == 'GET':
            # Fetch current brand settings
            cursor.execute('''
                SELECT store_name, description, contact_email, contact_phone, address, island_group
                FROM sellers
                WHERE id = %s
            ''', (seller['id'],))
            
            settings = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'settings': settings or {
                    'store_name': '',
                    'description': '',
                    'contact_email': '',
                    'contact_phone': '',
                    'address': '',
                    'island_group': 'Luzon'
                }
            }), 200
        
        else:  # POST - Update brand settings
            store_name = request.form.get('store_name', '').strip()
            description = request.form.get('description', '').strip()
            contact_email = request.form.get('contact_email', '').strip()
            contact_phone = request.form.get('contact_phone', '').strip()
            address = request.form.get('address', '').strip()
            island_group = request.form.get('island_group', 'Luzon').strip()
            
            # Validate island_group
            if island_group not in ['Luzon', 'Visayas', 'Mindanao']:
                island_group = 'Luzon'
            
            # Update seller record
            cursor.execute('''
                UPDATE sellers
                SET store_name = %s,
                    description = %s,
                    contact_email = %s,
                    contact_phone = %s,
                    address = %s,
                    island_group = %s
                WHERE id = %s
            ''', (store_name, description, contact_email, contact_phone, address, island_group, seller['id']))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Brand settings updated'}), 200
    
    except Exception as err:
        return jsonify({'success': False, 'error': str(err)}), 500

@app.route('/seller/account-settings', methods=['GET', 'POST'])
def seller_account_settings():
    """Get or update seller account settings"""
    print(f"[DEBUG] seller_account_settings called - Role: {session.get('role')}, Logged in: {session.get('logged_in')}")
    
    if not session.get('logged_in') or session.get('role') != 'seller':
        print(f"[DEBUG] Access denied - Role: {session.get('role')}, Logged in: {session.get('logged_in')}")
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        user_id = session.get('user_id')
        print(f"[DEBUG] User ID: {user_id}")
        
        conn = get_db()
        if not conn:
            print("[DEBUG] Database connection failed")
            return jsonify({'success': False, 'error': 'Database connection error'}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        # Get user info
        query = '''
            SELECT id, first_name, last_name, email, password, phone
            FROM users
            WHERE id = %s
        '''
        print(f"[DEBUG] Executing query: {query}")
        cursor.execute(query, (user_id,))
        
        user = cursor.fetchone()
        print(f"[DEBUG] User fetched: {user is not None}, User data: {user}")
        
        if not user:
            cursor.close()
            conn.close()
            print("[DEBUG] User not found in database")
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        if request.method == 'GET':
            # Return current account settings
            cursor.close()
            conn.close()
            
            full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
            response_data = {
                'success': True,
                'account': {
                    'username': f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                    'email': user.get('email', ''),
                    'full_name': full_name,
                    'phone_number': user.get('phone', '') or ''
                }
            }
            print(f"[DEBUG] Returning account settings: {response_data}")
            return jsonify(response_data), 200
        
        else:  # POST - Update account settings
            from werkzeug.security import check_password_hash, generate_password_hash
            
            full_name = request.form.get('full_name', '').strip()
            phone_number = request.form.get('phone_number', '').strip()
            new_email = request.form.get('email', '').strip()
            
            print(f"[DEBUG] Updating - full_name: {full_name}, phone: {phone_number}, email: {new_email}")
            
            # Split full name into first and last
            name_parts = full_name.split(' ', 1)
            first_name = name_parts[0] if len(name_parts) > 0 else ''
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            # If email is being changed, verify it's unique
            if new_email and new_email != user['email']:
                cursor.execute('SELECT id FROM users WHERE email = %s AND id != %s', (new_email, user_id))
                if cursor.fetchone():
                    cursor.close()
                    conn.close()
                    print(f"[DEBUG] Email already in use: {new_email}")
                    return jsonify({'success': False, 'error': 'Email already in use'}), 400
                
                # Update email
                cursor.execute('UPDATE users SET email = %s WHERE id = %s', (new_email, user_id))
                print(f"[DEBUG] Email updated to {new_email}")
            
            # Update user profile
            cursor.execute('''
                UPDATE users
                SET first_name = %s, last_name = %s, phone = %s
                WHERE id = %s
            ''', (first_name, last_name, phone_number, user_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print("[DEBUG] Account settings saved successfully")
            return jsonify({'success': True, 'message': 'Account settings updated'}), 200
    
    except Exception as err:
        print(f"[ERROR] seller_account_settings: {str(err)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(err)}), 500

@app.route('/seller/add-product', methods=['POST'])
def seller_add_product():
    if not session.get('logged_in') or session.get('role') != 'seller':
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        user_id = session.get('user_id')
        
        # Get seller ID and store name
        cursor.execute('SELECT id, store_name FROM sellers WHERE user_id = %s', (user_id,))
        seller = cursor.fetchone()
        
        if not seller:
            return jsonify({'error': 'Seller profile not found'}), 404
        
        # Get form data
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        price = request.form.get('price', '0')
        category_id = request.form.get('category_id', '').strip()
        brand = seller['store_name']  # Auto-fill brand from seller's store name
        sku = request.form.get('sku', '').strip()
        
        # If SKU is empty, generate a unique one
        if not sku:
            import time
            sku = f"SKU-{seller['id']}-{int(time.time() * 1000)}"
        
        # Validate required fields
        if not name:
            return jsonify({'error': 'Product name is required'}), 400
        if not price or float(price) <= 0:
            return jsonify({'error': 'Valid price is required'}), 400
        if not category_id:
            return jsonify({'error': 'Category is required'}), 400
        
        # Get category info to check if it's grooming
        cursor.execute('SELECT id, slug, name FROM categories WHERE id = %s AND is_active = TRUE', (category_id,))
        category = cursor.fetchone()
        if not category:
            return jsonify({'error': 'Invalid category selected'}), 400
        
        category_slug = category['slug']
        category_name = category['name']
        
        # Get sizes and colors
        sizes = request.form.getlist('sizes')
        colors = request.form.getlist('colors')
        
        # Add custom sizes if provided
        custom_sizes = request.form.get('custom-sizes', '').strip()
        print(f"[DEBUG] Custom sizes received: '{custom_sizes}'")
        if custom_sizes:
            custom_size_list = [s.strip() for s in custom_sizes.split(',') if s.strip()]
            sizes.extend(custom_size_list)
            print(f"[DEBUG] Custom sizes added: {custom_size_list}")
        
        # Add custom colors if provided
        custom_colors = request.form.get('custom-colors', '').strip()
        print(f"[DEBUG] Custom colors received: '{custom_colors}'")
        if custom_colors:
            custom_color_list = [c.strip() for c in custom_colors.split(',') if c.strip()]
            colors.extend(custom_color_list)
            print(f"[DEBUG] Custom colors added: {custom_color_list}")
        
        print(f"[DEBUG] Final sizes list: {sizes}")
        print(f"[DEBUG] Final colors list: {colors}")
        
        # Debug: Print all form keys that start with 'stock_'
        stock_keys = [key for key in request.form.keys() if key.startswith('stock_')]
        print(f"[DEBUG] Stock form keys received: {stock_keys}")
        
        # Validate sizes and colors for non-grooming products
        # Check if category slug contains 'grooming' or check category name
        is_grooming = 'grooming' in category_slug.lower() or 'grooming' in category_name.lower()
        
        if not is_grooming:
            if not sizes:
                return jsonify({'error': 'Please select at least one size'}), 400
            if not colors:
                return jsonify({'error': 'Please select at least one color'}), 400
        
        # Handle ingredients for grooming products
        ingredients = ''
        if is_grooming:
            ingredients = request.form.get('ingredients', '').strip()
            if not ingredients:
                return jsonify({'error': 'Ingredients are required for grooming products'}), 400
        
        # Handle multiple image uploads
        uploaded_images = []
        if 'product_images' in request.files:
            files = request.files.getlist('product_images')
            
            if not files or len(files) == 0:
                return jsonify({'error': 'At least one product image is required'}), 400
            
            if files and len(files) > 0:
                import os
                from werkzeug.utils import secure_filename
                import time
                
                # Create uploads directory if it doesn't exist
                upload_folder = os.path.join('static', 'images', 'products')
                os.makedirs(upload_folder, exist_ok=True)
                
                for file in files:
                    if file and file.filename:
                        # Validate file
                        if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.avif', '.webp')):
                            return jsonify({'error': 'Only image files (JPG, PNG, AVIF, WebP) are allowed'}), 400
                        
                        # Generate unique filename with timestamp
                        filename = secure_filename(file.filename)
                        timestamp = int(time.time() * 1000)  # milliseconds for uniqueness
                        unique_filename = f"{seller['id']}_{timestamp}_{filename}"
                        filepath = os.path.join(upload_folder, unique_filename)
                        file.save(filepath)
                        
                        # Store relative URL
                        image_url = f"/static/images/products/{unique_filename}"
                        uploaded_images.append(image_url)
        else:
            return jsonify({'error': 'At least one product image is required'}), 400
        
        # Create slug from name
        slug = name.lower().replace(' ', '-').replace('&', 'and').replace("'", '')
        
        # Insert product with is_active = 0 (pending approval)
        cursor.execute('''
            INSERT INTO products (seller_id, category_id, name, slug, description, brand, 
                                price, sku, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0)
        ''', (seller['id'], category_id, name, slug, description, brand, price, sku))
        
        product_id = cursor.lastrowid
        
        # Add product images if uploaded
        if uploaded_images:
            for idx, image_url in enumerate(uploaded_images):
                # First image is primary
                is_primary = 1 if idx == 0 else 0
                cursor.execute('''
                    INSERT INTO product_images (product_id, image_url, is_primary)
                    VALUES (%s, %s, %s)
                ''', (product_id, image_url, is_primary))
        
        # Calculate total stock from size-color combinations
        total_stock = 0
        
        # Add size and color variants with individual stock (skip for grooming)
        if category_name != 'grooming':
            import re
            for size in sizes:
                for color in colors:
                    # Sanitize size and color to match frontend naming (replace non-alphanumeric with underscore)
                    safe_size = re.sub(r'[^a-zA-Z0-9]', '_', size)
                    safe_color = re.sub(r'[^a-zA-Z0-9]', '_', color)
                    stock_key = f'stock_{safe_size}_{safe_color}'
                    variant_stock = int(request.form.get(stock_key, 0))
                    total_stock += variant_stock
                    
                    print(f"[DEBUG] Processing variant: size='{size}', color='{color}', stock_key='{stock_key}', stock={variant_stock}")
                    
                    # Insert product variant
                    cursor.execute('''
                        INSERT INTO product_variants (product_id, size, color, stock_quantity)
                        VALUES (%s, %s, %s, %s)
                    ''', (product_id, size, color, variant_stock))
        else:
            # For grooming products, store ingredients
            cursor.execute('''
                UPDATE products 
                SET description = CONCAT(description, '\n\nIngredients:\n', %s)
                WHERE id = %s
            ''', (ingredients, product_id))
            total_stock = int(request.form.get('stock_quantity', 0)) if 'stock_quantity' in request.form else 10
        
        # Add total inventory
        cursor.execute('''
            INSERT INTO inventory (product_id, stock_quantity, low_stock_threshold)
            VALUES (%s, %s, 10)
        ''', (product_id, total_stock))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Product submitted for admin approval!', 'product_id': product_id}), 200
        
    except Exception as err:
        print(f"[ERROR] Add product error: {str(err)}")
        return jsonify({'error': f'Error adding product: {str(err)}'}), 500

@app.route('/seller/update-stock', methods=['POST'])
def seller_update_stock():
    if not session.get('logged_in') or session.get('role') != 'seller':
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        user_id = session.get('user_id')
        
        # Get seller ID
        cursor.execute('SELECT id FROM sellers WHERE user_id = %s', (user_id,))
        seller = cursor.fetchone()
        
        if not seller:
            return jsonify({'error': 'Seller not found'}), 404
        
        product_id = request.form.get('product_id')
        stock_quantity = request.form.get('stock_quantity')
        
        # Verify product belongs to seller
        cursor.execute('SELECT id FROM products WHERE id = %s AND seller_id = %s', 
                      (product_id, seller['id']))
        product = cursor.fetchone()
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Update inventory
        cursor.execute('''
            UPDATE inventory 
            SET stock_quantity = %s, last_restocked_at = NOW()
            WHERE product_id = %s
        ''', (stock_quantity, product_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Stock updated successfully'}), 200
        
    except Exception as err:
        return jsonify({'error': str(err)}), 500

@app.route('/seller/archive-product', methods=['POST'])
def seller_archive_product():
    if not session.get('logged_in') or session.get('role') != 'seller':
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        user_id = session.get('user_id')
        
        # Get seller ID
        cursor.execute('SELECT id FROM sellers WHERE user_id = %s', (user_id,))
        seller = cursor.fetchone()
        
        if not seller:
            return jsonify({'error': 'Seller not found'}), 404
        
        product_id = request.form.get('product_id')
        reason = request.form.get('reason', '')
        
        # Verify product belongs to seller
        cursor.execute('SELECT id FROM products WHERE id = %s AND seller_id = %s', 
                      (product_id, seller['id']))
        product = cursor.fetchone()
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Update product archive status
        cursor.execute('''
            UPDATE products 
            SET archive_status = 'archived', archived_at = NOW(), archived_by = %s
            WHERE id = %s
        ''', (user_id, product_id))
        
        # Log the archive request
        cursor.execute('''
            INSERT INTO product_archive_requests 
            (product_id, seller_id, request_type, reason, status)
            VALUES (%s, %s, 'archive', %s, 'approved')
        ''', (product_id, seller['id'], reason))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Product archived successfully'}), 200
        
    except Exception as err:
        if conn:
            conn.rollback()
        return jsonify({'error': str(err)}), 500

@app.route('/seller/archived-products', methods=['GET'])
def seller_archived_products():
    if not session.get('logged_in') or session.get('role') != 'seller':
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        user_id = session.get('user_id')
        
        # Get seller ID
        cursor.execute('SELECT id FROM sellers WHERE user_id = %s', (user_id,))
        seller = cursor.fetchone()
        
        if not seller:
            return jsonify({'error': 'Seller not found'}), 404
        
        # Get archived products
        cursor.execute('''
            SELECT p.*, COALESCE(p.archive_status, 'active') as archive_status
            FROM products p
            WHERE p.seller_id = %s AND p.archive_status IN ('archived', 'pending_recovery')
            ORDER BY p.archived_at DESC
        ''', (seller['id'],))
        products = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({'products': products}), 200
        
    except Exception as err:
        return jsonify({'error': str(err)}), 500

@app.route('/seller/rejected-products', methods=['GET'])
def seller_rejected_products():
    """Get all rejected products for the logged-in seller"""
    if not session.get('logged_in') or session.get('role') != 'seller':
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        user_id = session.get('user_id')
        
        # Get seller ID
        cursor.execute('SELECT id FROM sellers WHERE user_id = %s', (user_id,))
        seller = cursor.fetchone()
        
        if not seller:
            return jsonify({'error': 'Seller not found'}), 404
        
        # Get rejected products with rejection reasons
        cursor.execute('''
            SELECT p.id, p.name, p.description, p.price, p.created_at,
                   p.rejection_reason, p.rejection_status
            FROM products p
            WHERE p.seller_id = %s AND p.rejection_status = 'rejected'
            ORDER BY p.created_at DESC
        ''', (seller['id'],))
        
        rejected_products = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({'products': rejected_products}), 200
        
    except Exception as err:
        print(f"[ERROR] seller_rejected_products: {err}")
        return jsonify({'error': str(err)}), 500

@app.route('/seller/request-recovery', methods=['POST'])
def seller_request_recovery():
    if not session.get('logged_in') or session.get('role') != 'seller':
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        user_id = session.get('user_id')
        
        # Get seller ID
        cursor.execute('SELECT id FROM sellers WHERE user_id = %s', (user_id,))
        seller = cursor.fetchone()
        
        if not seller:
            return jsonify({'error': 'Seller not found'}), 404
        
        product_id = request.form.get('product_id')
        reason = request.form.get('reason', '')
        
        # Verify product belongs to seller and is archived
        cursor.execute('''
            SELECT id FROM products 
            WHERE id = %s AND seller_id = %s AND archive_status = 'archived'
        ''', (product_id, seller['id']))
        product = cursor.fetchone()
        
        if not product:
            return jsonify({'error': 'Product not found or not archived'}), 404
        
        # Update product status to pending recovery
        cursor.execute('''
            UPDATE products 
            SET archive_status = 'pending_recovery'
            WHERE id = %s
        ''', (product_id,))
        
        # Create recovery request
        cursor.execute('''
            INSERT INTO product_archive_requests 
            (product_id, seller_id, request_type, reason, status)
            VALUES (%s, %s, 'recover', %s, 'pending')
        ''', (product_id, seller['id'], reason))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Recovery request submitted'}), 200
        
    except Exception as err:
        if conn:
            conn.rollback()
        return jsonify({'error': str(err)}), 500

@app.route('/seller/product/<int:product_id>', methods=['GET'])
def seller_get_product(product_id):
    if not session.get('logged_in') or session.get('role') != 'seller':
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        user_id = session.get('user_id')
        
        # Get seller ID
        cursor.execute('SELECT id FROM sellers WHERE user_id = %s', (user_id,))
        seller = cursor.fetchone()
        
        if not seller:
            return jsonify({'error': 'Seller not found'}), 404
        
        # Get product details
        cursor.execute('''
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.id = %s AND p.seller_id = %s
        ''', (product_id, seller['id']))
        product = cursor.fetchone()
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Get all categories for the dropdown
        cursor.execute('SELECT id, name FROM categories WHERE is_active = TRUE ORDER BY name')
        categories = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'product': product,
            'categories': categories
        }), 200
        
    except Exception as err:
        return jsonify({'error': str(err)}), 500

@app.route('/seller/edit-product', methods=['POST'])
def seller_edit_product():
    if not session.get('logged_in') or session.get('role') != 'seller':
        return jsonify({'error': 'Access denied'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        user_id = session.get('user_id')
        
        # Get seller ID
        cursor.execute('SELECT id FROM sellers WHERE user_id = %s', (user_id,))
        seller = cursor.fetchone()
        
        if not seller:
            return jsonify({'error': 'Seller not found'}), 404
        
        product_id = request.form.get('product_id')
        
        # Verify product belongs to seller
        cursor.execute('''
            SELECT * FROM products 
            WHERE id = %s AND seller_id = %s
        ''', (product_id, seller['id']))
        product = cursor.fetchone()
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # First, ensure product_edits table exists
        cursor.execute('''
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
                INDEX idx_product (product_id),
                INDEX idx_status (status),
                INDEX idx_seller (seller_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        
        # Check if edit_status column exists, if not add it
        cursor.execute('''
            SELECT COUNT(*) as count 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'products' 
            AND COLUMN_NAME = 'edit_status'
        ''', (DB_CONFIG['database'],))
        
        result = cursor.fetchone()
        if result['count'] == 0:
            cursor.execute('''
                ALTER TABLE products 
                ADD COLUMN edit_status ENUM('none', 'pending', 'approved', 'rejected') DEFAULT 'none'
            ''')
        
        # Track changes
        fields_to_check = {
            'name': 'Product Name',
            'description': 'Description',
            'price': 'Price',
            'brand': 'Brand',
            'category_id': 'Category'
        }
        
        changes_made = False
        
        for field, label in fields_to_check.items():
            new_value = request.form.get(field)
            old_value = str(product[field]) if product[field] is not None else ''
            
            if new_value and new_value != old_value:
                # Insert edit request
                cursor.execute('''
                    INSERT INTO product_edits 
                    (product_id, seller_id, field_name, old_value, new_value, status)
                    VALUES (%s, %s, %s, %s, %s, 'pending')
                ''', (product_id, seller['id'], field, old_value, new_value))
                changes_made = True
        
        if changes_made:
            # Update product edit_status
            cursor.execute('''
                UPDATE products 
                SET edit_status = 'pending'
                WHERE id = %s
            ''', (product_id,))
            
            conn.commit()
        
        cursor.close()
        conn.close()
        
        if not changes_made:
            return jsonify({'success': False, 'error': 'No changes detected'}), 400
        
        return jsonify({
            'success': True,
            'message': 'Product edit submitted for admin approval'
        }), 200
        
    except Exception as err:
        if conn:
            conn.rollback()
        return jsonify({'error': str(err)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/get_buyer_name')
def get_buyer_name():
    """Get the logged-in buyer's account details"""
    try:
        if not session.get('logged_in') or session.get('role') != 'buyer':
            return jsonify({'error': 'Not logged in'}), 401
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        user_id = session.get('user_id')
        cursor.execute('SELECT first_name, last_name, email, phone FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if user:
            return jsonify({
                'firstName': user['first_name'],
                'lastName': user.get('last_name', ''),
                'email': user.get('email', ''),
                'phone': user.get('phone', '')
            }), 200
        else:
            return jsonify({'firstName': 'Guest'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user-profile-navbar')
def api_user_profile_navbar():
    """Get user profile for navbar display (including profile picture)"""
    if not session.get('logged_in') or session.get('role') != 'buyer':
        return jsonify({'success': False, 'message': 'Not logged in'}), 403
    
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        user_id = session.get('user_id')
        
        cursor.execute('SHOW COLUMNS FROM users LIKE "profile_image"')
        has_profile_image = cursor.fetchone()
        
        if has_profile_image:
            cursor.execute('SELECT first_name, last_name, email, profile_image FROM users WHERE id = %s', (user_id,))
        else:
            cursor.execute('SELECT first_name, last_name, email FROM users WHERE id = %s', (user_id,))
        
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            return jsonify({
                'success': True,
                'first_name': user.get('first_name', ''),
                'last_name': user.get('last_name', ''),
                'email': user.get('email', ''),
                'profile_image': user.get('profile_image') if has_profile_image else None
            }), 200
        else:
            return jsonify({'success': False, 'message': 'User not found'}), 404
    except Exception as e:
        print(f"Error fetching navbar profile: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/check-db-schema', methods=['GET'])
def check_db_schema():
    """Check if coupons table has product_id column"""
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'DB connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SHOW COLUMNS FROM coupons LIKE 'product_id'")
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if result:
            return jsonify({
                'success': True,
                'message': 'product_id column exists',
                'column_info': result
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'product_id column NOT found - migration still needed'
            }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/products')
def api_products():
    """Get all active products for browsing with optional search and category filter"""
    try:
        conn = get_db()
        if not conn:
            return jsonify({
                'success': False,
                'error': 'Database connection failed'
            }), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        search = request.args.get('search', '').strip()
        category_id = request.args.get('category_id', type=int)
        
        # Build query with filters
        query = """
            SELECT 
                p.id,
                p.name,
                p.price,
                p.description,
                p.category_id,
                pi.image_url,
                c.name as category_name
            FROM products p
            LEFT JOIN product_images pi ON p.id = pi.product_id AND pi.is_primary = 1
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.is_active = 1
        """
        
        params = []
        
        # Add search filter
        if search:
            query += " AND (p.name LIKE %s OR p.description LIKE %s)"
            search_pattern = f"%{search}%"
            params.extend([search_pattern, search_pattern])
        
        # Add category filter
        if category_id:
            query += " AND p.category_id = %s"
            params.append(category_id)
        
        query += " ORDER BY p.created_at DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, tuple(params))
        products = cursor.fetchall()
        
        # Convert products to proper types for JSON serialization
        products_list = []
        for product in products:
            # Ensure all numeric fields are float/int
            product['price'] = float(product['price']) if product['price'] else 0
            product['id'] = int(product['id'])
            product['category_id'] = int(product['category_id']) if product['category_id'] else None
            products_list.append(product)
        
        # For each product, get available colors and active promotions
        for product in products_list:
            cursor.execute("""
                SELECT DISTINCT color 
                FROM product_variants 
                WHERE product_id = %s AND color IS NOT NULL AND color != '' AND stock_quantity > 0
                ORDER BY color
            """, (product['id'],))
            colors = cursor.fetchall()
            product['colors'] = [c['color'] for c in colors] if colors else []
            
            # Get active promotion for this product (must be approved)
            promotion = None
            try:
                cursor.execute("""
                    SELECT 
                        id,
                        discount_type,
                        discount_value,
                        start_date,
                        end_date,
                        description,
                        code
                    FROM promotions
                    WHERE product_id = %s 
                    AND is_active = TRUE
                    AND is_approved = TRUE
                    AND start_date <= NOW()
                    AND end_date >= NOW()
                    LIMIT 1
                """, (product['id'],))
                promotion = cursor.fetchone()
            except Exception as promo_err:
                # If there's any error, just skip promotions
                print(f"[WARNING] Could not fetch promotions: {promo_err}")
                promotion = None
            
            if promotion:
                # Convert discount_value to float for JSON serialization
                discount_val = float(promotion['discount_value']) if promotion['discount_value'] else 0
                
                product['promotion'] = {
                    'id': promotion['id'],
                    'discount_type': promotion['discount_type'],
                    'discount_value': discount_val,
                    'code': promotion['code'],
                    'description': promotion['description']
                }
                
                # Calculate discounted price
                if promotion['discount_type'] == 'percentage':
                    product['original_price'] = float(product['price'])
                    product['discounted_price'] = float(product['price']) * (1 - discount_val / 100)
                    product['discount_display'] = f"{int(discount_val)}% OFF"
                else:
                    product['original_price'] = float(product['price'])
                    product['discounted_price'] = float(product['price']) - discount_val
                    product['discount_display'] = f"₱{int(discount_val)} OFF"
                
                product['price_to_display'] = product['discounted_price']
            else:
                product['promotion'] = None
                product['price_to_display'] = float(product['price'])
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'products': products_list
        }), 200
    except Exception as e:
        print(f"[ERROR] /api/products: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/categories')
def api_categories():
    """Get all active categories for filtering"""
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, name, slug
            FROM categories
            WHERE is_active = TRUE
            ORDER BY name ASC
        """)
        categories = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'categories': categories
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/seller-products/<int:seller_id>')
def api_seller_products(seller_id):
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get products for the specified seller
        cursor.execute('''
            SELECT p.id, p.name, p.price, p.description, 
                   pi.image_url, p.seller_id, p.is_active,
                   c.name as category
            FROM products p
            LEFT JOIN product_images pi ON (p.id = pi.product_id AND pi.is_primary = 1)
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.seller_id = %s AND p.is_active = 1
            ORDER BY p.created_at DESC
            LIMIT 50
        ''', (seller_id,))
        
        products = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'products': products
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/user-orders')
def api_user_orders():
    """Get orders for logged-in user"""
    if not session.get('logged_in') or session.get('role') != 'buyer':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        user_id = session.get('user_id')
        
        # Fetch user's orders
        cursor.execute('''
            SELECT o.id, o.order_number, o.total_amount, o.order_status as status, o.created_at,
                   u.first_name, u.email
            FROM orders o
            JOIN users u ON o.user_id = u.id
            WHERE o.user_id = %s
            ORDER BY o.created_at DESC
            LIMIT 50
        ''', (user_id,))
        
        orders = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'orders': orders
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/my-orders')
def api_my_orders():
    """Get orders for logged-in user with shipment status mapping"""
    if not session.get('logged_in') or session.get('role') != 'buyer':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        user_id = session.get('user_id')
        
        # Fetch user's orders with shipment info
        cursor.execute('''
            SELECT o.id, o.order_number, o.total_amount, o.order_status, o.created_at,
                   u.first_name, u.email, 
                   s.id as shipment_id, s.status as shipment_status, s.delivered_at
            FROM orders o
            JOIN users u ON o.user_id = u.id
            LEFT JOIN shipments s ON o.id = s.order_id
            WHERE o.user_id = %s
            ORDER BY o.created_at DESC
            LIMIT 50
        ''', (user_id,))
        
        orders = cursor.fetchall()
        
        # Map order and shipment status to buyer-facing display status
        # Buyer flow: pending (waiting for seller) → confirmed (seller confirmed) → 
        #            waiting_for_pickup (preparing order) → released_to_rider (courier assigned) → 
        #            delivered (complete)
        
        # Convert Decimal to float and ensure id is present
        for order in orders:
            if order.get('total_amount'):
                order['total_amount'] = float(order['total_amount'])
            if 'id' in order and order['id']:
                order['id'] = int(order['id'])
            
            # Use order_status as primary source, fallback to shipment status for display
            current_order_status = order.get('order_status', 'pending')
            current_shipment_status = order.get('shipment_status', 'pending')
            
            # Map to buyer-facing display
            if current_order_status == 'pending':
                order['display_status'] = 'Waiting for Seller Confirmation'
                order['status_icon'] = '⏳'
            elif current_order_status == 'confirmed':
                order['display_status'] = 'Seller Confirmed - Preparing Order'
                order['status_icon'] = '✔️'
            elif current_order_status == 'waiting_for_pickup':
                order['display_status'] = 'Order Ready - Waiting for Courier'
                order['status_icon'] = '📦'
            elif current_order_status in ['released_to_rider', 'shipped']:
                if current_shipment_status == 'out_for_delivery':
                    order['display_status'] = 'Out for Delivery'
                    order['status_icon'] = '🚗'
                else:
                    order['display_status'] = 'Courier Assigned - In Transit'
                    order['status_icon'] = '📍'
            elif current_order_status == 'delivered':
                order['display_status'] = 'Delivered'
                order['status_icon'] = '✅'
            elif current_order_status == 'cancelled':
                order['display_status'] = 'Cancelled'
                order['status_icon'] = '❌'
            else:
                order['display_status'] = current_order_status.replace('_', ' ').title()
                order['status_icon'] = '📋'
            
            # Fetch order items with images
            cursor.execute('''
                SELECT oi.id, oi.product_id, oi.quantity, oi.unit_price, oi.subtotal,
                       p.name as product_name, 
                       COALESCE(pi_primary.image_url, pi_any.image_url) as image_url
                FROM order_items oi
                LEFT JOIN products p ON oi.product_id = p.id
                LEFT JOIN product_images pi_primary ON p.id = pi_primary.product_id AND pi_primary.is_primary = 1
                LEFT JOIN product_images pi_any ON p.id = pi_any.product_id
                WHERE oi.order_id = %s
                GROUP BY oi.id, oi.product_id
            ''', (order['id'],))
            
            items = cursor.fetchall()
            
            # Convert Decimal to float for items
            for item in items:
                if item.get('unit_price'):
                    item['unit_price'] = float(item['unit_price'])
                    item['price'] = float(item['unit_price'])
                if item.get('quantity'):
                    item['quantity'] = int(item['quantity'])
                if item.get('subtotal'):
                    item['subtotal'] = float(item['subtotal'])
            
            order['items'] = items
        
        cursor.close()
        conn.close()
        
        # Convert all Decimal objects to float before returning
        orders = convert_decimals_to_float(orders)
        
        return jsonify({
            'success': True,
            'orders': orders
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/order/complete', methods=['POST'])
def api_complete_order():
    """Buyer confirms order received and accepted"""
    if not session.get('logged_in') or session.get('role') != 'buyer':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        
        if not order_id:
            return jsonify({'success': False, 'error': 'Order ID required'}), 400
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        user_id = session.get('user_id')
        
        # Verify order belongs to user
        cursor.execute('SELECT id FROM orders WHERE id = %s AND user_id = %s', (order_id, user_id))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        # Update order status to completed (buyer confirmed)
        cursor.execute('''
            UPDATE orders 
            SET order_status = 'completed', updated_at = NOW()
            WHERE id = %s
        ''', (order_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"[✅] Order {order_id} completed by buyer {user_id}")
        return jsonify({'success': True, 'message': 'Order confirmed as received'}), 200
        
    except Exception as e:
        print(f"Error completing order: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/order/return', methods=['POST'])
def api_return_order():
    """Buyer initiates return or damage claim"""
    if not session.get('logged_in') or session.get('role') != 'buyer':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        reason = data.get('reason', 'Not specified')
        
        if not order_id:
            return jsonify({'success': False, 'error': 'Order ID required'}), 400
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        user_id = session.get('user_id')
        
        # Verify order belongs to user
        cursor.execute('SELECT id FROM orders WHERE id = %s AND user_id = %s', (order_id, user_id))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        # Update order status to return_requested
        cursor.execute('''
            UPDATE orders 
            SET order_status = 'return_requested', updated_at = NOW()
            WHERE id = %s
        ''', (order_id,))
        
        # Log return reason (you can create a separate returns table if needed)
        # For now, we'll update via a comment or create a returns record
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"[⚠️] Order {order_id} return initiated by buyer {user_id}. Reason: {reason}")
        return jsonify({'success': True, 'message': 'Return request submitted'}), 200
        
    except Exception as e:
        print(f"Error processing return: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/search-order', methods=['POST'])
def api_search_order():
    """Search for a specific order by order number and email"""
    try:
        data = request.json
        order_number = data.get('order_number')
        email = data.get('email')
        
        if not order_number or not email:
            return jsonify({'success': False, 'error': 'Order number and email required'}), 400
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Search for order
        cursor.execute('''
            SELECT o.id, o.order_number, o.total_amount, o.status, o.created_at,
                   u.first_name, u.email
            FROM orders o
            JOIN users u ON o.buyer_id = u.id
            WHERE o.order_number = %s AND u.email = %s
            LIMIT 1
        ''', (order_number, email))
        
        order = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not order:
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        return jsonify({
            'success': True,
            'order': order
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/order-details/<int:order_id>')
def api_order_details(order_id):
    """Get detailed order information for modal display"""
    if not session.get('logged_in') or session.get('role') != 'buyer':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        user_id = session.get('user_id')
        
        # Get order details
        cursor.execute('''
            SELECT o.*, u.first_name, u.email
            FROM orders o
            JOIN users u ON o.user_id = u.id
            WHERE o.id = %s AND o.user_id = %s
        ''', (order_id, user_id))
        
        order = cursor.fetchone()
        
        if not order:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        # Convert Decimal to float
        for key in ['total_amount', 'subtotal', 'shipping_fee', 'tax_amount', 'discount_amount']:
            if order.get(key):
                order[key] = float(order[key])
        
        # Get order items
        cursor.execute('''
            SELECT oi.*, p.name as product_name,
                   COALESCE(pi_primary.image_url, pi_any.image_url) as image_url
            FROM order_items oi
            LEFT JOIN products p ON oi.product_id = p.id
            LEFT JOIN product_images pi_primary ON p.id = pi_primary.product_id AND pi_primary.is_primary = 1
            LEFT JOIN product_images pi_any ON p.id = pi_any.product_id
            WHERE oi.order_id = %s
            GROUP BY oi.id, oi.product_id
        ''', (order_id,))
        
        items = cursor.fetchall()
        
        # Convert Decimal to float for items and add price alias for frontend compatibility
        for item in items:
            if item.get('unit_price'):
                item['unit_price'] = float(item['unit_price'])
                item['price'] = item['unit_price']  # Add price field for frontend compatibility
            if item.get('subtotal'):
                item['subtotal'] = float(item['subtotal'])
        
        # Get shipment information
        cursor.execute('''
            SELECT * FROM shipments WHERE order_id = %s
        ''', (order_id,))
        
        shipment = cursor.fetchone()
        if shipment:
            # Convert datetime objects to ISO strings for JSON
            for key in ['shipped_at', 'estimated_delivery', 'delivered_at', 'created_at', 'updated_at', 'seller_confirmed_at']:
                if shipment.get(key):
                    shipment[key] = shipment[key].isoformat() if hasattr(shipment[key], 'isoformat') else str(shipment[key])
        
        # Get shipping address
        cursor.execute('''
            SELECT * FROM addresses WHERE id = %s
        ''', (order.get('shipping_address_id'),)) if order.get('shipping_address_id') else None
        
        shipping_address = cursor.fetchone() if order.get('shipping_address_id') else None
        
        # Get billing address
        cursor.execute('''
            SELECT * FROM addresses WHERE id = %s
        ''', (order.get('billing_address_id'),)) if order.get('billing_address_id') else None
        
        billing_address = cursor.fetchone() if order.get('billing_address_id') else None
        
        cursor.close()
        conn.close()
        
        # Convert all Decimal objects to float before returning
        order = convert_decimals_to_float(order)
        items = convert_decimals_to_float(items)
        shipment = convert_decimals_to_float(shipment)
        shipping_address = convert_decimals_to_float(shipping_address)
        billing_address = convert_decimals_to_float(billing_address)
        
        return jsonify({
            'success': True,
            'order': order,
            'items': items,
            'shipment': shipment,
            'shipping_address': shipping_address,
            'billing_address': billing_address
        }), 200
        
    except Exception as e:
        print(f"[ERROR] api_order_details: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/buyer-dashboard')
def buyer_dashboard():
    if not session.get('logged_in') or session.get('role') != 'buyer':
        flash('Access denied. Please log in first.', 'error')
        return redirect(url_for('login'))
    return render_template('pages/indexLoggedIn.html')

@app.route('/cart')
def cart():
    if not session.get('logged_in') or session.get('role') != 'buyer':
        flash('Access denied. Please log in first.', 'error')
        return redirect(url_for('login'))
    return render_template('pages/cart.html')

@app.route('/account-details')
def account_details():
    """Account details page for buyers to view and edit their profile"""
    if not session.get('logged_in') or session.get('role') != 'buyer':
        flash('Access denied. Please log in first.', 'error')
        return redirect(url_for('login'))
    
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        user_id = session.get('user_id')
        # Check if profile_image column exists, if not, select without it
        cursor.execute('SHOW COLUMNS FROM users LIKE "profile_image"')
        has_profile_image = cursor.fetchone()
        
        if has_profile_image:
            cursor.execute('SELECT id, first_name, last_name, email, phone, profile_image FROM users WHERE id = %s', (user_id,))
        else:
            cursor.execute('SELECT id, first_name, last_name, email, phone FROM users WHERE id = %s', (user_id,))
        
        user = cursor.fetchone()
        if user and not has_profile_image:
            user['profile_image'] = None
        
        # Check if email_verified and phone_verified columns exist
        cursor.execute('SHOW COLUMNS FROM users LIKE "email_verified"')
        has_email_verified = cursor.fetchone()
        cursor.execute('SHOW COLUMNS FROM users LIKE "phone_verified"')
        has_phone_verified = cursor.fetchone()
        
        # Get verification status
        email_verified = False
        phone_verified = False
        
        if has_email_verified:
            cursor.execute('SELECT email_verified FROM users WHERE id = %s', (user_id,))
            result = cursor.fetchone()
            email_verified = result.get('email_verified', False) if result else False
        
        if has_phone_verified:
            cursor.execute('SELECT phone_verified FROM users WHERE id = %s', (user_id,))
            result = cursor.fetchone()
            phone_verified = result.get('phone_verified', False) if result else False
        
        # If columns don't exist, assume verified (for existing users)
        if not has_email_verified:
            email_verified = True
        if not has_phone_verified:
            phone_verified = True
        
        user['email_verified'] = email_verified
        user['phone_verified'] = phone_verified
        
        cursor.close()
        conn.close()
        
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('buyer_dashboard'))
        
        return render_template('pages/accountDetails.html', user=user)
    except Exception as e:
        print(f"Error fetching account details: {str(e)}")
        flash('Error loading account details', 'error')
        return redirect(url_for('buyer_dashboard'))

@app.route('/upload-profile-picture', methods=['POST'])
def upload_profile_picture():
    """Upload profile picture for buyer"""
    if not session.get('logged_in') or session.get('role') != 'buyer':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        if 'profile_image' not in request.files:
            return jsonify({'success': False, 'message': 'No file provided'}), 400
        
        file = request.files['profile_image']
        if not file or not file.filename:
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        # Validate file type
        if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.avif', '.webp')):
            return jsonify({'success': False, 'message': 'Only image files (JPG, PNG, AVIF, WebP) are allowed'}), 400
        
        import os
        from werkzeug.utils import secure_filename
        import time
        
        # Create uploads directory if it doesn't exist
        upload_folder = os.path.join('static', 'images', 'profiles')
        os.makedirs(upload_folder, exist_ok=True)
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        timestamp = int(time.time() * 1000)
        user_id = session.get('user_id')
        unique_filename = f"user_{user_id}_{timestamp}_{filename}"
        filepath = os.path.join(upload_folder, unique_filename)
        file.save(filepath)
        
        # Store relative URL
        image_url = f"/static/images/profiles/{unique_filename}"
        
        # Update database
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if profile_image column exists, if not, add it
        cursor.execute('SHOW COLUMNS FROM users LIKE "profile_image"')
        has_column = cursor.fetchone()
        if not has_column:
            cursor.execute('ALTER TABLE users ADD COLUMN profile_image VARCHAR(500)')
            conn.commit()
        
        # Update database with profile image path
        cursor.execute('UPDATE users SET profile_image = %s WHERE id = %s', (image_url, user_id))
        conn.commit()
        
        # Verify the update
        cursor.execute('SELECT profile_image FROM users WHERE id = %s', (user_id,))
        updated_user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if updated_user and updated_user[0] == image_url:
            print(f"Profile picture saved to database for user {user_id}: {image_url}")
            return jsonify({
                'success': True,
                'message': 'Profile picture saved successfully',
                'image_url': image_url
            })
        else:
            print(f"Warning: Profile picture may not have been saved correctly for user {user_id}")
            return jsonify({
                'success': True,
                'message': 'Profile picture uploaded, but database update may have failed',
                'image_url': image_url
            })
    except Exception as e:
        print(f"Error uploading profile picture: {str(e)}")
        return jsonify({'success': False, 'message': 'Error uploading profile picture'}), 500

@app.route('/send-email-change-otp', methods=['POST'])
def send_email_change_otp():
    """Send OTP for email change verification"""
    if not session.get('logged_in') or session.get('role') != 'buyer':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        new_email = data.get('new_email', '').strip()
        
        if not new_email:
            return jsonify({'success': False, 'message': 'Email is required'}), 400
        
        # Check if email is already taken
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        user_id = session.get('user_id')
        cursor.execute('SELECT id FROM users WHERE email = %s AND id != %s', (new_email, user_id))
        existing_user = cursor.fetchone()
        
        if existing_user:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Email is already taken'}), 400
        
        # Generate and send OTP
        ip_address = request.remote_addr
        otp_code, otp_id = OTPService.create_otp_record(
            conn,
            email=new_email,
            otp_type='email',
            purpose='email_change',
            ip_address=ip_address
        )
        
        cursor.close()
        conn.close()
        
        if otp_code:
            # Try to send email
            email_sent = OTPService.send_email_otp(new_email, otp_code, 'email_change')
            if email_sent:
                print(f"✅ Email change OTP sent to {new_email}")
            else:
                print(f"⚠️ Email sending failed, but OTP is available in console")
            
            print(f"\n{'='*60}")
            print(f"📧 EMAIL CHANGE OTP FOR {new_email}")
            print(f"OTP CODE: {otp_code}")
            print(f"{'='*60}\n")
            
            # Store in session for verification
            session['email_change'] = {
                'new_email': new_email,
                'otp_id': otp_id,
                'verified': False
            }
            
            return jsonify({
                'success': True,
                'message': 'Verification code sent to your new email',
                'otp_id': otp_id
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to generate verification code'}), 500
            
    except Exception as e:
        print(f"Error sending email change OTP: {str(e)}")
        return jsonify({'success': False, 'message': 'Error sending verification code'}), 500

@app.route('/verify-email-change', methods=['POST'])
def verify_email_change():
    """Verify OTP for email change"""
    if not session.get('logged_in') or session.get('role') != 'buyer':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        otp_code = data.get('otp', '')
        otp_id = data.get('otp_id')
        
        if not otp_code or 'email_change' not in session:
            return jsonify({'success': False, 'message': 'Invalid request'}), 400
        
        email_change_data = session['email_change']
        new_email = email_change_data.get('new_email')
        
        conn = get_db()
        
        # Verify OTP
        is_valid, message = OTPService.verify_otp(conn, otp_code, email=new_email, purpose='email_change')
        
        if is_valid:
            # Mark as verified in session
            session['email_change']['verified'] = True
            session.modified = True
            
            # Update email and email_verified in database
            cursor = conn.cursor()
            # Check if email_verified column exists, if not, add it
            cursor.execute('SHOW COLUMNS FROM users LIKE "email_verified"')
            has_column = cursor.fetchone()
            if not has_column:
                cursor.execute('ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE')
                conn.commit()
            
            # Update email and verification status
            user_id = session.get('user_id')
            cursor.execute('UPDATE users SET email = %s, email_verified = TRUE WHERE id = %s', (new_email, user_id))
            conn.commit()
            cursor.close()
            conn.close()
            
            # Update session email
            session['email'] = new_email
            
            return jsonify({
                'success': True,
                'message': 'Email verified and updated successfully'
            })
        else:
            conn.close()
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        print(f"Error verifying email change: {str(e)}")
        return jsonify({'success': False, 'message': 'Verification failed'}), 500

@app.route('/update-account', methods=['POST'])
def update_account():
    """Update user account details"""
    if not session.get('logged_in') or session.get('role') != 'buyer':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        
        if not first_name:
            return jsonify({'success': False, 'message': 'First name is required'}), 400
        
        if not email:
            return jsonify({'success': False, 'message': 'Email is required'}), 400
        
        # Check if email was changed and verify it was verified
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT email FROM users WHERE id = %s', (user_id,))
        current_user = cursor.fetchone()
        current_email = current_user['email'] if current_user else None
        
        if email != current_email:
            # Email was changed - check if it was verified
            if 'email_change' not in session or not session['email_change'].get('verified'):
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'message': 'Please verify your new email address first'}), 400
            
            if session['email_change'].get('new_email') != email:
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'message': 'Email mismatch. Please verify the correct email'}), 400
        
        # Check if email is already taken by another user
        cursor.execute('SELECT id FROM users WHERE email = %s AND id != %s', (email, user_id))
        existing_user = cursor.fetchone()
        
        if existing_user:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Email is already taken'}), 400
        
        # Check if email_verified and phone_verified columns exist
        cursor.execute('SHOW COLUMNS FROM users LIKE "email_verified"')
        has_email_verified = cursor.fetchone()
        cursor.execute('SHOW COLUMNS FROM users LIKE "phone_verified"')
        has_phone_verified = cursor.fetchone()
        
        # Get current values to check if they changed
        cursor.execute('SELECT email, phone FROM users WHERE id = %s', (user_id,))
        current_user = cursor.fetchone()
        current_email = current_user['email'] if current_user else None
        current_phone = current_user.get('phone') if current_user else None
        
        # Build update query
        update_fields = ['email = %s', 'phone = %s']
        update_values = [email, phone]
        
        # Reset verification status if email/phone changed
        if has_email_verified and email != current_email:
            update_fields.append('email_verified = FALSE')
        if has_phone_verified and phone != current_phone:
            update_fields.append('phone_verified = FALSE')
        
        # Update user details
        update_query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
        update_values.append(user_id)
        cursor.execute(update_query, tuple(update_values))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Update session
        session['email'] = email
        if 'email_change' in session:
            session.pop('email_change', None)
        
        return jsonify({
            'success': True,
            'message': 'Account updated successfully'
        })
    except Exception as e:
        print(f"Error updating account: {str(e)}")
        return jsonify({'success': False, 'message': 'Error updating account'}), 500

@app.route('/verify-password', methods=['POST'])
def verify_password():
    """Verify user password for account changes"""
    if not session.get('logged_in') or session.get('role') != 'buyer':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        password = data.get('password', '').strip()
        
        if not password:
            return jsonify({'success': False, 'message': 'Password is required'}), 400
        
        user_id = session.get('user_id')
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT password FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Check password (plain text comparison since passwords are stored as plain text)
        if user['password'] == password:
            return jsonify({
                'success': True,
                'message': 'Password verified'
            })
        else:
            return jsonify({'success': False, 'message': 'Incorrect password'}), 401
            
    except Exception as e:
        print(f"Error verifying password: {str(e)}")
        return jsonify({'success': False, 'message': 'Error verifying password'}), 500

@app.route('/send-phone-verification-otp', methods=['POST'])
def send_phone_verification_otp():
    """Send OTP for phone number verification"""
    if not session.get('logged_in') or session.get('role') != 'buyer':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        
        if not phone:
            return jsonify({'success': False, 'message': 'Phone number is required'}), 400
        
        # Generate and send OTP
        conn = get_db()
        ip_address = request.remote_addr
        otp_code, otp_id = OTPService.create_otp_record(
            conn,
            phone=phone,
            otp_type='sms',
            purpose='phone_verification',
            ip_address=ip_address
        )
        
        if otp_code:
            # Send SMS via email-to-SMS gateway (FREE)
            sms_sent = OTPService.send_sms_otp(phone, otp_code, 'phone_verification')
            
            print(f"\n{'='*60}")
            print(f"📱 PHONE VERIFICATION OTP FOR {phone}")
            print(f"OTP CODE: {otp_code}")
            print(f"{'='*60}\n")
            
            # Store in session for verification
            session['phone_verification'] = {
                'phone': phone,
                'otp_id': otp_id,
                'verified': False
            }
            
            conn.close()
            
            return jsonify({
                'success': True,
                'message': 'Verification code sent to your phone number',
                'otp_id': otp_id
            })
        else:
            conn.close()
            return jsonify({'success': False, 'message': 'Failed to generate verification code'}), 500
            
    except Exception as e:
        print(f"Error sending phone verification OTP: {str(e)}")
        return jsonify({'success': False, 'message': 'Error sending verification code'}), 500

@app.route('/verify-phone-otp', methods=['POST'])
def verify_phone_otp():
    """Verify OTP for phone number"""
    if not session.get('logged_in') or session.get('role') != 'buyer':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        otp_code = str(data.get('otp', '')).strip()  # Strip whitespace
        phone = data.get('phone', '').strip()
        
        if not otp_code or len(otp_code) != 6:
            return jsonify({'success': False, 'message': 'Invalid OTP code format'}), 400
        
        if not phone:
            return jsonify({'success': False, 'message': 'Phone number is required'}), 400
        
        conn = get_db()
        
        print(f"🔍 Verifying phone OTP:")
        print(f"   OTP Code: {otp_code}")
        print(f"   Phone: {phone}")
        print(f"   Purpose: phone_verification")
        
        # Verify OTP
        is_valid, message = OTPService.verify_otp(conn, otp_code, phone=phone, purpose='phone_verification')
        
        if is_valid:
            # Mark as verified in session
            if 'phone_verification' in session:
                session['phone_verification']['verified'] = True
                session.modified = True
            
            # Update phone and phone_verified in database
            cursor = conn.cursor()
            # Check if phone_verified column exists, if not, add it
            cursor.execute('SHOW COLUMNS FROM users LIKE "phone_verified"')
            has_column = cursor.fetchone()
            if not has_column:
                cursor.execute('ALTER TABLE users ADD COLUMN phone_verified BOOLEAN DEFAULT FALSE')
                conn.commit()
            
            # Update phone and verification status
            user_id = session.get('user_id')
            cursor.execute('UPDATE users SET phone = %s, phone_verified = TRUE WHERE id = %s', (phone, user_id))
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': 'Phone number verified and updated successfully'
            })
        else:
            conn.close()
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        print(f"Error verifying phone OTP: {str(e)}")
        return jsonify({'success': False, 'message': 'Verification failed'}), 500

@app.route('/admin/recent-orders')
def admin_recent_orders():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get recent orders (last 4)
        query = '''
            SELECT o.id, o.order_number, o.total_amount, o.order_status, o.created_at, u.first_name, u.last_name
            FROM orders o
            JOIN users u ON o.user_id = u.id
            ORDER BY o.created_at DESC
            LIMIT 4
        '''
        cursor.execute(query)
        orders = cursor.fetchall()
        
        # Format orders
        formatted_orders = []
        for order in orders:
            formatted_orders.append({
                'order_number': order['order_number'],
                'buyer_name': f"{order['first_name']} {order['last_name']}",
                'created_at': order['created_at'],
                'total_amount': order['total_amount'],
                'status': order['order_status']
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'orders': formatted_orders})
    except Exception as err:
        print(f"[ERROR] {err}")
        return jsonify({'success': False, 'error': str(err)}), 500

@app.route('/admin/best-product')
def admin_best_product():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get best selling product (by order count)
        query = '''
            SELECT p.id, p.name, pi.image_url, s.store_name,
                   COUNT(oi.id) as order_count
            FROM products p
            LEFT JOIN product_images pi ON p.id = pi.product_id AND pi.is_primary = 1
            LEFT JOIN sellers s ON p.seller_id = s.id
            LEFT JOIN order_items oi ON p.id = oi.product_id
            WHERE p.is_active = 1
            GROUP BY p.id, p.name, pi.image_url, s.store_name
            ORDER BY order_count DESC
            LIMIT 1
        '''
        cursor.execute(query)
        product = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if product:
            return jsonify({
                'success': True,
                'product': {
                    'id': product['id'],
                    'name': product['name'],
                    'image_url': product['image_url'],
                    'store_name': product['store_name'],
                    'order_count': product['order_count'] or 0
                }
            })
        else:
            return jsonify({'success': True, 'product': None})
    except Exception as err:
        print(f"[ERROR] {err}")
        return jsonify({'success': False, 'error': str(err)}), 500

@app.route('/seller/orders', methods=['GET'])
def seller_orders():
    """Get all orders for the logged-in seller with optional status filtering"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Not logged in'}), 401
        
        user_id = session['user_id']
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get the seller_id for this user (from sellers table)
        cursor.execute('SELECT id FROM sellers WHERE user_id = %s', (user_id,))
        seller_result = cursor.fetchone()
        if not seller_result:
            return jsonify({'success': False, 'error': 'Not a seller'}), 403
        
        seller_id = seller_result['id']
        
        # Get filter parameter from query string
        status_filter = request.args.get('status', None)
        
        # Fetch orders for this seller, including shipment status
        # Filter by status if provided: pending, confirmed, processing, shipped, delivered
        query = """
            SELECT
                o.id,
                o.order_number,
                o.user_id,
                o.rider_id,
                o.total_amount,
                o.order_status,
                o.seller_confirmed_rider,
                o.buyer_approved_rider,
                o.created_at,
                o.updated_at,
                CONCAT(u.first_name, ' ', u.last_name) as customer_name,
                (SELECT COUNT(*) FROM order_items oi2 
                 WHERE oi2.order_id = o.id) as item_count,
                IFNULL(s.status, 'pending') as shipment_status,
                IFNULL(s.rider_id, 0) as shipment_rider_id,
                IFNULL(s.seller_confirmed, FALSE) as seller_confirmed,
                s.id as shipment_id,
                a.city as shipping_city,
                a.province as shipping_province,
                a.postal_code as shipping_postal_code
            FROM orders o
            INNER JOIN order_items oi ON o.id = oi.order_id
            INNER JOIN products p ON oi.product_id = p.id
            LEFT JOIN users u ON o.user_id = u.id
            LEFT JOIN shipments s ON s.order_id = o.id
            LEFT JOIN addresses a ON o.shipping_address_id = a.id
            WHERE p.seller_id = %s
        """
        
        # Add status filter if provided
        if status_filter:
            # Map filter names to order_status values
            status_map = {
                'pending': 'pending',
                'confirmed': 'confirmed',
                'waiting_for_pickup': 'waiting_for_pickup',
                'processing': 'processing',
                'shipped': 'shipped',
                'delivered': 'delivered'
            }
            filtered_status = status_map.get(status_filter, status_filter)
            query += f" AND o.order_status = '{filtered_status}'"
        
        query += " GROUP BY o.id ORDER BY o.created_at DESC"
        
        cursor.execute(query, (seller_id,))
        orders = cursor.fetchall()
        
        print(f"[DEBUG] seller_orders: Found {len(orders)} orders for seller_id={seller_id}, filter={status_filter}")
        
        # Convert datetime objects to strings and Decimal to float
        for order in orders:
            if order.get('created_at'):
                order['created_at'] = order['created_at'].isoformat()
            if order.get('updated_at'):
                order['updated_at'] = order['updated_at'].isoformat() if order['updated_at'] else None
            if order.get('total_amount'):
                order['total_amount'] = float(order['total_amount'])
            # Ensure all fields are present
            if 'shipment_status' not in order:
                order['shipment_status'] = 'pending'
            if 'rider_id' not in order:
                order['rider_id'] = 0
            if 'seller_confirmed' not in order:
                order['seller_confirmed'] = False
            if 'shipment_id' not in order:
                order['shipment_id'] = None
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'orders': orders,
            'filter': status_filter
        }), 200
    except Exception as e:
        print(f"[ERROR] seller_orders: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/seller/update-order-status', methods=['POST'])
def update_order_status():
    """Update the status of an order (for seller fulfillment)
    
    FORWARD-ONLY STATE MACHINE:
    pending → confirmed → released_to_rider → delivered (FINAL)
                                             ↘ cancelled (FINAL)
                                             ↘ returned (FINAL)
    """
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Not logged in'}), 401
        
        user_id = session['user_id']
        order_id = request.form.get('order_id')
        new_status = request.form.get('new_status')
        
        # Validate input
        if not order_id or not new_status:
            return jsonify({'success': False, 'error': 'Missing order_id or new_status'}), 400
        
        # Define valid statuses
        valid_statuses = ['pending', 'confirmed', 'released_to_rider', 'delivered', 'cancelled', 'returned']
        if new_status not in valid_statuses:
            return jsonify({'success': False, 'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get the seller_id for this user
        cursor.execute('SELECT id FROM sellers WHERE user_id = %s', (user_id,))
        seller_result = cursor.fetchone()
        if not seller_result:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Not a seller'}), 403
        
        seller_id = seller_result['id']
        
        # Verify that this seller owns the products in this order
        verify_query = """
            SELECT o.id, o.order_status as current_status
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            LEFT JOIN products p ON oi.product_id = p.id
            WHERE o.id = %s AND p.seller_id = %s
            LIMIT 1
        """
        
        cursor.execute(verify_query, (order_id, seller_id))
        order_check = cursor.fetchone()
        
        if not order_check:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Order not found or you do not have permission to update it'}), 403
        
        current_status = order_check['current_status']
        
        # ===== FORWARD-ONLY STATE MACHINE VALIDATION =====
        # Define valid transitions (no backwards allowed)
        # Flow: pending → confirmed → waiting_for_pickup → released_to_rider → delivered
        valid_transitions = {
            'pending': ['confirmed'],
            'confirmed': ['waiting_for_pickup'],
            'waiting_for_pickup': ['released_to_rider'],
            'released_to_rider': ['delivered'],
            'delivered': [],  # Final state - no transitions
            'cancelled': [],  # Final state - no transitions
            'returned': []    # Final state - no transitions
        }
        
        # Check if transition is allowed
        allowed_next_statuses = valid_transitions.get(current_status, [])
        if new_status not in allowed_next_statuses:
            cursor.close()
            conn.close()
            
            if allowed_next_statuses:
                return jsonify({
                    'success': False,
                    'error': f'❌ Invalid status transition. Cannot go from "{current_status.upper()}" to "{new_status.upper()}". Forward-only transitions allowed. Next valid status: {", ".join([s.upper() for s in allowed_next_statuses])}',
                    'current_status': current_status,
                    'requested_status': new_status,
                    'allowed_next': allowed_next_statuses
                }), 400
            else:
                return jsonify({
                    'success': False,
                    'error': f'❌ Order is in final state "{current_status.upper()}" and cannot be modified.',
                    'current_status': current_status
                }), 400
        
        # ===== UPDATE ORDER STATUS =====
        update_query = """
            UPDATE orders
            SET order_status = %s, updated_at = NOW()
            WHERE id = %s
        """
        
        cursor.execute(update_query, (new_status, order_id))
        
        # Special handling for specific status transitions
        if new_status == 'confirmed':
            # When confirming an order: create/update shipment with seller_confirmed = TRUE
            cursor.execute('''
                SELECT o.shipping_address_id
                FROM orders o
                WHERE o.id = %s
            ''', (order_id,))
            order_info = cursor.fetchone()
            
            if order_info:
                # Find or create shipment
                cursor.execute('SELECT id FROM shipments WHERE order_id = %s', (order_id,))
                shipment = cursor.fetchone()
                
                if not shipment:
                    # Create new shipment
                    tracking_number = f"SHIP{order_id}{int(time.time())}"
                    cursor.execute('''
                        INSERT INTO shipments (order_id, tracking_number, status, seller_confirmed, seller_confirmed_at, created_at)
                        VALUES (%s, %s, 'pending', TRUE, NOW(), NOW())
                    ''', (order_id, tracking_number))
                    conn.commit()
                else:
                    # Update existing shipment to mark seller as confirmed
                    cursor.execute('''
                        UPDATE shipments
                        SET seller_confirmed = TRUE, seller_confirmed_at = NOW()
                        WHERE id = %s
                    ''', (shipment['id'],))
                    conn.commit()
        
        elif new_status == 'released_to_rider':
            # When releasing to rider: create/update shipment and assign rider
            # First, get the order details and shipping address
            cursor.execute('''
                SELECT o.shipping_address_id
                FROM orders o
                WHERE o.id = %s
            ''', (order_id,))
            order_info = cursor.fetchone()
            
            if order_info:
                # Get the shipping address
                cursor.execute('SELECT province, city, postal_code FROM addresses WHERE id = %s', (order_info['shipping_address_id'],))
                address = cursor.fetchone()
                
                # Find or create shipment
                cursor.execute('SELECT id, rider_id FROM shipments WHERE order_id = %s', (order_id,))
                shipment = cursor.fetchone()
                
                if shipment:
                    shipment_id = shipment['id']
                    existing_rider_id = shipment['rider_id']
                else:
                    # Create new shipment
                    tracking_number = f"SHIP{order_id}{int(time.time())}"
                    cursor.execute('''
                        INSERT INTO shipments (order_id, tracking_number, status, seller_confirmed, seller_confirmed_at, created_at)
                        VALUES (%s, %s, 'picked_up', TRUE, NOW(), NOW())
                    ''', (order_id, tracking_number))
                    conn.commit()
                    shipment_id = cursor.lastrowid
                    existing_rider_id = None
                
                # If no rider assigned yet, find an available one
                if not existing_rider_id and address:
                    cursor.execute('''
                        SELECT id FROM riders 
                        WHERE (service_area LIKE %s OR service_area LIKE %s OR service_area LIKE %s)
                        AND status = 'active'
                        AND is_available = TRUE
                        LIMIT 1
                    ''', (f'%{address["province"]}%', f'%{address["city"]}%', f'%{address["postal_code"]}%'))
                    
                    rider = cursor.fetchone()
                    if rider:
                        # Assign the rider and set status to picked_up
                        cursor.execute('''
                            UPDATE shipments 
                            SET rider_id = %s, seller_confirmed = TRUE, seller_confirmed_at = NOW(), status = 'picked_up'
                            WHERE id = %s
                        ''', (rider['id'], shipment_id))
                        print(f"[✅] Shipment {shipment_id} assigned to rider {rider['id']} with status picked_up")
                else:
                    # Already has a rider or can't find one, update shipment status to picked_up
                    cursor.execute('''
                        UPDATE shipments 
                        SET seller_confirmed = TRUE, seller_confirmed_at = NOW(), status = 'picked_up'
                        WHERE id = %s
                    ''', (shipment_id,))
        
        elif new_status == 'shipped':
            # When marking as shipped, update shipment status
            cursor.execute('''
                UPDATE shipments 
                SET status = 'in_transit', updated_at = NOW()
                WHERE order_id = %s
            ''', (order_id,))
        
        elif new_status == 'delivered':
            # When marking as delivered, update shipment status and confirm for rider
            cursor.execute('''
                UPDATE shipments 
                SET status = 'delivered', seller_confirmed = TRUE, seller_confirmed_at = NOW(), updated_at = NOW()
                WHERE order_id = %s
            ''', (order_id,))
        
        elif new_status == 'cancelled':
            # When cancelling, update shipment status
            cursor.execute('''
                UPDATE shipments 
                SET status = 'cancelled', updated_at = NOW()
                WHERE order_id = %s
            ''', (order_id,))
        
        conn.commit()
        
        print(f"[✅] ORDER STATUS UPDATE: Order {order_id} transitioned from '{current_status}' → '{new_status}' by seller {seller_id}")
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'✅ Order status successfully updated: {current_status.upper()} → {new_status.upper()}',
            'order_id': order_id,
            'previous_status': current_status,
            'new_status': new_status
        }), 200
    except Exception as e:
        print(f"[ERROR] update_order_status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/seller/approve-rider', methods=['POST'])
def seller_approve_rider():
    """Approve a rider who has accepted an order"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Not logged in'}), 401
        
        user_id = session['user_id']
        order_id = request.form.get('order_id')
        
        if not order_id:
            return jsonify({'success': False, 'error': 'Missing order_id'}), 400
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get the seller_id for this user
        cursor.execute('SELECT id FROM sellers WHERE user_id = %s', (user_id,))
        seller_result = cursor.fetchone()
        if not seller_result:
            return jsonify({'success': False, 'error': 'Not a seller'}), 403
        
        seller_id = seller_result['id']
        
        # Verify that this seller owns the products in this order
        verify_query = """
            SELECT o.id
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            LEFT JOIN products p ON oi.product_id = p.id
            WHERE o.id = %s AND p.seller_id = %s
            LIMIT 1
        """
        
        cursor.execute(verify_query, (order_id, seller_id))
        order_check = cursor.fetchone()
        
        if not order_check:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Order not found or you do not have permission'}), 403
        
        # Check if shipment exists and has a rider
        cursor.execute('''
            SELECT id, rider_id FROM shipments 
            WHERE order_id = %s AND rider_id IS NOT NULL
        ''', (order_id,))
        shipment = cursor.fetchone()
        
        if not shipment:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'No rider found for this order'}), 400
        
        # Update order status to "released_to_rider" when seller approves the rider
        cursor.execute('''
            UPDATE orders 
            SET order_status = 'released_to_rider', updated_at = NOW()
            WHERE id = %s
        ''', (order_id,))
        
        # Update shipment status to reflect the release
        cursor.execute('''
            UPDATE shipments 
            SET status = 'approved', seller_confirmed = TRUE
            WHERE id = %s
        ''', (shipment['id'],))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Rider approved! Order released to rider for delivery.'
        }), 200
    except Exception as e:
        print(f"[ERROR] seller_approve_rider: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============ RIDER PICKUP APPROVAL WORKFLOW ============
@app.route('/api/rider/request-pickup/<int:order_id>', methods=['POST'])
def rider_request_pickup(order_id):
    """Rider requests pickup approval from seller"""
    try:
        if 'user_id' not in session or session.get('role') != 'rider':
            return jsonify({'success': False, 'error': 'Not authorized'}), 403
        
        rider_user_id = session['user_id']
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Verify rider exists
        cursor.execute('SELECT id FROM riders WHERE user_id = %s', (rider_user_id,))
        rider = cursor.fetchone()
        if not rider:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Rider profile not found'}), 404
        
        # Get order and verify it's assigned to this rider
        cursor.execute('''
            SELECT o.id, o.order_number, o.rider_id, o.order_status, o.seller_id, s.store_name
            FROM orders o
            LEFT JOIN sellers s ON o.seller_id = s.id
            WHERE o.id = %s AND o.rider_id = %s
        ''', (order_id, rider['id']))
        
        order = cursor.fetchone()
        if not order:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Order not found or not assigned to you'}), 404
        
        # Check if shipment exists and update status to request_pickup
        cursor.execute('''
            SELECT id, status FROM shipments WHERE order_id = %s
        ''', (order_id,))
        shipment = cursor.fetchone()
        
        if not shipment:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Shipment not found'}), 404
        
        # Update shipment status to waiting for seller approval
        cursor.execute('''
            UPDATE shipments 
            SET status = 'pickup_requested'
            WHERE id = %s
        ''', (shipment['id'],))
        
        # Update order status to show awaiting seller approval
        cursor.execute('''
            UPDATE orders 
            SET order_status = 'awaiting_pickup_approval'
            WHERE id = %s
        ''', (order_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Pickup request sent to seller',
            'order_number': order['order_number']
        }), 200
        
    except Exception as e:
        print(f"[ERROR] rider_request_pickup: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/seller/approve-rider-pickup/<int:order_id>', methods=['POST'])
def seller_approve_rider_pickup(order_id):
    """Seller approves rider pickup of order"""
    try:
        if 'user_id' not in session or session.get('role') != 'seller':
            return jsonify({'success': False, 'error': 'Not authorized'}), 403
        
        seller_user_id = session['user_id']
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Verify seller exists
        cursor.execute('SELECT id FROM sellers WHERE user_id = %s', (seller_user_id,))
        seller = cursor.fetchone()
        if not seller:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Seller profile not found'}), 404
        
        # Verify seller owns this order
        cursor.execute('''
            SELECT o.id, o.order_number, o.rider_id, s.id as shipment_id, s.status
            FROM orders o
            LEFT JOIN shipments s ON o.id = s.order_id
            LEFT JOIN order_items oi ON o.id = oi.order_id
            LEFT JOIN products p ON oi.product_id = p.id
            WHERE o.id = %s AND p.seller_id = %s
            LIMIT 1
        ''', (order_id, seller['id']))
        
        order_data = cursor.fetchone()
        if not order_data:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Order not found or not authorized'}), 404
        
        if not order_data.get('rider_id'):
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'No rider assigned to this order'}), 400
        
        # Update shipment status to in_transit (rider approved and can start pickup)
        cursor.execute('''
            UPDATE shipments 
            SET status = 'in_transit', seller_confirmed = TRUE, seller_confirmed_at = NOW()
            WHERE id = %s
        ''', (order_data['shipment_id'],))
        
        # Update order status
        cursor.execute('''
            UPDATE orders 
            SET order_status = 'in_transit'
            WHERE id = %s
        ''', (order_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Rider approved for pickup! Order is now in transit.',
            'order_number': order_data['order_number']
        }), 200
        
    except Exception as e:
        print(f"[ERROR] seller_approve_rider_pickup: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/seller/reject-rider-pickup/<int:order_id>', methods=['POST'])
def seller_reject_rider_pickup(order_id):
    """Seller rejects rider pickup request"""
    try:
        if 'user_id' not in session or session.get('role') != 'seller':
            return jsonify({'success': False, 'error': 'Not authorized'}), 403
        
        seller_user_id = session['user_id']
        rejection_reason = request.form.get('reason', '') or (request.json.get('reason', '') if request.is_json else 'Order not ready for pickup')
        
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Verify seller
        cursor.execute('SELECT id FROM sellers WHERE user_id = %s', (seller_user_id,))
        seller = cursor.fetchone()
        if not seller:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Seller profile not found'}), 404
        
        # Verify order ownership
        cursor.execute('''
            SELECT o.id, o.order_number, s.id as shipment_id
            FROM orders o
            LEFT JOIN shipments s ON o.id = s.order_id
            LEFT JOIN order_items oi ON o.id = oi.order_id
            LEFT JOIN products p ON oi.product_id = p.id
            WHERE o.id = %s AND p.seller_id = %s
            LIMIT 1
        ''', (order_id, seller['id']))
        
        order_data = cursor.fetchone()
        if not order_data:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Order not found or not authorized'}), 404
        
        # Reset shipment status back to pending
        cursor.execute('''
            UPDATE shipments 
            SET status = 'pending'
            WHERE id = %s
        ''', (order_data['shipment_id'],))
        
        # Reset order status
        cursor.execute('''
            UPDATE orders 
            SET order_status = 'pending'
            WHERE id = %s
        ''', (order_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Rider pickup rejected: {rejection_reason}',
            'order_number': order_data['order_number']
        }), 200
        
    except Exception as e:
        print(f"[ERROR] seller_reject_rider_pickup: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ ORDER TRACKING ENDPOINTS FOR BUYERS ============
@app.route('/api/order-status/<order_id>', methods=['GET'])
def get_order_status(order_id):
    """API endpoint for buyers to check their order status in real-time"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        user_id = session.get('user_id')
        
        # Get order details - verify ownership
        cursor.execute('''
            SELECT 
                o.id, o.order_number, o.order_status, o.created_at, o.updated_at,
                o.total_amount, o.payment_method, o.rider_id, o.seller_confirmed_rider,
                o.buyer_approved_rider, u.first_name, u.last_name
            FROM orders o
            JOIN users u ON o.user_id = u.id
            WHERE o.id = %s AND o.user_id = %s
        ''', (order_id, user_id))
        
        order = cursor.fetchone()
        
        if not order:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        # Get order items
        cursor.execute('''
            SELECT product_name, quantity, unit_price, size, color
            FROM order_items
            WHERE order_id = %s
        ''', (order_id,))
        
        items = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Status progression timeline
        status_timeline = {
            'pending': {'label': 'Pending', 'emoji': '⏳', 'step': 1},
            'confirmed': {'label': 'Confirmed', 'emoji': '✔️', 'step': 2},
            'processing': {'label': 'Processing', 'emoji': '🔄', 'step': 3},
            'shipped': {'label': 'Shipped', 'emoji': '📦', 'step': 4},
            'delivered': {'label': 'Delivered', 'emoji': '✅', 'step': 5},
            'cancelled': {'label': 'Cancelled', 'emoji': '❌', 'step': 0},
            'returned': {'label': 'Returned', 'emoji': '↩️', 'step': 0}
        }
        
        current_status = order.get('order_status', 'pending')
        status_info = status_timeline.get(current_status, status_timeline['pending'])
        
        return jsonify({
            'success': True,
            'order': {
                'id': order['id'],
                'order_number': order['order_number'],
                'status': current_status,
                'status_label': status_info['label'],
                'status_emoji': status_info['emoji'],
                'progress_step': status_info['step'],
                'created_at': order['created_at'].isoformat() if order['created_at'] else None,
                'updated_at': order['updated_at'].isoformat() if order['updated_at'] else None,
                'total_amount': float(order['total_amount']),
                'payment_method': order['payment_method'],
                'customer_name': f"{order['first_name']} {order['last_name']}",
                'rider_id': order['rider_id'],
                'seller_confirmed_rider': order['seller_confirmed_rider'],
                'buyer_approved_rider': order['buyer_approved_rider']
            },
            'items': items,
            'timeline': status_timeline
        })
        
    except Exception as e:
        print(f"❌ Error getting order status: {str(e)}")
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user-orders-detailed', methods=['GET'])
def get_user_orders_detailed():
    """Get all orders for logged-in user with status details"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        user_id = session.get('user_id')
        
        # Get all user's orders with seller info
        cursor.execute('''
            SELECT 
                o.id, o.order_number, o.order_status, o.created_at, o.updated_at,
                o.total_amount, o.payment_method, s.store_name,
                COUNT(oi.id) as item_count
            FROM orders o
            LEFT JOIN sellers s ON o.seller_id = s.id
            LEFT JOIN order_items oi ON o.id = oi.order_id
            WHERE o.user_id = %s
            GROUP BY o.id
            ORDER BY o.created_at DESC
        ''', (user_id,))
        
        orders = cursor.fetchall()
        cursor.close()
        conn.close()
        
        status_emoji = {
            'pending': '⏳',
            'confirmed': '✔️',
            'processing': '🔄',
            'shipped': '📦',
            'delivered': '✅',
            'cancelled': '❌',
            'returned': '↩️'
        }
        
        return jsonify({
            'success': True,
            'orders': [
                {
                    'id': order['id'],
                    'order_number': order['order_number'],
                    'status': order['order_status'],
                    'status_emoji': status_emoji.get(order['order_status'], '📋'),
                    'created_at': order['created_at'].isoformat() if order['created_at'] else None,
                    'updated_at': order['updated_at'].isoformat() if order['updated_at'] else None,
                    'total_amount': float(order['total_amount']),
                    'payment_method': order['payment_method'],
                    'store_name': order['store_name'] or 'Store',
                    'item_count': order['item_count']
                }
                for order in orders
            ]
        })
        
    except Exception as e:
        print(f"❌ Error getting user orders: {str(e)}")
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500
# ============ END ORDER TRACKING ============

@app.route('/send-otp', methods=['POST'])
def send_otp():
    """Send OTP for verification"""
    try:
        data = request.get_json() if request.is_json else request.form
        email = data.get('email')
        phone = data.get('phone')
        verification_type = data.get('verification_type', 'email')
        purpose = data.get('purpose', 'registration')
        
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        ip_address = request.remote_addr
        
        otp_code, otp_id = OTPService.create_otp_record(
            conn, 
            email=email if verification_type == 'email' else None,
            phone=phone if verification_type == 'sms' else None,
            otp_type=verification_type,
            purpose=purpose,
            ip_address=ip_address
        )
        
        if not otp_code:
            conn.close()
            return jsonify({'success': False, 'message': 'Failed to generate OTP'}), 500
        
        success = False
        if verification_type == 'email' and email:
            success = OTPService.send_email_otp(email, otp_code, purpose)
        elif verification_type == 'sms' and phone:
            success = OTPService.send_sms_otp(phone, otp_code, purpose)
        
        conn.close()
        
        if success:
            session['pending_otp_verification'] = {
                'email': email,
                'phone': phone,
                'verification_type': verification_type,
                'purpose': purpose
            }
            return jsonify({'success': True, 'message': 'OTP sent successfully', 'otp_id': otp_id})
        else:
            return jsonify({'success': False, 'message': 'Failed to send OTP'}), 500
            
    except Exception as e:
        print(f"Error sending OTP: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/verify-otp-page')
def verify_otp_page():
    """Display OTP verification page"""
    pending_verification = session.get('pending_otp_verification')
    
    if not pending_verification:
        flash('No pending verification', 'error')
        return redirect(url_for('login'))
    
    verification_type = pending_verification.get('verification_type', 'email')
    email = pending_verification.get('email', '')
    phone = pending_verification.get('phone', '')
    purpose = pending_verification.get('purpose', 'registration')
    
    verification_target = email if verification_type == 'email' else phone
    
    return render_template('auth/verify_otp.html',
                         verification_type=verification_type,
                         verification_target=verification_target,
                         email=email,
                         phone=phone,
                         purpose=purpose)

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    """Verify OTP code"""
    try:
        data = request.get_json() if request.is_json else request.form
        otp_code = data.get('otp_code')
        email = data.get('email')
        phone = data.get('phone')
        purpose = data.get('purpose', 'registration')
        
        # Get email/phone from session if not provided in request
        pending_verification = session.get('pending_otp_verification', {})
        if not email and pending_verification.get('email'):
            email = pending_verification.get('email')
        if not phone and pending_verification.get('phone'):
            phone = pending_verification.get('phone')
        if not purpose or purpose == 'None':
            purpose = pending_verification.get('purpose', 'registration')
        
        print(f"[VERIFY OTP] OTP Code: {otp_code}, Email: {email}, Phone: {phone}, Purpose: {purpose}")
        print(f"[VERIFY OTP] Pending verification in session: {pending_verification}")
        print(f"[VERIFY OTP] Pending seller signup in session: {session.get('pending_seller_signup')}")
        
        if not otp_code or len(otp_code) != 6:
            return jsonify({'success': False, 'message': 'Invalid OTP code'}), 400
        
        if not email and not phone:
            return jsonify({'success': False, 'message': 'Email or phone number is required'}), 400
        
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        success, message = OTPService.verify_otp(conn, otp_code, email=email, phone=phone, purpose=purpose)
        
        if not success:
            OTPService.increment_attempt(conn, otp_code, email=email, phone=phone)
            conn.close()
            return jsonify({'success': False, 'message': message}), 400
        
        session.pop('pending_otp_verification', None)
        
        if purpose == 'registration':
            # Check for regular signup
            pending_signup = session.get('pending_signup')
            if pending_signup:
                conn = get_db()
                if conn:
                    try:
                        cursor = conn.cursor()
                        cursor.execute('INSERT INTO users (email, password, first_name, last_name, phone, role) VALUES (%s, %s, %s, %s, %s, %s)',
                                       (pending_signup['email'], pending_signup['password'], pending_signup['first_name'], 
                                        pending_signup['last_name'], pending_signup['phone'], pending_signup['role']))
                        conn.commit()
                        cursor.close()
                        conn.close()
                        session.pop('pending_signup', None)
                        session['email_verified'] = True
                        return jsonify({
                            'success': True, 
                            'message': 'Registration successful! Welcome to Varón.',
                            'redirect': url_for('login')
                        })
                    except Exception as e:
                        conn.close()
                        return jsonify({'success': False, 'message': f'Failed to complete registration: {str(e)}'}), 500
                else:
                    return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
            # Check for rider signup
            pending_rider_signup = session.get('pending_rider_signup')
            if pending_rider_signup:
                conn = get_db()
                if conn:
                    try:
                        cursor = conn.cursor(dictionary=True)
                        cursor.execute('''
                            INSERT INTO users (first_name, last_name, email, password, phone, role) 
                            VALUES (%s, %s, %s, %s, %s, 'rider')
                        ''', (pending_rider_signup['first_name'], pending_rider_signup['last_name'], 
                              pending_rider_signup['email'], pending_rider_signup['password'], pending_rider_signup['phone']))
                        user_id = cursor.lastrowid

                        # Create rider profile
                        cursor.execute('''
                            INSERT INTO riders (user_id, vehicle_type, license_number, vehicle_plate, service_area) 
                            VALUES (%s, %s, %s, %s, %s)
                        ''', (user_id, pending_rider_signup.get('vehicle_type', 'motorcycle'), pending_rider_signup['license_number'], 
                              pending_rider_signup.get('vehicle_plate', ''), pending_rider_signup['service_area']))

                        conn.commit()
                        cursor.close()
                        conn.close()
                        session.pop('pending_rider_signup', None)
                        session['email_verified'] = True
                        return jsonify({
                            'success': True, 
                            'message': 'Rider registration successful! Welcome to Varón.',
                            'redirect': url_for('login')
                        })
                    except Exception as e:
                        conn.close()
                        return jsonify({'success': False, 'message': f'Failed to complete rider registration: {str(e)}'}), 500
                else:
                    return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
            # Check for seller signup
            pending_seller_signup = session.get('pending_seller_signup')
            print(f"[VERIFY OTP] Checking for seller signup: {pending_seller_signup is not None}")
            
            if pending_seller_signup:
                print(f"[VERIFY OTP] Seller signup data found: {pending_seller_signup}")
                conn = get_db()
                if conn:
                    try:
                        cursor = conn.cursor(dictionary=True)
                        
                        # Check if this is an existing user registering as seller
                        is_existing_user = pending_seller_signup.get('is_existing_user', False)
                        existing_user_id = pending_seller_signup.get('existing_user_id')
                        
                        print(f"[VERIFY OTP] Is existing user: {is_existing_user}, User ID: {existing_user_id}")
                        
                        if is_existing_user and existing_user_id:
                            # Update existing user's role to seller
                            cursor.execute('UPDATE users SET role = %s WHERE id = %s', ('seller', existing_user_id))
                            user_id = existing_user_id
                            print(f"[VERIFY OTP] Updated existing user {user_id} to seller role")
                        else:
                            # Create new user account (use shop name as first/last name for sellers)
                            name_parts = pending_seller_signup['shop_name'].split(' ', 1)
                            first_name = name_parts[0] if len(name_parts) > 0 else pending_seller_signup['shop_name']
                            last_name = name_parts[1] if len(name_parts) > 1 else 'Shop'
                            
                            print(f"[VERIFY OTP] Creating new user: {first_name} {last_name}, Email: {pending_seller_signup['email']}")
                            
                            cursor.execute('INSERT INTO users (first_name, last_name, email, password, phone, role) VALUES (%s, %s, %s, %s, %s, %s)',
                                         (first_name, last_name, pending_seller_signup['email'], pending_seller_signup['password'], 
                                          pending_seller_signup['phone'], 'seller'))
                            user_id = cursor.lastrowid
                            print(f"[VERIFY OTP] Created new user with ID: {user_id}")

                        # Check if seller profile already exists
                        cursor.execute('SELECT id FROM sellers WHERE user_id = %s', (user_id,))
                        existing_seller = cursor.fetchone()
                        
                        if not existing_seller:
                            # Create store slug from shop name
                            store_slug = pending_seller_signup['shop_name'].lower().replace(' ', '-').replace("'", '')

                            # Create seller profile with pending status
                            cursor.execute('INSERT INTO sellers (user_id, store_name, store_slug, status) VALUES (%s, %s, %s, %s)',
                                         (user_id, pending_seller_signup['shop_name'], store_slug, 'pending'))
                            print(f"[VERIFY OTP] Created seller profile for user {user_id}")

                        conn.commit()
                        cursor.close()
                        conn.close()
                        session.pop('pending_seller_signup', None)
                        session['email_verified'] = True
                        
                        # Update session role if user was already logged in
                        if is_existing_user:
                            session['role'] = 'seller'
                            session['logged_in'] = True
                            session['user_id'] = existing_user_id
                            print(f"[VERIFY OTP] Redirecting existing user to seller dashboard")
                            return jsonify({
                                'success': True, 
                                'message': 'Seller account created successfully! Redirecting to seller dashboard...',
                                'redirect': url_for('seller_dashboard')
                            })
                        else:
                            print(f"[VERIFY OTP] Redirecting new user to login")
                            return jsonify({
                                'success': True, 
                                'message': 'Seller account created successfully! Please log in.',
                                'redirect': url_for('login')
                            })
                    except Exception as e:
                        import traceback
                        print(f"[VERIFY OTP] Error creating seller account: {str(e)}")
                        traceback.print_exc()
                        conn.close()
                        return jsonify({'success': False, 'message': f'Failed to complete seller registration: {str(e)}'}), 500
                else:
                    return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
            print(f"[VERIFY OTP] No pending seller signup found. Available session keys: {list(session.keys())}")
            return jsonify({'success': False, 'message': 'No pending signup data found. Please try registering again.'}), 400
        elif purpose == 'login':
            redirect_url = url_for('buyer_dashboard')
        else:
            redirect_url = url_for('index')
        
        return jsonify({
            'success': True, 
            'message': 'Verification successful',
            'redirect': redirect_url
        })
        
    except Exception as e:
        print(f"Error verifying OTP: {str(e)}")
        return jsonify({'success': False, 'message': 'Verification failed'}), 500

@app.route('/resend-otp', methods=['POST'])
def resend_otp():
    """Resend OTP code"""
    try:
        data = request.get_json() if request.is_json else request.form
        email = data.get('email')
        phone = data.get('phone')
        verification_type = data.get('verification_type', 'email')
        purpose = data.get('purpose', 'registration')
        
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        ip_address = request.remote_addr
        
        otp_code, otp_id = OTPService.create_otp_record(
            conn,
            email=email if verification_type == 'email' else None,
            phone=phone if verification_type == 'sms' else None,
            otp_type=verification_type,
            purpose=purpose,
            ip_address=ip_address
        )
        
        if not otp_code:
            conn.close()
            return jsonify({'success': False, 'message': 'Failed to generate OTP'}), 500
        
        success = False
        if verification_type == 'email' and email:
            success = OTPService.send_email_otp(email, otp_code, purpose)
        elif verification_type == 'sms' and phone:
            success = OTPService.send_sms_otp(phone, otp_code, purpose)
        
        conn.close()
        
        if success:
            return jsonify({'success': True, 'message': 'OTP resent successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to resend OTP'}), 500
            
    except Exception as e:
        print(f"Error resending OTP: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/cart/add', methods=['POST'])
def api_add_to_cart():
    """Add item to server-side cart in database"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        variant_id = data.get('variant_id')
        
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('''
            SELECT id, quantity FROM cart 
            WHERE user_id = %s AND product_id = %s AND (variant_id = %s OR (variant_id IS NULL AND %s IS NULL))
        ''', (user_id, product_id, variant_id, variant_id))
        
        existing = cursor.fetchone()
        
        if existing:
            new_quantity = existing['quantity'] + quantity
            cursor.execute('UPDATE cart SET quantity = %s WHERE id = %s', (new_quantity, existing['id']))
        else:
            cursor.execute('''
                INSERT INTO cart (user_id, product_id, variant_id, quantity)
                VALUES (%s, %s, %s, %s)
            ''', (user_id, product_id, variant_id, quantity))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Added to cart'})
    except Exception as e:
        print(f"Error adding to cart: {e}")
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cart/get', methods=['GET'])
def api_get_cart():
    """Get cart items from database and return unique product count for badge"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not logged in', 'unique_count': 0}), 401
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error', 'unique_count': 0}), 500
    
    try:
        user_id = session.get('user_id')
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('''
            SELECT 
                c.id as cart_id,
                c.product_id as id,
                c.quantity,
                p.name,
                p.price,
                pi.image_url,
                pv.size,
                pv.color
            FROM cart c
            JOIN products p ON c.product_id = p.id
            LEFT JOIN product_images pi ON p.id = pi.product_id AND pi.is_primary = 1
            LEFT JOIN product_variants pv ON c.variant_id = pv.id
            WHERE c.user_id = %s AND p.is_active = 1
        ''', (user_id,))
        
        items = cursor.fetchall()
        
        # Count unique products (not total quantity) for cart badge
        unique_product_count = len(set(item['id'] for item in items)) if items else 0
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'items': items,
            'unique_count': unique_product_count,
            'total_quantity': sum(item['quantity'] for item in items) if items else 0
        })
    except Exception as e:
        print(f"Error getting cart: {e}")
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': str(e), 'unique_count': 0}), 500

@app.route('/api/cart/update', methods=['POST'])
def api_update_cart():
    """Update cart item quantity"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        cart_id = data.get('cart_id')
        quantity = int(data.get('quantity', 1))
        
        cursor = conn.cursor()
        
        if quantity <= 0:
            cursor.execute('DELETE FROM cart WHERE id = %s AND user_id = %s', (cart_id, user_id))
        else:
            cursor.execute('UPDATE cart SET quantity = %s WHERE id = %s AND user_id = %s', (quantity, cart_id, user_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error updating cart: {e}")
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cart/remove', methods=['POST'])
def api_remove_from_cart():
    """Remove item from cart"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        cart_id = data.get('cart_id')
        
        cursor = conn.cursor()
        cursor.execute('DELETE FROM cart WHERE id = %s AND user_id = %s', (cart_id, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error removing from cart: {e}")
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cart/clear', methods=['POST'])
def api_clear_cart():
    """Clear all cart items"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
    try:
        user_id = session.get('user_id')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM cart WHERE user_id = %s', (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error clearing cart: {e}")
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ ADDRESS MANAGEMENT ============
@app.route('/api/addresses/get', methods=['GET'])
def api_get_addresses():
    """Get all saved addresses for the logged-in user"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
    try:
        user_id = session.get('user_id')
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('''
            SELECT * FROM addresses 
            WHERE user_id = %s 
            ORDER BY is_default DESC, created_at DESC
        ''', (user_id,))
        
        addresses = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'addresses': addresses
        })
    except Exception as e:
        print(f"Error getting addresses: {e}")
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/addresses/add', methods=['POST'])
def api_add_address():
    """Add a new address for the logged-in user"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
    try:
        user_id = session.get('user_id')
        cursor = conn.cursor()
        
        # If this is set as default, unset other defaults
        if data.get('is_default'):
            cursor.execute('UPDATE addresses SET is_default = FALSE WHERE user_id = %s', (user_id,))
        
        cursor.execute('''
            INSERT INTO addresses (
                user_id, address_type, full_name, phone, street_address, 
                barangay, city, province, postal_code, country, is_default
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            user_id,
            data.get('address_type', 'shipping'),
            data.get('full_name'),
            data.get('phone'),
            data.get('street_address'),
            data.get('barangay'),
            data.get('city'),
            data.get('province'),
            data.get('postal_code'),
            data.get('country', 'Philippines'),
            data.get('is_default', False)
        ))
        
        address_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'address_id': address_id,
            'message': 'Address saved successfully'
        })
    except Exception as e:
        print(f"Error adding address: {e}")
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/addresses/delete/<int:address_id>', methods=['DELETE'])
def api_delete_address(address_id):
    """Delete a saved address"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
    try:
        user_id = session.get('user_id')
        cursor = conn.cursor()
        
        # Ensure user owns this address
        cursor.execute('DELETE FROM addresses WHERE id = %s AND user_id = %s', (address_id, user_id))
        conn.commit()
        
        deleted = cursor.rowcount > 0
        cursor.close()
        conn.close()
        
        if deleted:
            return jsonify({'success': True, 'message': 'Address deleted'})
        else:
            return jsonify({'success': False, 'error': 'Address not found'}), 404
    except Exception as e:
        print(f"Error deleting address: {e}")
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/rider/available-orders', methods=['GET'])
def api_rider_available_orders():
    """Get available orders for riders in their service area"""
    if not session.get('logged_in') or session.get('role') != 'rider':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
    try:
        user_id = session.get('user_id')
        cursor = conn.cursor(dictionary=True)
        
        # Get rider's internal ID and service area
        cursor.execute('SELECT id, service_area FROM riders WHERE user_id = %s', (user_id,))
        rider = cursor.fetchone()
        
        if not rider or not rider.get('service_area'):
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'orders': [], 'service_area': None, 'message': 'No service area assigned'})
        
        rider_db_id = rider['id']
        rider_service_area = rider['service_area']
        
        # Parse service area - can be comma-separated list of regions/provinces/cities
        # Examples: "NCR,Cavite,Laguna" or "Manila,Cebu" or "South Luzon"
        service_areas = [area.strip() for area in rider_service_area.split(',') if area.strip()]
        
        print(f"[DEBUG] Rider {rider_db_id} service area: {rider_service_area}")
        print(f"[DEBUG] Parsed service areas: {service_areas}")
        
        # Get all waiting_for_pickup orders with seller confirmation (these are ready for rider pickup)
        cursor.execute('''
            SELECT o.id, o.order_number, o.user_id, o.total_amount, o.order_status, o.created_at,
                   CONCAT(a.street_address, ', ', a.city, ', ', a.province, ' ', IFNULL(a.postal_code, '')) as delivery_address,
                   a.province as delivery_province,
                   a.postal_code as delivery_postal_code,
                   a.city as delivery_city,
                   CONCAT(u.first_name, ' ', u.last_name) as customer_name,
                   u.phone as customer_phone,
                   u.email,
                   IFNULL(s.id, 0) as shipment_id,
                   IFNULL(s.status, 'pending') as shipment_status,
                   IFNULL(s.seller_confirmed, FALSE) as seller_confirmed,
                   IFNULL(s.rider_id, 0) as assigned_rider_id
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN addresses a ON o.shipping_address_id = a.id
            LEFT JOIN shipments s ON s.order_id = o.id
            WHERE o.order_status = 'waiting_for_pickup'
            AND IFNULL(s.rider_id, 0) = 0
            ORDER BY o.created_at DESC
        ''')
        
        all_orders = cursor.fetchall()
        print(f"[DEBUG] Found {len(all_orders)} confirmed/pending orders total")
        
        # Filter orders by rider's service area
        filtered_orders = []
        
        # Define region-to-cities mapping for better matching
        region_city_mapping = {
            'north luzon': ['baguio', 'la union', 'benguet', 'ifugao', 'mountain province', 'nueva vizcaya', 'nueva ecija', 'tarlac', 'pangasinan', 'quirino', 'aurora'],
            'south luzon': ['cavite', 'laguna', 'quezon', 'batangas', 'marinduque', 'oriental mindoro', 'occidental mindoro', 'romblon', 'tayabas'],
            'metro manila': ['ncr', 'manila', 'makati', 'quezon city', 'pasig', 'taguig', 'mandaluyong', 'san juan', 'marikina', 'parañaque', 'muntinlupa', 'las piñas', 'bacoor', 'caloocan', 'malabon', 'navotas', 'valenzuela'],
            'visayas': ['cebu', 'bohol', 'negros', 'antique', 'capiz', 'iloilo', 'guimaras', 'siquijor'],
            'mindanao': ['davao', 'cagayan de oro', 'zamboanga', 'butuan', 'general santos', 'koronadal', 'iligan', 'marawi', 'cotabato', 'surigao'],
            'bicol': ['albay', 'camarines norte', 'camarines sur', 'catanduanes', 'masbate', 'sorsogon'],
            'calabarzon': ['cavite', 'laguna', 'batangas', 'rizal', 'quezon'],
            'mimaropa': ['marinduque', 'mindoro', 'palawan', 'romblon'],
            'calamansi': ['camarines norte', 'camarines sur', 'albay'],
        }
        
        for order in all_orders:
            order_province = order.get('delivery_province', '').strip().lower()
            order_city = order.get('delivery_city', '').strip().lower()
            
            # Check if order matches rider's service area
            matches_service_area = False
            for service_area in service_areas:
                service_area_lower = service_area.lower()
                
                # Direct matches
                if (service_area_lower == order_province or
                    service_area_lower == order_city or
                    service_area_lower in order_province or
                    order_province in service_area_lower or
                    service_area_lower in order_city or
                    order_city in service_area_lower):
                    matches_service_area = True
                    print(f"[DEBUG] Order {order['order_number']}: DIRECT MATCH - {order_city}, {order_province} matches service area '{service_area}'")
                    break
                
                # Regional mapping checks
                if service_area_lower in region_city_mapping:
                    cities_in_region = region_city_mapping[service_area_lower]
                    if order_city in cities_in_region or order_province in cities_in_region:
                        matches_service_area = True
                        print(f"[DEBUG] Order {order['order_number']}: REGIONAL MATCH - {order_city}, {order_province} is in region '{service_area}'")
                        break
            
            if matches_service_area:
                filtered_orders.append(order)
            else:
                print(f"[DEBUG] Order {order['order_number']}: NO MATCH - {order_city}, {order_province} | Service areas: {service_areas}")
        
        print(f"[DEBUG] Filtered to {len(filtered_orders)} orders in service area")
        
        # If no shipment exists, create one for each order
        for order in filtered_orders:
            if order['shipment_id'] == 0:
                tracking_number = f"SHIP{order['id']}{int(time.time())}"
                cursor.execute('''
                    INSERT INTO shipments (order_id, tracking_number, status, seller_confirmed, created_at)
                    VALUES (%s, %s, 'pending', %s, NOW())
                ''', (order['id'], tracking_number, order.get('seller_confirmed', False)))
                conn.commit()
                order['shipment_id'] = cursor.lastrowid
            
            # Convert Decimal to float for JSON serialization
            if order.get('total_amount'):
                order['total_amount'] = float(order['total_amount'])
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'orders': filtered_orders,
            'service_area': rider_service_area,
            'total_filtered': len(filtered_orders),
            'total_available': len(all_orders)
        })
    except Exception as e:
        print(f"[ERROR] Error fetching available orders: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/rider/active-deliveries', methods=['GET'])
def api_rider_active_deliveries():
    """Get active deliveries for the logged-in rider filtered by their service region"""
    if not session.get('logged_in') or session.get('role') != 'rider':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
    try:
        rider_id = session.get('user_id')
        cursor = conn.cursor(dictionary=True)
        
        # Get rider's internal ID and service area from riders table
        cursor.execute('SELECT id, service_area FROM riders WHERE user_id = %s', (rider_id,))
        rider_record = cursor.fetchone()
        if not rider_record:
            print(f"⚠️ No rider record found for user_id: {rider_id}")
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'deliveries': [], 'service_area': None, 'message': 'No rider profile found'})
        
        rider_db_id = rider_record['id']
        service_area = rider_record.get('service_area', '')
        
        # Parse service_area - it can contain multiple regions separated by commas
        # e.g., "Manila, NCR" or "Metro Manila"
        service_areas = [area.strip() for area in service_area.split(',') if area.strip()]
        
        # Get filter parameters from query string
        filter_province = request.args.get('province', '').strip()
        filter_city = request.args.get('city', '').strip()
        filter_postal = request.args.get('postal_code', '').strip()
        
        cursor.execute('''
            SELECT o.id, o.order_number, o.user_id, o.total_amount, o.order_status, o.created_at,
                   CONCAT(a.street_address, ', ', a.city, ', ', a.province, ' ', IFNULL(a.postal_code, '')) as delivery_address,
                   u.first_name, u.last_name, u.email, u.phone as customer_phone,
                   CONCAT(u.first_name, ' ', u.last_name) as customer_name,
                   s.id as shipment_id, s.status as shipment_status,
                   s.seller_confirmed, s.seller_confirmed_at, s.rider_id,
                   a.province, a.city, a.postal_code
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN addresses a ON o.shipping_address_id = a.id
            JOIN shipments s ON s.order_id = o.id
            WHERE s.status IN ('pending', 'picked_up', 'in_transit', 'out_for_delivery')
            AND (s.rider_id = %s OR s.rider_id IS NULL)
            ORDER BY s.rider_id DESC, s.seller_confirmed DESC, o.created_at DESC
        ''', (rider_db_id,))
        # Get all unfiltered deliveries first
        all_deliveries = cursor.fetchall()
        
        print(f"[DEBUG] Query returned {len(all_deliveries)} deliveries for rider {rider_db_id}")
        for d in all_deliveries:
            print(f"  - Order {d['order_number']}: {d.get('city')}, {d.get('province')} | rider_id={d.get('rider_id')} | status={d.get('shipment_status')}")
        
        # Simple filtering: get all deliveries assigned to this rider, plus any with no rider assigned
        deliveries = []
        for delivery in all_deliveries:
            # Include if assigned to this rider OR if unassigned
            if delivery.get('rider_id') == rider_db_id or delivery.get('rider_id') is None:
                deliveries.append(delivery)
        
        print(f"[DEBUG] After rider filtering: {len(deliveries)} deliveries")
        
        # Apply optional user filters if provided
        if filter_province or filter_city or filter_postal:
            filtered_by_user = []
            for delivery in deliveries:
                order_province = delivery.get('province', '').strip().lower()
                order_city = delivery.get('city', '').strip().lower()
                order_postal = delivery.get('postal_code', '').strip() or ''
                
                # Check each filter
                if filter_province and filter_province.lower() != order_province:
                    continue
                if filter_city and filter_city.lower() != order_city:
                    continue
                if filter_postal and filter_postal not in order_postal:
                    continue
                
                filtered_by_user.append(delivery)
            
            deliveries = filtered_by_user
            print(f"[DEBUG] After user filters: {len(deliveries)} deliveries")
        
        # Convert Decimal to float and format dates for JSON serialization
        for delivery in deliveries:
            if delivery.get('total_amount'):
                delivery['total_amount'] = float(delivery['total_amount'])
            if delivery.get('created_at'):
                delivery['created_at'] = delivery['created_at'].isoformat() if hasattr(delivery['created_at'], 'isoformat') else str(delivery['created_at'])
            # Ensure seller_confirmed is boolean
            if delivery.get('seller_confirmed') is None:
                delivery['seller_confirmed'] = False
        
        print(f"[DEBUG] Final active deliveries for rider {rider_db_id}: {len(deliveries)} deliveries")
        for d in deliveries:
            print(f"  - Order {d['order_number']}: {d['city']}, {d['province']} | status={d['shipment_status']}, rider_id={d.get('rider_id')}")
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'deliveries': deliveries, 'service_area': service_area})
    except Exception as e:
        print(f"❌ Error fetching active deliveries: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': str(e), 'details': 'Check server logs for more information'}), 500

@app.route('/api/rider/delivery-history', methods=['GET'])
def api_rider_delivery_history():
    """Get delivery history with individual transaction records for the logged-in rider"""
    if not session.get('logged_in') or session.get('role') != 'rider':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
    try:
        rider_id = session.get('user_id')
        cursor = conn.cursor(dictionary=True)
        
        # Get rider's internal ID from riders table
        cursor.execute('SELECT id FROM riders WHERE user_id = %s', (rider_id,))
        rider_record = cursor.fetchone()
        if not rider_record:
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'history': []})
        
        rider_db_id = rider_record['id']
        
        # Get all completed transactions with order and rider transaction details
        cursor.execute('''
            SELECT o.id, o.order_number, o.user_id, o.total_amount, o.order_status, o.created_at,
                   CONCAT(a.street_address, ', ', a.city, ', ', a.province, ' ', IFNULL(a.postal_code, '')) as delivery_address,
                   u.first_name, u.last_name, u.email, u.phone as customer_phone,
                   CONCAT(u.first_name, ' ', u.last_name) as customer_name,
                   s.id as shipment_id, s.status as shipment_status, s.delivered_at,
                   a.province, a.city, a.postal_code,
                   rt.id as transaction_id, rt.earning_amount, rt.commission_rate, rt.completed_at
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN addresses a ON o.shipping_address_id = a.id
            JOIN shipments s ON s.order_id = o.id
            JOIN rider_transactions rt ON rt.shipment_id = s.id AND rt.rider_id = %s
            WHERE rt.status = 'completed'
            ORDER BY rt.completed_at DESC
            LIMIT 100
        ''', (rider_db_id,))
        
        history = cursor.fetchall()
        
        # Convert Decimal to float for JSON serialization
        for item in history:
            if item.get('total_amount'):
                item['total_amount'] = float(item['total_amount'])
            if item.get('earning_amount'):
                item['earning_amount'] = float(item['earning_amount'])
            if item.get('commission_rate'):
                item['commission_rate'] = float(item['commission_rate'])
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'history': history})
    except Exception as e:
        print(f"Error fetching delivery history: {e}")
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/rider/shipment-details/<int:shipment_id>', methods=['GET'])
def api_rider_shipment_details(shipment_id):
    """Get detailed shipment information for the logged-in rider"""
    if not session.get('logged_in') or session.get('role') != 'rider':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
    try:
        rider_id = session.get('user_id')
        cursor = conn.cursor(dictionary=True)
        
        # Get rider's internal ID
        cursor.execute('SELECT id FROM riders WHERE user_id = %s', (rider_id,))
        rider_record = cursor.fetchone()
        if not rider_record:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Rider not found'})
        
        rider_db_id = rider_record['id']
        
        # Get shipment details
        cursor.execute('''
            SELECT s.id, s.order_id, s.rider_id, s.status, s.created_at, s.updated_at, s.delivered_at,
                   o.order_number, o.total_amount, u.first_name, u.last_name,
                   CONCAT(u.first_name, ' ', u.last_name) as customer_name,
                   a.street_address, a.city, a.province, a.postal_code,
                   CONCAT(a.street_address, ', ', a.city, ', ', a.province, ' ', IFNULL(a.postal_code, '')) as delivery_address
            FROM shipments s
            JOIN orders o ON s.order_id = o.id
            JOIN users u ON o.user_id = u.id
            JOIN addresses a ON o.shipping_address_id = a.id
            WHERE s.id = %s AND (s.rider_id = %s OR s.rider_id IS NULL OR s.status = 'pending')
        ''', (shipment_id, rider_db_id))
        
        shipment = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not shipment:
            return jsonify({'success': False, 'error': 'Shipment not found or access denied'})
        
        # Convert Decimal to float
        if shipment.get('total_amount'):
            shipment['total_amount'] = float(shipment['total_amount'])
        
        return jsonify({'success': True, 'shipment': shipment})
    except Exception as e:
        print(f"Error fetching shipment details: {e}")
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/rider/earnings', methods=['GET'])
def api_rider_earnings():
    """Get earnings summary for the logged-in rider from rider_transactions table"""
    if not session.get('logged_in') or session.get('role') != 'rider':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
    try:
        user_id = session.get('user_id')
        cursor = conn.cursor(dictionary=True)
        
        # Get rider ID from user_id
        cursor.execute('SELECT id FROM riders WHERE user_id = %s', (user_id,))
        rider = cursor.fetchone()
        
        if not rider:
            return jsonify({'success': False, 'error': 'Rider not found'}), 404
        
        rider_id = rider['id']
        
        # Calculate today's earnings from rider_transactions (completed transactions)
        cursor.execute('''
            SELECT COALESCE(SUM(earning_amount), 0) as today_earnings
            FROM rider_transactions
            WHERE rider_id = %s AND status = 'completed'
            AND DATE(completed_at) = CURDATE()
        ''', (rider_id,))
        today_data = cursor.fetchone()
        today_earnings = float(today_data['today_earnings']) if today_data else 0
        
        # Calculate weekly earnings (last 7 days)
        cursor.execute('''
            SELECT COALESCE(SUM(earning_amount), 0) as weekly_earnings
            FROM rider_transactions
            WHERE rider_id = %s AND status = 'completed'
            AND completed_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        ''', (rider_id,))
        weekly_data = cursor.fetchone()
        weekly_earnings = float(weekly_data['weekly_earnings']) if weekly_data else 0
        
        # Calculate monthly earnings (current month)
        cursor.execute('''
            SELECT COALESCE(SUM(earning_amount), 0) as monthly_earnings
            FROM rider_transactions
            WHERE rider_id = %s AND status = 'completed'
            AND YEAR(completed_at) = YEAR(CURDATE())
            AND MONTH(completed_at) = MONTH(CURDATE())
        ''', (rider_id,))
        monthly_data = cursor.fetchone()
        monthly_earnings = float(monthly_data['monthly_earnings']) if monthly_data else 0
        
        # Calculate breakdown (simple distribution)
        # Assuming: 70% base fare, 20% tips, 10% bonuses
        base_fare = weekly_earnings * 0.70
        tips = weekly_earnings * 0.20
        bonuses = weekly_earnings * 0.10
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'today_earnings': today_earnings,
            'weekly_earnings': weekly_earnings,
            'monthly_earnings': monthly_earnings,
            'breakdown': {
                'base_fare': base_fare,
                'tips': tips,
                'bonuses': bonuses
            }
        })
    except Exception as e:
        print(f"Error fetching earnings: {e}")
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/rider/ratings', methods=['GET'])
def api_rider_ratings():
    """Get ratings and reviews for the logged-in rider"""
    if not session.get('logged_in') or session.get('role') != 'rider':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
    try:
        user_id = session.get('user_id')
        cursor = conn.cursor(dictionary=True)
        
        # Get rider ID
        cursor.execute('SELECT id FROM riders WHERE user_id = %s', (user_id,))
        rider = cursor.fetchone()
        if not rider:
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'overall_rating': 0, 'total_ratings': 0, 'reviews': []})
        
        rider_id = rider['id']
        
        # Get ratings from shipments/orders (customers can rate riders)
        # Check if there's a rider_ratings table, otherwise use mock data
        cursor.execute('''
            SELECT AVG(CAST(rating AS DECIMAL(3,1))) as avg_rating, COUNT(*) as total_count
            FROM shipments s
            JOIN orders o ON s.order_id = o.id
            WHERE s.rider_id = %s AND s.rider_rating IS NOT NULL
        ''', (rider_id,))
        
        rating_data = cursor.fetchone()
        overall_rating = float(rating_data['avg_rating']) if rating_data and rating_data['avg_rating'] else 4.8
        total_ratings = int(rating_data['total_count']) if rating_data else 0
        
        # Get individual reviews if available
        cursor.execute('''
            SELECT o.created_at, CONCAT(u.first_name, ' ', u.last_name) as customer_name,
                   s.rider_rating as rating, s.rider_comment as comment
            FROM shipments s
            JOIN orders o ON s.order_id = o.id
            JOIN users u ON o.user_id = u.id
            WHERE s.rider_id = %s AND s.rider_rating IS NOT NULL
            ORDER BY o.created_at DESC
            LIMIT 20
        ''', (rider_id,))
        
        reviews = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'overall_rating': overall_rating,
            'total_ratings': total_ratings,
            'reviews': reviews or []
        })
    except Exception as e:
        print(f"Error fetching ratings: {e}")
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/rider/update-profile', methods=['POST'])
def api_rider_update_profile():
    """Update rider profile information"""
    if not session.get('logged_in') or session.get('role') != 'rider':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
    try:
        user_id = session.get('user_id')
        cursor = conn.cursor(dictionary=True)
        
        # Get values from request
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        vehicle_type = data.get('vehicle_type', '').strip()
        license_number = data.get('license_number', '').strip()
        
        # Validation
        if not first_name or not last_name:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'First and last name are required'}), 400
        
        if not email:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Email is required'}), 400
        
        if not phone:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Phone number is required'}), 400
        
        # Update users table
        cursor.execute('''
            UPDATE users 
            SET first_name = %s, last_name = %s, email = %s, phone = %s
            WHERE id = %s
        ''', (first_name, last_name, email, phone, user_id))
        
        # Update riders table (vehicle_type, license_number)
        if vehicle_type or license_number:
            cursor.execute('SELECT id FROM riders WHERE user_id = %s', (user_id,))
            rider = cursor.fetchone()
            
            if rider:
                update_fields = []
                params = []
                
                if vehicle_type:
                    update_fields.append('vehicle_type = %s')
                    params.append(vehicle_type)
                
                if license_number:
                    update_fields.append('license_number = %s')
                    params.append(license_number)
                
                if update_fields:
                    params.append(rider['id'])
                    query = f"UPDATE riders SET {', '.join(update_fields)} WHERE id = %s"
                    cursor.execute(query, params)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Update session name if needed
        session['name'] = f"{first_name} {last_name}"
        
        return jsonify({'success': True, 'message': 'Profile updated successfully'})
    
    except Exception as e:
        print(f"Error updating profile: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/rider/change-password', methods=['POST'])
def api_rider_change_password():
    """Change rider password"""
    if not session.get('logged_in') or session.get('role') != 'rider':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
    try:
        user_id = session.get('user_id')
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        if not current_password or not new_password:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Both passwords are required'}), 400
        
        cursor = conn.cursor(dictionary=True)
        
        # Get current user
        cursor.execute('SELECT password FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Verify current password (plain text comparison for now)
        if user['password'] != current_password:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Current password is incorrect'}), 401
        
        # Validate new password
        if len(new_password) < 6:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'New password must be at least 6 characters'}), 400
        
        # Check for letters and numbers
        has_letter = any(c.isalpha() for c in new_password)
        has_number = any(c.isdigit() for c in new_password)
        
        if not (has_letter and has_number):
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Password must contain letters and numbers'}), 400
        
        # Update password
        cursor.execute('UPDATE users SET password = %s WHERE id = %s', (new_password, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Password changed successfully'})
    
    except Exception as e:
        print(f"Error changing password: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/rider/accept-order/<int:order_id>', methods=['POST'])
def api_rider_accept_order(order_id):
    """Accept an order for delivery"""
    if not session.get('logged_in') or session.get('role') != 'rider':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
    try:
        rider_id = session.get('user_id')
        cursor = conn.cursor()
        
        # Update order with rider_id and change status
        cursor.execute('''
            UPDATE orders 
            SET rider_id = %s, status = 'accepted'
            WHERE id = %s AND rider_id IS NULL
        ''', (rider_id, order_id))
        
        conn.commit()
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Order already taken or not found'}), 400
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Order accepted'})
    except Exception as e:
        print(f"Error accepting order: {e}")
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/rider/update-status/<int:order_id>', methods=['POST'])
def api_rider_update_status(order_id):
    """Update order delivery status"""
    if not session.get('logged_in') or session.get('role') != 'rider':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status not in ['in_transit', 'delivered']:
        return jsonify({'success': False, 'error': 'Invalid status'}), 400
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
    try:
        rider_id = session.get('user_id')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE orders 
            SET status = %s
            WHERE id = %s AND rider_id = %s
        ''', (new_status, order_id, rider_id))
        
        conn.commit()
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Order not found or unauthorized'}), 404
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': f'Order status updated to {new_status}'})
    except Exception as e:
        print(f"Error updating order status: {e}")
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/rider/accept-order', methods=['POST'])
def api_rider_accept_order_by_shipment():
    """Accept an order for delivery using shipment_id - sets status to picked_up"""
    if not session.get('logged_in') or session.get('role') != 'rider':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    shipment_id = data.get('shipment_id')
    
    if not shipment_id:
        return jsonify({'success': False, 'error': 'Missing shipment_id'}), 400
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
    try:
        user_id = session.get('user_id')
        cursor = conn.cursor(dictionary=True)
        
        # Get rider's internal ID
        cursor.execute('SELECT id FROM riders WHERE user_id = %s', (user_id,))
        rider_record = cursor.fetchone()
        if not rider_record:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Rider profile not found'}), 404
        
        rider_db_id = rider_record['id']
        
        # Verify shipment is in 'assigned_to_rider' or 'pending' status and seller has confirmed
        cursor.execute('''
            SELECT id, seller_confirmed FROM shipments 
            WHERE id = %s AND (status = 'assigned_to_rider' OR status = 'pending')
        ''', (shipment_id,))
        shipment = cursor.fetchone()
        
        if not shipment:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Shipment not found or not available for acceptance'}), 400
        
        # Update shipment status to 'picked_up' to indicate rider has accepted
        # This allows the delivery status buttons to appear
        cursor.execute('''
            UPDATE shipments 
            SET rider_id = %s, 
                status = 'picked_up',
                updated_at = NOW()
            WHERE id = %s
        ''', (rider_db_id, shipment_id))
        
        # Also update order status to 'released_to_rider' to indicate rider has accepted
        cursor.execute('''
            UPDATE orders
            SET order_status = 'released_to_rider', updated_at = NOW()
            WHERE id = (SELECT order_id FROM shipments WHERE id = %s)
        ''', (shipment_id,))
        
        conn.commit()
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Failed to accept order'}), 400
        
        cursor.close()
        conn.close()
        
        print(f"[✅] Rider {rider_db_id} accepted shipment {shipment_id} - status set to 'picked_up'")
        return jsonify({'success': True, 'message': 'Order accepted! You can now start the delivery.'})
    except Exception as e:
        print(f"Error accepting order: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/rider/update-delivery-status', methods=['POST'])
def api_rider_update_delivery_status():
    """Update delivery status using shipment_id"""
    if not session.get('logged_in') or session.get('role') != 'rider':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    shipment_id = data.get('shipment_id')
    new_status = data.get('status')
    
    if not shipment_id or not new_status:
        return jsonify({'success': False, 'error': 'Missing shipment_id or status'}), 400
    
    valid_statuses = ['picked_up', 'in_transit', 'out_for_delivery', 'delivered', 'failed']
    if new_status not in valid_statuses:
        return jsonify({'success': False, 'error': 'Invalid status'}), 400
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
    try:
        user_id = session.get('user_id')
        cursor = conn.cursor(dictionary=True)
        
        # Get rider's internal ID
        cursor.execute('SELECT id FROM riders WHERE user_id = %s', (user_id,))
        rider_record = cursor.fetchone()
        if not rider_record:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Rider profile not found'}), 404
        
        rider_db_id = rider_record['id']
        
        # Check if seller has confirmed (required for all status updates)
        cursor.execute('SELECT seller_confirmed FROM shipments WHERE id = %s AND rider_id = %s', (shipment_id, rider_db_id))
        shipment = cursor.fetchone()
        
        if not shipment:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Shipment not found or unauthorized'}), 404
        
        if not shipment['seller_confirmed']:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Cannot update status - awaiting seller confirmation'}), 403
        
        # Update shipment status
        update_fields = ['status = %s']
        params = [new_status]
        
        if new_status == 'delivered':
            update_fields.append('delivered_at = NOW()')
        elif new_status in ['picked_up', 'in_transit']:
            update_fields.append('shipped_at = NOW()')
        
        query = f'''
            UPDATE shipments 
            SET {', '.join(update_fields)}
            WHERE id = %s AND rider_id = %s
        '''
        params.extend([shipment_id, rider_db_id])
        
        cursor.execute(query, params)
        conn.commit()
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Shipment not found or unauthorized'}), 404
        
        # Get order ID for updates
        cursor.execute('SELECT order_id FROM shipments WHERE id = %s', (shipment_id,))
        shipment_result = cursor.fetchone()
        order_id = shipment_result['order_id'] if shipment_result else None
        
        # Update corresponding order status based on shipment status
        status_mapping = {
            'picked_up': 'released_to_rider',
            'in_transit': 'released_to_rider',
            'out_for_delivery': 'released_to_rider',
            'delivered': 'delivered'
        }
        
        if order_id and new_status in status_mapping:
            order_status = status_mapping[new_status]
            cursor.execute('''
                UPDATE orders
                SET order_status = %s, updated_at = NOW()
                WHERE id = %s
            ''', (order_status, order_id))
            conn.commit()
        
        # If delivered, also create rider transaction
        if new_status == 'delivered' and order_id:
            # Get order details for transaction
            cursor.execute('''
                SELECT id, total_amount
                FROM orders
                WHERE id = %s
            ''', (order_id,))
            order = cursor.fetchone()
            
            if order:
                # Calculate rider earning (15% commission) - convert Decimal to float first
                earning_amount = float(order['total_amount']) * 0.15
                
                # Create individual rider transaction record
                cursor.execute('''
                    INSERT INTO rider_transactions (
                        rider_id, order_id, shipment_id, earning_amount, 
                        commission_rate, status, completed_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
                ''', (rider_db_id, order['id'], shipment_id, earning_amount, 15.00, 'completed'))
                
                # Update rider's total earnings in riders table
                cursor.execute('''
                    UPDATE riders
                    SET total_deliveries = total_deliveries + 1,
                        earnings = earnings + %s
                    WHERE id = %s
                ''', (earning_amount, rider_db_id))
                
                conn.commit()
                print(f"[✅] Created rider transaction: Rider {rider_db_id}, Order {order['id']}, Amount ₱{earning_amount:.2f}")
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': f'Delivery status updated to {new_status}'})
    except Exception as e:
        print(f"Error updating delivery status: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Send OTP to email for password reset"""
    try:
        data = request.get_json()
        email = data.get('email') if data else request.form.get('email')
        
        if not email:
            return jsonify({'success': False, 'message': 'Email is required'}), 400
        
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT id, first_name FROM users WHERE email = %s', (email,))
            user = cursor.fetchone()
            
            if not user:
                cursor.close()
                conn.close()
                # Return error for better UX - user needs to know email is not registered
                return jsonify({
                    'success': False, 
                    'message': 'No account found with this email address. Please check and try again.'
                })
            
            # Generate and send OTP
            ip_address = request.remote_addr
            otp_code, otp_id = OTPService.create_otp_record(
                conn,
                email=email,
                otp_type='email',
                purpose='password_reset',
                ip_address=ip_address
            )
        except Exception as db_error:
            print(f"Database error in forgot password: {str(db_error)}")
            if cursor:
                cursor.close()
            if conn:
                conn.close()
            return jsonify({'success': False, 'message': 'Database error occurred'}), 500
        
        print(f"\n{'='*60}")
        print(f"🔑 PASSWORD RESET OTP FOR {email}")
        print(f"OTP CODE: {otp_code}")
        print(f"{'='*60}\n")
        
        # Store session data regardless of email send success (for development)
        session['password_reset'] = {
            'email': email,
            'user_id': user['id'],
            'otp_id': otp_id,
            'verified': False
        }
        
        cursor.close()
        conn.close()
        
        if otp_code:
            # Try to send email, but continue even if it fails (OTP is printed in console)
            email_sent = OTPService.send_email_otp(email, otp_code, 'password_reset')
            if email_sent:
                print(f"✅ Email sent successfully to {email}")
            else:
                print(f"⚠️ Email sending failed, but OTP is available in console")
            
            return jsonify({
                'success': True,
                'message': 'Verification code sent to your email'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to generate verification code. Please try again.'
            }), 500
            
    except Exception as e:
        print(f"Forgot password error: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred'}), 500

@app.route('/verify-reset-otp', methods=['POST'])
def verify_reset_otp():
    """Verify OTP for password reset"""
    try:
        data = request.get_json()
        otp_code = data.get('otp') if data else request.form.get('otp')
        
        if not otp_code or 'password_reset' not in session:
            return jsonify({'success': False, 'message': 'Invalid request'}), 400
        
        reset_data = session['password_reset']
        email = reset_data.get('email')
        
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        try:
            # Verify OTP (correct parameter order: conn, otp_code, email, phone, purpose)
            is_valid, message = OTPService.verify_otp(conn, otp_code, email=email, purpose='password_reset')
            
            if is_valid:
                # Mark as verified in session
                session['password_reset']['verified'] = True
                session.modified = True
                print(f"[DEBUG] Password reset OTP verified for {email}")
                conn.close()
                
                return jsonify({
                    'success': True,
                    'message': 'OTP verified successfully. You can now reset your password.'
                })
            else:
                conn.close()
                return jsonify({'success': False, 'message': message or 'Invalid OTP'}), 400
        except Exception as db_error:
            print(f"[ERROR] OTP verification error: {db_error}")
            conn.close()
            return jsonify({'success': False, 'message': 'Verification failed'}), 500
            
    except Exception as e:
        print(f"[ERROR] verify_reset_otp: {str(e)}")
        return jsonify({'success': False, 'message': 'Verification failed'}), 500

@app.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password after OTP verification"""
    try:
        data = request.get_json()
        new_password = data.get('new_password') if data else request.form.get('password')
        
        if not new_password or 'password_reset' not in session:
            return jsonify({'success': False, 'message': 'Invalid request'}), 400
        
        reset_data = session['password_reset']
        
        if not reset_data.get('verified'):
            return jsonify({'success': False, 'message': 'Please verify OTP first'}), 400
        
        # Validate password: minimum 6 characters with letters and numbers
        if len(new_password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters long'}), 400
        
        has_letter = any(c.isalpha() for c in new_password)
        has_number = any(c.isdigit() for c in new_password)
        
        if not (has_letter and has_number):
            return jsonify({'success': False, 'message': 'Password must contain both letters and numbers'}), 400
        
        email = reset_data.get('email')
        user_id = reset_data.get('user_id')
        
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        # Store password as plain text
        cursor.execute('UPDATE users SET password = %s WHERE id = %s AND email = %s',
                      (new_password, user_id, email))
        conn.commit()
        cursor.close()
        conn.close()
        
        # Clear password reset session
        session.pop('password_reset', None)
        
        return jsonify({
            'success': True,
            'message': 'Password reset successfully'
        })
        
    except Exception as e:
        print(f"Password reset error: {str(e)}")
        return jsonify({'success': False, 'message': 'Password reset failed'}), 500

# ===== PASSWORD CHANGE ROUTES =====
@app.route('/initiate-password-change', methods=['POST'])
def initiate_password_change():
    """Initiate password change by sending OTP"""
    if not session.get('logged_in') or session.get('role') != 'buyer':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        otp_method = data.get('otp_method')  # 'sms' or 'email'
        
        if otp_method not in ['sms', 'email']:
            return jsonify({'success': False, 'message': 'Invalid OTP method'}), 400
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        user_id = session.get('user_id')
        
        # Get user info
        cursor.execute('SELECT email, phone FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Create OTP record
        ip_address = request.remote_addr
        
        if otp_method == 'email':
            otp_code, otp_id = OTPService.create_otp_record(
                conn,
                email=user['email'],
                otp_type='email',
                purpose='password_change',
                ip_address=ip_address
            )
            
            if otp_code:
                email_sent = OTPService.send_email_otp(user['email'], otp_code, 'password_change')
                if email_sent:
                    print(f"✅ Password change OTP sent to {user['email']}")
                else:
                    print(f"⚠️ Email sending failed for password change OTP")
                
                print(f"\n{'='*60}")
                print(f"📧 PASSWORD CHANGE OTP FOR {user['email']}")
                print(f"OTP CODE: {otp_code}")
                print(f"{'='*60}\n")
        else:  # SMS
            otp_code, otp_id = OTPService.create_otp_record(
                conn,
                phone=user['phone'],
                otp_type='sms',
                purpose='password_change',
                ip_address=ip_address
            )
            
            if otp_code:
                print(f"\n{'='*60}")
                print(f"📱 PASSWORD CHANGE OTP FOR {user['phone']}")
                print(f"OTP CODE: {otp_code}")
                print(f"{'='*60}\n")
        
        cursor.close()
        conn.close()
        
        if otp_code:
            session['password_change'] = {
                'otp_id': otp_id,
                'otp_method': otp_method,
                'verified': False
            }
            
            return jsonify({
                'success': True,
                'message': f'Verification code sent to your {otp_method}',
                'otp_id': otp_id
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to generate verification code'}), 500
            
    except Exception as e:
        print(f"Error in initiate password change: {str(e)}")
        return jsonify({'success': False, 'message': 'Error sending verification code'}), 500

@app.route('/confirm-password-change', methods=['POST'])
def confirm_password_change():
    """Confirm password change with OTP verification"""
    if not session.get('logged_in') or session.get('role') != 'buyer':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        otp_code = data.get('otp', '')
        new_password = data.get('new_password', '')
        otp_id = data.get('otp_id')
        
        if not otp_code or not new_password or 'password_change' not in session:
            return jsonify({'success': False, 'message': 'Invalid request'}), 400
        
        # Validate password
        if len(new_password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400
        
        if not any(c.isalpha() for c in new_password) or not any(c.isdigit() for c in new_password):
            return jsonify({'success': False, 'message': 'Password must contain both letters and numbers'}), 400
        
        conn = get_db()
        
        # Verify OTP
        otp_method = session['password_change'].get('otp_method')
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT email, phone FROM users WHERE id = %s', (session.get('user_id'),))
        user = cursor.fetchone()
        
        if otp_method == 'email':
            is_valid, message = OTPService.verify_otp(conn, otp_code, email=user['email'], purpose='password_change')
        else:  # SMS
            is_valid, message = OTPService.verify_otp(conn, otp_code, phone=user['phone'], purpose='password_change')
        
        if is_valid:
            # Update password
            user_id = session.get('user_id')
            cursor.execute('UPDATE users SET password = %s WHERE id = %s', (new_password, user_id))
            conn.commit()
            
            cursor.close()
            conn.close()
            
            # Clear session
            session.pop('password_change', None)
            
            return jsonify({
                'success': True,
                'message': 'Password changed successfully'
            })
        else:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        print(f"Error confirming password change: {str(e)}")
        return jsonify({'success': False, 'message': 'Password change failed'}), 500

# ===== SHIPPING ADDRESS ROUTES =====
@app.route('/get-shipping-addresses')
def get_shipping_addresses():
    """Get all shipping addresses for logged-in buyer"""
    if not session.get('logged_in') or session.get('role') != 'buyer':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        user_id = session.get('user_id')
        
        cursor.execute('''SELECT id, full_name, phone, street_address, barangay, 
                         city, province, postal_code, country, address_type, is_default 
                         FROM addresses WHERE user_id = %s ORDER BY is_default DESC, created_at DESC''', 
                      (user_id,))
        addresses = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'addresses': addresses or []
        })
    except Exception as e:
        print(f"Error getting addresses: {str(e)}")
        return jsonify({'success': False, 'message': 'Error loading addresses'}), 500

@app.route('/get-address/<int:address_id>')
def get_address(address_id):
    """Get a specific address"""
    if not session.get('logged_in') or session.get('role') != 'buyer':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        user_id = session.get('user_id')
        
        cursor.execute('''SELECT id, full_name, phone, street_address, barangay, 
                         city, province, postal_code, country, address_type, is_default 
                         FROM addresses WHERE id = %s AND user_id = %s''', 
                      (address_id, user_id))
        address = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not address:
            return jsonify({'success': False, 'message': 'Address not found'}), 404
        
        return jsonify({
            'success': True,
            'address': address
        })
    except Exception as e:
        print(f"Error getting address: {str(e)}")
        return jsonify({'success': False, 'message': 'Error loading address'}), 500

@app.route('/save-shipping-address', methods=['POST'])
def save_shipping_address():
    """Save a new shipping address"""
    if not session.get('logged_in') or session.get('role') != 'buyer':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        
        # Validate required fields
        required_fields = ['full_name', 'phone', 'street_address', 'barangay', 'city', 'province', 'address_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field} is required'}), 400
        
        full_name = data.get('full_name', '').strip()
        phone = data.get('phone', '').strip()
        street_address = data.get('street_address', '').strip()
        barangay = data.get('barangay', '').strip()
        city = data.get('city', '').strip()
        province = data.get('province', '').strip()
        postal_code = data.get('postal_code', '').strip()
        address_type = data.get('address_type', 'shipping')
        is_default = data.get('is_default', False)
        
        conn = get_db()
        cursor = conn.cursor()
        
        # If this is to be default, unset other defaults
        if is_default:
            cursor.execute('UPDATE addresses SET is_default = FALSE WHERE user_id = %s', (user_id,))
        
        cursor.execute('''INSERT INTO addresses 
                         (user_id, full_name, phone, street_address, barangay, city, 
                          province, postal_code, country, address_type, is_default)
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                      (user_id, full_name, phone, street_address, barangay, city, 
                       province, postal_code, 'Philippines', address_type, is_default))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Address saved successfully'
        })
    except Exception as e:
        print(f"Error saving address: {str(e)}")
        return jsonify({'success': False, 'message': 'Error saving address'}), 500

@app.route('/update-shipping-address/<int:address_id>', methods=['PUT'])
def update_shipping_address(address_id):
    """Update an existing shipping address"""
    if not session.get('logged_in') or session.get('role') != 'buyer':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        
        # Validate required fields
        required_fields = ['full_name', 'phone', 'street_address', 'barangay', 'city', 'province', 'address_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field} is required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if address belongs to user
        cursor.execute('SELECT id FROM addresses WHERE id = %s AND user_id = %s', (address_id, user_id))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Address not found'}), 404
        
        full_name = data.get('full_name', '').strip()
        phone = data.get('phone', '').strip()
        street_address = data.get('street_address', '').strip()
        barangay = data.get('barangay', '').strip()
        city = data.get('city', '').strip()
        province = data.get('province', '').strip()
        postal_code = data.get('postal_code', '').strip()
        address_type = data.get('address_type', 'shipping')
        is_default = data.get('is_default', False)
        
        # If this is to be default, unset other defaults
        if is_default:
            cursor.execute('UPDATE addresses SET is_default = FALSE WHERE user_id = %s', (user_id,))
        
        cursor.execute('''UPDATE addresses SET 
                         full_name = %s, phone = %s, street_address = %s, barangay = %s,
                         city = %s, province = %s, postal_code = %s, address_type = %s, is_default = %s
                         WHERE id = %s AND user_id = %s''',
                      (full_name, phone, street_address, barangay, city, province, 
                       postal_code, address_type, is_default, address_id, user_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Address updated successfully'
        })
    except Exception as e:
        print(f"Error updating address: {str(e)}")
        return jsonify({'success': False, 'message': 'Error updating address'}), 500

@app.route('/delete-shipping-address/<int:address_id>', methods=['DELETE'])
def delete_shipping_address(address_id):
    """Delete a shipping address"""
    if not session.get('logged_in') or session.get('role') != 'buyer':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        user_id = session.get('user_id')
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if address belongs to user
        cursor.execute('SELECT is_default FROM addresses WHERE id = %s AND user_id = %s', (address_id, user_id))
        address = cursor.fetchone()
        
        if not address:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Address not found'}), 404
        
        # Delete the address
        cursor.execute('DELETE FROM addresses WHERE id = %s AND user_id = %s', (address_id, user_id))
        
        # If deleted address was default, set another as default
        if address[0]:  # is_default was True
            cursor.execute('''UPDATE addresses SET is_default = TRUE 
                             WHERE user_id = %s ORDER BY created_at DESC LIMIT 1''', (user_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Address deleted successfully'
        })
    except Exception as e:
        print(f"Error deleting address: {str(e)}")
        return jsonify({'success': False, 'message': 'Error deleting address'}), 500

@app.route('/set-default-address/<int:address_id>', methods=['PUT'])
def set_default_address(address_id):
    """Set an address as default"""
    if not session.get('logged_in') or session.get('role') != 'buyer':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        user_id = session.get('user_id')
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if address belongs to user
        cursor.execute('SELECT id FROM addresses WHERE id = %s AND user_id = %s', (address_id, user_id))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Address not found'}), 404
        
        # Unset all defaults for this user
        cursor.execute('UPDATE addresses SET is_default = FALSE WHERE user_id = %s', (user_id,))
        
        # Set this address as default
        cursor.execute('UPDATE addresses SET is_default = TRUE WHERE id = %s', (address_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Default address updated successfully'
        })
    except Exception as e:
        print(f"Error setting default address: {str(e)}")
        return jsonify({'success': False, 'message': 'Error updating default address'}), 500

# ============ NEW ORDER CONFIRMATION FLOW ENDPOINTS ============

@app.route('/seller/confirm-order', methods=['POST'])
def seller_confirm_order():
    """Seller confirms an order - immediately assigns to available rider in service area"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Not logged in'}), 401
        
        user_id = session['user_id']
        order_id = request.form.get('order_id')
        
        if not order_id:
            return jsonify({'success': False, 'error': 'Missing order_id'}), 400
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get the seller_id for this user
        cursor.execute('SELECT id FROM sellers WHERE user_id = %s', (user_id,))
        seller_result = cursor.fetchone()
        if not seller_result:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Not a seller'}), 403
        
        seller_id = seller_result['id']
        
        # Verify that this seller owns the products in this order
        verify_query = """
            SELECT o.id, o.shipping_address_id
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            LEFT JOIN products p ON oi.product_id = p.id
            WHERE o.id = %s AND p.seller_id = %s
            LIMIT 1
        """
        
        cursor.execute(verify_query, (order_id, seller_id))
        order_check = cursor.fetchone()
        
        if not order_check:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Order not found or you do not have permission'}), 403
        
        # Get order's shipping address location
        cursor.execute('SELECT province, city, postal_code FROM addresses WHERE id = %s', (order_check['shipping_address_id'],))
        address = cursor.fetchone()
        
        # Update order status to 'confirmed'
        cursor.execute('''
            UPDATE orders
            SET order_status = 'confirmed', updated_at = NOW()
            WHERE id = %s
        ''', (order_id,))
        
        conn.commit()
        
        # Find or create shipment
        cursor.execute('SELECT id FROM shipments WHERE order_id = %s', (order_id,))
        shipment = cursor.fetchone()
        
        if shipment:
            shipment_id = shipment['id']
            # Update existing shipment to mark seller as confirmed
            cursor.execute('''
                UPDATE shipments
                SET seller_confirmed = TRUE, seller_confirmed_at = NOW()
                WHERE id = %s
            ''', (shipment_id,))
            conn.commit()
        else:
            tracking_number = f"SHIP{order_id}{int(time.time())}"
            cursor.execute('''
                INSERT INTO shipments (order_id, tracking_number, status, seller_confirmed, seller_confirmed_at, created_at)
                VALUES (%s, %s, 'pending', TRUE, NOW(), NOW())
            ''', (order_id, tracking_number))
            conn.commit()
            shipment_id = cursor.lastrowid
        
        # Find an available rider in the same service area
        if address:
            # Build query to find riders covering this area
            cursor.execute('''
                SELECT id, user_id FROM riders 
                WHERE (service_area LIKE %s OR service_area LIKE %s OR service_area LIKE %s)
                AND status = 'active'
                AND is_available = TRUE
                LIMIT 1
            ''', (f'%{address["province"]}%', f'%{address["city"]}%', f'%{address["postal_code"]}%'))
            
            rider = cursor.fetchone()
            
            if rider:
                # Assign the rider to this shipment
                cursor.execute('''
                    UPDATE shipments 
                    SET rider_id = %s, seller_confirmed = TRUE, seller_confirmed_at = NOW()
                    WHERE id = %s
                ''', (rider['id'], shipment_id))
                conn.commit()
                print(f"[✅] Order {order_id} confirmed and assigned to rider {rider['id']}")
                
                cursor.close()
                conn.close()
                
                return jsonify({
                    'success': True,
                    'message': 'Order confirmed and assigned to a rider! They will start the delivery soon.',
                    'rider_assigned': True
                }), 200
            else:
                # No rider available - just set seller_confirmed to TRUE so rider will see it
                cursor.execute('''
                    UPDATE shipments 
                    SET seller_confirmed = TRUE, seller_confirmed_at = NOW()
                    WHERE id = %s
                ''', (shipment_id,))
                conn.commit()
                print(f"[⚠️] Order {order_id} confirmed but no rider available in area")
                
                cursor.close()
                conn.close()
                
                return jsonify({
                    'success': True,
                    'message': 'Order confirmed! Waiting for a rider to accept in your area.',
                    'rider_assigned': False
                }), 200
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Order confirmed! Waiting for a rider to accept.'
        }), 200
        
    except Exception as e:
        print(f"[ERROR] seller_confirm_order: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/seller/release-to-rider', methods=['POST'])
def seller_release_to_rider():
    """Seller releases order to rider for delivery with rider assignment"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Not logged in'}), 401
        
        user_id = session['user_id']
        order_id = request.form.get('order_id')
        rider_id = request.form.get('rider_id')
        new_status = request.form.get('new_status', 'released_to_rider')
        
        if not order_id or not rider_id:
            return jsonify({'success': False, 'error': 'Missing order_id or rider_id'}), 400
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get the seller_id for this user
        cursor.execute('SELECT id FROM sellers WHERE user_id = %s', (user_id,))
        seller_result = cursor.fetchone()
        if not seller_result:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Not a seller'}), 403
        
        seller_id = seller_result['id']
        
        # Verify that this seller owns the products in this order
        verify_query = """
            SELECT o.id, o.order_status
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            LEFT JOIN products p ON oi.product_id = p.id
            WHERE o.id = %s AND p.seller_id = %s
            LIMIT 1
        """
        
        cursor.execute(verify_query, (order_id, seller_id))
        order_check = cursor.fetchone()
        
        if not order_check:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Order not found or you do not have permission'}), 403
        
        # Verify rider exists and get rider info from users table
        cursor.execute('''
            SELECT r.id, u.first_name, u.last_name 
            FROM riders r
            JOIN users u ON r.user_id = u.id
            WHERE r.id = %s
        ''', (rider_id,))
        rider = cursor.fetchone()
        if not rider:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Rider not found'}), 404
        
        # Update order status to 'released_to_rider'
        cursor.execute('''
            UPDATE orders
            SET order_status = %s, updated_at = NOW()
            WHERE id = %s
        ''', (new_status, order_id))
        
        # Update shipment with rider assignment and seller confirmation
        cursor.execute('''
            UPDATE shipments
            SET rider_id = %s, 
                seller_confirmed = TRUE, 
                seller_confirmed_at = NOW(),
                status = 'assigned_to_rider',
                updated_at = NOW()
            WHERE order_id = %s
        ''', (rider_id, order_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        rider_name = f"{rider.get('first_name', '')} {rider.get('last_name', '')}".strip()
        print(f"[✅] Seller {seller_id} assigned rider {rider_id} ({rider_name}) to order {order_id}, status updated to {new_status}")
        
        return jsonify({
            'success': True,
            'message': f'Order assigned to rider {rider_name} for delivery!',
            'rider_id': rider_id,
            'rider_name': rider_name,
            'order_id': order_id,
            'new_status': new_status
        }), 200
    except Exception as e:
        print(f"[ERROR] seller_release_to_rider: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/sellers/available-riders', methods=['GET'])
def api_get_available_riders():
    """Get list of available active riders filtered by ORDER's delivery location (city/province), not seller's location.
    
    Uses order_id parameter to get delivery address and determine which region the order is in.
    Matches riders to the order's delivery region for nearby rider matching.
    Supports sub-regions: North Luzon, Central Luzon, South Luzon, Visayas, Mindanao
    """
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Not logged in'}), 401
        
        user_id = session['user_id']
        order_id = request.args.get('order_id')  # Get order_id from query parameter
        
        if not order_id:
            return jsonify({'success': False, 'error': 'Missing order_id parameter'}), 400
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Verify this is a seller
        cursor.execute('SELECT id FROM sellers WHERE user_id = %s', (user_id,))
        seller = cursor.fetchone()
        if not seller:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Not a seller'}), 403
        
        # Get order's shipping address to determine delivery region
        cursor.execute('''
            SELECT a.city, a.province, a.barangay
            FROM orders o
            JOIN addresses a ON o.shipping_address_id = a.id
            WHERE o.id = %s
        ''', (order_id,))
        
        address = cursor.fetchone()
        if not address:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Order or shipping address not found'}), 404
        
        # Determine delivery region from order's address
        delivery_city = address.get('city', '')
        delivery_province = address.get('province', '')
        delivery_region = get_delivery_region(delivery_city, delivery_province)
        
        print(f"[📍] Order {order_id} delivery location: {delivery_city}, {delivery_province} → Region: {delivery_region}")
        
        if delivery_region == 'Unknown':
            print(f"[⚠️] WARNING: Could not determine region for {delivery_city}, {delivery_province}")
            # Still try to fetch riders matching "All areas"
            region_match = 'All areas'
        else:
            region_match = delivery_region
        
        # Get all available riders filtered by delivery region (not seller's region!)
        # Match riders to the ORDER's delivery region for nearby rider assignments
        cursor.execute('''
            SELECT r.id, 
                   u.first_name, u.last_name,
                   r.vehicle_type, r.service_area, r.sub_region,
                   r.is_available, r.status, r.created_at,
                   COUNT(DISTINCT s.id) as total_deliveries,
                   COALESCE(r.rating, 0) as rating
            FROM riders r
            JOIN users u ON r.user_id = u.id
            LEFT JOIN shipments s ON r.id = s.rider_id AND s.status = 'delivered'
            WHERE r.is_available = TRUE 
              AND r.status IN ('active', 'approved')
              AND (r.sub_region = %s OR r.sub_region = 'All areas')
            GROUP BY r.id
            ORDER BY COALESCE(r.rating, 0) DESC, r.created_at ASC
            LIMIT 50
        ''', (region_match,))
        
        riders = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Format rider data
        formatted_riders = []
        for rider in riders:
            formatted_riders.append({
                'id': rider['id'],
                'first_name': rider.get('first_name', ''),
                'last_name': rider.get('last_name', ''),
                'vehicle_type': rider.get('vehicle_type', 'Not specified'),
                'service_area': rider.get('service_area', 'All areas'),
                'sub_region': rider.get('sub_region', 'All areas'),
                'rating': float(rider.get('rating', 0)) if rider.get('rating') else 0,
                'total_deliveries': int(rider.get('total_deliveries', 0)),
                'is_available': bool(rider.get('is_available', True)),
                'status': rider.get('status', 'active')
            })
        
        print(f"[✅] Retrieved {len(formatted_riders)} available riders for delivery region: {region_match} (Order location: {delivery_city}, {delivery_province})")
        if len(formatted_riders) == 0:
            print(f"[⚠️] WARNING: No available riders found for {region_match} - check riders table sub_region assignment and availability")
        
        return jsonify({
            'success': True,
            'riders': formatted_riders,
            'count': len(formatted_riders),
            'delivery_region': delivery_region,
            'delivery_location': {
                'city': delivery_city,
                'province': delivery_province
            }
        }), 200
    except Exception as e:
        print(f"[ERROR] api_get_available_riders: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/seller/approve-rider-for-delivery', methods=['POST'])
def seller_approve_rider_for_delivery():
    """Seller approves the assigned rider for delivery"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Not logged in'}), 401
        
        user_id = session['user_id']
        order_id = request.form.get('order_id')
        rider_id = request.form.get('rider_id')
        
        if not order_id or not rider_id:
            return jsonify({'success': False, 'error': 'Missing order_id or rider_id'}), 400
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get the seller_id for this user
        cursor.execute('SELECT id FROM sellers WHERE user_id = %s', (user_id,))
        seller_result = cursor.fetchone()
        if not seller_result:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Not a seller'}), 403
        
        seller_id = seller_result['id']
        
        # Verify that this seller owns the products in this order
        verify_query = """
            SELECT o.id
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            LEFT JOIN products p ON oi.product_id = p.id
            WHERE o.id = %s AND p.seller_id = %s
            LIMIT 1
        """
        
        cursor.execute(verify_query, (order_id, seller_id))
        order_check = cursor.fetchone()
        
        if not order_check:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Order not found or you do not have permission'}), 403
        
        # Update order to mark seller confirmed rider
        cursor.execute('''
            UPDATE orders
            SET seller_confirmed_rider = TRUE, updated_at = NOW()
            WHERE id = %s
        ''', (order_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"[✅] Seller {seller_id} approved rider {rider_id} for order {order_id}")
        
        return jsonify({
            'success': True,
            'message': 'Rider approved for delivery!'
        }), 200
    except Exception as e:
        print(f"[ERROR] seller_approve_rider_for_delivery: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/rider-details/<rider_id>', methods=['GET'])
def get_rider_details(rider_id):
    """Get rider details for display in approval modal"""
    try:
        if not session.get('logged_in'):
            return jsonify({'success': False, 'error': 'Not logged in'}), 401
        
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Get rider information
        cursor.execute('''
            SELECT 
                u.id, u.first_name, u.last_name, u.phone,
                r.rating, r.profile_image_url
            FROM users u
            LEFT JOIN riders r ON u.id = r.user_id
            WHERE u.id = %s AND u.role = 'rider'
        ''', (rider_id,))
        
        rider = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not rider:
            return jsonify({'success': False, 'error': 'Rider not found'}), 404
        
        return jsonify({
            'success': True,
            'rider': {
                'id': rider['id'],
                'first_name': rider['first_name'],
                'last_name': rider['last_name'],
                'phone': rider['phone'],
                'rating': rider['rating'] or 0,
                'profile_image_url': rider['profile_image_url']
            }
        }), 200
    except Exception as e:
        print(f"[ERROR] get_rider_details: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/order-rider-info/<order_id>', methods=['GET'])
def get_order_rider_info(order_id):
    """Get rider info for an order"""
    try:
        if not session.get('logged_in'):
            return jsonify({'success': False, 'error': 'Not logged in'}), 401
        
        user_id = session.get('user_id')
        
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Verify order ownership
        cursor.execute('''
            SELECT rider_id FROM orders
            WHERE id = %s AND user_id = %s
        ''', (order_id, user_id))
        
        order = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not order:
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        if not order.get('rider_id'):
            return jsonify({'success': False, 'error': 'No rider assigned'}), 400
        
        return jsonify({
            'success': True,
            'rider_id': order['rider_id']
        }), 200
    except Exception as e:
        print(f"[ERROR] get_order_rider_info: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/approve-rider-delivery', methods=['POST'])
def approve_rider_delivery():
    """Buyer approves rider for delivery"""
    try:
        if not session.get('logged_in'):
            return jsonify({'success': False, 'error': 'Not logged in'}), 401
        
        user_id = session.get('user_id')
        data = request.json
        order_id = data.get('order_id')
        rider_id = data.get('rider_id')
        
        if not order_id or not rider_id:
            return jsonify({'success': False, 'error': 'Missing order_id or rider_id'}), 400
        
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Verify order ownership
        cursor.execute('''
            SELECT id FROM orders
            WHERE id = %s AND user_id = %s
        ''', (order_id, user_id))
        
        order = cursor.fetchone()
        if not order:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        # Mark order as approved for rider delivery
        cursor.execute('''
            UPDATE orders
            SET buyer_approved_rider = TRUE, updated_at = NOW()
            WHERE id = %s
        ''', (order_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"[✅] Buyer {user_id} approved rider {rider_id} for order {order_id}")
        
        return jsonify({
            'success': True,
            'message': 'Rider approved for delivery!'
        }), 200
    except Exception as e:
        print(f"[ERROR] approve_rider_delivery: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ END ORDER CONFIRMATION FLOW ENDPOINTS ============

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
