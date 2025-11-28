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
    
    print("🔧 Adding seller_confirmed columns to shipments table...")
    
    # Add seller_confirmed column
    try:
        cursor.execute('''
            ALTER TABLE shipments 
            ADD COLUMN seller_confirmed BOOLEAN DEFAULT FALSE AFTER status
        ''')
        print("✅ Added seller_confirmed column")
    except mysql.connector.Error as e:
        if e.errno == 1060:  # Duplicate column name
            print("⚠️  seller_confirmed column already exists")
        else:
            print(f"❌ Error adding seller_confirmed: {e}")
    
    # Add seller_confirmed_at column
    try:
        cursor.execute('''
            ALTER TABLE shipments 
            ADD COLUMN seller_confirmed_at TIMESTAMP NULL AFTER seller_confirmed
        ''')
        print("✅ Added seller_confirmed_at column")
    except mysql.connector.Error as e:
        if e.errno == 1060:  # Duplicate column name
            print("⚠️  seller_confirmed_at column already exists")
        else:
            print(f"❌ Error adding seller_confirmed_at: {e}")
    
    conn.commit()
    
    # Show current table structure
    print("\n📋 Current shipments table structure:")
    cursor.execute("DESCRIBE shipments")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
    cursor.close()
    conn.close()
    
    print("\n✅ Migration completed successfully!")

except mysql.connector.Error as e:
    print(f"❌ Database error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
