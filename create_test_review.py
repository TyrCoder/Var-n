import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    database='varon'
)

cursor = conn.cursor()

# First, check if we have test data
print("Checking for test users and products...")

cursor.execute('SELECT COUNT(*) FROM users WHERE role = "buyer"')
buyer_count = cursor.fetchone()[0]
print(f"Total buyers: {buyer_count}")

cursor.execute('SELECT COUNT(*) FROM orders WHERE order_status = "delivered"')
delivered_count = cursor.fetchone()[0]
print(f"Total delivered orders: {delivered_count}")

cursor.execute('SELECT COUNT(*) FROM products')
product_count = cursor.fetchone()[0]
print(f"Total products: {product_count}")

# Get a sample delivered order with products
cursor.execute('''
    SELECT o.id, o.user_id, oi.product_id 
    FROM orders o
    JOIN order_items oi ON o.id = oi.order_id
    WHERE o.order_status = "delivered"
    LIMIT 1
''')
result = cursor.fetchone()

if result:
    order_id, user_id, product_id = result
    print(f"\nFound test data: Order {order_id}, User {user_id}, Product {product_id}")
    
    # Insert a test review
    cursor.execute('''
        INSERT INTO reviews (product_id, user_id, order_id, rating, title, comment, is_verified_purchase, is_approved, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, 1, 1, NOW())
    ''', (product_id, user_id, order_id, 5, "Excellent Quality!", "This product exceeded my expectations. Highly recommended!", ))
    
    review_id = cursor.lastrowid
    print(f"Inserted test review with ID: {review_id}")
    
    conn.commit()
    print("Test review committed to database")
else:
    print("\nNo delivered orders found - cannot create test review")

conn.close()
