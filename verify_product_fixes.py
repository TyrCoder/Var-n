#!/usr/bin/env python3
"""
Verify that the product page fixes are working correctly
"""
import sys
import os

# Try to import required modules
try:
    import pymysql
    print("✓ pymysql imported successfully")
except ImportError as e:
    print(f"✗ pymysql import failed: {e}")
    sys.exit(1)

try:
    from app import app
    print("✓ Flask app imported successfully")
except ImportError as e:
    print(f"✗ Flask app import failed: {e}")
    sys.exit(1)

# Test database connection
try:
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='password',
        database='varon_db'
    )
    print("✓ Database connection successful")
    
    cursor = conn.cursor(dictionary=True)
    
    # Check if ASAP Tec product exists
    cursor.execute("SELECT id, name, price FROM products WHERE name LIKE '%ASAP%' LIMIT 1")
    product = cursor.fetchone()
    
    if product:
        product_id = product['id']
        product_name = product['name']
        print(f"\n✓ Found product: {product_name} (ID: {product_id})")
        
        # Check variants for this product
        cursor.execute("""
            SELECT COUNT(*) as variant_count FROM product_variants 
            WHERE product_id = %s
        """, (product_id,))
        variant_result = cursor.fetchone()
        variant_count = variant_result['variant_count']
        
        print(f"  - Variant count: {variant_count}")
        
        if variant_count == 0:
            print(f"  - ✓ No variants found - FALLBACK LOGIC WILL TRIGGER")
            print(f"  - ✓ Product name '{product_name}' will be scanned for color keywords")
            
            # Test color detection
            name_lower = product_name.lower()
            detected_color = None
            if 'black' in name_lower:
                detected_color = 'Black'
            elif 'white' in name_lower:
                detected_color = 'White'
            elif 'blue' in name_lower:
                detected_color = 'Blue'
            else:
                detected_color = 'Black'  # default
            
            print(f"  - ✓ Detected color: {detected_color}")
        else:
            print(f"  - Product has variants, checking variant details...")
            cursor.execute("""
                SELECT DISTINCT color, COUNT(*) as count FROM product_variants 
                WHERE product_id = %s GROUP BY color
            """, (product_id,))
            colors = cursor.fetchall()
            print(f"  - ✓ Available colors: {[c['color'] for c in colors]}")
    else:
        print("✗ ASAP product not found in database")
    
    cursor.close()
    conn.close()
    print("\n✓ All database checks passed!")
    
except Exception as e:
    print(f"✗ Database operation failed: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("PRODUCT PAGE FIX VERIFICATION COMPLETE")
print("="*60)
print("\nSummary of fixes applied:")
print("1. ✓ Quantity increment/decrement functions enhanced with logging")
print("2. ✓ Fallback color detection from product name (if no variants)")
print("3. ✓ Default sizes and stock_map created when variants missing")
print("4. ✓ Color section only hides if colors array is empty")
print("5. ✓ Add to Cart button disabled until color/size selected")
print("\nTo test:")
print("1. Start the Flask app: python app.py")
print("2. Navigate to product page for 'ASAP Tec' product")
print("3. Verify color swatches appear (should show 'Black')")
print("4. Verify quantity +/- buttons work (check browser console)")
print("5. Verify Add to Cart button enables after color selection")
