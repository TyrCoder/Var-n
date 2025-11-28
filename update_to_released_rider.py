from app import get_db

conn = get_db()
cursor = conn.cursor()

try:

    cursor.execute("""
        UPDATE orders
        SET order_status = 'released_to_rider'
        WHERE order_status = 'delivered'
    """)
    conn.commit()

    print(f"✅ Updated {cursor.rowcount} orders from 'delivered' to 'released_to_rider'")

except Exception as e:
    print(f"❌ Error: {e}")
finally:
    cursor.close()
    conn.close()
