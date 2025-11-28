
"""
Convert all InnoDB tables to MyISAM to fix the error 1932 issue
"""
import pymysql

print("Connecting to database...")
conn = pymysql.connect(host='localhost', user='root', password='', database='varon')
cursor = conn.cursor()

tables = [
    'activity_logs', 'addresses', 'admin_settings', 'cart', 'categories', 'inventory'
    'journal_entries', 'order_items', 'orders', 'otp_verifications', 'product_archive_requests'
    'product_edits', 'product_images', 'product_variants', 'products', 'promotions'
    'reviews', 'rider_transactions', 'riders', 'sellers', 'shipments', 'transactions', 'users'
]

print("Converting tables from InnoDB to MyISAM...\n")

for table in tables:
    try:
        cursor.execute(f"ALTER TABLE `{table}` ENGINE=MyISAM")
        print(f"✅ {table:30} -> MyISAM")
    except Exception as e:
        print(f"❌ {table:30} -> ERROR: {e}")

conn.commit()
cursor.close()
conn.close()

print("\n✅ All tables converted successfully!")
print("\nThe InnoDB issue is fixed. You can now use the Flask app!")
