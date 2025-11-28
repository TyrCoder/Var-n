import mysql.connector
from mysql.connector import Error

try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='varon'
    )
    
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("UPDATE sellers SET status = 'approved' WHERE status = 'pending'")
    updated_count = cursor.rowcount
    
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) as total FROM sellers")
    total = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as approved FROM sellers WHERE status = 'approved'")
    approved = cursor.fetchone()['approved']
    
    cursor.close()
    conn.close()
    
    print(f"✅ SUCCESS: Updated {updated_count} sellers from 'pending' to 'approved'")
    print(f"📊 Status: {approved}/{total} sellers are now APPROVED")
    
except Error as e:
    print(f"❌ ERROR: {e}")
except Exception as e:
    print(f"❌ ERROR: {e}")
