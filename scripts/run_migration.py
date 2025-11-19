"""
Migration script to add profile_image column to riders table
Run this with: python run_migration.py
"""
import mysql.connector
from mysql.connector import Error

def run_migration():
    try:
        # Connect to database
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',  # Add your password here if needed
            database='varon'
        )
        
        if conn.is_connected():
            cursor = conn.cursor()
            
            print("Connected to database successfully!")
            print("\nRunning migration: Adding profile_image column to riders table...")
            
            # Check if column already exists
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = 'varon' 
                AND TABLE_NAME = 'riders' 
                AND COLUMN_NAME = 'profile_image'
            """)
            
            exists = cursor.fetchone()[0]
            
            if exists:
                print("✓ Column 'profile_image' already exists in riders table. No migration needed.")
            else:
                # Add the column
                cursor.execute("""
                    ALTER TABLE riders 
                    ADD COLUMN profile_image VARCHAR(500) AFTER service_area
                """)
                conn.commit()
                print("✓ Successfully added 'profile_image' column to riders table!")
            
            # Show the table structure
            print("\nCurrent riders table structure:")
            cursor.execute("DESCRIBE riders")
            columns = cursor.fetchall()
            
            for col in columns:
                print(f"  - {col[0]}: {col[1]}")
            
            cursor.close()
            conn.close()
            print("\n✓ Migration completed successfully!")
            
    except Error as e:
        print(f"✗ Error: {e}")
        if conn:
            conn.close()

if __name__ == "__main__":
    run_migration()
