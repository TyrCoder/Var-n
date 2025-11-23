import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def add_otp_table():
    """Add OTP verification table to existing database"""

    # Database configuration
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'varon')
    }

    try:
        # Connect to database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        print("Connected to database successfully")

        # Check if OTP table already exists
        cursor.execute("SHOW TABLES LIKE 'otp_verifications'")
        if cursor.fetchone():
            print("OTP table already exists. Skipping migration.")
            cursor.close()
            conn.close()
            return

        # Create OTP table
        create_table_sql = """
        CREATE TABLE otp_verifications (
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
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """

        cursor.execute(create_table_sql)
        conn.commit()

        print("✅ OTP verification table created successfully!")

        cursor.close()
        conn.close()

    except mysql.connector.Error as err:
        print(f"❌ Database error: {err}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Starting OTP table migration...")
    add_otp_table()
    print("Migration completed!")