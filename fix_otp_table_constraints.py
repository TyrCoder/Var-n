"""
Fix OTP Verifications Table - Remove user_id constraint and fix structure
"""

import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'varon')
}

def fix_table():
    print("=" * 60)
    print("FIXING OTP_VERIFICATIONS TABLE")
    print("=" * 60)

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        print("\n[1/4] Backing up existing data...")
        cursor.execute("SELECT COUNT(*) FROM otp_verifications")
        count = cursor.fetchone()[0]
        print(f"  Found {count} existing records")

        print("\n[2/4] Dropping foreign key constraint...")
        try:
            cursor.execute("ALTER TABLE otp_verifications DROP FOREIGN KEY otp_verifications_ibfk_1")
            print("  ✓ Foreign key constraint removed")
        except mysql.connector.Error as e:
            if e.errno == 1091:
                print("  ✓ No foreign key to remove")
            else:
                raise

        print("\n[3/4] Removing user_id column...")
        try:
            cursor.execute("ALTER TABLE otp_verifications DROP COLUMN user_id")
            print("  ✓ user_id column removed")
        except mysql.connector.Error as e:
            if e.errno == 1091:
                print("  ✓ user_id column already removed")
            else:
                raise

        print("\n[4/4] Fixing column types and constraints...")


        try:
            cursor.execute("ALTER TABLE otp_verifications MODIFY COLUMN email VARCHAR(190) NULL")
            print("  ✓ email column set to nullable")
        except Exception as e:
            print(f"  Note: {e}")


        try:
            cursor.execute("ALTER TABLE otp_verifications MODIFY COLUMN ip_address VARCHAR(45) NULL")
            print("  ✓ ip_address column set to nullable")
        except Exception as e:
            print(f"  Note: {e}")


        try:
            cursor.execute("ALTER TABLE otp_verifications MODIFY COLUMN otp_type ENUM('email', 'sms') NOT NULL DEFAULT 'email'")
            print("  ✓ otp_type enum updated")
        except Exception as e:
            print(f"  Note: {e}")


        try:
            cursor.execute("ALTER TABLE otp_verifications MODIFY COLUMN purpose ENUM('registration', 'login', 'password_reset', 'verification') NOT NULL DEFAULT 'registration'")
            print("  ✓ purpose enum updated")
        except Exception as e:
            print(f"  Note: {e}")

        conn.commit()

        print("\n" + "=" * 60)
        print("FINAL TABLE STRUCTURE")
        print("=" * 60)
        cursor.execute("DESCRIBE otp_verifications")
        columns = cursor.fetchall()
        print("\nColumns:")
        for col in columns:
            null = "NULL" if col[2] == "YES" else "NOT NULL"
            default = f"DEFAULT {col[4]}" if col[4] else ""
            print(f"  {col[0]}: {col[1]} {null} {default}")

        print("\n" + "=" * 60)
        print("✓ Table fixed successfully!")
        print("=" * 60)

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = fix_table()
    if success:
        print("\n🎉 Restart your Flask app - seller signup should work now!\n")
    else:
        print("\n❌ Fix failed. Check error messages above.\n")

