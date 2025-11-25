from app import get_db

conn = get_db()
cursor = conn.cursor(dictionary=True)

try:
    # Check confirmed orders
    cursor.execute("""
        SELECT o.id, o.order_number, o.order_status, s.id as shipment_id, s.status as shipment_status, s.rider_id
        FROM orders o
        LEFT JOIN shipments s ON o.id = s.order_id
        WHERE o.order_status IN ('confirmed', 'released_to_rider')
        LIMIT 5
    """)
    orders = cursor.fetchall()
    
    if orders:
        print("Confirmed/Released Orders:")
        for order in orders:
            print(f"  Order {order['order_number']}: status={order['order_status']}, shipment_status={order['shipment_status']}, rider_id={order['rider_id']}")
    else:
        print("No confirmed or released orders found")
        
        # Create a test order in confirmed status
        print("\nCreating a test order in 'confirmed' status...")
        cursor.execute("""
            INSERT INTO orders (order_number, user_id, seller_id, shipping_address_id, subtotal, total_amount, order_status, payment_status)
            SELECT 'TEST-' + UUID(), u.id, s.id, a.id, 1000, 1000, 'confirmed', 'paid'
            FROM users u
            JOIN sellers s ON s.user_id = u.id
            JOIN addresses a ON a.user_id = u.id
            WHERE u.role = 'seller' AND a.city IS NOT NULL
            LIMIT 1
        """)
        conn.commit()
        if cursor.rowcount > 0:
            print(f"✅ Created test order")
        
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    cursor.close()
    conn.close()
