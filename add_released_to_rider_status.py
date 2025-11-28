import mysql.connector

print("🔧 Adding 'released_to_rider' to order_status ENUM...")

try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='varon'
    )
    
    cursor = conn.cursor()
    
    # Update the ENUM to include released_to_rider
    cursor.execute("""
        ALTER TABLE orders 
        MODIFY COLUMN order_status ENUM(
            'pending', 
            'confirmed', 
            'waiting_for_pickup', 
            'processing', 
            'shipped', 
            'released_to_rider',
            'delivered', 
            'cancelled', 
            'returned'
        ) DEFAULT 'pending'
    """)
    
    conn.commit()
    print("✅ Successfully added 'released_to_rider' to order_status ENUM")
    
    # Verify the change
    cursor.execute("SHOW COLUMNS FROM orders LIKE 'order_status'")
    result = cursor.fetchone()
    
    print("\n📋 Current order_status column definition:")
    print(f"  Field: {result[0]}")
    print(f"  Type: {result[1]}")
    print(f"  Null: {result[2]}")
    print(f"  Default: {result[4]}")
    
    cursor.close()
    conn.close()
    
    print("\n✅ Migration completed successfully!")
    
except mysql.connector.Error as err:
    print(f"❌ Error: {err}")
    if conn:
        conn.close()
