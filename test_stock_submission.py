"""
Test script to verify stocks are being saved correctly in add-product form
"""
import requests
import json
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'varon')
}

def query_db(sql, params=None):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, params or ())
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

def main():
    print("\n" + "="*60)
    print("STOCK SUBMISSION TEST")
    print("="*60)
    
    # Get a seller account
    sellers = query_db("SELECT * FROM sellers LIMIT 1")
    if not sellers:
        print("[ERROR] No sellers found in database")
        return
    
    seller = sellers[0]
    seller_id = seller['id']
    print(f"\n[OK] Using seller ID: {seller_id}")
    
    # Get a category
    categories = query_db("SELECT * FROM categories WHERE category_type = 'tops' LIMIT 1")
    if not categories:
        print("[ERROR] No tops categories found")
        return
    
    category = categories[0]
    category_id = category['id']
    print(f"[OK] Using category ID: {category_id} ({category['name']})")
    
    # Prepare product data with specific stock values
    product_data = {
        'category_id': str(category_id),
        'category_type': 'tops',
        'name': 'Test Product - Stock Verification',
        'description': 'This is a test product to verify stock saving',
        'brand': 'Test Brand',
        'price': '1500',
        'colors': json.dumps(['Red', 'Blue']),
        'sizes': json.dumps(['M', 'L']),
        'seller_id': str(seller_id),
        # Add specific stock values
        'stock_Red_M': '10',
        'stock_Red_L': '15',
        'stock_Blue_M': '20',
        'stock_Blue_L': '25',
    }
    
    print("\n[INFO] Product data to submit:")
    print(f"  Name: {product_data['name']}")
    print(f"  Stock mapping: Red-M=10, Red-L=15, Blue-M=20, Blue-L=25")
    
    # Create form data with files
    files = {
        'category_id': (None, product_data['category_id']),
        'category_type': (None, product_data['category_type']),
        'name': (None, product_data['name']),
        'description': (None, product_data['description']),
        'brand': (None, product_data['brand']),
        'price': (None, product_data['price']),
        'colors': (None, product_data['colors']),
        'sizes': (None, product_data['sizes']),
        'color_sizes_mapping': (None, json.dumps({'Red': ['M', 'L'], 'Blue': ['M', 'L']})),
        'stock_Red_M': (None, product_data['stock_Red_M']),
        'stock_Red_L': (None, product_data['stock_Red_L']),
        'stock_Blue_M': (None, product_data['stock_Blue_M']),
        'stock_Blue_L': (None, product_data['stock_Blue_L']),
    }
    
    # Add a dummy image file
    import io
    dummy_image = io.BytesIO(b'\x89PNG\r\n\x1a\n...')
    dummy_image.name = 'test.png'
    files['product_images'] = ('test.png', dummy_image, 'image/png')
    
    try:
        print("\n[INFO] Sending request to /seller/add-product...")
        response = requests.post('http://localhost:5000/seller/add-product', files=files)
        print(f"Response status: {response.status_code}")
        resp_json = response.json()
        print(f"Response: {resp_json}")
        
        if response.status_code == 200 and resp_json.get('success'):
            product_id = resp_json.get('product_id')
            print(f"\n[SUCCESS] Product created with ID: {product_id}")
            
            # Query the database to verify stocks
            print("\n[INFO] Checking database for saved stocks...")
            variants = query_db(
                "SELECT size, color, stock_quantity FROM product_variants WHERE product_id = %s ORDER BY color, size",
                (product_id,)
            )
            
            if variants:
                print(f"\n[INFO] Found {len(variants)} variants:")
                for v in variants:
                    print(f"  - {v['color']} {v['size']}: {v['stock_quantity']} units")
                
                # Check inventory total
                inventory = query_db(
                    "SELECT stock_quantity FROM inventory WHERE product_id = %s",
                    (product_id,)
                )
                if inventory:
                    print(f"\n[INFO] Inventory total: {inventory[0]['stock_quantity']} units")
                
                # Verify expected values
                expected = {
                    'Red M': 10,
                    'Red L': 15,
                    'Blue M': 20,
                    'Blue L': 25,
                }
                
                print("\n[VERIFICATION] Checking stored values:")
                all_match = True
                for v in variants:
                    key = f"{v['color']} {v['size']}"
                    expected_stock = expected.get(key)
                    if expected_stock and v['stock_quantity'] == expected_stock:
                        print(f"  [OK] {key}: {v['stock_quantity']}")
                    else:
                        print(f"  [FAIL] {key}: Expected {expected_stock}, got {v['stock_quantity']}")
                        all_match = False
                
                if all_match:
                    print("\n[SUCCESS] ALL STOCKS SAVED CORRECTLY!")
                else:
                    print("\n[FAIL] STOCK MISMATCH!")
            else:
                print("[ERROR] No variants found in database")
        else:
            print(f"[ERROR] Request failed: {resp_json}")
            
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)

if __name__ == '__main__':
    main()
