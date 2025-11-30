"""
Comprehensive cart debugging script
"""
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def debug_cart_system():
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'varon')
        )
        cursor = conn.cursor(dictionary=True)
        
        print("=" * 60)
        print("CART DEBUGGING")
        print("=" * 60)
        
        # 1. Check if tables exist
        print("\n1. Checking tables...")
        for table in ['users', 'cart', 'products', 'product_images']:
            cursor.execute(f"SHOW TABLES LIKE '{table}'")
            exists = "✓" if cursor.fetchone() else "✗"
            print(f"   {exists} {table}")
        
        # 2. Get all users
        print("\n2. Users in database:")
        cursor.execute("SELECT id, email, first_name, role FROM users LIMIT 5")
        users = cursor.fetchall()
        if users:
            for user in users:
                print(f"   ID {user['id']}: {user['first_name']} ({user['email']}) - Role: {user['role']}")
        else:
            print("   No users found!")
        
        # 3. Get all cart items
        print("\n3. Cart items in database:")
        cursor.execute('''
            SELECT c.id, c.user_id, c.product_id, c.quantity, c.variant_id,
                   u.email, p.name
            FROM cart c
            LEFT JOIN users u ON c.user_id = u.id
            LEFT JOIN products p ON c.product_id = p.id
            LIMIT 10
        ''')
        carts = cursor.fetchall()
        if carts:
            for cart in carts:
                print(f"   Cart {cart['id']}: User {cart['user_id']} ({cart['email']}) - {cart['name']} x{cart['quantity']}")
        else:
            print("   No cart items found!")
        
        # 4. Check products and images
        print("\n4. Products and their images:")
        cursor.execute('''
            SELECT p.id, p.name, COUNT(pi.id) as image_count
            FROM products p
            LEFT JOIN product_images pi ON p.id = pi.product_id
            GROUP BY p.id
            LIMIT 5
        ''')
        products = cursor.fetchall()
        if products:
            for prod in products:
                print(f"   Product {prod['id']}: {prod['name']} ({prod['image_count']} images)")
        else:
            print("   No products found!")
        
        cursor.close()
        conn.close()
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_cart_system()
