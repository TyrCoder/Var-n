
"""Apply migration: Fix riders table to support multiple vehicle types"""

import mysql.connector
import sys
import os


db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'varon')
}

try:

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    print("Applying migration: Fix riders table to support multiple vehicle types...")


    cursor.execute("DESCRIBE riders vehicle_type")
    result = cursor.fetchone()
    print(f"Current column definition: {result}")


    cursor.execute("""
        ALTER TABLE riders
        MODIFY COLUMN vehicle_type TEXT NOT NULL
    """)

    conn.commit()
    print("✓ Successfully modified riders.vehicle_type column to TEXT")
    print("✓ Riders can now have multiple vehicle types stored as comma-separated values")

    cursor.close()
    conn.close()

except mysql.connector.Error as err:
    if err.errno == 2003:
        print(f"ERROR: Cannot connect to database. Check that MySQL is running.")
    else:
        print(f"ERROR: {err.msg}")
    sys.exit(1)
except Exception as err:
    print(f"ERROR: {err}")
    sys.exit(1)

print("\nMigration completed successfully!")
