from app import get_db

conn = get_db()
cursor = conn.cursor(dictionary=True)

try:

    cursor.execute("SELECT id FROM users WHERE role = 'buyer' LIMIT 1")
    buyer = cursor.fetchone()

    if not buyer:
        print("❌ No buyer found")
        exit(1)


    cursor.execute("""
        INSERT INTO addresses (user_id, street_address, city, province, postal_code, is_default)
        VALUES (%s, '123 Main St', 'Pila', 'Laguna', '4010', TRUE)
    """, (buyer['id'],))

    conn.commit()
    print(f"✅ Created address for buyer {buyer['id']}")

except Exception as e:
    print(f"❌ Error: {e}")
finally:
    cursor.close()
    conn.close()
