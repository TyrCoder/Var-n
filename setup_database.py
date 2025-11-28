#!/usr/bin/env python3
import mysql.connector
import sys

def init_database():
    """Initialize the MySQL database"""
    try:
        print("Attempting to connect to MySQL...")
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password=''
        )
        print("✓ Connected to MySQL")
        
        cursor = conn.cursor()
        
        print("Creating database 'varon' if it doesn't exist...")
        cursor.execute("CREATE DATABASE IF NOT EXISTS varon")
        print("✓ Database 'varon' ready")
        
        cursor.execute("USE varon")
        
        print("Initializing database tables...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) UNIQUE,
                password VARCHAR(255),
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                phone VARCHAR(20),
                role ENUM('buyer', 'seller', 'rider', 'admin') DEFAULT 'buyer',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✓ Tables initialized")
        
        cursor.close()
        conn.close()
        print("\n✓ SUCCESS: Database initialized and ready!")
        return True
        
    except mysql.connector.Error as err:
        if err.errno == 2003:
            print(f"✗ ERROR: Cannot connect to MySQL server on 'localhost'")
            print("  Please ensure:")
            print("  1. MySQL Server is installed")
            print("  2. MySQL service is running")
            print("  3. MySQL is accessible on localhost:3306")
        elif err.errno == 1045:
            print(f"✗ ERROR: Access denied for user 'root'")
            print("  Check your MySQL root password in the app config")
        else:
            print(f"✗ ERROR: {err}")
        return False
    except Exception as err:
        print(f"✗ ERROR: {err}")
        return False

if __name__ == '__main__':
    success = init_database()
    sys.exit(0 if success else 1)
