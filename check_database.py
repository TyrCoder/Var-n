import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='varon'
)

cursor = conn.cursor(dictionary=True)

# List all users
cursor.execute("SELECT id, email, role FROM users")
users = cursor.fetchall()
print("All users in database:")
for user in users:
    print(user)
print()

# Check orders
cursor.execute("SELECT COUNT(*) as count FROM orders")
order_count = cursor.fetchone()
print(f"Total orders: {order_count['count']}")

# Check addresses
cursor.execute("SELECT id, city, province, postal_code FROM addresses LIMIT 5")
addresses = cursor.fetchall()
print("\nSample addresses:")
for addr in addresses:
    print(addr)

cursor.close()
conn.close()
