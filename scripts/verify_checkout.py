#!/usr/bin/env python3
"""
Checkout Flow Verification Script
Verifies all prerequisites for checkout to work
"""

import mysql.connector

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'varon'
}

def get_db():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Exception as err:
        print(f"❌ Database Connection Error: {err}")
        return None

def check_products_active():
    conn = get_db()
    if not conn:
        return False
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT COUNT(*) as count FROM products WHERE is_active = 1')
    result = cursor.fetchone()
    count = result['count'] if result else 0
    
    print(f"\n✅ Active Products: {count}")
    if count > 0:
        cursor.execute('SELECT id, name, price FROM products WHERE is_active = 1 LIMIT 3')
        for row in cursor.fetchall():
            print(f"   - ID: {row['id']}, Name: {row['name']}, Price: ₱{row['price']}")
    else:
        print("   ⚠️  No active products found!")
    
    cursor.close()
    conn.close()
    return count > 0

def check_product_images():
    conn = get_db()
    if not conn:
        return False
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT COUNT(DISTINCT p.id) as count 
        FROM products p
        LEFT JOIN product_images pi ON p.id = pi.product_id
        WHERE p.is_active = 1 AND pi.id IS NOT NULL
    ''')
    result = cursor.fetchone()
    count = result['count'] if result else 0
    
    print(f"\n✅ Products with Images: {count}")
    if count > 0:
        cursor.execute('''
            SELECT p.id, p.name, COUNT(pi.id) as image_count
            FROM products p
            LEFT JOIN product_images pi ON p.id = pi.product_id
            WHERE p.is_active = 1 AND pi.id IS NOT NULL
            GROUP BY p.id
            LIMIT 3
        ''')
        for row in cursor.fetchall():
            print(f"   - Product ID: {row['id']}, Name: {row['name']}, Images: {row['image_count']}")
    else:
        print("   ⚠️  Products without images found!")
    
    cursor.close()
    conn.close()
    return count > 0

def check_inventory():
    conn = get_db()
    if not conn:
        return False
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT COUNT(DISTINCT p.id) as count
        FROM products p
        LEFT JOIN inventory i ON p.id = i.product_id
        WHERE p.is_active = 1 AND i.id IS NOT NULL AND i.stock_quantity > 0
    ''')
    result = cursor.fetchone()
    count = result['count'] if result else 0
    
    print(f"\n✅ Products with Stock: {count}")
    if count > 0:
        cursor.execute('''
            SELECT p.id, p.name, i.stock_quantity
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            WHERE p.is_active = 1 AND i.stock_quantity > 0
            LIMIT 3
        ''')
        for row in cursor.fetchall():
            stock = row['stock_quantity'] if row['stock_quantity'] else 0
            print(f"   - Product ID: {row['id']}, Name: {row['name']}, Stock: {stock}")
    else:
        print("   ⚠️  No inventory found!")
    
    cursor.close()
    conn.close()
    return count > 0

def check_sellers():
    conn = get_db()
    if not conn:
        return False
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT COUNT(*) as count FROM sellers')
    result = cursor.fetchone()
    count = result['count'] if result else 0
    
    print(f"\n✅ Total Sellers: {count}")
    if count > 0:
        cursor.execute('SELECT id, store_name, user_id FROM sellers LIMIT 3')
        for row in cursor.fetchall():
            print(f"   - ID: {row['id']}, Store: {row['store_name']}, User ID: {row['user_id']}")
    
    cursor.close()
    conn.close()
    return count > 0

def check_orders():
    conn = get_db()
    if not conn:
        return False
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT COUNT(*) as count FROM orders')
    result = cursor.fetchone()
    count = result['count'] if result else 0
    
    print(f"\n✅ Total Orders: {count}")
    if count > 0:
        cursor.execute('''
            SELECT order_number, user_id, total_amount, order_status 
            FROM orders 
            ORDER BY created_at DESC 
            LIMIT 3
        ''')
        for row in cursor.fetchall():
            print(f"   - Order: {row['order_number']}, Total: ₱{row['total_amount']}, Status: {row['order_status']}")
    else:
        print("   ℹ️  No orders placed yet")
    
    cursor.close()
    conn.close()
    return True

def check_database_schema():
    """Check if all required columns exist"""
    conn = get_db()
    if not conn:
        return False
    
    cursor = conn.cursor(dictionary=True)
    
    # Check products table
    cursor.execute("DESCRIBE products")
    columns = {row['Field'] for row in cursor.fetchall()}
    
    required_columns = {'id', 'name', 'price', 'is_active', 'archive_status', 'seller_id'}
    missing = required_columns - columns
    
    print(f"\n✅ Database Schema Check")
    if missing:
        print(f"   ❌ Missing columns in products table: {missing}")
        return False
    else:
        print(f"   ✅ All required columns present")
    
    cursor.close()
    conn.close()
    return True

def main():
    print("=" * 60)
    print("🔍 CHECKOUT FLOW VERIFICATION")
    print("=" * 60)
    
    checks = [
        ("Database Schema", check_database_schema),
        ("Active Products", check_products_active),
        ("Product Images", check_product_images),
        ("Inventory Stock", check_inventory),
        ("Sellers", check_sellers),
        ("Orders", check_orders),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Error checking {name}: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\n{passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All checks passed! Checkout flow should work correctly.")
    else:
        print("\n⚠️  Some checks failed. Please review the issues above.")

if __name__ == '__main__':
    main()
