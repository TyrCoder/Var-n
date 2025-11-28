import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='varon'
)

cursor = conn.cursor(dictionary=True)


cursor.execute('''
    SELECT s.*, u.email, u.first_name, u.last_name, u.phone
    FROM sellers s
    JOIN users u ON s.user_id = u.id
    ORDER BY s.created_at DESC
    LIMIT 5
''')

sellers = cursor.fetchall()

print(f'\n✅ Found {len(sellers)} seller(s):\n')

for seller in sellers:
    print(f"Store: {seller['store_name']}")
    print(f"Email: {seller['email']}")
    print(f"Phone: {seller['phone']}")
    print(f"Name: {seller['first_name']} {seller['last_name']}")
    print(f"Status: {seller['status']}")
    print(f"Created: {seller['created_at']}")
    print("-" * 50)

conn.close()
