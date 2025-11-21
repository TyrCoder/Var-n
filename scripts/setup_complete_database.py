import mysql.connector
from datetime import datetime, timedelta
import random

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='varon'
)

cursor = conn.cursor()

print("Setting up complete Varon database...")

print("\n1. Creating sample categories...")
categories_data = [
    ('Shirts', 'shirts', 'Formal and casual shirts', None),
    ('Pants', 'pants', 'Trousers and jeans', None),
    ('Shorts', 'shorts', 'Casual and sport shorts', None),
    ('Jackets', 'jackets', 'Outerwear and blazers', None),
    ('Shoes', 'shoes', 'Formal and casual footwear', None),
    ('Accessories', 'accessories', 'Belts, wallets, and more', None),
    ('Formal', 'formal', 'Formal wear collection', None),
    ('Casual', 'casual', 'Casual everyday wear', None)
]

for cat in categories_data:
    cursor.execute("""
        INSERT INTO categories (name, slug, description, parent_id, is_active)
        VALUES (%s, %s, %s, %s, 1)
        ON DUPLICATE KEY UPDATE name=VALUES(name)
    """, cat)

conn.commit()
print(f"✓ Created {len(categories_data)} categories")

print("\n2. Getting or creating sample seller...")
cursor.execute("SELECT id FROM users WHERE email = 'seller@varon.com' AND role = 'seller'")
seller_user = cursor.fetchone()

if not seller_user:
    cursor.execute("""
        INSERT INTO users (first_name, last_name, email, password, role, status)
        VALUES ('Varon', 'Store', 'seller@varon.com', 'seller123', 'seller', 'active')
    """)
    seller_user_id = cursor.lastrowid
    print(f"✓ Created seller user (ID: {seller_user_id})")
else:
    seller_user_id = seller_user[0]
    print(f"✓ Using existing seller user (ID: {seller_user_id})")

cursor.execute("SELECT id FROM sellers WHERE user_id = %s", (seller_user_id,))
seller = cursor.fetchone()

if not seller:
    cursor.execute("""
        INSERT INTO sellers (user_id, store_name, store_slug, description, address, city, province, status)
        VALUES (%s, 'Varon Official Store', 'varon-official', 
                'Premium menswear collection', '123 Fashion St', 'Makati', 'Metro Manila', 'approved')
    """, (seller_user_id,))
    seller_id = cursor.lastrowid
    print(f"✓ Created seller profile (ID: {seller_id})")
else:
    seller_id = seller[0]
    print(f"✓ Using existing seller (ID: {seller_id})")

conn.commit()

print("\n3. Creating sample products...")
cursor.execute("SELECT id, name FROM categories ORDER BY id")
categories = cursor.fetchall()

products_data = [
    {
        'name': 'Classic Oxford Shirt',
        'category': 'Shirts',
        'description': 'Premium cotton oxford shirt with button-down collar',
        'price': 1299.00,
        'brand': 'Varon',
        'material': '100% Cotton',
        'sku': 'VRN-SHR-001'
    },
    {
        'name': 'Slim Fit Chinos',
        'category': 'Pants',
        'description': 'Comfortable stretch chinos for everyday wear',
        'price': 1599.00,
        'brand': 'Varon',
        'material': '98% Cotton, 2% Elastane',
        'sku': 'VRN-PNT-001'
    },
    {
        'name': 'Linen Summer Shorts',
        'category': 'Shorts',
        'description': 'Breathable linen shorts perfect for warm weather',
        'price': 999.00,
        'brand': 'Varon',
        'material': '100% Linen',
        'sku': 'VRN-SHT-001'
    },
    {
        'name': 'Navy Blazer',
        'category': 'Jackets',
        'description': 'Versatile navy blazer for formal occasions',
        'price': 3999.00,
        'brand': 'Varon',
        'material': 'Wool Blend',
        'sku': 'VRN-JKT-001'
    },
    {
        'name': 'Leather Derby Shoes',
        'category': 'Shoes',
        'description': 'Genuine leather formal shoes',
        'price': 2799.00,
        'brand': 'Varon',
        'material': 'Genuine Leather',
        'sku': 'VRN-SHO-001'
    },
    {
        'name': 'Leather Belt',
        'category': 'Accessories',
        'description': 'Classic leather belt with silver buckle',
        'price': 599.00,
        'brand': 'Varon',
        'material': 'Genuine Leather',
        'sku': 'VRN-ACC-001'
    },
    {
        'name': 'Formal White Shirt',
        'category': 'Formal',
        'description': 'Crisp white shirt for formal events',
        'price': 1499.00,
        'brand': 'Varon',
        'material': '100% Cotton',
        'sku': 'VRN-FRM-001'
    },
    {
        'name': 'Casual Polo Shirt',
        'category': 'Casual',
        'description': 'Comfortable polo for casual wear',
        'price': 899.00,
        'brand': 'Varon',
        'material': 'Cotton Pique',
        'sku': 'VRN-CSL-001'
    }
]

