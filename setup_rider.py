import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='varon'
)

cursor = conn.cursor(dictionary=True)

# Check if user exists
cursor.execute("SELECT id, email, role FROM users WHERE email = 'sedocoder7@gmail.com'")
user = cursor.fetchone()

if user:
    print(f"User exists: {user}")
    
    # Check if rider profile exists
    cursor.execute("SELECT * FROM riders WHERE user_id = %s", (user['id'],))
    rider = cursor.fetchone()
    
    if not rider:
        print("Creating rider profile...")
        cursor.execute("""
            INSERT INTO riders (user_id, vehicle_type, service_area, is_available, status)
            VALUES (%s, 'motorcycle', 'South Luzon', TRUE, 'approved')
        """, (user['id'],))
        conn.commit()
        print("Rider profile created!")
    else:
        print(f"Rider profile exists: {rider}")
else:
    print("User not found")

cursor.close()
conn.close()
