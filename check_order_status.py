from app import get_db

conn = get_db()
cursor = conn.cursor(dictionary=True)

try:
    cursor.execute("""
        SELECT o.id, o.order_number, u.name, o.total_amount, o.order_status
        FROM orders o
        LEFT JOIN users u ON o.user_id = u.id
        ORDER BY o.created_at DESC
        LIMIT 10
    """)
    orders = cursor.fetchall()

    print("Current Orders:")
    print("-" * 80)
    for order in orders:
        print(f"ID: {order['id']:3} | Order: {order['order_number']:15} | Customer: {str(order['name'])[:20]:20} | Status: {order['order_status']:20} | Amount: ₱{order['total_amount']}")

except Exception as e:
    print(f"❌ Error: {e}")
finally:
    cursor.close()
    conn.close()
