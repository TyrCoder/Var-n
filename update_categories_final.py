#!/usr/bin/env python3
"""
Script to update product categories to the final polished structure
"""
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'varon')
}

# Final categories structure
CATEGORIES = [
    # TOPS
    ('Barong', 'barong', 'A traditional Filipino formal shirt'),
    ('Suits & Blazers', 'suits-blazers', 'Formal suits and blazers'),
    ('Casual Shirts', 'casual-shirts', 'Casual shirts for everyday wear'),
    ('Polo Shirt', 'polo-shirt', 'Polo shirts for casual and semi-formal occasions'),
    ('Outerwear & Jackets', 'outerwear-jackets', 'Jackets and outerwear for layering'),
    ('Activewear & Fitness Tops', 'activewear-fitness-tops', 'Breathable tops for sports and fitness'),
    
    # BOTTOMS
    ('Pants', 'pants', 'Trousers and dress pants'),
    ('Shorts', 'shorts', 'Casual and formal shorts'),
    ('Activewear & Fitness Bottoms', 'activewear-fitness-bottoms', 'Shorts and bottoms for sports and fitness'),
    
    # FOOTWEAR
    ('Footwear', 'footwear', 'All types of mens shoes and footwear'),
    
    # ACCESSORIES
    ('Accessories', 'accessories', 'Belts, wallets, hats, bags, watches, eyewear, and more'),
    
    # GROOMING PRODUCTS
    ('Grooming Products', 'grooming-products', 'Skincare, haircare, fragrances, and grooming essentials'),
]

def update_categories():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # First, get all existing categories
        cursor.execute("SELECT id, slug FROM categories")
        existing_categories = {row[1]: row[0] for row in cursor.fetchall()}
        
        print("=" * 70)
        print("UPDATING PRODUCT CATEGORIES")
        print("=" * 70)
        
        added = 0
        updated = 0
        deleted = 0
        
        # Process each category
        for name, slug, description in CATEGORIES:
            if slug in existing_categories:
                # Update existing category
                cursor.execute(
                    "UPDATE categories SET name = %s, description = %s, is_active = 1 WHERE slug = %s",
                    (name, description, slug)
                )
                conn.commit()
                print(f"✓ Updated: {name}")
                updated += 1
            else:
                # Insert new category
                cursor.execute(
                    "INSERT INTO categories (name, slug, description, is_active) VALUES (%s, %s, %s, %s)",
                    (name, slug, description, 1)
                )
                conn.commit()
                print(f"✓ Added: {name}")
                added += 1
        
        # Delete categories that are not in the new list
        slugs_to_keep = {cat[1] for cat in CATEGORIES}
        for slug, category_id in existing_categories.items():
            if slug not in slugs_to_keep:
                # Check if any products use this category
                cursor.execute("SELECT COUNT(*) FROM products WHERE category_id = %s", (category_id,))
                product_count = cursor.fetchone()[0]
                
                if product_count == 0:
                    # Safe to delete
                    cursor.execute("DELETE FROM categories WHERE id = %s", (category_id,))
                    conn.commit()
                    print(f"✓ Deleted: {slug}")
                    deleted += 1
                else:
                    # Cannot delete - has products
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
        
        # Display final categories
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
