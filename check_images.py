import mysql.connector
from config import DB_CONFIG


conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor(dictionary=True)


cursor.execute("""
    SELECT p.id, p.name, pi.image_url, pi.is_primary
    FROM products p
    LEFT JOIN product_images pi ON p.id = pi.product_id
    WHERE p.is_active = 1
    ORDER BY p.id, pi.is_primary DESC
    LIMIT 20
""")

products = cursor.fetchall()

print("Products and their images:")
print("-" * 80)
for product in products:
    print(f"ID: {product['id']}")
    print(f"Name: {product['name']}")
    print(f"Image URL: {product['image_url']}")
    print(f"Is Primary: {product['is_primary']}")
    print("-" * 80)

cursor.close()
conn.close()
