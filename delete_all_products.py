import mysql.connector

# Database config
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'varon'
}

print("="*80)
print("Deleting All Products")
print("="*80)

try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Get count before deletion
    cursor.execute("SELECT COUNT(*) FROM products")
    product_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM product_images")
    image_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM product_variants")
    variant_count = cursor.fetchone()[0]
    
    print(f"\nCurrent records:")
    print(f"  Products: {product_count}")
    print(f"  Product Images: {image_count}")
    print(f"  Product Variants: {variant_count}")
    
    # Delete in correct order (child tables first)
    print("\nDeleting records...")
    
    # Delete order items first (they reference products)
    cursor.execute("DELETE FROM order_items")
    print(f"  ✅ Deleted {cursor.rowcount} order items")
    
    cursor.execute("DELETE FROM product_images")
    print(f"  ✅ Deleted {cursor.rowcount} product images")
    
    cursor.execute("DELETE FROM product_variants")
    print(f"  ✅ Deleted {cursor.rowcount} product variants")
    
    cursor.execute("DELETE FROM products")
    print(f"  ✅ Deleted {cursor.rowcount} products")
    
    # Reset auto increment
    cursor.execute("ALTER TABLE products AUTO_INCREMENT = 1")
    cursor.execute("ALTER TABLE product_images AUTO_INCREMENT = 1")
    cursor.execute("ALTER TABLE product_variants AUTO_INCREMENT = 1")
    print("\n  ✅ Reset auto increment counters")
    
    conn.commit()
    
    print("\n" + "="*80)
    print("✅ All products and related data deleted successfully!")
    print("="*80)
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    if 'conn' in locals():
        conn.rollback()
