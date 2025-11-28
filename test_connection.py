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

print("Attempting connection with config:")
print(f"  host: {DB_CONFIG['host']}")
print(f"  user: {DB_CONFIG['user']}")
print(f"  password: {'(empty)' if not DB_CONFIG['password'] else '(set)'}")
print(f"  database: {DB_CONFIG['database']}")
print()

try:
    print("Connecting...")
    conn = mysql.connector.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database']
    )
    print(f"✅ Connected! Database: {conn.database}")

    cursor = conn.cursor()
    cursor.execute("SELECT DATABASE()")
    current_db = cursor.fetchone()[0]
    print(f"✅ Current database: {current_db}")

    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print(f"✅ Tables found: {len(tables)}")
    for table in tables:
        print(f"   - {table[0]}")

    cursor.close()
    conn.close()
    print("\n✅ ALL TESTS PASSED!")

except Exception as e:
    print(f"❌ ERROR: {e}")
    print(f"Type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
