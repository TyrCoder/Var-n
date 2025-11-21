import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

# Connect to database
conn = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)

cursor = conn.cursor()

print("Creating flash sales tables...")

# Read and execute migration
with open('migrations/add_flash_sales.sql', 'r') as f:
    sql_commands = f.read().split(';')
    
    for command in sql_commands:
        command = command.strip()
        if command:
            try:
                cursor.execute(command)
                print(f"✓ Executed: {command[:50]}...")
            except mysql.connector.Error as err:
                print(f"⚠ Warning: {err}")
                # Continue anyway - table might already exist

conn.commit()
cursor.close()
conn.close()

print("\n✅ Flash sales migration completed!")
