
"""
Script to update product categories to the final polished structure
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

    ('Barong', 'barong', 'A traditional Filipino formal shirt'),
    ('Suits & Blazers', 'suits-blazers', 'Formal suits and blazers'),
    ('Casual Shirts', 'casual-shirts', 'Casual shirts for everyday wear'),
    ('Polo Shirt', 'polo-shirt', 'Polo shirts for casual and semi-formal occasions'),
    ('Outerwear & Jackets', 'outerwear-jackets', 'Jackets and outerwear for layering'),
    ('Activewear & Fitness Tops', 'activewear-fitness-tops', 'Breathable tops for sports and fitness'),


    ('Pants', 'pants', 'Trousers and dress pants'),
    ('Shorts', 'shorts', 'Casual and formal shorts'),
    ('Activewear & Fitness Bottoms', 'activewear-fitness-bottoms', 'Shorts and bottoms for sports and fitness'),


    ('Footwear', 'footwear', 'All types of mens shoes and footwear'),


    ('Accessories', 'accessories', 'Belts, wallets, hats, bags, watches, eyewear, and more'),


    ('Grooming Products', 'grooming-products', 'Skincare, haircare, fragrances, and grooming essentials'),
]

def update_categories():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()


        cursor.execute("SELECT id, slug FROM categories")
        existing_categories = {row[1]: row[0] for row in cursor.fetchall()}

        print("=" * 70)
        print("UPDATING PRODUCT CATEGORIES")
        print("=" * 70)

        added = 0
        updated = 0
        deleted = 0


        for name, slug, description in CATEGORIES:
            if slug in existing_categories:

                cursor.execute(
                    "UPDATE categories SET name = %s, description = %s, is_active = 1 WHERE slug = %s",
                    (name, description, slug)
                )
                conn.commit()
                print(f"✓ Updated: {name}")
                updated += 1
            else:

                cursor.execute(
                    "INSERT INTO categories (name, slug, description, is_active) VALUES (%s, %s, %s, %s)",
                    (name, slug, description, 1)
                )
                conn.commit()
                print(f"✓ Added: {name}")
                added += 1


        slugs_to_keep = {cat[1] for cat in CATEGORIES}
        for slug, category_id in existing_categories.items():
            if slug not in slugs_to_keep:

                cursor.execute("SELECT COUNT(*) FROM products WHERE category_id = %s", (category_id,))
                product_count = cursor.fetchone()[0]

                if product_count == 0:

                    cursor.execute("DELETE FROM categories WHERE id = %s", (category_id,))
                    conn.commit()
                    print(f"✓ Deleted: {slug}")
                    deleted += 1
                else:

                    cursor.execute(
                        "UPDATE categories SET is_active = 0 WHERE id = %s",
                        (category_id,)
                    )
                    conn.commit()
                    print(f"⚠ Deactivated (has {product_count} products): {slug}")

        cursor.close()
        conn.close()

        print("\n" + "=" * 70)
        print(f"SUMMARY: {added} added, {updated} updated, {deleted} deleted")
        print("=" * 70)


        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, slug, is_active FROM categories WHERE is_active = 1 ORDER BY id")

        print("\nFINAL ACTIVE CATEGORIES:")
        print("-" * 70)
        for cat_id, cat_name, cat_slug, is_active in cursor.fetchall():
            print(f"  {cat_id:3d} | {cat_name:35} | {cat_slug}")

        cursor.close()
        conn.close()

        print("-" * 70)
        return True

    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print()
    update_categories()
