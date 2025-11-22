import mysql.connector
from config import DB_CONFIG

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

print('\n=== product_variants table structure ===')
cursor.execute('DESCRIBE product_variants')
for row in cursor.fetchall():
    print(row)

print('\n=== cart table structure ===')
cursor.execute('DESCRIBE cart')
for row in cursor.fetchall():
    print(row)

print('\n=== Sample cart data ===')
cursor.execute('''
    SELECT c.id, c.user_id, c.product_id, c.variant_id, c.quantity,
           pv.color, pv.size, p.name
    FROM cart c
    LEFT JOIN product_variants pv ON c.variant_id = pv.id
    LEFT JOIN products p ON c.product_id = p.id
    LIMIT 5
''')
for row in cursor.fetchall():
    print(row)

conn.close()
