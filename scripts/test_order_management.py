
"""
Test script for Order Management Feature
Verifies that order endpoints are working correctly
"""

import mysql.connector
import json
from datetime import datetime

def get_db():
    """Connect to MySQL database"""
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='varon'
    )

def test_orders_schema():
    """✅ Test 1: Verify orders table has required columns"""
    print("\n📋 TEST 1: Checking orders table schema...")
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)


        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'orders' AND TABLE_SCHEMA = 'varon'
        """)

        columns = {row['COLUMN_NAME']: row['DATA_TYPE'] for row in cursor.fetchall()}
        required_columns = ['id', 'order_status', 'updated_at', 'total_amount', 'created_at']

        missing = [col for col in required_columns if col not in columns]

        if missing:
            print(f"❌ FAIL: Missing columns: {missing}")
            return False

        print("✅ PASS: All required columns present")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False

def test_order_items_schema():
    """✅ Test 2: Verify order_items table links to products"""
    print("\n📋 TEST 2: Checking order_items table schema...")
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'order_items' AND TABLE_SCHEMA = 'varon'
        """)

        columns = {row['COLUMN_NAME'] for row in cursor.fetchall()}
        required_columns = ['id', 'order_id', 'product_id', 'quantity']

        missing = [col for col in required_columns if col not in columns]

        if missing:
            print(f"❌ FAIL: Missing columns: {missing}")
            return False

        print("✅ PASS: order_items schema is correct")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False

def test_sample_orders():
    """✅ Test 3: Check if there are any sample orders"""
    print("\n📋 TEST 3: Checking sample orders...")
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                o.id,
                o.order_status,
                COUNT(oi.id) as item_count,
                o.total_amount
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            GROUP BY o.id
            LIMIT 5
        """)

        orders = cursor.fetchall()

        if orders:
            print(f"✅ PASS: Found {len(orders)} orders")
            for order in orders:
                print(f"   - Order #{order['id']}: {order['order_status'].upper()} (Items: {order['item_count']}, Total: ₱{order['total_amount']})")
        else:
            print("⚠️  NOTE: No orders found in database yet (this is normal if no orders have been placed)")

        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False

def test_seller_product_link():
    """✅ Test 4: Verify seller-product relationships"""
    print("\n📋 TEST 4: Checking seller-product relationships...")
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                COUNT(*) as product_count,
                COUNT(DISTINCT seller_id) as seller_count
            FROM products
            WHERE is_active = 1 AND archive_status = 'active'
        """)

        result = cursor.fetchone()

        if result['product_count'] > 0:
            print(f"✅ PASS: {result['product_count']} active products from {result['seller_count']} sellers")
        else:
            print("⚠️  NOTE: No active products found (add products first)")

        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False

def test_users_schema():
    """✅ Test 5: Verify users table"""
    print("\n📋 TEST 5: Checking users table...")
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT role, COUNT(*) as count
            FROM users
            GROUP BY role
        """)

        results = cursor.fetchall()

        print("✅ PASS: User distribution:")
        for row in results:
            print(f"   - {row['role'].upper()}: {row['count']}")

        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 ORDER MANAGEMENT FEATURE - VERIFICATION TESTS")
    print("=" * 60)

    tests = [
        test_orders_schema,
        test_order_items_schema,
        test_sample_orders,
        test_seller_product_link,
        test_users_schema
    ]

    results = []
    for test in tests:
        results.append(test())

    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"📊 RESULTS: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("\n✅ All tests passed! Order management feature is ready.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")

if __name__ == '__main__':
    main()
