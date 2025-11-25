from app import get_db

conn = get_db()
cursor = conn.cursor()

try:
    # Update the order_status enum to include 'released_to_rider'
    sql = """ALTER TABLE orders MODIFY COLUMN order_status ENUM('pending','confirmed','released_to_rider','delivered','cancelled','returned') DEFAULT 'pending'"""
    cursor.execute(sql)
    conn.commit()
    print("✅ order_status enum updated successfully to include 'released_to_rider'")
except Exception as e:
    print(f"❌ Error updating enum: {e}")
finally:
    cursor.close()
    conn.close()
