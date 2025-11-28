
import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='root',
    database='varon'
)

cursor = conn.cursor(dictionary=True)

print("=" * 60)
print("RECENT ORDERS")
print("=" * 60)
cursor.execute('SELECT id, order_number, seller_id, order_status, created_at FROM orders ORDER BY created_at DESC LIMIT 5')
for row in cursor.fetchall():
    print(row)

print("\n" + "=" * 60)
print("RECENT ORDER ITEMS")
print("=" * 60)
cursor.execute('SELECT oi.id, oi.order_id, oi.product_id, p.seller_id FROM order_items oi LEFT JOIN products p ON oi.product_id = p.id LIMIT 5')
for row in cursor.fetchall():
    print(row)

print("\n" + "=" * 60)
print("SELLERS")
print("=" * 60)
cursor.execute('SELECT id, first_name, role FROM users WHERE role = "seller" LIMIT 3')
for row in cursor.fetchall():
    print(row)

print("\n" + "=" * 60)
print("TEST QUERY: Orders for seller_id=1")
print("=" * 60)
query = """
    SELECT
        o.id,
        o.order_number,
        o.seller_id,
        o.order_status,
        COUNT(oi.id) as item_count
    FROM orders o
    LEFT JOIN order_items oi ON o.id = oi.order_id
    LEFT JOIN products p ON oi.product_id = p.id
    WHERE p.seller_id = %s
    GROUP BY o.id
    ORDER BY o.created_at DESC
"""
cursor.execute(query, (1,))
for row in cursor.fetchall():
    print(row)

cursor.close()
conn.close()
