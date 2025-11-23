from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, jsonify
import os
import mysql.connector
import time
from dotenv import load_dotenv
from utils.otp_service import OTPService

# Load environment variables
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder='templates', static_folder='static', static_url_path='/static')
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production-please')

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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
            FOREIGN KEY (rider_id) REFERENCES riders(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
        
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
        
        # Coupons/Discounts
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
            start_date DATETIME NOT NULL,
            end_date DATETIME NOT NULL,
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
                WHERE p.is_active = 1 AND p.archive_status = 'active'
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
                
                # Get available sizes and colors from variants
                cursor.execute('''
                    SELECT DISTINCT size, color
                    FROM product_variants
                    WHERE product_id = %s AND stock_quantity > 0
                    ORDER BY size, color
                ''', (product_id,))
                
                variants = cursor.fetchall()
                
                # Extract unique sizes and colors
                sizes = sorted(list(set([v['size'] for v in variants if v['size']])))
                colors = sorted(list(set([v['color'] for v in variants if v['color']])))
            
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
        
        # First, create or get shipping address
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
        
        conn.commit()
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
            SELECT oi.*, pi.image_url
            FROM order_items oi
            LEFT JOIN products p ON oi.product_id = p.id
            LEFT JOIN product_images pi ON p.id = pi.product_id AND pi.is_primary = 1
            WHERE oi.order_id = %s
        ''', (order['id'],))
        
        items = cursor.fetchall()
        
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
            
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
        try:
            cursor = conn.cursor()
            
            # Check if email already exists
            cursor.execute('SELECT id FROM users WHERE email = %s', (email,))
            if cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'message': 'Email already registered'}), 400
            
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
                conn.close()
                return jsonify({'success': False, 'message': 'Failed to generate OTP'}), 500
            
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
                return jsonify({'success': False, 'message': 'Failed to send OTP'}), 500
                
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
        vehicle_type = request.form.get('vehicle_type')
        vehicle_plate = request.form.get('vehicle_plate')
        license_number = request.form.get('license_number')
        service_area = request.form.get('service_area')
        tnc = request.form.get('tnc')

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

        # Only require plate and license if not bicycle
        if vehicle_type != 'bicycle':
            required_fields['vehicle_plate'] = vehicle_plate
            required_fields['license_number'] = license_number

        # Check required fields
        missing_fields = [field for field, value in required_fields.items() if not value]
        if missing_fields:
            return jsonify({'success': False, 'message': f'Missing required fields: {", ".join(missing_fields)}'}), 400

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

            # Check if email already exists
            cursor.execute('SELECT id FROM users WHERE email = %s', (email,))
            if cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'message': 'Email already registered'}), 400

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
                conn.close()
                return jsonify({'success': False, 'message': 'Failed to generate OTP'}), 500
            
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
                return jsonify({'success': False, 'message': 'Failed to send OTP'}), 500
                
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

        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500

        try:
            cursor = conn.cursor(dictionary=True)

            # Check if email already exists
            cursor.execute('SELECT id FROM users WHERE email = %s', (email,))
            if cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'message': 'Email already registered'}), 400

            # Check if shop name exists
            cursor.execute('SELECT id FROM sellers WHERE store_name = %s', (shop_name,))
            if cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'message': 'Shop name already taken'}), 400

            # Store seller signup data in session for later use
            session['pending_seller_signup'] = {
                'email': email,
                'password': password,
                'phone': phone,
                'shop_name': shop_name
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
                conn.close()
                return jsonify({'success': False, 'message': 'Failed to generate OTP'}), 500
            
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
                return jsonify({'success': False, 'message': 'Failed to send OTP'}), 500
                
        except Exception as err:
            return jsonify({'success': False, 'message': f'Registration failed: {str(err)}'}), 500

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
        pending_products = cursor.fetchone()['count']
        
        # Get pending sellers count
        cursor.execute("SELECT COUNT(*) as count FROM sellers WHERE status = 'pending'")
        pending_sellers = cursor.fetchone()['count']
        
        # Get pending riders count
        cursor.execute("SELECT COUNT(*) as count FROM riders WHERE status = 'pending'")
        pending_riders = cursor.fetchone()['count']
        
        # Get total orders
        cursor.execute('SELECT COUNT(*) as count FROM orders')
        total_orders = cursor.fetchone()['count']
        
        # Get total users
        cursor.execute('SELECT COUNT(*) as count FROM users')
        total_users = cursor.fetchone()['count']
        
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
        
        # Get all pending products
        cursor.execute('''
            SELECT p.*, s.store_name, u.email as seller_email,
                   COALESCE(i.stock_quantity, 0) as stock
            FROM products p
            JOIN sellers s ON p.seller_id = s.id
            JOIN users u ON s.user_id = u.id
            LEFT JOIN inventory i ON p.id = i.product_id
            WHERE p.is_active = 0
            ORDER BY p.created_at DESC
        ''')
        pending_products = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({'products': pending_products}), 200
        
    except Exception as err:
        return jsonify({'error': str(err)}), 500

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
        
        # Delete product and related inventory
        cursor.execute('DELETE FROM inventory WHERE product_id = %s', (product_id,))
        cursor.execute('DELETE FROM products WHERE id = %s', (product_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Product rejected and removed'}), 200
        
    except Exception as err:
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
        
        pending_count = cursor.fetchone()['count']
        
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
        
        pending_count = cursor.fetchone()['count']
        
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

@app.route('/seller-dashboard')
def seller_dashboard():
    if not session.get('logged_in') or session.get('role') != 'seller':
        flash('Access denied. Please log in as a seller.', 'error')
        return redirect(url_for('login'))
    
    conn = get_db()
    if not conn:
        flash('Database error', 'error')
        return redirect(url_for('login'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        user_id = session.get('user_id')
        
        # Get seller info
        cursor.execute('''
            SELECT s.*, u.first_name, u.last_name, u.email 
            FROM sellers s 
            JOIN users u ON s.user_id = u.id 
            WHERE s.user_id = %s
        ''', (user_id,))
        seller = cursor.fetchone()
        
        if not seller:
            flash('Seller profile not found', 'error')
            return redirect(url_for('login'))
        
        # Get product count
        cursor.execute('SELECT COUNT(*) as count FROM products WHERE seller_id = %s', (seller['id'],))
        product_count = cursor.fetchone()['count']
        
        # Get low stock products
        cursor.execute('''
            SELECT p.name, p.id, i.stock_quantity, i.low_stock_threshold
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            WHERE p.seller_id = %s AND i.stock_quantity <= i.low_stock_threshold
            ORDER BY i.stock_quantity ASC
            LIMIT 5
        ''', (seller['id'],))
        low_stock = cursor.fetchall()
        
        # Get recent orders
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
        ''', (seller['id'],))
        recent_orders = cursor.fetchall()
        
        # Get today's sales
        cursor.execute('''
            SELECT COALESCE(SUM(total_amount), 0) as today_sales
            FROM orders
            WHERE seller_id = %s AND DATE(created_at) = CURDATE()
            AND order_status != 'cancelled'
        ''', (seller['id'],))
        today_sales = cursor.fetchone()['today_sales']
        
        # Get pending orders count
        cursor.execute('''
            SELECT COUNT(*) as pending_count
            FROM orders
            WHERE seller_id = %s AND order_status = 'pending'
        ''', (seller['id'],))
        pending_orders = cursor.fetchone()['pending_count']
        
        # Get top performing products
        cursor.execute('''
            SELECT p.id, p.name, p.sales_count
            FROM products p
            WHERE p.seller_id = %s AND p.is_active = 1
            ORDER BY p.sales_count DESC
            LIMIT 3
        ''', (seller['id'],))
        top_products = cursor.fetchall()
        
        # Get weekly sales (last 7 days)
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
        ''', (seller['id'],))
        weekly_sales_raw = cursor.fetchall()
        
        # Create a dictionary for all days of the week with default 0
        days_order = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        weekly_sales = {day: 0 for day in days_order}
        
        # Fill in actual sales data
        for row in weekly_sales_raw:
            weekly_sales[row['day_name']] = float(row['daily_sales'])
        
        # Get max sales for percentage calculation (ensure it's never 0 to prevent division by zero)
        max_value = max(weekly_sales.values()) if weekly_sales.values() else 0
        max_weekly_sales = max_value if max_value > 0 else 1
        
        cursor.close()
        conn.close()
        
        return render_template('pages/SellerDashboard.html',
                             seller=seller,
                             product_count=product_count,
                             low_stock=low_stock,
                             recent_orders=recent_orders,
                             today_sales=today_sales,
                             pending_orders=pending_orders,
                             top_products=top_products,
                             weekly_sales=weekly_sales,
                             max_weekly_sales=max_weekly_sales)
        
    except Exception as err:
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
                   COALESCE(SUM(o.total_amount * 0.15), 0) as earnings_today
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
        
        # Get all products for this seller with edit status (excluding archived)
        cursor.execute('''
            SELECT p.*, c.name as category_name,
                   COALESCE(i.stock_quantity, 0) as stock,
                   COALESCE(i.low_stock_threshold, 10) as threshold,
                   COALESCE(p.edit_status, 'none') as edit_status,
                   COALESCE(p.archive_status, 'active') as archive_status,
                   (SELECT COUNT(*) FROM product_edits 
                    WHERE product_id = p.id AND status = 'pending') as pending_edits
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN inventory i ON p.id = i.product_id
            WHERE p.seller_id = %s AND COALESCE(p.archive_status, 'active') = 'active'
            ORDER BY p.created_at DESC
        ''', (seller['id'],))
        products = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({'products': products}), 200
        
    except Exception as err:
        return jsonify({'error': str(err)}), 500

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
        
        # Get seller ID
        cursor.execute('SELECT id FROM sellers WHERE user_id = %s', (user_id,))
        seller = cursor.fetchone()
        
        if not seller:
            return jsonify({'error': 'Seller profile not found'}), 404
        
        # Get form data
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        price = request.form.get('price', '0')
        category_name = request.form.get('category', 'casual')
        brand = request.form.get('brand', '').strip()
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
        if not category_name:
            return jsonify({'error': 'Category is required'}), 400
        
        # Get sizes and colors
        sizes = request.form.getlist('sizes')
        colors = request.form.getlist('colors')
        
        # Add custom sizes if provided
        custom_sizes = request.form.get('custom-sizes', '').strip()
        if custom_sizes:
            custom_size_list = [s.strip() for s in custom_sizes.split(',') if s.strip()]
            sizes.extend(custom_size_list)
        
        # Add custom colors if provided
        custom_colors = request.form.get('custom-colors', '').strip()
        if custom_colors:
            custom_color_list = [c.strip() for c in custom_colors.split(',') if c.strip()]
            colors.extend(custom_color_list)
        
        # Validate sizes and colors for non-grooming products
        if category_name != 'grooming':
            if not sizes:
                return jsonify({'error': 'Please select at least one size'}), 400
            if not colors:
                return jsonify({'error': 'Please select at least one color'}), 400
        
        # Handle ingredients for grooming products
        ingredients = ''
        if category_name == 'grooming':
            ingredients = request.form.get('ingredients', '').strip()
            if not ingredients:
                return jsonify({'error': 'Ingredients are required for grooming products'}), 400
        
        # Get or create category
        cursor.execute('SELECT id FROM categories WHERE slug = %s', (category_name,))
        category = cursor.fetchone()
        
        if not category:
            # Create category if it doesn't exist
            cursor.execute('INSERT INTO categories (name, slug) VALUES (%s, %s)', 
                         (category_name.replace('-', ' ').title(), category_name))
            category_id = cursor.lastrowid
        else:
            category_id = category['id']
        
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
            for size in sizes:
                for color in colors:
                    stock_key = f'stock_{size}_{color}'
                    variant_stock = int(request.form.get(stock_key, 0))
                    total_stock += variant_stock
                    
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
    """Get the logged-in buyer's first name"""
    try:
        if not session.get('logged_in') or session.get('role') != 'buyer':
            return jsonify({'error': 'Not logged in'}), 401
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        user_id = session.get('user_id')
        cursor.execute('SELECT first_name FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if user:
            return jsonify({'firstName': user['first_name']}), 200
        else:
            return jsonify({'firstName': 'Guest'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products')
def api_products():
    """Get all active products for browsing"""
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Fetch products with images
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
            WHERE p.is_active = 1 AND p.archive_status = 'active'
            ORDER BY p.created_at DESC
            LIMIT 50
        """
        
        cursor.execute(query)
        products = cursor.fetchall()
        
        # For each product, get available colors
        for product in products:
            cursor.execute("""
                SELECT DISTINCT color 
                FROM product_variants 
                WHERE product_id = %s AND color IS NOT NULL AND color != '' AND stock_quantity > 0
                ORDER BY color
            """, (product['id'],))
            colors = cursor.fetchall()
            product['colors'] = [c['color'] for c in colors] if colors else []
        
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
            WHERE p.seller_id = %s AND p.is_active = 1 AND p.archive_status = 'active'
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
            SELECT o.id, o.order_number, o.total_amount, o.status, o.created_at,
                   u.first_name, u.email
            FROM orders o
            JOIN users u ON o.buyer_id = u.id
            WHERE o.buyer_id = %s
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

@app.route('/admin/recent-orders')
def admin_recent_orders():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get recent orders (last 4)
        query = '''
            SELECT o.id, o.order_number, o.total_amount, o.status, o.created_at, u.first_name, u.last_name
            FROM orders o
            JOIN users u ON o.buyer_id = u.id
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
                'status': order['status']
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
            WHERE p.is_active = 1 AND p.archive_status = 'active'
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
    """Get all orders for the logged-in seller"""
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
        
        # Fetch orders for this seller
        query = """
            SELECT 
                o.id,
                o.order_number,
                o.user_id,
                o.total_amount,
                o.order_status,
                o.created_at,
                o.updated_at,
                u.first_name as customer_name,
                COUNT(oi.id) as item_count
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.id
            LEFT JOIN order_items oi ON o.id = oi.order_id
            WHERE o.seller_id = %s
            GROUP BY o.id
            ORDER BY o.created_at DESC
        """
        
        cursor.execute(query, (seller_id,))
        orders = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Convert datetime objects to strings
        for order in orders:
            if order['created_at']:
                order['created_at'] = order['created_at'].isoformat()
        
        return jsonify({
            'success': True,
            'orders': orders
        }), 200
    except Exception as e:
        print(f"[ERROR] seller_orders: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/seller/update-order-status', methods=['POST'])
def update_order_status():
    """Update the status of an order (for seller fulfillment)"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Not logged in'}), 401
        
        user_id = session['user_id']
        order_id = request.form.get('order_id')
        new_status = request.form.get('new_status')
        
        # Validate input
        if not order_id or not new_status:
            return jsonify({'success': False, 'error': 'Missing order_id or new_status'}), 400
        
        valid_statuses = ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'returned']
        if new_status not in valid_statuses:
            return jsonify({'success': False, 'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
        
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
            return jsonify({'success': False, 'error': 'Order not found or you do not have permission to update it'}), 403
        
        # Update the order status
        update_query = """
            UPDATE orders
            SET order_status = %s, updated_at = NOW()
            WHERE id = %s
        """
        
        cursor.execute(update_query, (new_status, order_id))
        conn.commit()
        
        print(f"[✅] Order {order_id} status updated to {new_status} by seller {seller_id}")
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Order status updated to {new_status}'
        }), 200
    except Exception as e:
        print(f"[ERROR] update_order_status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
                o.total_amount, o.payment_method, u.first_name, u.last_name
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
                'customer_name': f"{order['first_name']} {order['last_name']}"
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
        
        if not otp_code or len(otp_code) != 6:
            return jsonify({'success': False, 'message': 'Invalid OTP code'}), 400
        
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
                        ''', (user_id, pending_rider_signup['vehicle_type'], pending_rider_signup['license_number'], 
                              pending_rider_signup['vehicle_plate'], pending_rider_signup['service_area']))

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
            if pending_seller_signup:
                conn = get_db()
                if conn:
                    try:
                        cursor = conn.cursor(dictionary=True)
                        
                        # Create user account (use shop name as first/last name for sellers)
                        name_parts = pending_seller_signup['shop_name'].split(' ', 1)
                        first_name = name_parts[0] if len(name_parts) > 0 else pending_seller_signup['shop_name']
                        last_name = name_parts[1] if len(name_parts) > 1 else 'Shop'
                        
                        cursor.execute('INSERT INTO users (first_name, last_name, email, password, phone, role) VALUES (%s, %s, %s, %s, %s, %s)',
                                     (first_name, last_name, pending_seller_signup['email'], pending_seller_signup['password'], 
                                      pending_seller_signup['phone'], 'seller'))
                        user_id = cursor.lastrowid

                        # Create store slug from shop name
                        store_slug = pending_seller_signup['shop_name'].lower().replace(' ', '-').replace("'", '')

                        # Create seller profile with pending status
                        cursor.execute('INSERT INTO sellers (user_id, store_name, store_slug, status) VALUES (%s, %s, %s, %s)',
                                     (user_id, pending_seller_signup['shop_name'], store_slug, 'pending'))

                        conn.commit()
                        cursor.close()
                        conn.close()
                        session.pop('pending_seller_signup', None)
                        session['email_verified'] = True
                        return jsonify({
                            'success': True, 
                            'message': 'Seller account created successfully! Please log in.',
                            'redirect': url_for('login')
                        })
                    except Exception as e:
                        conn.close()
                        return jsonify({'success': False, 'message': f'Failed to complete seller registration: {str(e)}'}), 500
                else:
                    return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
            return jsonify({'success': False, 'message': 'No pending signup data found'}), 400
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
    """Get cart items from database"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
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
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'items': items})
    except Exception as e:
        print(f"Error getting cart: {e}")
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

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
        
        # Get rider's service area
        cursor.execute('SELECT service_area FROM riders WHERE user_id = %s', (user_id,))
        rider = cursor.fetchone()
        
        if not rider or not rider.get('service_area'):
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'orders': []})
        
        rider_service_area = rider['service_area']
        
        # Regional mapping - maps major regions to cities/provinces with postal code ranges
        region_mappings = {
            'North Luzon': {
                'cities': ['Baguio', 'Benguet', 'Laoag', 'Ilocos Norte', 'Ilocos Sur', 'Vigan', 'Tuguegarao', 'Cagayan', 'Santiago', 'Isabela', 'La Union', 'Pangasinan', 'CAR', 'Cordillera', 'Abra', 'Apayao', 'Ifugao', 'Kalinga', 'Mountain Province'],
                'postal_prefixes': ['26', '29']  # 2600-2699, 2900-2999
            },
            'Central Luzon': {
                'cities': ['Manila', 'Quezon City', 'Makati', 'Pasig', 'Taguig', 'Mandaluyong', 'Pasay', 'Parañaque', 'Las Piñas', 'Muntinlupa', 'Caloocan', 'Malabon', 'Navotas', 'Valenzuela', 'San Juan', 'Marikina', 'NCR', 'Metro Manila', 'Angeles', 'Pampanga', 'San Fernando', 'Olongapo', 'Zambales', 'Tarlac', 'Nueva Ecija', 'Cabanatuan', 'Bataan', 'Bulacan', 'Malolos', 'Balanga'],
                'postal_prefixes': ['10', '11', '12', '13', '14', '15', '16', '20', '21', '22', '23']  # NCR & Central Luzon
            },
            'South Luzon': {
                'cities': ['Calamba', 'Santa Cruz', 'Los Baños', 'San Pablo', 'Biñan', 'Cabuyao', 'Laguna', 'Batangas', 'Lipa', 'Tanauan', 'Lucena', 'Quezon', 'Antipolo', 'Rizal', 'Cavite', 'Bacoor', 'Imus', 'Dasmariñas', 'Tagaytay', 'Legazpi', 'Albay', 'Naga', 'Camarines Norte', 'Camarines Sur', 'Sorsogon', 'Bicol', 'Puerto Princesa', 'Palawan', 'Mindoro', 'Occidental Mindoro', 'Oriental Mindoro', 'Marinduque', 'Romblon', 'CALABARZON', 'MIMAROPA'],
                'postal_prefixes': ['40', '41', '42', '43', '44', '45', '46', '47', '48', '49', '50', '51', '52', '53', '54', '55']
            },
            'Visayas': {
                'cities': ['Cebu', 'Mandaue', 'Lapu-Lapu', 'Iloilo', 'Bacolod', 'Negros Occidental', 'Negros Oriental', 'Roxas', 'Capiz', 'Aklan', 'Kalibo', 'Tagbilaran', 'Bohol', 'Dumaguete', 'Tacloban', 'Ormoc', 'Leyte', 'Eastern Samar', 'Western Samar', 'Northern Samar', 'Samar', 'Calbayog', 'Antique', 'Guimaras', 'Biliran', 'Southern Leyte'],
                'postal_prefixes': ['56', '60', '61', '62', '63', '64', '65', '66', '67', '68', '69']
            },
            'Mindanao': {
                'cities': ['Davao', 'Tagum', 'Panabo', 'Digos', 'Mati', 'Davao del Norte', 'Davao del Sur', 'Davao Oriental', 'Davao Occidental', 'Davao de Oro', 'Cagayan de Oro', 'CDO', 'Misamis Oriental', 'Misamis Occidental', 'Iligan', 'Lanao del Norte', 'Lanao del Sur', 'Valencia', 'Malaybalay', 'Bukidnon', 'Zamboanga', 'Zamboanga del Norte', 'Zamboanga del Sur', 'Zamboanga Sibugay', 'Pagadian', 'Dipolog', 'General Santos', 'Koronadal', 'Cotabato', 'North Cotabato', 'South Cotabato', 'Maguindanao', 'Sultan Kudarat', 'Kidapawan', 'Tacurong', 'Butuan', 'Agusan del Norte', 'Agusan del Sur', 'Surigao del Norte', 'Surigao del Sur', 'Dinagat Islands', 'Tandag', 'Marawi', 'Basilan', 'Sulu', 'Tawi-Tawi', 'BARMM', 'Camiguin'],
                'postal_prefixes': ['70', '80', '81', '82', '83', '84', '85', '86', '87', '88', '89', '90', '91', '92', '93', '94', '95', '96', '97', '98']
            }
        }
        
        # Get cities and postal prefixes covered by rider's region
        region_data = region_mappings.get(rider_service_area, {'cities': [rider_service_area], 'postal_prefixes': []})
        covered_cities = region_data['cities']
        postal_prefixes = region_data['postal_prefixes']
        
        # Build LIKE conditions for cities, provinces, and postal codes
        # Check against address table fields: city, province, postal_code, street_address
        conditions = []
        params = []
        
        # Match by city or province
        for city in covered_cities:
            conditions.append('a.city LIKE %s')
            params.append(f'%{city}%')
            conditions.append('a.province LIKE %s')
            params.append(f'%{city}%')
        
        # Match by postal code prefix
        for prefix in postal_prefixes:
            conditions.append('a.postal_code LIKE %s')
            params.append(f'{prefix}%')
        
        like_conditions = ' OR '.join(conditions) if conditions else '1=0'
        
        # Get orders in the rider's service area by joining with addresses table
        query = f'''
            SELECT o.id, o.order_number, o.user_id, o.total_amount, o.created_at,
                   CONCAT(a.street_address, ', ', a.city, ', ', a.province, ' ', IFNULL(a.postal_code, '')) as delivery_address,
                   CONCAT(u.first_name, ' ', u.last_name) as customer_name,
                   u.phone as customer_phone,
                   u.email,
                   IFNULL(s.id, 0) as shipment_id,
                   IFNULL(s.status, 'pending') as shipment_status
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN addresses a ON o.shipping_address_id = a.id
            LEFT JOIN shipments s ON s.order_id = o.id
            WHERE o.order_status = 'confirmed'
            AND (s.rider_id IS NULL OR s.rider_id = 0)
            AND ({like_conditions})
            ORDER BY o.created_at DESC
        '''
        
        cursor.execute(query, params)
        orders = cursor.fetchall()
        
        # If no shipment exists, create one for each order
        for order in orders:
            if order['shipment_id'] == 0:
                cursor = conn.cursor(dictionary=True)
                tracking_number = f"SHIP{order['id']}{int(time.time())}"
                cursor.execute('''
                    INSERT INTO shipments (order_id, tracking_number, status, created_at)
                    VALUES (%s, %s, 'pending', NOW())
                ''', (order['id'], tracking_number))
                conn.commit()
                order['shipment_id'] = cursor.lastrowid
                cursor.close()
            
            # Convert Decimal to float for JSON serialization
            if order.get('total_amount'):
                order['total_amount'] = float(order['total_amount'])
        
        cursor = conn.cursor(dictionary=True)
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'orders': orders})
    except Exception as e:
        print(f"Error fetching available orders: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/rider/active-deliveries', methods=['GET'])
def api_rider_active_deliveries():
    """Get active deliveries for the logged-in rider"""
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
            print(f"⚠️ No rider record found for user_id: {rider_id}")
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'deliveries': [], 'message': 'No rider profile found'})
        
        rider_db_id = rider_record['id']
        
        cursor.execute('''
            SELECT o.id, o.order_number, o.user_id, o.total_amount, o.order_status, o.created_at,
                   CONCAT(a.street_address, ', ', a.city, ', ', a.province, ' ', IFNULL(a.postal_code, '')) as delivery_address,
                   u.first_name, u.last_name, u.email, u.phone as customer_phone,
                   CONCAT(u.first_name, ' ', u.last_name) as customer_name,
                   s.id as shipment_id, s.status as shipment_status,
                   s.seller_confirmed, s.seller_confirmed_at
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN addresses a ON o.shipping_address_id = a.id
            JOIN shipments s ON s.order_id = o.id
            WHERE s.rider_id = %s AND s.status IN ('pending', 'picked_up', 'in_transit', 'out_for_delivery')
            ORDER BY s.seller_confirmed ASC, o.created_at DESC
        ''', (rider_db_id,))
        deliveries = cursor.fetchall()
        
        # Convert Decimal to float and format dates for JSON serialization
        for delivery in deliveries:
            if delivery.get('total_amount'):
                delivery['total_amount'] = float(delivery['total_amount'])
            if delivery.get('created_at'):
                delivery['created_at'] = delivery['created_at'].isoformat() if hasattr(delivery['created_at'], 'isoformat') else str(delivery['created_at'])
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'deliveries': deliveries})
    except Exception as e:
        print(f"❌ Error fetching active deliveries: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': str(e), 'details': 'Check server logs for more information'}), 500

@app.route('/api/rider/delivery-history', methods=['GET'])
def api_rider_delivery_history():
    """Get delivery history for the logged-in rider"""
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
        
        cursor.execute('''
            SELECT o.id, o.order_number, o.user_id, o.total_amount, o.order_status, o.created_at,
                   CONCAT(a.street_address, ', ', a.city, ', ', a.province, ' ', IFNULL(a.postal_code, '')) as delivery_address,
                   u.first_name, u.last_name
            FROM orders o
            JOIN users u ON o.user_id = u.id
            JOIN addresses a ON o.shipping_address_id = a.id
            JOIN shipments s ON s.order_id = o.id
            WHERE s.rider_id = %s AND s.status = 'delivered'
            ORDER BY o.created_at DESC
            LIMIT 50
        ''', (rider_id,))
        history = cursor.fetchall()
        
        # Convert Decimal to float for JSON serialization
        for item in history:
            if item.get('total_amount'):
                item['total_amount'] = float(item['total_amount'])
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'history': history})
    except Exception as e:
        print(f"Error fetching delivery history: {e}")
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/rider/earnings', methods=['GET'])
def api_rider_earnings():
    """Get earnings summary for the logged-in rider"""
    if not session.get('logged_in') or session.get('role') != 'rider':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
    try:
        rider_id = session.get('user_id')
        cursor = conn.cursor(dictionary=True)
        
        # Calculate total earnings (assume 10% of order total as rider earnings)
        cursor.execute('''
            SELECT 
                COUNT(*) as total_deliveries,
                COALESCE(SUM(total_amount * 0.10), 0) as total_earnings,
                COALESCE(SUM(CASE WHEN DATE(created_at) = CURDATE() THEN total_amount * 0.10 ELSE 0 END), 0) as today_earnings
            FROM orders
            WHERE rider_id = %s AND status = 'delivered'
        ''', (rider_id,))
        earnings = cursor.fetchone()
        
        # Convert Decimal to float for JSON serialization
        if earnings:
            if earnings.get('total_earnings'):
                earnings['total_earnings'] = float(earnings['total_earnings'])
            if earnings.get('today_earnings'):
                earnings['today_earnings'] = float(earnings['today_earnings'])
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'earnings': earnings})
    except Exception as e:
        print(f"Error fetching earnings: {e}")
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/rider/ratings', methods=['GET'])
def api_rider_ratings():
    """Get ratings for the logged-in rider"""
    if not session.get('logged_in') or session.get('role') != 'rider':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database error'}), 500
    
    try:
        rider_id = session.get('user_id')
        cursor = conn.cursor(dictionary=True)
        
        # For now, return mock rating data since we don't have a ratings table
        # In production, you'd query an actual ratings table
        ratings = {
            'average_rating': 4.8,
            'total_ratings': 127,
            'five_star': 98,
            'four_star': 23,
            'three_star': 4,
            'two_star': 1,
            'one_star': 1
        }
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'ratings': ratings})
    except Exception as e:
        print(f"Error fetching ratings: {e}")
        if conn:
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
    """Accept an order for delivery using shipment_id"""
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
        
        # Update shipment with rider and set awaiting seller confirmation
        cursor.execute('''
            UPDATE shipments 
            SET rider_id = %s, seller_confirmed = FALSE
            WHERE id = %s AND rider_id IS NULL
        ''', (rider_db_id, shipment_id))
        
        conn.commit()
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Order already taken or not found'}), 400
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Order accepted! Waiting for seller confirmation...'})
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
        
        # If delivered, also update the order status
        if new_status == 'delivered':
            cursor.execute('''
                UPDATE orders o
                JOIN shipments s ON s.order_id = o.id
                SET o.order_status = 'delivered'
                WHERE s.id = %s
            ''', (shipment_id,))
            conn.commit()
        
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
        email = request.form.get('email')
        
        if not email:
            return jsonify({'success': False, 'error': 'Email is required'}), 400
        
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
                    'error': 'No account found with this email address. Please check and try again.'
                })
            
            # Generate and send OTP
            ip_address = request.remote_addr
            otp_code, otp_id = OTPService.create_otp_record(
                conn,
                email=email,
                user_id=user['id'],
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
            return jsonify({'success': False, 'error': 'Database error occurred'}), 500
        
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
                'error': 'Failed to generate verification code. Please try again.'
            }), 500
            
    except Exception as e:
        print(f"Forgot password error: {str(e)}")
        return jsonify({'success': False, 'error': 'An error occurred'}), 500

