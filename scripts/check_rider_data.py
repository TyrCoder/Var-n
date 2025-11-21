import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'varon')
}

try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    
    print("=" * 60)
    print("RIDER DATA CHECK")
    print("=" * 60)
    
    # Get all riders with their service areas
    cursor.execute('''
        SELECT r.id, r.user_id, r.service_area, r.vehicle_type, 
               u.first_name, u.last_name, u.email
        FROM riders r
        JOIN users u ON r.user_id = u.id
    ''')
    riders = cursor.fetchall()
    
    if riders:
        for rider in riders:
            print(f"\nRider ID: {rider['id']}")
            print(f"Name: {rider['first_name']} {rider['last_name']}")
            print(f"Email: {rider['email']}")
            print(f"Service Area: '{rider['service_area']}'")
            print(f"Vehicle Type: {rider['vehicle_type']}")
            print("-" * 60)
    else:
        print("\nNo riders found in database!")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
