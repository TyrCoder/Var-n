import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='varon'
)

cursor = conn.cursor(dictionary=True)

# Get rider info for sedocode7
cursor.execute("""
    SELECT r.*, u.email 
    FROM riders r
    JOIN users u ON r.user_id = u.id
    WHERE u.email = 'sedocode7@gmail.com'
""")
rider = cursor.fetchone()
print("Rider Info:")
print(rider)
print()

# Check the order
cursor.execute("""
    SELECT o.id, o.order_number, o.order_status, o.user_id,
           a.street_address, a.city, a.province, a.postal_code
    FROM orders o
    JOIN addresses a ON o.shipping_address_id = a.id
""")
order = cursor.fetchone()
print("Order Info:")
print(order)
print()

# Check shipments
cursor.execute("SELECT * FROM shipments")
shipments = cursor.fetchall()
print("Shipments:")
for s in shipments:
    print(s)

cursor.close()
conn.close()
