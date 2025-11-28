import mysql.connector

try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='varon'
    )
    
    cursor = conn.cursor()
    
    # First, try to add the category_type column if it doesn't exist
    alter_sql = """
    ALTER TABLE categories 
    ADD COLUMN IF NOT EXISTS category_type VARCHAR(100) DEFAULT NULL
    """
    
    try:
        cursor.execute(alter_sql)
        conn.commit()
        print("✅ Added category_type column (or already exists)")
    except Exception as e:
        print(f"⚠️ Column update: {e}")
    
    # Now insert the categories
    insert_sql = """
    INSERT INTO categories (name, slug, description, category_type, is_active) VALUES
    ('Grooming Products', 'grooming-products', 'Personal grooming and care products', 'GROOMING PRODUCTS', TRUE),
    ('Activewear & Fitness', 'activewear-fitness', 'Athletic wear and fitness apparel', 'TOPS', TRUE),
    ('Shoes & Accessories', 'shoes-accessories', 'Footwear and fashion accessories', 'FOOTWEAR', TRUE),
    ('Outerwear & Jackets', 'outerwear-jackets', 'Jackets, coats, and outer layers', 'TOPS', TRUE),
    ('Casual Shirts & Pants', 'casual-shirts-pants', 'Casual everyday clothing', 'TOPS', TRUE),
    ('Suits & Blazers', 'suits-blazers', 'Formal wear and blazers', 'TOPS', TRUE)
    ON DUPLICATE KEY UPDATE description = VALUES(description), is_active = TRUE
    """
    
    cursor.execute(insert_sql)
    conn.commit()
    
    print("✅ Categories added/updated successfully!")
    
    cursor.execute("SELECT id, name, slug, category_type FROM categories ORDER BY name")
    categories = cursor.fetchall()
    
    print(f"\n📊 Total categories: {len(categories)}")
    for cat_id, name, slug, cat_type in categories:
        print(f"  ID: {cat_id:2d} | {name:30s} | Type: {cat_type}")
    
    cursor.close()
    conn.close()
    
except mysql.connector.Error as err:
    if err.errno == 2003:
        print("❌ Cannot connect to MySQL. Is it running? Make sure MySQL is started.")
        print("   Start MySQL manually or try: net start MySQL80")
    else:
        print(f"❌ MySQL Error ({err.errno}): {err.msg}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
