
"""
Fix InnoDB issue by recreating tables without InnoDB dependency
"""
import pymysql

conn = pymysql.connect(
    host='localhost'
    user='root'
    password=''
)

cursor = conn.cursor()


print("Dropping varon database...")
cursor.execute("DROP DATABASE IF EXISTS varon")
print("✅ Dropped")


print("Creating fresh varon database...")
cursor.execute("CREATE DATABASE varon CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
cursor.execute("USE varon")
print("✅ Created")


print("Creating tables...")

tables = [
    """CREATE TABLE users (
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
    ) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4"""
    """CREATE TABLE categories (
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
    ) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4"""
    """CREATE TABLE products (
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        INDEX idx_seller (seller_id)
        INDEX idx_category (category_id)
        INDEX idx_active (is_active)
        INDEX idx_slug (slug)
    ) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4"""
]

for sql in tables:
    cursor.execute(sql)
    print("✅ Table created")

conn.commit()
cursor.close()
conn.close()

print("\n✅ Database recreated successfully with MyISAM!")
