import mysql.connector
import os

# Read the migration file
with open('migrations/update_categories.sql', 'r') as f:
    sql_content = f.read()

# Connect to database
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='varon'
)
cursor = conn.cursor()

# Split SQL statements and execute them
statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]

print("Running category migration...")
print("-" * 80)

for statement in statements:
    if statement.upper().startswith('USE'):
        cursor.execute(statement)
        print("✓ Database selected")
    elif 'FOREIGN_KEY_CHECKS' in statement.upper():
        cursor.execute(statement)
        if '= 0' in statement:
            print("✓ Foreign key checks disabled")
        else:
            print("✓ Foreign key checks re-enabled")
    elif statement.upper().startswith('TRUNCATE'):
        cursor.execute(statement)
        print("✓ Existing categories cleared")
    elif statement.upper().startswith('INSERT'):
        cursor.execute(statement)
        print("✓ New categories inserted")
    elif statement.upper().startswith('SELECT'):
        cursor.execute(statement)
        results = cursor.fetchall()
        print("\nCategories in database:")
        print("-" * 80)
        for row in results:
            print(f"ID: {row[0]}, Name: {row[1]}, Slug: {row[2]}")

conn.commit()
cursor.close()
conn.close()

print("\n✓ Migration completed successfully!\n")
