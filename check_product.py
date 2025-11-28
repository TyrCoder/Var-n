import mysql.connector
import traceback

try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='varon'
    )
    
    cursor = conn.cursor(dictionary=True)
    
    # Check total products
    cursor.execute('SELECT COUNT(*) as count FROM products')
    result = cursor.fetchone()
    print(f"Total products: {result['count']}")
    
    # List all products
    cursor.execute('SELECT id, name, seller_id FROM products')
    all_products = cursor.fetchall()
    print("\nAll products:")
    for p in all_products:
        print(f"  ID: {p['id']}, Name: {p['name']}, Seller: {p['seller_id']}")
    
    # Find the ASAP product specifically
    cursor.execute('SELECT id, name, seller_id FROM products WHERE name LIKE "%ASAP%" OR name LIKE "%Tec%"')
    asap_products = cursor.fetchall()
    if asap_products:
        print("\nASAP/Tec products found:")
        for p in asap_products:
            print(f"  ID: {p['id']}, Name: {p['name']}")
            
            # Check variants
            cursor.execute('SELECT * FROM product_variants WHERE product_id = %s', (p['id'],))
            variants = cursor.fetchall()
            print(f"    Variants: {len(variants)}")
            if variants:
                for v in variants:
                    print(f"      - Size: {v['size']}, Color: {v['color']}, Stock: {v['stock_quantity']}")
    else:
        print("\nNo ASAP/Tec product found")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
