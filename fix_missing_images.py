import mysql.connector
from pathlib import Path


DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'varon'
}


static_dir = Path(r"c:\Users\windows\OneDrive\Documents\GitHub\Var-n\static\images\products")
fs_files = set(f.name for f in static_dir.glob("*") if f.is_file())


conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor(dictionary=True)


cursor.execute("""
    SELECT pi.id, pi.product_id, pi.image_url, pi.is_primary, p.name
    FROM product_images pi
    JOIN products p ON pi.product_id = p.id
    ORDER BY pi.product_id, pi.is_primary DESC
""")
all_images = cursor.fetchall()

print("="*80)
print("Fixing Missing Images")
print("="*80)

updated_count = 0
placeholder_url = "/static/images/placeholder.svg"

for img in all_images:
    filename = img['image_url'].split('/')[-1]
    file_exists = filename in fs_files

    if not file_exists:
        print(f"\n❌ Missing: {filename}")
        print(f"   Product: {img['name']} (ID: {img['product_id']})")
        print(f"   Setting to placeholder...")


        cursor.execute(
            "UPDATE product_images SET image_url = %s WHERE id = %s",
            (placeholder_url, img['id'])
        )
        updated_count += 1

conn.commit()
cursor.close()
conn.close()

print("\n" + "="*80)
print(f"✅ Updated {updated_count} image URLs to use placeholder")
print("="*80)
print("\nProducts will now display with placeholder images until real images are uploaded.")
