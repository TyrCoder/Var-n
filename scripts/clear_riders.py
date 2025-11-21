import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'varon')
}

try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("CLEARING RIDERS FROM DATABASE")
    print("=" * 60)
    
    # Get count before deletion
    cursor.execute('SELECT COUNT(*) FROM riders')
    count_before = cursor.fetchone()[0]
    print(f"\nRiders before deletion: {count_before}")
    
    if count_before > 0:
        # Delete all riders
        cursor.execute('DELETE FROM riders')
        conn.commit()
        
        # Verify deletion
        cursor.execute('SELECT COUNT(*) FROM riders')
        count_after = cursor.fetchone()[0]
        
        print(f"Riders after deletion: {count_after}")
        print(f"\n✓ Successfully deleted {count_before} riders")
    else:
        print("\nNo riders to delete")
    
    cursor.close()
    conn.close()
    print("=" * 60)
    
except Exception as e:
    print(f"Error: {e}")
