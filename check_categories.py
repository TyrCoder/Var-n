import mysql.connector

# Connect to database
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='varon'
)
cursor = conn.cursor()

# Fetch all categories
cursor.execute("SELECT id, name, slug, is_active FROM categories ORDER BY name")
categories = cursor.fetchall()

print("\nCategories in database:")
print("-" * 80)
print(f"{'ID':<5} {'Name':<30} {'Slug':<30} {'Active':<10}")
print("-" * 80)

for cat in categories:
    print(f"{cat[0]:<5} {cat[1]:<30} {cat[2]:<30} {'Yes' if cat[3] else 'No':<10}")

print(f"\nTotal categories: {len(categories)}")
print("-" * 80)

cursor.close()
conn.close()
