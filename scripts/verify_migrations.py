import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'varon'
}

def verify_migrations():
    """Verify all migrations were applied correctly"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if not conn.is_connected():
            print("❌ Failed to connect to database")
            return False
        
        cursor = conn.cursor()
        all_good = True
        
        print("=" * 80)
        print("MIGRATION VERIFICATION REPORT")
        print("=" * 80)
        
        # Check 1: Users table has verification columns
        print("\n✓ Checking 1: Users table verification columns")
        cursor.execute("SHOW COLUMNS FROM users WHERE Field IN ('email_verified', 'phone_verified', 'email_verified_at', 'phone_verified_at', 'verification_token')")
        verify_cols = cursor.fetchall()
        if len(verify_cols) == 5:
            print("  ✓ All 5 verification columns present")
            for col in verify_cols:
                print(f"    - {col[0]}")
        else:
            print(f"  ❌ Missing verification columns (found {len(verify_cols)}/5)")
            all_good = False
        
        # Check 2: Products table has edit and archive columns
        print("\n✓ Checking 2: Products table edit/archive columns")
        cursor.execute("SHOW COLUMNS FROM products WHERE Field IN ('edit_status', 'archive_status', 'archived_at', 'archived_by')")
        prod_cols = cursor.fetchall()
        if len(prod_cols) == 4:
            print("  ✓ All 4 product edit/archive columns present")
            for col in prod_cols:
                print(f"    - {col[0]}")
        else:
            print(f"  ❌ Missing product columns (found {len(prod_cols)}/4)")
            all_good = False
        
        # Check 3: Required tables exist
        print("\n✓ Checking 3: All required tables exist")
        required_tables = [
            'users', 'sellers', 'riders', 'products', 'orders', 'order_items',
            'shipments', 'addresses', 'flash_sales', 'flash_sale_products',
            'product_edits', 'product_archive_requests', 'otp_verifications'
        ]
        cursor.execute("SHOW TABLES")
        existing_tables = [t[0] for t in cursor.fetchall()]
        missing_tables = set(required_tables) - set(existing_tables)
        
        if not missing_tables:
            print(f"  ✓ All {len(required_tables)} required tables present")
        else:
            print(f"  ❌ Missing tables: {missing_tables}")
            all_good = False
        
        # Check 4: Data integrity
        print("\n✓ Checking 4: Data integrity")
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM users) as cnt_users,
                (SELECT COUNT(*) FROM sellers) as cnt_sellers,
                (SELECT COUNT(*) FROM riders) as cnt_riders,
                (SELECT COUNT(*) FROM products) as cnt_products,
                (SELECT COUNT(*) FROM orders) as cnt_orders,
                (SELECT COUNT(*) FROM order_items) as cnt_order_items
        """)
        counts = cursor.fetchone()
        print(f"  Users: {counts[0]}")
        print(f"  Sellers: {counts[1]}")
        print(f"  Riders: {counts[2]}")
        print(f"  Products: {counts[3]}")
        print(f"  Orders: {counts[4]}")
        print(f"  Order Items: {counts[5]}")
        
        # Check 5: Foreign key constraints
        print("\n✓ Checking 5: Key relationships")
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM orders WHERE seller_id IS NOT NULL) as orders_with_seller,
                (SELECT COUNT(*) FROM orders WHERE user_id IS NOT NULL) as orders_with_user,
                (SELECT COUNT(*) FROM products WHERE seller_id IS NOT NULL) as products_with_seller
        """)
        relations = cursor.fetchone()
        print(f"  Orders with seller_id: {relations[0]}")
        print(f"  Orders with user_id: {relations[1]}")
        print(f"  Products with seller_id: {relations[2]}")
        
        print("\n" + "=" * 80)
        if all_good:
            print("✓ ALL MIGRATIONS VERIFIED SUCCESSFULLY!")
        else:
            print("⚠ Some migrations may need attention")
        print("=" * 80)
        
        cursor.close()
        conn.close()
        return all_good
        
    except Error as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    verify_migrations()
