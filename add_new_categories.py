import mysql.connector
from mysql.connector import Error
import os
import sys

# Add parent directory to path to import from app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Database configuration
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'varon'),
    'autocommit': False
}

def add_categories():
    """Add new categories to the database"""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # Categories to add (excluding GROOMING, LOCAL, and PENSHOPPE)
        categories = [
            ('Grooming Products', 'grooming-products', 'Personal grooming and care products'),
            ('Activewear & Fitness', 'activewear-fitness', 'Athletic wear and fitness apparel'),
            ('Shoes & Accessories', 'shoes-accessories', 'Footwear and fashion accessories'),
            ('Outerwear & Jackets', 'outerwear-jackets', 'Jackets, coats, and outer layers'),
            ('Casual Shirts & Pants', 'casual-shirts-pants', 'Casual everyday clothing'),
            ('Suits & Blazers', 'suits-blazers', 'Formal wear and blazers'),
        ]
        
        inserted = 0
        for name, slug, description in categories:
            try:
                cursor.execute(
                    """
                    INSERT INTO categories (name, slug, description, is_active)
                    VALUES (%s, %s, %s, TRUE)
                    ON DUPLICATE KEY UPDATE
                    description = VALUES(description),
                    is_active = TRUE
                    """,
                    (name, slug, description)
                )
                conn.commit()
                print(f"✅ Added/Updated category: {name}")
                inserted += 1
            except Error as e:
                print(f"⚠️ Error adding {name}: {e}")
                conn.rollback()
        
        # Verify categories were added
        cursor.execute("SELECT id, name, slug FROM categories ORDER BY name")
        all_categories = cursor.fetchall()
        
        print(f"\n📊 Total categories in database: {len(all_categories)}")
        print("Categories:")
        for cat_id, name, slug in all_categories:
            print(f"  - ID: {cat_id}, Name: {name}, Slug: {slug}")
        
        cursor.close()
        conn.close()
        
        print(f"\n✅ Successfully added {inserted} new categories!")
        
    except Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    add_categories()
