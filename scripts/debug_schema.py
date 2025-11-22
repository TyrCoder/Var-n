import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'varon'
}

def debug_database():
    """Debug database schema and data"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if not conn.is_connected():
            print("Failed to connect to database")
            return
        
        cursor = conn.cursor()
        
        print("=" * 80)
        print("USERS TABLE SCHEMA")
        print("=" * 80)
        cursor.execute("DESCRIBE users")
        columns = cursor.fetchall()
        for col in columns:
            null_val = col[2] if col[2] else 'N/A'
            key_val = col[3] if col[3] else 'N/A'
            extra_val = col[5] if col[5] else 'N/A'
            print(f"{col[0]:<20} {col[1]:<20} {null_val:<5} {key_val:<5} {extra_val:<15}")
        
        print("\n" + "=" * 80)
        print("USERS TABLE DATA")
        print("=" * 80)
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        print(f"Total users: {len(users)}\n")
        for user in users:
            print(user)
        
        print("\n" + "=" * 80)
        print("ALL TABLES IN DATABASE")
        print("=" * 80)
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"{table[0]:<30} ({count} rows)")
        
        print("\n" + "=" * 80)
        print("CHECKING FOR MISSING COLUMNS IN USERS TABLE")
        print("=" * 80)
        
        # Expected columns based on migrations
        expected_columns = [
            'id', 'first_name', 'last_name', 'email', 'password', 'phone', 'role',
            'status', 'created_at', 'updated_at'
            # Potential columns from migrations
        ]
        
        actual_columns = [col[0] for col in columns]
        missing = set(expected_columns) - set(actual_columns)
        extra = set(actual_columns) - set(expected_columns)
        
        if missing:
            print(f"\n❌ Missing columns: {missing}")
        else:
            print("\n✓ All basic columns present")
        
        if extra:
            print(f"\n📌 Extra columns found: {extra}")
        
        cursor.close()
        conn.close()
        
    except Error as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    debug_database()
