
"""Test script to verify order retrieval"""

import sys
sys.path.insert(0, '/Users/windows/OneDrive/Documents/GitHub/Var-n')

from app import get_db


conn = get_db()
if not conn:
    print("❌ Failed to connect to database")
    sys.exit(1)

cursor = conn.cursor(dictionary=True)

print("\n" + "="*60)
print("RECENT ORDERS")
print("="*60)
cursor.execute('SELECT id, order_number, seller_id, order_status FROM orders ORDER BY created_at DESC LIMIT 5')
orders = cursor.fetchall()
if not orders:
    print("  No orders found")
else:
    for order in orders:
        print(f"  Order {order['id']}: {order['order_number']} (seller_id: {order['seller_id']}, status: {order['order_status']})")

print("\n" + "="*60)
print("SELLERS (User role=seller)")
print("="*60)
cursor.execute('SELECT id, first_name, role FROM users WHERE role = "seller" LIMIT 5')
sellers = cursor.fetchall()
if not sellers:
    print("  No sellers found")
else:
    for seller in sellers:
        print(f"  Seller {seller['id']}: {seller['first_name']} ({seller['role']})")

print("\n" + "="*60)
print("TEST QUERY: Orders for seller_id=1")
print("="*60)
query = """
    SELECT
        o.id,
        o.order_number,
        o.seller_id,
        o.order_status,
        COUNT(oi.id) as item_count
    FROM orders o
    LEFT JOIN order_items oi ON o.id = oi.order_id
    WHERE o.seller_id = %s
    GROUP BY o.id
    ORDER BY o.created_at DESC
"""
cursor.execute(query, (1,))
results = cursor.fetchall()
if not results:
    print("  No orders for seller_id=1")
else:
    for row in results:
        print(f"  {row}")

cursor.close()
conn.close()
print("\n✅ Test complete")
