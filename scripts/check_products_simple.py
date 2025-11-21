import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='varon'
)

cursor = conn.cursor(dictionary=True)
cursor.execute('SELECT id, name, is_active, archive_status FROM products')
products = cursor.fetchall()

print('Products in database:')
for p in products:
    print(f"ID: {p['id']}, Name: {p['name']}, Active: {p['is_active']}, Archive: {p['archive_status']}")

cursor.close()
conn.close()
