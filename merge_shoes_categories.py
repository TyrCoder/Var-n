
"""
Script to merge duplicate Shoes categories
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

def merge_categories():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)


        cursor.execute("SELECT id, name FROM categories WHERE name IN ('Shoes', 'Shoes & Accessories')")
        results = cursor.fetchall()

        shoes_id = None
        shoes_accessories_id = None

        for row in results:
            if row['name'] == 'Shoes':
                shoes_id = row['id']
            elif row['name'] == 'Shoes & Accessories':
                shoes_accessories_id = row['id']

        if not shoes_id or not shoes_accessories_id:
            print("✗ Could not find both categories")
            cursor.close()
            conn.close()
            return False

        print(f"Found 'Shoes' (ID: {shoes_id})")
        print(f"Found 'Shoes & Accessories' (ID: {shoes_accessories_id})")


        cursor.execute(
            "UPDATE products SET category_id = %s WHERE category_id = %s",
            (shoes_accessories_id, shoes_id)
        )
        affected_rows = cursor.rowcount
        conn.commit()
        print(f"\n✓ Updated {affected_rows} products to use 'Shoes & Accessories'")


        cursor.execute("DELETE FROM categories WHERE id = %s", (shoes_id,))
        conn.commit()
        print(f"✓ Deleted duplicate 'Shoes' category")

        cursor.close()
        conn.close()

        print("\n✓ Categories merged successfully!")
        return True

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

if __name__ == '__main__':
    print("Merging Shoes categories...\n")
    merge_categories()
