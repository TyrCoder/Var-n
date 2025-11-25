from app import get_db

conn = get_db()
cursor = conn.cursor(dictionary=True)

try:
    cursor.execute("DESCRIBE users")
    result = cursor.fetchall()
    
    print("Users table columns:")
    for row in result:
        print(f"  - {row['Field']} ({row['Type']})")
        
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    cursor.close()
    conn.close()
