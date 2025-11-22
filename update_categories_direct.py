import mysql.connector

# Connect to database
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='varon'
)
cursor = conn.cursor()

print("Updating categories...")
print("-" * 80)

# Disable foreign key checks
cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
print("✓ Foreign key checks disabled")

# Clear existing categories
cursor.execute("TRUNCATE TABLE categories")
print("✓ Existing categories cleared")

# Re-enable foreign key checks
cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
print("✓ Foreign key checks re-enabled")

# Insert new categories
categories = [
    ('Suits & Blazers', 'suits-blazers', 'Formal suits, blazers, and professional attire', True),
    ('Shoes & Accessories', 'shoes-accessories', 'Footwear and fashion accessories', True),
    ('Outerwear & Jackets', 'outerwear-jackets', 'Jackets, coats, and outerwear', True),
    ('Grooming Products', 'grooming', 'Personal care and grooming items', True),
    ('Casual Shirts & Pants', 'casual-shirts-pants', 'Everyday casual wear', True),
    ('Activewear & Fitness', 'activewear-fitness', 'Athletic and fitness apparel', True)
]

insert_query = "INSERT INTO categories (name, slug, description, is_active) VALUES (%s, %s, %s, %s)"
cursor.executemany(insert_query, categories)
print(f"✓ {len(categories)} new categories inserted")

# Commit changes
conn.commit()

# Verify
cursor.execute("SELECT id, name, slug FROM categories ORDER BY name")
results = cursor.fetchall()

print("\nCategories in database:")
print("-" * 80)
print(f"{'ID':<5} {'Name':<30} {'Slug':<30}")
print("-" * 80)
for row in results:
    print(f"{row[0]:<5} {row[1]:<30} {row[2]:<30}")

print(f"\nTotal categories: {len(results)}")
print("-" * 80)

cursor.close()
conn.close()

print("\n✓ Migration completed successfully!\n")
