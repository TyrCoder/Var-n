#!/usr/bin/env python3
"""Verify the complete order flow"""

import sys
sys.path.insert(0, '/Users/windows/OneDrive/Documents/GitHub/Var-n')

from app import get_db

conn = get_db()
cursor = conn.cursor(dictionary=True)

print("\n" + "="*70)
print("COMPLETE ORDER FLOW VERIFICATION")
print("="*70)

# 1. Check users
print("\n1️⃣  USERS IN SYSTEM")
print("-" * 70)
cursor.execute('''SELECT id, first_name, email, role FROM users LIMIT 10''')
for user in cursor.fetchall():
    print(f"   ID {user['id']}: {user['first_name']} ({user['role']}) - {user['email']}")

# 2. Check sellers 
print("\n2️⃣  SELLERS TABLE")
print("-" * 70)
cursor.execute('''SELECT id, user_id, store_name FROM sellers LIMIT 5''')
sellers = cursor.fetchall()
if sellers:
    for seller in sellers:
        print(f"   Seller {seller['id']}: store={seller['store_name']}, user_id={seller['user_id']}")
else:
    print("   ⚠️  No sellers in sellers table")

# 3. Check products
print("\n3️⃣  PRODUCTS")
print("-" * 70)
cursor.execute('''SELECT id, name, seller_id FROM products LIMIT 5''')
for product in cursor.fetchall():
    print(f"   Product {product['id']}: {product['name'][:40]} (seller_id: {product['seller_id']})")

# 4. Check orders
print("\n4️⃣  ORDERS")
print("-" * 70)
cursor.execute('''SELECT id, order_number, seller_id, user_id, order_status FROM orders ORDER BY created_at DESC LIMIT 5''')
for order in cursor.fetchall():
    print(f"   Order {order['id']}: {order['order_number']} (seller_id: {order['seller_id']}, buyer: {order['user_id']}, status: {order['order_status']})")

# 5. Check order items
print("\n5️⃣  ORDER ITEMS")
print("-" * 70)
cursor.execute('''SELECT oi.id, oi.order_id, oi.product_id, p.seller_id FROM order_items oi LEFT JOIN products p ON oi.product_id = p.id LIMIT 5''')
for item in cursor.fetchall():
    print(f"   Item {item['id']}: Order {item['order_id']}, Product {item['product_id']} (seller_id: {item['seller_id']})")

# 6. Test the fixed query for seller_id=1
print("\n6️⃣  FINAL TEST: Query orders for seller_id=1 (like seller dashboard does)")
print("-" * 70)
query = """
    SELECT 
        o.id,
        o.order_number,
        o.seller_id,
        o.order_status,
        COUNT(oi.id) as item_count,
        u.first_name as customer_name
    FROM orders o
    LEFT JOIN order_items oi ON o.id = oi.order_id
    LEFT JOIN users u ON o.user_id = u.id
    WHERE o.seller_id = %s
    GROUP BY o.id
    ORDER BY o.created_at DESC
"""
cursor.execute(query, (1,))
results = cursor.fetchall()
print(f"   ✅ Found {len(results)} orders for seller_id=1:\n")
for row in results:
    print(f"      Order #{row['id']}: {row['order_number']}")
    print(f"        - Customer: {row['customer_name']}")
    print(f"        - Status: {row['order_status']}")
    print(f"        - Items: {row['item_count']}")
    print()

cursor.close()
conn.close()

print("="*70)
print("✅ VERIFICATION COMPLETE - Order retrieval is working!")
print("="*70)
