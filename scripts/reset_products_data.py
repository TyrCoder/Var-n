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

TABLES_TO_TRUNCATE = [
    'cart',
    'order_items',
    'reviews',
    'seller_notifications',
    'product_archive_requests',
    'product_edits',
    'inventory',
    'product_variants',
    'product_images',
    'products'
]


def get_connection():
    return mysql.connector.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database']
    )


def reset_products_data():
    conn = get_connection()
    cursor = conn.cursor()

    print('[RESET] Starting product data reset...')

    cursor.execute('SET FOREIGN_KEY_CHECKS = 0;')

    for table in TABLES_TO_TRUNCATE:
        try:
            print(f'[RESET] Truncating table: {table}')
            cursor.execute(f'TRUNCATE TABLE {table};')
        except mysql.connector.Error as err:
            print(f'[RESET] Could not truncate {table}: {err}')

    cursor.execute('SET FOREIGN_KEY_CHECKS = 1;')

    conn.commit()
    cursor.close()
    conn.close()

    print('[RESET] Product data reset completed.')


if __name__ == '__main__':
    reset_products_data()
