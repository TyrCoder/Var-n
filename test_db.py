import os
import sys

print("Python version:", sys.version)
print("Current directory:", os.getcwd())
print("Script path:", __file__)

try:
    import mysql.connector
    print("✅ MySQL connector imported")
except ImportError as e:
    print(f"❌ Failed to import mysql.connector: {e}")
    sys.exit(1)

db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'varon'),
}

print(f"DB Config: host={db_config['host']}, user={db_config['user']}, db={db_config['database']}")

try:
    conn = mysql.connector.connect(**db_config)
    print("✅ Connected to database")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM categories")
    count = cursor.fetchone()[0]
    print(f"✅ Current categories: {count}")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