category_map = {cat[1]: cat[0] for cat in categories}

for prod in products_data:
    cat_id = category_map.get(prod['category'], 1)
    
    cursor.execute("""
        INSERT INTO products (seller_id, category_id, name, slug, description, brand, 
                            price, material, sku, is_active, is_featured, archive_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1, 1, 'active')
        ON DUPLICATE KEY UPDATE name=VALUES(name)
    """, (
        seller_id, cat_id, prod['name'], 
        prod['name'].lower().replace(' ', '-'),
        prod['description'], prod['brand'], prod['price'],
        prod['material'], prod['sku']
    ))
    
    product_id = cursor.lastrowid
    if product_id > 0:
        cursor.execute("""
            INSERT INTO product_images (product_id, image_url, is_primary, sort_order)
            VALUES (%s, '/static/images/products/placeholder.jpg', 1, 0)
            ON DUPLICATE KEY UPDATE image_url=VALUES(image_url)
        """, (product_id,))
        
        cursor.execute("""
            INSERT INTO inventory (product_id, variant_id, stock_quantity, reserved_quantity)
            VALUES (%s, NULL, %s, 0)
            ON DUPLICATE KEY UPDATE stock_quantity=VALUES(stock_quantity)
        """, (product_id, random.randint(20, 100)))

conn.commit()
print(f"✓ Created {len(products_data)} products with inventory")

print("\n4. Creating sample variants (sizes)...")
cursor.execute("SELECT id FROM products WHERE seller_id = %s LIMIT 5", (seller_id,))
product_ids = [p[0] for p in cursor.fetchall()]

sizes = ['S', 'M', 'L', 'XL', 'XXL']
for pid in product_ids:
    for size in sizes:
        cursor.execute("""
            INSERT INTO product_variants (product_id, size, stock_quantity, is_active, sku)
            VALUES (%s, %s, %s, 1, CONCAT('VRN-', %s, '-', %s))
            ON DUPLICATE KEY UPDATE stock_quantity=VALUES(stock_quantity)
        """, (pid, size, random.randint(10, 50), pid, size))

conn.commit()
print(f"✓ Created variants for {len(product_ids)} products")

print("\n5. Setting up sample buyer...")
cursor.execute("SELECT id FROM users WHERE email = 'buyer@varon.com'")
buyer = cursor.fetchone()

if not buyer:
    cursor.execute("""
        INSERT INTO users (first_name, last_name, email, password, role, phone, status)
        VALUES ('John', 'Doe', 'buyer@varon.com', 'buyer123', 'buyer', '09123456789', 'active')
    """)
    buyer_id = cursor.lastrowid
    print(f"✓ Created sample buyer (ID: {buyer_id})")
else:
    buyer_id = buyer[0]
    print(f"✓ Using existing buyer (ID: {buyer_id})")

cursor.execute("SELECT COUNT(*) FROM addresses WHERE user_id = %s", (buyer_id,))
if cursor.fetchone()[0] == 0:
    cursor.execute("""
        INSERT INTO addresses (user_id, address_type, full_name, phone, street_address, 
                             barangay, city, province, postal_code, is_default)
        VALUES (%s, 'both', 'John Doe', '09123456789', '123 Main St', 
                'Barangay 1', 'Makati', 'Metro Manila', '1200', 1)
    """, (buyer_id,))
    print("✓ Created sample address")

conn.commit()

print("\n6. Creating sample rider...")
cursor.execute("SELECT id FROM users WHERE email = 'rider@varon.com' AND role = 'rider'")
rider_user = cursor.fetchone()

if not rider_user:
    cursor.execute("""
        INSERT INTO users (first_name, last_name, email, password, role, phone, status)
        VALUES ('Mike', 'Santos', 'rider@varon.com', 'rider123', 'rider', '09987654321', 'active')
    """)
    rider_user_id = cursor.lastrowid
    
    cursor.execute("""
        INSERT INTO riders (user_id, vehicle_type, license_number, vehicle_plate, 
                          is_available, status)
        VALUES (%s, 'motorcycle', 'A12-34-567890', 'ABC1234', 1, 'approved')
    """, (rider_user_id,))
    print(f"✓ Created sample rider")
else:
    print("✓ Rider already exists")

conn.commit()

print("\n✅ Database setup complete!")
print("\n" + "="*50)
print("Sample Accounts Created:")
print("="*50)
print("Admin: admin@varon.com / admin123")
print("Seller: seller@varon.com / seller123")
print("Buyer: buyer@varon.com / buyer123")
print("Rider: rider@varon.com / rider123")
print("="*50)

cursor.execute("SELECT COUNT(*) FROM products WHERE is_active = 1")
product_count = cursor.fetchone()[0]
print(f"\nTotal Active Products: {product_count}")

cursor.execute("SELECT COUNT(*) FROM categories WHERE is_active = 1")
category_count = cursor.fetchone()[0]
print(f"Total Categories: {category_count}")

cursor.close()
conn.close()

print("\n✓ All done! You can now use the system.")
