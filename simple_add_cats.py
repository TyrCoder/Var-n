import mysql.connector

try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='varon'
    )
    
    cursor = conn.cursor()
    
    sql = """
    INSERT INTO categories (name, slug, description, is_active) VALUES
    ('Grooming Products', 'grooming-products', 'Personal grooming and care products', TRUE),
    ('Activewear & Fitness', 'activewear-fitness', 'Athletic wear and fitness apparel', TRUE),
    ('Shoes & Accessories', 'shoes-accessories', 'Footwear and fashion accessories', TRUE),
    ('Outerwear & Jackets', 'outerwear-jackets', 'Jackets, coats, and outer layers', TRUE),
    ('Casual Shirts & Pants', 'casual-shirts-pants', 'Casual everyday clothing', TRUE),
    ('Suits & Blazers', 'suits-blazers', 'Formal wear and blazers', TRUE)
    ON DUPLICATE KEY UPDATE description = VALUES(description), is_active = TRUE
    """
    
    cursor.execute(sql)
    conn.commit()
    
    print("✅ Categories added successfully!")
    
    cursor.execute("SELECT id, name, slug FROM categories ORDER BY name")
    categories = cursor.fetchall()
    
    print(f"\n📊 Total categories: {len(categories)}")
    for cat_id, name, slug in categories:
        print(f"  ID: {cat_id} | Name: {name} | Slug: {slug}")
    
    cursor.close()
    conn.close()
    
except mysql.connector.Error as err:
    if err.errno == 2003:
        print("❌ Cannot connect to MySQL. Is it running?")
    else:
        print(f"❌ MySQL Error: {err}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
