#!/usr/bin/env python3
"""
Direct login test - simulates what happens when you submit the login form
"""
import mysql.connector
import requests
from dotenv import load_dotenv
import os

load_dotenv()

# Test credentials - use a known user from the database
test_users = [
    {"email": "admin@varon.com", "password": "admin123"},
    {"email": "MNL@gmail.com", "password": "kirito12"},
    {"email": "tbalbieranvi@gmail.com", "password": "kirito12"},
    {"email": "razeel@gmail.com", "password": "razeel123"},
    {"email": "ashleymay.martinez@lspu.edu.ph", "password": "A"},
]

print("=" * 60)
print("DIRECT LOGIN TEST")
print("=" * 60)

# Test 1: Direct database verification
print("\n1️⃣ VERIFYING DATABASE CREDENTIALS:")
print("-" * 60)

try:
    conn = mysql.connector.connect(
        host=os.getenv('MYSQL_HOST'),
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        database=os.getenv('MYSQL_DB')
    )
    cursor = conn.cursor(dictionary=True)
    
    for test_user in test_users:
        cursor.execute('SELECT id, email, password, role FROM users WHERE email = %s', (test_user['email'],))
        user = cursor.fetchone()
        
        if user:
            db_password = user['password']
            input_password = test_user['password']
            match = "✅ MATCH" if db_password == input_password else "❌ NO MATCH"
            print(f"  Email: {user['email']}")
            print(f"    DB Password: {db_password}")
            print(f"    Input Password: {input_password}")
            print(f"    Result: {match}")
            print()
        else:
            print(f"  ❌ User not found: {test_user['email']}\n")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"❌ Database error: {e}")

# Test 2: Flask login endpoint test
print("\n2️⃣ TESTING FLASK LOGIN ENDPOINT:")
print("-" * 60)

base_url = "http://127.0.0.1:5000"

# Create a session to maintain cookies
session = requests.Session()

try:
    # Try each test user
    for test_user in test_users:
        print(f"\n  Testing: {test_user['email']}")
        
        response = session.post(
            f"{base_url}/login",
            data={
                'email': test_user['email'],
                'password': test_user['password']
            },
            allow_redirects=False
        )
        
        print(f"    Status Code: {response.status_code}")
        
        if response.status_code == 302:
            print(f"    ✅ Redirect: {response.headers.get('Location', 'N/A')}")
            print(f"    Session cookies: {list(session.cookies.keys())}")
        elif response.status_code == 200:
            # Check if there's a flash message in the response
            if 'Invalid email or password' in response.text:
                print(f"    ❌ Error: Invalid email or password")
            elif 'flash' in response.text:
                print(f"    ⚠️ Response contains flash messages")
            else:
                print(f"    ⚠️ Got 200 response (no redirect)")
        else:
            print(f"    ⚠️ Unexpected status code")

except requests.exceptions.ConnectionError:
    print(f"  ❌ Cannot connect to Flask server at {base_url}")
    print(f"     Is Flask running? Try: python app.py")
except Exception as e:
    print(f"  ❌ Error: {e}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
