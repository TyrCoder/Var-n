"""
Setup Men's Apparel Categories with Subcategories
This script creates a comprehensive men's apparel category structure with parent-child relationships
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

# Define the category structure with parent-child relationships
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
        'Shoes'
    ],
    'ACCESSORIES': [
        'Belts',
        'Wallets',
        'Hats',
        'Bags',
        'Watches',
        'Eyewear'
    ],
    'GROOMING PRODUCTS': [
        'Skincare',
        'Haircare',
        'Fragrances'
    ]
}

def get_slug(text):
    """Convert text to URL-friendly slug"""
    return text.lower().replace(' ', '-').replace('&', 'and').replace(',', '')

def clear_categories():
    """Clear existing categories from database"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("🗑️  Clearing existing categories...")
        cursor.execute("DELETE FROM categories")
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Database cleared")
        return True
    except mysql.connector.Error as err:
        print(f"❌ Database Error: {err}")
        return False

def setup_categories():
    """Create the men's apparel category structure with subcategories"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("\n🔄 Setting up Men's Apparel Categories with Subcategories...")
        print("=" * 70)
        
        # First clear the database
        cursor.execute("DELETE FROM categories")
        
        # Reset auto-increment
        cursor.execute("ALTER TABLE categories AUTO_INCREMENT = 1")
        
        parent_categories = {}
        
        # Create parent categories and subcategories
        for main_category, subcategories in MENS_CATEGORIES.items():
            print(f"\n📂 {main_category}")
            
            # Insert parent category
            parent_slug = get_slug(main_category)
            query = """
            INSERT INTO categories (name, slug, description, parent_id, is_active)
            VALUES (%s, %s, %s, NULL, 1)
            """
            
            cursor.execute(query, (main_category, parent_slug, f"Men's {main_category.lower()}"))
            parent_id = cursor.lastrowid
            parent_categories[main_category] = parent_id
            
            print(f"   └─ Parent Category ID: {parent_id}")
            
            # Insert subcategories
            for subcat_name in subcategories:
                subcat_slug = get_slug(subcat_name)
                
                subcat_query = """
                INSERT INTO categories (name, slug, description, parent_id, is_active)
                VALUES (%s, %s, %s, %s, 1)
                """
                
                cursor.execute(subcat_query, (
                    subcat_name, 
                    subcat_slug, 
                    f"{main_category} - {subcat_name}",
                    parent_id
                ))
                
                print(f"      ├─ ✓ {subcat_name}")
        
        conn.commit()
        
        print("\n" + "=" * 70)
        print("✅ Men's Apparel Categories Setup Complete!\n")
        
        # Display created categories in hierarchical format
        cursor.execute("""
            SELECT id, name, parent_id 
            FROM categories 
            ORDER BY parent_id ASC, id ASC
        """)
        
        categories = cursor.fetchall()
        
        print(f"📊 Total Categories: {len(categories)}")
        print("-" * 70)
        print("\n📋 CATEGORY STRUCTURE:\n")
        
        current_parent = None
        parent_name_map = {}
        
        # First pass - get parent names
        for cat_id, cat_name, parent_id in categories:
            if parent_id is None:
                parent_name_map[cat_id] = cat_name
        
        # Second pass - display hierarchically
        for cat_id, cat_name, parent_id in categories:
            if parent_id is None:
                # Parent category
                print(f"📁 {cat_name} (ID: {cat_id})")
            else:
                # Subcategory
                print(f"   └─ {cat_name} (ID: {cat_id})")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 70)
        print("✨ Setup completed successfully!\n")
        
    except mysql.connector.Error as err:
        print(f"❌ Database Error: {err}")
        return False
    except Exception as err:
        print(f"❌ Error: {err}")
        return False
    
    return True

if __name__ == "__main__":
    print("\n🎯 Men's Apparel Category Setup\n")
    
    # Clear existing categories
    if clear_categories():
        # Setup new structure
        success = setup_categories()
        exit(0 if success else 1)
    else:
        exit(1)
