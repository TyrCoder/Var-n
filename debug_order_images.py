import mysql.connector

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'varon'
}

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor(dictionary=True)

print("=" * 100)
print("DEBUGGING PRODUCT IMAGES FOR ORDERS")
print("=" * 100)

# Check 1: Products and their images
print("\n1. PRODUCTS WITH IMAGES:")
print("-" * 100)
cursor.execute('''
    SELECT p.id, p.name, COUNT(pi.id) as total_images, 
           SUM(CASE WHEN pi.is_primary = 1 THEN 1 ELSE 0 END) as primary_count
    FROM products p
    LEFT JOIN product_images pi ON p.id = pi.product_id
    WHERE p.is_active = 1
    GROUP BY p.id
    LIMIT 10
''')

for row in cursor.fetchall():
    print(f"Product ID: {row['id']:3d}, Name: {row['name']:30s}, Total Images: {row['total_images']}, Primary: {row['primary_count']}")

# Check 2: Sample order with items
print("\n\n2. SAMPLE ORDER WITH ITEMS AND IMAGES:")
print("-" * 100)
cursor.execute('''
    SELECT o.id, o.order_number, COUNT(oi.id) as item_count
    FROM orders o
    LEFT JOIN order_items oi ON o.id = oi.order_id
    GROUP BY o.id
    LIMIT 1
''')

sample_order = cursor.fetchone()
if sample_order:
    order_id = sample_order['id']
    print(f"Order ID: {order_id}, Order Number: {sample_order['order_number']}, Items: {sample_order['item_count']}")
    
    # Get order items with image URLs
    cursor.execute('''
        SELECT oi.id, oi.product_id, p.name, oi.quantity,
               pi.image_url, pi.is_primary
        FROM order_items oi
        LEFT JOIN products p ON oi.product_id = p.id
        LEFT JOIN product_images pi ON p.id = pi.product_id AND pi.is_primary = 1
        WHERE oi.order_id = %s
    ''', (order_id,))
    
    print("\nOrder Items:")
    for item in cursor.fetchall():
        print(f"  Item ID: {item['id']}, Product: {item['name']}, Image: {item['image_url']}, Primary: {item['is_primary']}")

# Check 3: Products with NO primary image
print("\n\n3. PRODUCTS WITH MISSING PRIMARY IMAGES:")
print("-" * 100)
cursor.execute('''
    SELECT p.id, p.name, COUNT(pi.id) as image_count
    FROM products p
    LEFT JOIN product_images pi ON p.id = pi.product_id
    WHERE p.is_active = 1
    GROUP BY p.id
    HAVING COUNT(CASE WHEN pi.is_primary = 1 THEN 1 END) = 0 AND COUNT(pi.id) > 0
    LIMIT 10
''')

results = cursor.fetchall()
if results:
    print(f"Found {len(results)} products with images but NO primary image:")
    for row in results:
        print(f"  Product ID: {row['id']}, Name: {row['name']}, Total Images: {row['image_count']}")
else:
    print("✅ All products with images have a primary image!")

cursor.close()
conn.close()
