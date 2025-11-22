"""
Test login flow and identify issues
"""
import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'varon'
}

def test_login_flow():
    """Test the complete login flow"""
    print("\n" + "=" * 80)
    print("LOGIN FLOW DIAGNOSTIC")
    print("=" * 80)
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # Get all users in system
        print("\n1️⃣  All Users in System:")
        print("-" * 80)
        cursor.execute("SELECT id, first_name, last_name, email, password, role FROM users ORDER BY created_at DESC LIMIT 10")
        users = cursor.fetchall()
        
        if not users:
            print("❌ No users found in database!")
        else:
            for user in users:
                print(f"  ID: {user['id']:<3} | {user['first_name']} {user['last_name']:<20} | {user['email']:<30} | Role: {user['role']:<8} | Pass: {user['password'][:20]}...")
        
        # Check seller accounts
        print("\n2️⃣  Seller Accounts:")
        print("-" * 80)
        cursor.execute("""
            SELECT s.id, s.user_id, s.store_name, s.status, u.email, u.first_name 
            FROM sellers s
            JOIN users u ON s.user_id = u.id
        """)
        sellers = cursor.fetchall()
        
        if not sellers:
            print("❌ No sellers found!")
        else:
            for seller in sellers:
                print(f"  Seller ID: {seller['id']:<3} | User ID: {seller['user_id']:<3} | Store: {seller['store_name']:<20} | Email: {seller['email']:<30} | Status: {seller['status']}")
        
        # Check buyer accounts
        print("\n3️⃣  Buyer Accounts:")
        print("-" * 80)
        cursor.execute("SELECT id, email, first_name, password FROM users WHERE role = 'buyer'")
        buyers = cursor.fetchall()
        
        if not buyers:
            print("❌ No buyers found!")
        else:
            for buyer in buyers:
                print(f"  ID: {buyer['id']:<3} | {buyer['first_name']:<15} | {buyer['email']:<30} | Pass: {buyer['password'][:20]}...")
        
        # Test a login attempt
        print("\n4️⃣  Testing Login with First User:")
        print("-" * 80)
        
        if users:
            test_user = users[0]
            test_email = test_user['email']
            test_password = test_user['password']
            
            print(f"  Testing with: {test_email}")
            print(f"  Password: {test_password}")
            
            # Simulate login query
            cursor.execute("SELECT * FROM users WHERE email = %s", (test_email,))
            login_user = cursor.fetchone()
            
            if login_user:
                print(f"  ✓ User found in database")
                
                # Test password comparison
                if test_password == login_user['password']:
                    print(f"  ✓ Password matches!")
                    print(f"  ✓ LOGIN WOULD SUCCEED")
                    print(f"  Would redirect to: {login_user['role']}_dashboard")
                else:
                    print(f"  ❌ Password mismatch!")
                    print(f"    Expected: {login_user['password']}")
                    print(f"    Got: {test_password}")
            else:
                print(f"  ❌ User not found in database!")
        
        # Check for any data issues
        print("\n5️⃣  Data Integrity Checks:")
        print("-" * 80)
        
        # Check for NULL passwords
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE password IS NULL OR password = ''")
        null_pass = cursor.fetchone()['count']
        if null_pass > 0:
            print(f"  ⚠️  {null_pass} users with NULL or empty passwords")
        else:
            print(f"  ✓ All users have passwords")
        
        # Check for valid roles
        cursor.execute("SELECT DISTINCT role FROM users")
        roles = cursor.fetchall()
        print(f"  ✓ Valid roles in system: {[r['role'] for r in roles]}")
        
        # Check session/auth settings
        print("\n6️⃣  Recommendations:")
        print("-" * 80)
        print("  ✓ Try logging in with any account from the list above")
        print("  ✓ Use the email and password shown above")
        print("  ✓ If login fails, check browser console for JavaScript errors")
        print("  ✓ Verify cookies/session are enabled in browser")
        
        cursor.close()
        conn.close()
        
    except Error as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    test_login_flow()
    print("\n" + "=" * 80 + "\n")
