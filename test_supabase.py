#!/usr/bin/env python
"""Test Supabase PostgreSQL connection"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'port': int(os.getenv('DB_PORT', 5432))
}

print("Testing Supabase connection...")
print(f"Host: {db_config['host']}")
print(f"User: {db_config['user']}")
print(f"Database: {db_config['database']}")
print()

try:
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    
    # Test 1: Version
    cursor.execute("SELECT version()")
    version = cursor.fetchone()
    print("✓ Connected to PostgreSQL!")
    print(f"  Version: {version[0][:60]}...")
    print()
    
    # Test 2: List tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    tables = cursor.fetchall()
    print(f"✓ Found {len(tables)} tables:")
    for table in tables:
        print(f"  - {table[0]}")
    print()
    
    # Test 3: Check users table
    if tables:
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        print(f"✓ Users table has {count} records")
    
    cursor.close()
    conn.close()
    print("\n✓ All tests passed! Supabase is connected and has data.")
    
except psycopg2.Error as err:
    print(f"✗ Database error: {err}")
except Exception as err:
    print(f"✗ Error: {err}")
