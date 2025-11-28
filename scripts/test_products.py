import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='varon'
)

cursor = conn.cursor(dictionary=True)


cursor.execute('SELECT COUNT(*) as count FROM products WHERE is_active = 1 AND archive_status = "active"')
result = cursor.fetchone()
print(f'Active products: {result["count"]}')


cursor.execute('''
    SELECT p.id, p.name, p.price, pi.image_url
    FROM products p
    LEFT JOIN product_images pi ON p.id = pi.product_id AND pi.is_primary = 1
    WHERE p.is_active = 1 AND p.archive_status = 'active'
    LIMIT 5
''')
products = cursor.fetchall()
for p in products:
    print(f'ID: {p["id"]}, Name: {p["name"]}, Price: {p["price"]}, Image: {p["image_url"]}')

cursor.close()
conn.close()
