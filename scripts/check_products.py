#!/usr/bin/env python3
"""Check products in database"""

import sys
sys.path.insert(0, '/Users/windows/OneDrive/Documents/GitHub/Var-n')

from app import get_db

conn = get_db()
if not conn:
    print("❌ Failed to connect to database")
    sys.exit(1)

cursor = conn.cursor(dictionary=True)

print("\n" + "="*60)
print("ALL PRODUCTS")
print("="*60)
cursor.execute('SELECT id, name, seller_id FROM products LIMIT 10')
products = cursor.fetchall()
if not products:
    print("  No products found")
else:
    for p in products:
        print(f"  Product {p['id']}: {p['name']} (seller_id: {p['seller_id']})")

print("\n" + "="*60)
print("ORDER ITEMS (shows which products in orders)")
print("="*60)
cursor.execute('''
    SELECT oi.order_id, oi.product_id, oi.product_name, p.seller_id 
    FROM order_items oi
    LEFT JOIN products p ON oi.product_id = p.id
    LIMIT 10
''')
items = cursor.fetchall()
if not items:
    print("  No order items found")
else:
    for item in items:
        print(f"  Order {item['order_id']}: Product {item['product_id']} {item['product_name']} (seller_id: {item['seller_id']})")

cursor.close()
conn.close()
