import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import get_db

# Check database for product images
conn = get_db()
cursor = conn.cursor(dictionary=True)

print("\n" + "="*80)
print("DATABASE: Product Images Check")
print("="*80)

cursor.execute("""
    SELECT p.id, p.name, pi.image_url, pi.is_primary
    FROM products p
    LEFT JOIN product_images pi ON p.id = pi.product_id
    WHERE p.is_active = 1 AND p.archive_status = 'active'
    ORDER BY p.id, pi.is_primary DESC
    LIMIT 5
""")
results = cursor.fetchall()

if results:
    for row in results:
        print(f"Product {row['id']}: {row['name']}")
        print(f"  Image URL: {row['image_url']}")
        print(f"  Primary: {row['is_primary']}")
        if row['image_url']:
            # Check if file exists
            file_path = row['image_url'].replace('/static/', 'static/')
            exists = os.path.exists(file_path)
            print(f"  File exists: {exists} ({file_path})")
        print()
else:
    print("No products with images found!")

print("\n" + "="*80)
print("FILESYSTEM: Check image files")
print("="*80)

image_dir = "static/images/products"
if os.path.exists(image_dir):
    files = os.listdir(image_dir)
    print(f"Found {len(files)} files in {image_dir}:")
    for f in files[:5]:
        full_path = os.path.join(image_dir, f)
        size = os.path.getsize(full_path)
        print(f"  {f} ({size} bytes)")
else:
    print(f"ERROR: Directory not found: {image_dir}")

print("\n" + "="*80)
print("API TEST: /api/products endpoint")
print("="*80)

cursor.execute("""
    SELECT 
        p.id,
        p.name,
        p.price,
        pi.image_url
    FROM products p
    LEFT JOIN product_images pi ON p.id = pi.product_id AND pi.is_primary = 1
    WHERE p.is_active = 1 AND p.archive_status = 'active'
    LIMIT 3
""")
api_products = cursor.fetchall()

for product in api_products:
    print(f"Product {product['id']}: {product['name']}")
    print(f"  Price: ₱{product['price']}")
    print(f"  Image URL: {product['image_url']}")
    print()

cursor.close()
conn.close()
