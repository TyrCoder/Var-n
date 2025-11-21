import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='varon'
)

cursor = conn.cursor(dictionary=True)

# Get rider info
cursor.execute("""
    SELECT r.id, r.user_id, r.service_area, u.email 
    FROM riders r
    JOIN users u ON r.user_id = u.id
    WHERE u.email = 'sedocoder7@gmail.com'
""")
rider = cursor.fetchone()
print("Rider Info:")
print(rider)
print()

if rider:
    # Check for orders
    cursor.execute("SELECT id, order_number, order_status FROM orders LIMIT 5")
    orders = cursor.fetchall()
    print("Sample Orders:")
    for order in orders:
        print(order)
    print()
    
    # Check shipments
    cursor.execute("""
        SELECT s.id, s.order_id, s.rider_id, s.status, o.order_number
        FROM shipments s
        LEFT JOIN orders o ON s.order_id = o.id
        LIMIT 5
    """)
    shipments = cursor.fetchall()
    print("Sample Shipments:")
    for shipment in shipments:
        print(shipment)
    print()
    
    # Check for orders with addresses in rider's region
    cursor.execute("""
        SELECT o.id, o.order_number, a.city, a.province, a.postal_code
        FROM orders o
        JOIN addresses a ON o.shipping_address_id = a.id
        WHERE o.order_status = 'pending'
        LIMIT 5
    """)
    pending_orders = cursor.fetchall()
    print("Pending Orders with Addresses:")
    for order in pending_orders:
        print(order)

cursor.close()
conn.close()
