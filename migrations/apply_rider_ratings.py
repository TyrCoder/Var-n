#!/usr/bin/env python3
"""
Migration script to create rider_ratings table
"""
import mysql.connector
import os

def get_db_connection():
    """Get database connection"""
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='123456',
        database='varon'
    )

def main():
    """Apply rider_ratings migration"""
    print("Creating rider_ratings table...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Read SQL file
        sql_file = os.path.join(os.path.dirname(__file__), 'create_rider_ratings.sql')
        with open(sql_file, 'r') as f:
            sql_script = f.read()
        
        # Split into individual statements and execute
        statements = [s.strip() for s in sql_script.split(';') if s.strip()]
        
        for statement in statements:
            if statement:
                cursor.execute(statement)
                print(f"✓ Executed: {statement[:60]}...")
        
        conn.commit()
        print("\n✓ rider_ratings table created successfully!")
        
        # Verify table exists
        cursor.execute("SHOW TABLES LIKE 'rider_ratings'")
        result = cursor.fetchone()
        if result:
            print("✓ Verified: rider_ratings table exists")
            
            # Show table structure
            cursor.execute("DESCRIBE rider_ratings")
            columns = cursor.fetchall()
            print("\nTable structure:")
            for col in columns:
                print(f"  {col[0]}: {col[1]}")
        
    except mysql.connector.Error as e:
        print(f"✗ Error: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()
    
    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
