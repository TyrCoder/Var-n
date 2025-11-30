import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'varon')
}


def get_connection():
    return mysql.connector.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database']
    )


def reset_database_preserve_categories():
    conn = get_connection()
    cursor = conn.cursor()

    print("[RESET] Starting database reset while preserving categories...")

    # Tables that reference categories via foreign keys and will be truncated
    tables_to_truncate = [
        'product_archive_requests',
        'product_edits',
        'inventory',
        'product_variants',
        'product_images',
        'orders',
        'addresses',
        'products',
        'sellers',
        'users',
        'otp_codes',
        'rider_ratings',
        'shipments'
    ]

    # Turn off foreign key checks to allow truncation in any order
    cursor.execute('SET FOREIGN_KEY_CHECKS = 0;')

    for table in tables_to_truncate:
        try:
            print(f"[RESET] Truncating table: {table}")
            cursor.execute(f'TRUNCATE TABLE {table};')
        except mysql.connector.Error as err:
            # Some tables may not exist in older schemas; just log and continue
            print(f"[RESET] Skipping table {table} (error: {err})")

    cursor.execute('SET FOREIGN_KEY_CHECKS = 1;')

    # Insert admin user account
    print("[RESET] Inserting admin user account...")
    admin_email = 'admin@varon.com'
    admin_password = 'admin123'  # NOTE: plaintext for demo only; hash in production

    # Remove any existing admin with same email to avoid duplicate key issues
    cursor.execute("DELETE FROM users WHERE email = %s", (admin_email,))

    cursor.execute(
        """
        INSERT INTO users (first_name, last_name, email, password, phone, role, status)
        VALUES (%s, %s, %s, %s, %s, 'admin', 'active')
        """,
        ('Admin', 'User', admin_email, admin_password, '0000000000')
    )

    conn.commit()
    cursor.close()
    conn.close()

    print("[RESET] Done. Categories preserved and admin account created.")


if __name__ == '__main__':
    reset_database_preserve_categories()
