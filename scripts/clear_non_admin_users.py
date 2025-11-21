import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'varon')
}

try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    
    print("=" * 60)
    print("CLEARING NON-ADMIN USERS FROM DATABASE")
    print("=" * 60)
    
    # Get count before deletion
    cursor.execute('SELECT COUNT(*) as total FROM users')
    count_before = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as admin_count FROM users WHERE role = 'admin'")
    admin_count = cursor.fetchone()['admin_count']
    
    print(f"\nTotal users before: {count_before}")
    print(f"Admin users: {admin_count}")
    print(f"Non-admin users: {count_before - admin_count}")
    
    # Get admin user IDs to exclude
    cursor.execute("SELECT id, email, role FROM users WHERE role = 'admin'")
    admins = cursor.fetchall()
    
    print("\nPreserving admin accounts:")
    for admin in admins:
        print(f"  - {admin['email']} (ID: {admin['id']})")
    
    if count_before > admin_count:
        # Delete related records first (foreign key constraints - in correct order)
        
        # 1. Delete shipments (references orders and riders)
        cursor.execute("""
            DELETE FROM shipments 
            WHERE order_id IN (SELECT id FROM orders WHERE user_id IN (SELECT id FROM users WHERE role != 'admin'))
            OR rider_id IN (SELECT id FROM riders WHERE user_id IN (SELECT id FROM users WHERE role != 'admin'))
        """)
        shipments_deleted = cursor.rowcount
        
        # 2. Delete order_items (references orders)
        cursor.execute("DELETE FROM order_items WHERE order_id IN (SELECT id FROM orders WHERE user_id IN (SELECT id FROM users WHERE role != 'admin'))")
        order_items_deleted = cursor.rowcount
        
        # 3. Delete orders (references users and sellers)
        cursor.execute("DELETE FROM orders WHERE user_id IN (SELECT id FROM users WHERE role != 'admin')")
        orders_deleted = cursor.rowcount
        
        # 4. Delete products (references sellers)
        cursor.execute("DELETE FROM products WHERE seller_id IN (SELECT id FROM sellers WHERE user_id IN (SELECT id FROM users WHERE role != 'admin'))")
        products_deleted = cursor.rowcount
        
        # 5. Delete from cart table
        cursor.execute("DELETE FROM cart WHERE user_id IN (SELECT id FROM users WHERE role != 'admin')")
        cart_deleted = cursor.rowcount
        
        # 6. Delete from addresses table
        cursor.execute("DELETE FROM addresses WHERE user_id IN (SELECT id FROM users WHERE role != 'admin')")
        addresses_deleted = cursor.rowcount
        
        # 7. Delete from otp_verifications table
        cursor.execute("DELETE FROM otp_verifications WHERE user_id IN (SELECT id FROM users WHERE role != 'admin')")
        otp_deleted = cursor.rowcount
        
        # 8. Delete from sellers table
        cursor.execute("DELETE FROM sellers WHERE user_id IN (SELECT id FROM users WHERE role != 'admin')")
        sellers_deleted = cursor.rowcount
        
        # 9. Delete from riders table
        cursor.execute("DELETE FROM riders WHERE user_id IN (SELECT id FROM users WHERE role != 'admin')")
        riders_deleted = cursor.rowcount
        
        # 10. Finally delete non-admin users
        cursor.execute("DELETE FROM users WHERE role != 'admin'")
        users_deleted = cursor.rowcount
        
        conn.commit()
        
        # Verify deletion
        cursor.execute('SELECT COUNT(*) as total FROM users')
        count_after = cursor.fetchone()['total']
        
        print(f"\n✓ Successfully cleaned database:")
        print(f"  - {shipments_deleted} shipments deleted")
        print(f"  - {order_items_deleted} order items deleted")
        print(f"  - {orders_deleted} orders deleted")
        print(f"  - {products_deleted} products deleted")
        print(f"  - {cart_deleted} cart items deleted")
        print(f"  - {addresses_deleted} addresses deleted")
        print(f"  - {otp_deleted} OTP records deleted")
        print(f"  - {sellers_deleted} seller records deleted")
        print(f"  - {riders_deleted} rider records deleted")
        print(f"  - {users_deleted} user accounts deleted")
        print(f"\nUsers remaining: {count_after} (all admins)")
    else:
        print("\nNo non-admin users to delete")
    
    cursor.close()
    conn.close()
    print("=" * 60)
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
