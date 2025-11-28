import mysql.connector
from mysql.connector import Error

try:

    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='varon'
    )

    cursor = conn.cursor(dictionary=True)

    print("=" * 70)
    print("TESTING FIXED QUERY - GET AVAILABLE RIDERS")
    print("=" * 70)


    cursor.execute('''
        SELECT r.id,
               u.first_name, u.last_name,
               r.vehicle_type, r.service_area,
               r.is_available, r.status, r.created_at,
               COUNT(DISTINCT s.id) as total_deliveries,
               COALESCE(r.rating, 0) as rating
        FROM riders r
        JOIN users u ON r.user_id = u.id
        LEFT JOIN shipments s ON r.id = s.rider_id AND s.status = 'delivered'
        WHERE r.is_available = TRUE
          AND r.status IN ('active', 'approved')
        GROUP BY r.id
        ORDER BY COALESCE(r.rating, 0) DESC, r.created_at ASC
        LIMIT 50
    ''')

    riders = cursor.fetchall()

    print(f"\n✅ Query executed successfully!")
    print(f"📊 Retrieved {len(riders)} available riders\n")

    if len(riders) == 0:
        print("❌ PROBLEM: Still no riders found!")
    else:
        print("✅ SUCCESS: Riders found!\n")
        print("-" * 70)

        for idx, rider in enumerate(riders, 1):
            print(f"\nRider #{idx}:")
            print(f"  ID: {rider['id']}")
            print(f"  Name: {rider['first_name']} {rider['last_name']}")
            print(f"  Vehicle: {rider['vehicle_type'] or 'Not specified'}")
            print(f"  Service Area: {rider['service_area'] or 'All areas'}")
            print(f"  Rating: {'⭐' if rider['rating'] > 0 else '📍'} {rider['rating']}")
            print(f"  Deliveries: {rider['total_deliveries']}")
            print(f"  Status: {rider['status']}")
            print(f"  Available: {'✅ Yes' if rider['is_available'] else '❌ No'}")

    print("\n" + "=" * 70)

    cursor.close()
    conn.close()

except Error as e:
    print(f'❌ Database error: {e}')
    import traceback
    traceback.print_exc()
