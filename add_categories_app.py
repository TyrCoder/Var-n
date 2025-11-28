#!/usr/bin/env python
"""Quick script to add categories to the database"""

import sys
import os
from pathlib import Path

# Change to app directory
os.chdir(Path(__file__).parent)

# Now import from app
from app import app, get_db
from flask import jsonify

# Create app context
with app.app_context():
    print("🔄 Connecting to database...")
    conn = get_db()
    
    if not conn:
        print("❌ Failed to connect!")
        sys.exit(1)
    
    print("✅ Connected!")
    
    cursor = conn.cursor()
    
    # Add category_type column if missing
    try:
        cursor.execute("""
            ALTER TABLE categories 
            ADD COLUMN category_type VARCHAR(100) DEFAULT NULL
        """)
        conn.commit()
        print("✅ Column category_type added")
    except:
        print("⚠️ Column category_type already exists")
    
    # Insert categories
    sql = """
    INSERT INTO categories (name, slug, description, category_type, is_active) VALUES
    (%s, %s, %s, %s, TRUE),
    (%s, %s, %s, %s, TRUE),
    (%s, %s, %s, %s, TRUE),
    (%s, %s, %s, %s, TRUE),
    (%s, %s, %s, %s, TRUE),
    (%s, %s, %s, %s, TRUE)
    ON DUPLICATE KEY UPDATE description = VALUES(description), is_active = TRUE
    """
    
    data = (
        'Grooming Products', 'grooming-products', 'Personal grooming and care products', 'GROOMING PRODUCTS',
        'Activewear & Fitness', 'activewear-fitness', 'Athletic wear and fitness apparel', 'TOPS',
        'Shoes & Accessories', 'shoes-accessories', 'Footwear and fashion accessories', 'FOOTWEAR',
        'Outerwear & Jackets', 'outerwear-jackets', 'Jackets, coats, and outer layers', 'TOPS',
        'Casual Shirts & Pants', 'casual-shirts-pants', 'Casual everyday clothing', 'TOPS',
        'Suits & Blazers', 'suits-blazers', 'Formal wear and blazers', 'TOPS'
    )
    
    try:
        cursor.execute(sql, data)
        conn.commit()
        print("✅ Categories inserted!")
    except Exception as e:
        print(f"❌ Insert failed: {e}")
        conn.close()
        sys.exit(1)
    
    # Show all categories
    cursor.execute("SELECT id, name, slug, category_type FROM categories ORDER BY name")
    categories = cursor.fetchall()
    
    print(f"\n📊 Total categories: {len(categories)}")
    for cat_id, name, slug, cat_type in categories:
        print(f"  ID: {cat_id:2d} | Name: {name:30s} | Type: {cat_type if cat_type else 'N/A'}")
    
    cursor.close()
    conn.close()
    
    print("\n✅ Done!")
