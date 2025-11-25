from app import get_db

conn = get_db()
cursor = conn.cursor(dictionary=True)

try:
    cursor.execute("SELECT COLUMN_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='orders' AND COLUMN_NAME='order_status'")
    result = cursor.fetchone()
    print(f"✅ Order Status Enum: {result['COLUMN_TYPE']}")
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    cursor.close()
    conn.close()
