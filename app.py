from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
import os
import mysql.connector

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=BASE_DIR, static_folder=BASE_DIR, static_url_path='')
app.secret_key = 'your-secret-key'
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'varon'
}

def get_db():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Exception as err:
        print(f"[DB ERROR] {err}")
        return None

def init_db():
    try:
        conn = mysql.connector.connect(host=DB_CONFIG['host'], user=DB_CONFIG['user'], password=DB_CONFIG['password'])
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        conn.database = DB_CONFIG['database']
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            email VARCHAR(190) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            role ENUM('buyer', 'seller', 'admin', 'rider') NOT NULL DEFAULT 'buyer',
            phone VARCHAR(20),
            status ENUM('active', 'inactive', 'pending', 'suspended') DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        
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
            status ENUM('pending', 'approved', 'rejected', 'suspended') DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        
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
            INDEX idx_active (is_active)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS product_images (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id INT NOT NULL,
            image_url VARCHAR(500) NOT NULL,
            is_primary BOOLEAN DEFAULT FALSE,
            sort_order INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS product_variants (
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
            INDEX idx_product (product_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        
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
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
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
            INDEX idx_status (order_status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        
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
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS riders (
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
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
            FOREIGN KEY (rider_id) REFERENCES riders(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        
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
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS coupons (
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        
        conn.commit()
        print("[DB] All tables created successfully!")
        cursor.close()
        conn.close()
    except Exception as err:
        print(f"[DB INIT ERROR] {err}")

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/script.js')
def static_script():
    return send_from_directory(BASE_DIR, 'script.js')

@app.route('/shop')
def shop():
    return render_template('shop.html')

@app.route('/browse')
def browse():
    return render_template('browse.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            flash('Email and password are required', 'error')
            return redirect(url_for('login'))
        conn = get_db()
        if not conn:
            flash('Database connection failed', 'error')
            return redirect(url_for('login'))
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
                if user['role'] == 'admin':
                    return redirect('/dashboard')
                else:
                    return redirect(url_for('index'))
            flash('Invalid email or password', 'error')
            return redirect(url_for('login'))
        except Exception as err:
            flash(f'Login error: {err}', 'error')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'buyer')
        if not email or not password:
            flash('Email and password are required', 'error')
            return redirect(url_for('signup'))
        conn = get_db()
        if not conn:
            flash('Database connection failed', 'error')
            return redirect(url_for('signup'))
        try:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (email, password, role) VALUES (%s, %s, %s)',
                           (email, password, role))
            conn.commit()
            cursor.close()
            conn.close()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as err:
            flash(f'Registration failed: {err}', 'error')
            return redirect(url_for('signup'))
    return render_template('signup.html')

@app.route('/signup/rider', methods=['GET', 'POST'])
def signup_rider():
    if request.method == 'POST':
        try:
            # Extract user information
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            email = request.form.get('email')
            password = request.form.get('password')
            phone = request.form.get('phone')
            
            # Extract rider specific information
            vehicle_type = request.form.get('vehicle_type')
            license_number = request.form.get('license_number')  # Updated to match form field
            vehicle_plate = request.form.get('vehicle_plate')    # Updated to match form field
            service_area = request.form.get('service_area')      # Added service area

            # Validate required fields
            required_fields = {
                'First Name': first_name,
                'Last Name': last_name,
                'Email': email,
                'Password': password,
                'Vehicle Type': vehicle_type
            }
            
            missing_fields = [field for field, value in required_fields.items() if not value]
            if missing_fields:
                flash(f"Required fields missing: {', '.join(missing_fields)}", 'error')
                return redirect(url_for('signup_rider'))

            conn = get_db()
            if not conn:
                flash('Database connection failed', 'error')
                return redirect(url_for('signup_rider'))

            cursor = conn.cursor(dictionary=True)
            
            # Check if email already exists
            cursor.execute('SELECT id FROM users WHERE email = %s', (email,))
            if cursor.fetchone():
                flash('Email already registered', 'error')
                return redirect(url_for('signup_rider'))
            
            # Begin transaction
            cursor.execute('START TRANSACTION')
            
            # Create user with rider role
            cursor.execute('''
                INSERT INTO users (first_name, last_name, email, password, phone, role, status)
                VALUES (%s, %s, %s, %s, %s, 'rider', 'pending')
            ''', (first_name, last_name, email, password, phone))
            
            # Get the new user's ID
            user_id = cursor.lastrowid
            
            # Create rider record
            cursor.execute('''
                INSERT INTO riders (user_id, vehicle_type, license_number, vehicle_plate, service_area, status)
                VALUES (%s, %s, %s, %s, %s, 'pending')
            ''', (user_id, vehicle_type, license_number, vehicle_plate, service_area))
            
            # Commit transaction
            conn.commit()
            
            # Log the registration
            cursor.execute('''
                INSERT INTO activity_logs (user_id, action, entity_type, entity_id, description)
                VALUES (%s, 'REGISTER', 'rider', %s, 'New rider registration')
            ''', (user_id, cursor.lastrowid))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Rider registration successful! Your account is pending approval.', 'success')
            return redirect(url_for('login'))
            
        except mysql.connector.Error as err:
            if conn:
                conn.rollback()
            if err.errno == 1062:  # Duplicate entry error
                flash('This email is already registered', 'error')
            else:
                flash(f'Registration failed: {err}', 'error')
            return redirect(url_for('signup_rider'))
        except Exception as err:
            if conn:
                conn.rollback()
            flash(f'Registration failed: {err}', 'error')
            return redirect(url_for('signup_rider'))
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals() and conn.is_connected():
                conn.close()
            
    return render_template('signupRider.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
