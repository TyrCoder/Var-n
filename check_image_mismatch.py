import mysql.connector
import os
from pathlib import Path


DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'varon'
}


conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor(dictionary=True)
cursor.execute("""
    SELECT DISTINCT p.id, p.name, pi.image_url
    FROM products p
    LEFT JOIN product_images pi ON p.id = pi.product_id AND pi.is_primary = 1
    ORDER BY p.id
""")
db_products = cursor.fetchall()
cursor.close()
conn.close()


static_dir = Path(r"c:\Users\windows\OneDrive\Documents\GitHub\Var-n\static\images\products")
fs_files = set(f.name for f in static_dir.glob("*") if f.is_file())

print("="*80)
print("DATABASE vs FILESYSTEM Analysis")
print("="*80)

missing_count = 0
found_count = 0

for product in db_products:
    if not product['image_url']:
        print(f"\n❌ Product {product['id']}: {product['name']}")
        print(f"   NO IMAGE IN DATABASE")
        missing_count += 1
        continue


    filename = product['image_url'].split('/')[-1]
    file_exists = filename in fs_files

    if file_exists:
        print(f"\n✅ Product {product['id']}: {product['name']}")
        print(f"   Image: {filename}")
        found_count += 1
    else:
        print(f"\n❌ Product {product['id']}: {product['name']}")
        print(f"   Missing: {filename}")
        print(f"   DB Path: {product['image_url']}")
        missing_count += 1

print("\n" + "="*80)
print(f"Summary: {found_count} images found, {missing_count} missing")
print("="*80)

print(f"\nTotal files in filesystem: {len(fs_files)}")
print(f"Total active products: {len(db_products)}")

print("\n" + "="*80)
print("Available files in filesystem:")
print("="*80)
for filename in sorted(fs_files)[:10]:
    print(f"  {filename}")
if len(fs_files) > 10:
    print(f"  ... and {len(fs_files) - 10} more")
