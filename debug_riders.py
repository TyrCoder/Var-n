import mysql.connector
from mysql.connector import Error

try:
    # Connect to MySQL
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='varon'
    )
    
    cursor = conn.cursor(dictionary=True)
    
    # Check riders table structure
    print("=" * 60)
    print("RIDERS TABLE COLUMNS:")
    print("=" * 60)
    cursor.execute('DESCRIBE riders')
    columns = cursor.fetchall()
    for col in columns:
        print(f"  - {col['Field']}: {col['Type']}")
    
    # Check how many riders exist
    cursor.execute('SELECT COUNT(*) as count FROM riders')
    result = cursor.fetchone()
    print(f"\nTotal riders in database: {result['count']}")
    
    # Check available riders
    cursor.execute('SELECT COUNT(*) as count FROM riders WHERE is_available = TRUE')
    result = cursor.fetchone()
    print(f"Available riders (is_available=TRUE): {result['count']}")
    
    # Check status='active' riders
    cursor.execute('SELECT COUNT(*) as count FROM riders WHERE status = "active"')
    result = cursor.fetchone()
    print(f"Riders with status='active': {result['count']}")
    
    # List all riders with details
    print("\n" + "=" * 60)
    print("ALL RIDERS IN DATABASE:")
    print("=" * 60)
    cursor.execute('SELECT id, user_id, vehicle_type, is_available, status FROM riders')
    riders = cursor.fetchall()
    
    if len(riders) == 0:
        print("❌ NO RIDERS FOUND IN DATABASE!")
    else:
        for rider in riders:
            print(f"\nID: {rider['id']}")
            print(f"  User ID: {rider['user_id']}")
            print(f"  Vehicle: {rider['vehicle_type']}")
            print(f"  Available: {rider['is_available']}")
            print(f"  Status: {rider['status']}")
    
    # Check if there are users with role='rider'
    print("\n" + "=" * 60)
    print("USERS WITH ROLE='RIDER':")
    print("=" * 60)
    cursor.execute('SELECT id, first_name, last_name, email, role FROM users WHERE role = "rider"')
    users = cursor.fetchall()
    print(f"Total riders (user role): {len(users)}")
    for user in users:
        print(f"  - {user['first_name']} {user['last_name']} (ID: {user['id']}, Email: {user['email']})")
    
    # Check shipments status values
    print("\n" + "=" * 60)
    print("SHIPMENT STATUS VALUES:")
    print("=" * 60)
    cursor.execute('SELECT DISTINCT status FROM shipments')
    statuses = cursor.fetchall()
    for status in statuses:
        print(f"  - {status['status']}")
    
    cursor.close()
    conn.close()
    
except Error as e:
    print(f'Database error: {e}')