@app.route('/verify-reset-otp', methods=['POST'])
def verify_reset_otp():
    """Verify OTP for password reset"""
    try:
        otp_code = request.form.get('otp')
        
        if not otp_code or 'password_reset' not in session:
            return jsonify({'success': False, 'error': 'Invalid request'}), 400
        
        reset_data = session['password_reset']
        email = reset_data.get('email')
        
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        # Verify OTP (correct parameter order: conn, otp_code, email, phone, purpose)
        is_valid, message = OTPService.verify_otp(conn, otp_code, email=email, purpose='password_reset')
        
        if is_valid:
            # Mark as verified in session
            session['password_reset']['verified'] = True
            session.modified = True
            conn.close()
            
            return jsonify({
                'success': True,
                'message': 'OTP verified successfully'
            })
        else:
            conn.close()
            return jsonify({'success': False, 'error': message}), 400
            
    except Exception as e:
        print(f"OTP verification error: {str(e)}")
        return jsonify({'success': False, 'error': 'Verification failed'}), 500

@app.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password after OTP verification"""
    try:
        new_password = request.form.get('password')
        
        if not new_password or 'password_reset' not in session:
            return jsonify({'success': False, 'error': 'Invalid request'}), 400
        
        reset_data = session['password_reset']
        
        if not reset_data.get('verified'):
            return jsonify({'success': False, 'error': 'Please verify OTP first'}), 400
        
        # Validate password: minimum 6 characters with letters and numbers
        if len(new_password) < 6:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters long'}), 400
        
        has_letter = any(c.isalpha() for c in new_password)
        has_number = any(c.isdigit() for c in new_password)
        
        if not (has_letter and has_number):
            return jsonify({'success': False, 'error': 'Password must contain both letters and numbers'}), 400
        
        email = reset_data.get('email')
        user_id = reset_data.get('user_id')
        
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
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
        return jsonify({'success': False, 'error': 'Password reset failed'}), 500

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
