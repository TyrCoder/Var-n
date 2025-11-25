from app import get_db
import json

conn = get_db()
cursor = conn.cursor(dictionary=True)

try:
    # Get a seller and their order
    cursor.execute("""
        SELECT o.id, o.order_number, s.id as shipment_id, s.status as shipment_status
        FROM orders o
        LEFT JOIN shipments s ON o.id = s.order_id
        WHERE o.order_status = 'released_to_rider'
        LIMIT 1
    """)
    
    order = cursor.fetchone()
    
    if order:
        print(f"✅ Found order: {order['order_number']}")
        print(f"   Shipment ID: {order['shipment_id']}")
        print(f"   Current Shipment Status: {order['shipment_status']}")
        print(f"\nNow checking if this order will show in rider's active deliveries...")
        
        # Check what the active deliveries query would return
        if order['shipment_id']:
            cursor.execute("""
                SELECT id, status FROM shipments
                WHERE id = %s AND status IN ('pending', 'picked_up', 'in_transit', 'out_for_delivery')
            """, (order['shipment_id'],))
            
            shipment = cursor.fetchone()
            if shipment:
                print(f"✅ Shipment {shipment['id']} IS eligible for active deliveries (status: {shipment['status']})")
            else:
                print(f"❌ Shipment status '{order['shipment_status']}' is NOT in active delivery statuses")
                print(f"   Active statuses: pending, picked_up, in_transit, out_for_delivery")
    else:
        print("No released orders found")
        
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    cursor.close()
    conn.close()
