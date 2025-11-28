
"""
Quick database verification script
"""
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

print("=" * 60)
print("DATABASE CONNECTION TEST")
print("=" * 60)
print(f"\nConnecting to:")
print(f"  Host: {DB_CONFIG['host']}")
print(f"  User: {DB_CONFIG['user']}")
print(f"  Database: {DB_CONFIG['database']}")
print()

try:

    conn = mysql.connector.connect(**DB_CONFIG)
    conn.database = DB_CONFIG['database']
    print("✅ Connection successful!")


    cursor = conn.cursor()


    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]
    print(f"✅ Users table: {user_count} records")


    cursor.execute('SELECT COUNT(*) FROM products')
    product_count = cursor.fetchone()[0]
    print(f"✅ Products table: {product_count} records")


    cursor.execute('SELECT COUNT(*) FROM orders')
    order_count = cursor.fetchone()[0]
    print(f"✅ Orders table: {order_count} records")


    cursor.execute("""
        SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = %s
        ORDER BY TABLE_NAME
    """, (DB_CONFIG['database'],))

    tables = cursor.fetchall()
    print(f"\n✅ Total tables in database: {len(tables)}")
    print("\nTables:")
    for table in tables:
        print(f"  • {table[0]}")

    cursor.close()
    conn.close()

    print("\n" + "=" * 60)
    print("✅ DATABASE IS READY!")
    print("=" * 60)

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\n" + "=" * 60)
    print("❌ DATABASE CONNECTION FAILED")
    print("=" * 60)
