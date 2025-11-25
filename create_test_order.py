from app import get_db
from datetime import datetime

conn = get_db()
cursor = conn.cursor(dictionary=True)

try:
    # Get a test seller and user
    cursor.execute("""
        SELECT u.id as user_id, s.id as seller_id
        FROM users u
        JOIN sellers s ON s.user_id = u.id
        WHERE u.role = 'seller'
        LIMIT 1
    """)
    
    seller = cursor.fetchone()
    if not seller:
        print("❌ No seller found")
        exit(1)
    
    print(f"Using seller user_id={seller['user_id']}, seller_id={seller['seller_id']}")
    
    # Get a buyer/customer
    cursor.execute("""
        SELECT id FROM users WHERE role = 'buyer' LIMIT 1
    """)
    buyer = cursor.fetchone()
    
    if not buyer:
        print("❌ No buyer found")
        exit(1)
    
    # Get their address
    cursor.execute("""
        SELECT id FROM addresses WHERE user_id = %s LIMIT 1
    """, (buyer['id'],))
    
    address = cursor.fetchone()
    if not address:
        print("❌ No address found for buyer")
        exit(1)
    
    # Get a product from this seller
    cursor.execute("""
        SELECT id FROM products WHERE seller_id = %s LIMIT 1
    """, (seller['seller_id'],))
    
    product = cursor.fetchone()
    if not product:
        print("❌ No product found for seller")
        exit(1)
    
    # Create a test order in confirmed status
    order_number = f"TEST-{int(datetime.now().timestamp())}"
    
    cursor.execute("""
        INSERT INTO orders (
            order_number, user_id, seller_id, shipping_address_id, 
            subtotal, total_amount, order_status, payment_status, created_at
        ) VALUES (%s, %s, %s, %s, 1000, 1000, 'confirmed', 'paid', NOW())
    """, (order_number, buyer['id'], seller['seller_id'], address['id']))
    
    conn.commit()
    order_id = cursor.lastrowid
    
    # Add an order item
    cursor.execute("""
        INSERT INTO order_items (order_id, product_id, quantity, unit_price)
        VALUES (%s, %s, 1, 1000)
    """, (order_id, product['id']))
    
    conn.commit()
    
    print(f"✅ Created test order: {order_number} (ID: {order_id}) in 'confirmed' status")
    print(f"\n📦 Now simulating seller clicking 'Release to Rider' button...")
    print(f"   This will call /seller/update-order-status with new_status='released_to_rider'")
    print(f"\n✓ Expected behavior:")
    print(f"   1. Order status changes: confirmed → released_to_rider")
    print(f"   2. Shipment is created (if not exists)")
    print(f"   3. Rider is assigned from service area")
    print(f"   4. Shipment status set to 'pending'")
    print(f"   5. Order appears in rider's Active Deliveries")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    cursor.close()
    conn.close()
