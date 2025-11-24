"""
Database Migration Script for Varon E-commerce
This script will fix the otp_verifications table and ensure all tables are properly configured
"""

import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'varon')
}

def run_migration():
    """Run database migration to fix tables"""
    print("=" * 60)
    print("DATABASE MIGRATION SCRIPT")
    print("=" * 60)
    
    try:
        # Connect to database
        print(f"\n[1/5] Connecting to database '{DB_CONFIG['database']}'...")
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("✓ Connected successfully")
        
        # Check if otp_verifications table exists
        print("\n[2/5] Checking otp_verifications table...")
        cursor.execute("SHOW TABLES LIKE 'otp_verifications'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("✗ Table does not exist. Creating table...")
            cursor.execute('''CREATE TABLE otp_verifications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(190),
                phone VARCHAR(20),
                otp_code VARCHAR(10) NOT NULL,
                otp_type ENUM('email', 'sms') NOT NULL DEFAULT 'email',
                purpose ENUM('registration', 'login', 'password_reset', 'verification') NOT NULL DEFAULT 'registration',
                expires_at TIMESTAMP NOT NULL,
                used_at TIMESTAMP NULL,
                attempts INT DEFAULT 0,
                ip_address VARCHAR(45),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_email (email),
                INDEX idx_phone (phone),
                INDEX idx_code (otp_code),
                INDEX idx_expires (expires_at),
                INDEX idx_purpose (purpose)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
            conn.commit()
            print("✓ Table created successfully")
        else:
            print("✓ Table exists")
        
        # Check and add missing columns
        print("\n[3/5] Checking for missing columns...")
        cursor.execute("SHOW COLUMNS FROM otp_verifications")
        columns = [col[0] for col in cursor.fetchall()]
        
        migrations_applied = []
        
        # Check for phone column
        if 'phone' not in columns:
            print("  → Adding 'phone' column...")
            cursor.execute("ALTER TABLE otp_verifications ADD COLUMN phone VARCHAR(20) AFTER email")
            migrations_applied.append("Added 'phone' column")
        else:
            print("  ✓ 'phone' column exists")
        
        # Check for used_at column
        if 'used_at' not in columns:
            print("  → Adding 'used_at' column...")
            cursor.execute("ALTER TABLE otp_verifications ADD COLUMN used_at TIMESTAMP NULL AFTER expires_at")
            migrations_applied.append("Added 'used_at' column")
        else:
            print("  ✓ 'used_at' column exists")
        
        # Check for attempts column
        if 'attempts' not in columns:
            print("  → Adding 'attempts' column...")
            cursor.execute("ALTER TABLE otp_verifications ADD COLUMN attempts INT DEFAULT 0 AFTER used_at")
            migrations_applied.append("Added 'attempts' column")
        else:
            print("  ✓ 'attempts' column exists")
        
        # Check for ip_address column
        if 'ip_address' not in columns:
            print("  → Adding 'ip_address' column...")
            cursor.execute("ALTER TABLE otp_verifications ADD COLUMN ip_address VARCHAR(45) AFTER attempts")
            migrations_applied.append("Added 'ip_address' column")
        else:
            print("  ✓ 'ip_address' column exists")
        
        # Check and add missing indexes
        print("\n[4/5] Checking for missing indexes...")
        cursor.execute("SHOW INDEX FROM otp_verifications")
        indexes = [idx[2] for idx in cursor.fetchall()]
        
        if 'idx_phone' not in indexes:
            print("  → Adding 'idx_phone' index...")
            try:
                cursor.execute("CREATE INDEX idx_phone ON otp_verifications(phone)")
                migrations_applied.append("Added 'idx_phone' index")
            except mysql.connector.Error as e:
                if e.errno != 1061:  # Duplicate key name
                    raise
                print("  ✓ 'idx_phone' index already exists")
        else:
            print("  ✓ 'idx_phone' index exists")
        
        if 'idx_email' not in indexes:
            print("  → Adding 'idx_email' index...")
            try:
                cursor.execute("CREATE INDEX idx_email ON otp_verifications(email)")
                migrations_applied.append("Added 'idx_email' index")
            except mysql.connector.Error as e:
                if e.errno != 1061:
                    raise
                print("  ✓ 'idx_email' index already exists")
        else:
            print("  ✓ 'idx_email' index exists")
        
        # Create journal_entries table if not exists
        print("\n[5/5] Checking journal_entries table...")
        cursor.execute("SHOW TABLES LIKE 'journal_entries'")
        journal_exists = cursor.fetchone()
        
        if not journal_exists:
            print("  → Creating journal_entries table...")
            cursor.execute('''CREATE TABLE journal_entries (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                image_url VARCHAR(500),
                link_url VARCHAR(500),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                created_by INT,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
                INDEX idx_active (is_active),
                INDEX idx_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4''')
            migrations_applied.append("Created 'journal_entries' table")
        else:
            print("  ✓ journal_entries table exists")
        
        # Commit all changes
        conn.commit()
        
        # Display final table structure
        print("\n" + "=" * 60)
        print("FINAL TABLE STRUCTURE")
        print("=" * 60)
        cursor.execute("DESCRIBE otp_verifications")
        columns = cursor.fetchall()
        print("\notp_verifications columns:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]}")
        
        # Summary
        print("\n" + "=" * 60)
        print("MIGRATION SUMMARY")
        print("=" * 60)
        if migrations_applied:
            print(f"\n✓ Applied {len(migrations_applied)} migration(s):")
            for migration in migrations_applied:
                print(f"  • {migration}")
        else:
            print("\n✓ No migrations needed - database is up to date")
        
        print("\n✓ Migration completed successfully!")
        print("=" * 60)
        
        cursor.close()
        conn.close()
        
        return True
        
    except mysql.connector.Error as err:
        print(f"\n✗ Database error: {err}")
        print(f"Error code: {err.errno}")
        print(f"SQL State: {err.sqlstate}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("\nStarting database migration...")
    print("This script will fix the otp_verifications table structure.\n")
    
    success = run_migration()
    
    if success:
        print("\n🎉 You can now restart your Flask application!")
        print("The seller signup should work correctly now.\n")
    else:
        print("\n❌ Migration failed. Please check the error messages above.")
        print("You may need to run the SQL commands manually.\n")

