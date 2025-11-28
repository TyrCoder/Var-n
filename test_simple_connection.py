import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'varon')
}

print("Test 1: Simple connection (no database)")
try:
    print("Connecting to localhost as root...")
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password=''
    )
    print(f"✅ Connected!")

    cursor = conn.cursor()
    cursor.execute("SHOW DATABASES")
    databases = cursor.fetchall()
    print(f"✅ Databases: {len(databases)}")
    for db in databases:
        if 'varon' in db[0] or 'test' in db[0]:
            print(f"   - {db[0]}")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
