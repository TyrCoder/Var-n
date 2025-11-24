#!/usr/bin/env python3
"""
Verification script to check if the HTTP 500 order loading error is fixed
"""

import mysql.connector
import sys

def check_database_columns():
    """Verify all required columns exist in orders table"""
    print("\n" + "="*60)
    print("🔍 CHECKING DATABASE COLUMNS")
    print("="*60)
    
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='varon'
        )
        cursor = conn.cursor(dictionary=True)
        
        # Get all columns in orders table
        cursor.execute('DESCRIBE orders')
        columns = cursor.fetchall()
        column_names = [col['Field'] for col in columns]
        
        # Check required columns
        required_columns = ['rider_id', 'seller_confirmed_rider', 'buyer_approved_rider']
        all_present = True
        
        for col in required_columns:
            if col in column_names:
                print(f"✅ Column '{col}' exists")
            else:
                print(f"❌ Column '{col}' MISSING")
                all_present = False
        
        cursor.close()
        conn.close()
        
        return all_present
    except Exception as e:
        print(f"❌ Error checking columns: {e}")
        return False

def test_query():
    """Test the seller orders query"""
    print("\n" + "="*60)
    print("🧪 TESTING SQL QUERY")
    print("="*60)
    
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='varon'
        )
        cursor = conn.cursor(dictionary=True)
        
        # Get first seller
        cursor.execute('SELECT id, store_name FROM sellers LIMIT 1')
        seller = cursor.fetchone()
        
        if not seller:
            print("⚠️ No sellers found in database")
            cursor.close()
            conn.close()
            return True  # Not a failure, just no data
        
        seller_id = seller['id']
        print(f"Testing with seller: {seller['store_name']} (id: {seller_id})")
        
        # Run the fixed query
        query = """
            SELECT
                o.id,
                o.order_number,
                o.user_id,
                o.rider_id,
                o.total_amount,
                o.order_status,
                o.seller_confirmed_rider,
                o.buyer_approved_rider,
                o.created_at,
                o.updated_at,
                CONCAT(u.first_name, ' ', u.last_name) as customer_name,
                (SELECT COUNT(*) FROM order_items oi2 
                 WHERE oi2.order_id = o.id) as item_count,
                IFNULL(s.status, 'pending') as shipment_status,
                IFNULL(s.rider_id, 0) as shipment_rider_id,
                IFNULL(s.seller_confirmed, FALSE) as seller_confirmed,
                s.id as shipment_id
            FROM orders o
            INNER JOIN order_items oi ON o.id = oi.order_id
            INNER JOIN products p ON oi.product_id = p.id
            LEFT JOIN users u ON o.user_id = u.id
            LEFT JOIN shipments s ON s.order_id = o.id
            WHERE p.seller_id = %s
            GROUP BY o.id
            ORDER BY o.created_at DESC
        """
        
        cursor.execute(query, (seller_id,))
        orders = cursor.fetchall()
        
        print(f"✅ Query executed successfully!")
        print(f"   Found {len(orders)} orders")
        
        if len(orders) > 0:
            first_order = orders[0]
            print(f"   First order: {first_order['order_number']}")
            print(f"   Status: {first_order['order_status']}")
            print(f"   Seller confirmed rider: {first_order['seller_confirmed_rider']}")
            print(f"   Buyer approved rider: {first_order['buyer_approved_rider']}")
            
            # Check all expected fields
            expected_fields = [
                'id', 'order_number', 'user_id', 'rider_id', 'total_amount',
                'order_status', 'seller_confirmed_rider', 'buyer_approved_rider',
                'created_at', 'updated_at', 'customer_name', 'item_count',
                'shipment_status', 'shipment_rider_id', 'seller_confirmed', 'shipment_id'
            ]
            
            missing_fields = [f for f in expected_fields if f not in first_order]
            if missing_fields:
                print(f"❌ Missing fields: {missing_fields}")
                cursor.close()
                conn.close()
                return False
            else:
                print(f"✅ All expected fields present")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return False

def check_foreign_key():
    """Check if foreign key constraint exists"""
    print("\n" + "="*60)
    print("🔗 CHECKING FOREIGN KEY CONSTRAINT")
    print("="*60)
    
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='varon'
        )
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT CONSTRAINT_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_NAME='orders' AND COLUMN_NAME='rider_id' AND REFERENCED_TABLE_NAME IS NOT NULL
        """)
        
        fk = cursor.fetchone()
        if fk:
            print(f"✅ Foreign key constraint exists: {fk['CONSTRAINT_NAME']}")
            cursor.close()
            conn.close()
            return True
        else:
            print("⚠️ Foreign key constraint not found (not critical, but recommended)")
            cursor.close()
            conn.close()
            return True
    except Exception as e:
        print(f"⚠️ Error checking foreign key: {e}")
        return True

def check_index():
    """Check if performance index exists"""
    print("\n" + "="*60)
    print("📊 CHECKING PERFORMANCE INDEX")
    print("="*60)
    
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='varon'
        )
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SHOW INDEX FROM orders WHERE Column_name='rider_id'")
        index = cursor.fetchone()
        
        if index:
            print(f"✅ Index exists on rider_id")
            cursor.close()
            conn.close()
            return True
        else:
            print("⚠️ Index not found on rider_id (not critical, but recommended for performance)")
            cursor.close()
            conn.close()
            return True
    except Exception as e:
        print(f"⚠️ Error checking index: {e}")
        return True

def main():
    """Run all verification checks"""
    print("\n" + "="*60)
    print("🔧 HTTP 500 ERROR FIX VERIFICATION")
    print("="*60)
    
    results = {
        'Columns': check_database_columns(),
        'Query': test_query(),
        'Foreign Key': check_foreign_key(),
        'Index': check_index()
    }
    
    print("\n" + "="*60)
    print("📋 VERIFICATION SUMMARY")
    print("="*60)
    
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL CHECKS PASSED - ERROR SHOULD BE FIXED!")
        print("   The Seller Dashboard orders should now load correctly.")
        return 0
    else:
        print("❌ SOME CHECKS FAILED - PLEASE REVIEW ABOVE")
        return 1

if __name__ == '__main__':
    sys.exit(main())
