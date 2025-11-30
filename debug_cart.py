import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'varon')
    )
    cursor = conn.cursor(dictionary=True)
    
    # Check if cart table exists
    cursor.execute("SHOW TABLES LIKE 'cart'")
    result = cursor.fetchone()
    if not result:
        print('⚠️  CART TABLE DOES NOT EXIST!')
        print('\nCreating cart table...')
    else:
        print('✓ Cart table exists')
    
    # Check cart table contents
    cursor.execute('SELECT * FROM cart LIMIT 10')
    carts = cursor.fetchall()
    print(f'\nTotal cart items in database: {len(carts)}')
    if carts:
        print('\nCart data:')
        for cart in carts:
            print(f"  - Cart ID {cart.get('id')}: User {cart.get('user_id')}, Product {cart.get('product_id')}, Qty {cart.get('quantity')}")
    else:
        print('No items in cart table')
    
    # Check users
    cursor.execute('SELECT id, email, first_name FROM users LIMIT 5')
    users = cursor.fetchall()
    print(f'\nUsers in database: {len(users)}')
    for user in users:
        print(f"  - User {user.get('id')}: {user.get('first_name')} ({user.get('email')})")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
