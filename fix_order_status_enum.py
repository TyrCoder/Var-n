import mysql.connector

try:
    # Connect to database
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='varon'
    )
    cursor = conn.cursor()
    
    print("🔧 Updating order_status ENUM to include waiting_for_pickup...")
    
    # Update the order_status ENUM to include waiting_for_pickup
    cursor.execute('''
        ALTER TABLE orders 
        MODIFY COLUMN order_status ENUM(
            'pending', 
            'confirmed', 
            'waiting_for_pickup',
            'processing', 
            'shipped', 
            'delivered', 
            'cancelled', 
            'returned'
        ) DEFAULT 'pending'
    ''')
    
    conn.commit()
    
    print("✅ Successfully updated order_status ENUM")
    
    # Show current table structure
    print("\n📋 Current order_status column definition:")
    cursor.execute("SHOW COLUMNS FROM orders LIKE 'order_status'")
    for row in cursor.fetchall():
        print(f"  Field: {row[0]}")
        print(f"  Type: {row[1]}")
        print(f"  Null: {row[2]}")
        print(f"  Default: {row[4]}")
    
    cursor.close()
    conn.close()
    
    print("\n✅ Migration completed successfully!")

except mysql.connector.Error as e:
    print(f"❌ Database error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
