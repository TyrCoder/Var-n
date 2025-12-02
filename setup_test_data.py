import mysql.connector

conn = mysql.connector.connect(host='localhost', user='root', database='varon')
cursor = conn.cursor(dictionary=True)

# Check rider_ratings table
cursor.execute("SHOW TABLES LIKE 'rider_ratings'")
print("rider_ratings table exists:", bool(cursor.fetchone()))

# Check reviews count
cursor.execute("SELECT COUNT(*) as cnt FROM reviews")
print("Reviews in DB:", cursor.fetchone()['cnt'])

# Check rider_ratings count
cursor.execute("SELECT COUNT(*) as cnt FROM rider_ratings")
print("Rider ratings in DB:", cursor.fetchone()['cnt'])

# Get a delivered order
cursor.execute('''
    SELECT o.id, o.user_id, oi.product_id, s.rider_id
    FROM orders o
    LEFT JOIN order_items oi ON o.id = oi.order_id
    LEFT JOIN shipments s ON o.id = s.order_id
    WHERE o.order_status = "delivered" LIMIT 1
''')
result = cursor.fetchone()

if result:
    order_id, user_id, product_id, rider_id = result['id'], result['user_id'], result['product_id'], result['rider_id']
    print(f"\nTest order #{order_id}: User {user_id}, Product {product_id}, Rider {rider_id}")
    
    # Try to insert test review
    try:
        cursor.execute('''
            INSERT INTO reviews (product_id, user_id, order_id, rating, title, comment, is_verified_purchase, is_approved)
            VALUES (%s, %s, %s, 5, "Test Review", "Excellent!", 1, 1)
        ''', (product_id, user_id, order_id))
        conn.commit()
        print("✓ Test review inserted")
    except Exception as e:
        print(f"✗ Review error: {e}")
    
    # Try to insert test rider rating  
    if rider_id:
        try:
            cursor.execute('''
                INSERT INTO rider_ratings (rider_id, user_id, order_id, rating, comment)
                VALUES (%s, %s, %s, 5, "Great delivery!")
            ''', (rider_id, user_id, order_id))
            conn.commit()
            print("✓ Test rider rating inserted")
        except Exception as e:
            print(f"✗ Rider rating error: {e}")

conn.close()
print("\nDone!")
