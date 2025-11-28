
"""
Script to add missing product categories to the database
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


CATEGORIES = [
    ('Grooming Products', 'grooming-products', True),
    ('Activewear & Fitness', 'activewear-fitness', True),
    ('Shoes & Accessories', 'shoes-accessories', True),
    ('Outerwear & Jackets', 'outerwear-jackets', True),
    ('Casual Shirts & Pants', 'casual-shirts-pants', True),
    ('Suits & Blazers', 'suits-blazers', True),
    ('Tops', 'tops', True),
    ('Bottoms', 'bottoms', True),
    ('Formal Wear', 'formal-wear', True),
]

def add_categories():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        added = 0
        skipped = 0

        for name, slug, is_active in CATEGORIES:

            cursor.execute(
                "SELECT id FROM categories WHERE slug = %s",
                (slug,)
            )
            existing = cursor.fetchone()

            if existing:
                print(f"✓ Category '{name}' already exists")
                skipped += 1
            else:

                cursor.execute(
                    "INSERT INTO categories (name, slug, is_active) VALUES (%s, %s, %s)",
                    (name, slug, is_active)
                )
                conn.commit()
                print(f"✓ Added category: {name}")
                added += 1

        cursor.close()
        conn.close()

        print(f"\n✓ Process complete: {added} added, {skipped} skipped")

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

    return True

if __name__ == '__main__':
    print("Adding missing product categories...\n")
    add_categories()
