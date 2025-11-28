from app import get_db

conn = get_db()
cursor = conn.cursor(dictionary=True)

try:

    cursor.execute("SELECT id, email, role FROM users LIMIT 10")
    users = cursor.fetchall()

    print("Users in database:")
    for user in users:
        print(f"  ID: {user['id']}, Email: {user['email']}, Role: {user['role']}")


    cursor.execute("SELECT id, user_id, store_name FROM sellers LIMIT 5")
    sellers = cursor.fetchall()

    print("\nSellers in database:")
    for seller in sellers:
        print(f"  Seller ID: {seller['id']}, User ID: {seller['user_id']}, Store: {seller['store_name']}")

except Exception as e:
    print(f"❌ Error: {e}")
finally:
    cursor.close()
    conn.close()
