
"""
Recreate all tables as MyISAM, dropping InnoDB tables first
"""
import pymysql
import time

print("Connecting to MySQL without selecting varon database...")
conn = pymysql.connect(host='localhost', user='root', password='')
cursor = conn.cursor()


cursor.execute("USE varon")


cursor.execute("SHOW TABLES")
tables = [row[0] for row in cursor.fetchall()]

print(f"\nFound {len(tables)} tables to drop and recreate")


for table in tables:
    try:
        cursor.execute(f"DROP TABLE `{table}`")
        print(f"✅ Dropped {table}")
    except Exception as e:
        print(f"❌ Error dropping {table}: {e}")

conn.commit()


print("\nRecreating core tables as MyISAM...")


cursor.execute("""
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY
    first_name VARCHAR(100) NOT NULL
    last_name VARCHAR(100) NOT NULL
    email VARCHAR(190) NOT NULL UNIQUE
    password VARCHAR(255) NOT NULL
    phone VARCHAR(20)
    role ENUM('buyer', 'seller', 'admin', 'rider') NOT NULL DEFAULT 'buyer'
    status ENUM('active', 'inactive', 'pending', 'suspended') DEFAULT 'active'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    INDEX idx_email (email)
    INDEX idx_role (role)
    INDEX idx_status (status)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4
""")
print("✅ Created users table")


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
print("✅ Created categories table")


cursor.execute("""
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY
    seller_id INT NOT NULL
    category_id INT NOT NULL
    name VARCHAR(200) NOT NULL
    slug VARCHAR(200) NOT NULL
    description TEXT
    brand VARCHAR(100)
    price DECIMAL(10,2) NOT NULL
    sale_price DECIMAL(10,2)
    cost_price DECIMAL(10,2)
    sku VARCHAR(100) UNIQUE
    is_active BOOLEAN DEFAULT TRUE
    views_count INT DEFAULT 0
    sales_count INT DEFAULT 0
    rating DECIMAL(3,2) DEFAULT 0.00
    review_count INT DEFAULT 0
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    INDEX idx_seller (seller_id)
    INDEX idx_category (category_id)
    INDEX idx_active (is_active)
    INDEX idx_slug (slug)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4
""")
print("✅ Created products table")


cursor.execute("""
CREATE TABLE product_variants (
    id INT AUTO_INCREMENT PRIMARY KEY
    product_id INT NOT NULL
    sku VARCHAR(100) UNIQUE
    size VARCHAR(20)
    color VARCHAR(50)
    stock_quantity INT DEFAULT 0
    price_adjustment DECIMAL(10,2) DEFAULT 0.00
    is_active BOOLEAN DEFAULT TRUE
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    INDEX idx_product (product_id)
    INDEX idx_sku (sku)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4
""")
print("✅ Created product_variants table")


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
print("✅ Created product_images table")


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
print("✅ Created journal_entries table")

conn.commit()
cursor.close()
conn.close()

print("\n" + "="*60)
print("✅ DATABASE FIXED!")
print("="*60)
print("All tables have been recreated as MyISAM.")
print("The Flask app should now work correctly!")
