"""
Setup Men's Apparel Categories
This script creates a comprehensive men's apparel category structure
"""

import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'varon')
}

# Define the category structure
MENS_CATEGORIES = {
    'TOPS': [
        'Barong',
        'Suits & Blazers',
        'Casual Shirts',
        'Polo Shirt',
        'Outerwear & Jackets',
        'Activewear & Fitness Tops'
    ],
    'BOTTOMS': [
        'Pants',
        'Shorts',
        'Activewear & Fitness Bottoms'
    ],
    'FOOTWEAR': [
        'Shoes'  # General category for all types of men's shoes
    ],
    'ACCESSORIES': [
        'Belts, Wallets, Hats, Bags, Watches, Eyewear'  # General category
    ],
    'GROOMING PRODUCTS': [
        'Skincare, Haircare, Fragrances'  # General category
    ]
}

def get_slug(text):
    """Convert text to URL-friendly slug"""
    return text.lower().replace(' ', '-').replace('&', 'and').replace(',', '')

def setup_categories():
    """Create the men's apparel category structure"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("🔄 Setting up Men's Apparel Categories...")
        print("=" * 60)
        
        # First, clear existing categories (optional - comment out to preserve)
        # cursor.execute("DELETE FROM categories")
        # print("✅ Cleared existing categories")
        
        category_id = 1
        
        for main_category, subcategories in MENS_CATEGORIES.items():
            print(f"\n📂 {main_category}")
            
            for subcat in subcategories:
                slug = get_slug(subcat)
                
                # Insert category
                query = """
                INSERT INTO categories (name, slug, description, is_active)
                VALUES (%s, %s, %s, 1)
                ON DUPLICATE KEY UPDATE name=name
                """
                
                cursor.execute(query, (subcat, slug, f"Men's {subcat.lower()}"))
                
                print(f"   ✓ {subcat}")
                category_id += 1
        
        conn.commit()
        print("\n" + "=" * 60)
        print("✅ Men's Apparel Categories Setup Complete!")
        print(f"📊 Total categories created")
        
        # Display created categories
        cursor.execute("SELECT id, name, slug FROM categories ORDER BY id")
        categories = cursor.fetchall()
        
        print(f"\n📋 Total Categories in Database: {len(categories)}")
        print("-" * 60)
        
        current_group = None
        for cat_id, cat_name, cat_slug in categories:
            print(f"  {cat_id:3d}. {cat_name:40s} ({cat_slug})")
        
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as err:
        print(f"❌ Database Error: {err}")
        return False
    except Exception as err:
        print(f"❌ Error: {err}")
        return False
    
    return True

if __name__ == "__main__":
    success = setup_categories()
    exit(0 if success else 1)
