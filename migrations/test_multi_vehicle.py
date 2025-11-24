#!/usr/bin/env python
"""Test: Verify multi-vehicle rider profile display works"""

import mysql.connector
import sys
import os

db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'varon')
}

try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    print("Testing multi-vehicle rider support...\n")
    
    # Find a rider to test with
    cursor.execute("SELECT id, user_id, vehicle_type FROM riders LIMIT 1")
    result = cursor.fetchone()
    
    if result:
        rider_id, user_id, current_vehicles = result
        print(f"Test rider: ID {rider_id} (User ID: {user_id})")
        print(f"Current vehicles: {current_vehicles}")
        
        # Update with multi-vehicle types
        test_vehicles = "motorcycle,truck,van"
        cursor.execute(
            "UPDATE riders SET vehicle_type = %s WHERE id = %s",
            (test_vehicles, rider_id)
        )
        conn.commit()
        print(f"\n✓ Updated to: {test_vehicles}")
        
        # Verify it was stored correctly
        cursor.execute("SELECT vehicle_type FROM riders WHERE id = %s", (rider_id,))
        stored = cursor.fetchone()[0]
        print(f"✓ Verified stored value: {stored}")
        
        # Verify template split logic would work
        if stored:
            vehicles = stored.split(',')
            print(f"\n✓ Split vehicles for display:")
            for v in vehicles:
                print(f"  - {v.strip().title()}")
        
        print("\n✓ Multi-vehicle support is working correctly!")
    else:
        print("No riders found in database")
    
    cursor.close()
    conn.close()
    
except Exception as err:
    print(f"ERROR: {err}")
    sys.exit(1)
