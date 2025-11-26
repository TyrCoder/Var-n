#!/usr/bin/env python3
"""
Script to update categories with grouping type information
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

# Categories organized by type
CATEGORIES_BY_TYPE = {
    'TOPS': [
        ('Barong', 'barong'),
        ('Suits & Blazers', 'suits-blazers'),
        ('Casual Shirts', 'casual-shirts'),
        ('Polo Shirt', 'polo-shirt'),
        ('Outerwear & Jackets', 'outerwear-jackets'),
        ('Activewear & Fitness Tops', 'activewear-fitness-tops'),
    ],
    'BOTTOMS': [
        ('Pants', 'pants'),
        ('Shorts', 'shorts'),
        ('Activewear & Fitness Bottoms', 'activewear-fitness-bottoms'),
    ],
    'FOOTWEAR': [
        ('Footwear', 'footwear'),
    ],
    'ACCESSORIES': [
        ('Accessories', 'accessories'),
    ],
    'GROOMING PRODUCTS': [
        ('Grooming Products', 'grooming-products'),
    ],
}

def add_type_column():
    """Add category_type column if it doesn't exist"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("""
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME='categories' AND COLUMN_NAME='category_type'
        """)
        
        if not cursor.fetchone():
            # Add column
            cursor.execute("""
                ALTER TABLE categories ADD COLUMN category_type VARCHAR(50) DEFAULT 'OTHER'
            """)
            conn.commit()
            print("✓ Added category_type column to categories table")
        else:
            print("✓ category_type column already exists")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Error adding column: {str(e)}")
        return False

def update_categories_with_types():
    """Update categories with their type groupings"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("\n" + "=" * 70)
        print("UPDATING CATEGORIES WITH TYPE GROUPINGS")
        print("=" * 70)
        
        total_updated = 0
        
        for category_type, categories in CATEGORIES_BY_TYPE.items():
            for name, slug in categories:
                cursor.execute(
                    "UPDATE categories SET category_type = %s WHERE slug = %s",
                    (category_type, slug)
                )
                conn.commit()
                total_updated += 1
                print(f"✓ {category_type:25} | {name}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 70)
        print(f"TOTAL UPDATED: {total_updated} categories")
        print("=" * 70)
        
        # Display final result
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT category_type, name, slug 
            FROM categories 
            WHERE is_active = 1 
            ORDER BY 
                CASE 
                    WHEN category_type = 'TOPS' THEN 1
                    WHEN category_type = 'BOTTOMS' THEN 2
                    WHEN category_type = 'FOOTWEAR' THEN 3
                    WHEN category_type = 'ACCESSORIES' THEN 4
                    WHEN category_type = 'GROOMING PRODUCTS' THEN 5
                    ELSE 6
                END,
                name
        """)
        
        print("\nFINAL CATEGORY STRUCTURE:")
        print("-" * 70)
        current_type = None
        for cat_type, cat_name, cat_slug in cursor.fetchall():
            if cat_type != current_type:
                print(f"\n{cat_type}:")
                current_type = cat_type
            print(f"  • {cat_name}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"✗ Error updating categories: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print()
    if add_type_column():
        update_categories_with_types()
