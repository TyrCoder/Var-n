#!/usr/bin/env python
"""Add categories to the database using Flask context"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, get_db

def add_categories():
    """Add categories to database"""
    with app.app_context():
        conn = get_db()
        if not conn:
            print("❌ Failed to connect to database")
            return
        
        cursor = conn.cursor(dictionary=True)
        
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
                print(f"✅ Added/Updated category: {name}")
                inserted += 1
            except Exception as e:
                print(f"⚠️ Error adding {name}: {e}")
        
        # Verify
        cursor.execute("SELECT id, name, slug FROM categories ORDER BY name")
        all_cats = cursor.fetchall()
        
        print(f"\n📊 Total categories: {len(all_cats)}")
        for cat in all_cats:
            print(f"  - {cat['name']} ({cat['slug']})")
        
        cursor.close()
        conn.close()
        print(f"\n✅ Added {inserted} categories!")

if __name__ == '__main__':
    add_categories()
