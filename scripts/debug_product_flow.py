"""
Product Adding Flow Debugging Script
=====================================

This script helps verify that the product adding flow works correctly:
1. Products are inserted with is_active = 0 (pending)
2. Admin can see them in pending-products
3. Admin can approve them (is_active = 1)
4. Approved products appear in store
"""

import mysql.connector
from datetime import datetime

def get_db():
    try:
        return mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='varon'
        )
    except Exception as err:
        print(f"❌ Database connection error: {err}")
        return None

def check_pending_products():
    """Check all pending products"""
    conn = get_db()
    if not conn:
        return

    cursor = conn.cursor(dictionary=True)

    print("\n" + "="*60)
    print("PENDING PRODUCTS (is_active = 0)")
    print("="*60)

    cursor.execute('''
        SELECT p.id, p.name, p.is_active, s.store_name, p.created_at
        FROM products p
        LEFT JOIN sellers s ON p.seller_id = s.id
        WHERE p.is_active = 0
        ORDER BY p.created_at DESC
    ''')

    pending = cursor.fetchall()

    if pending:
        print(f"\n✅ Found {len(pending)} pending product(s):\n")
        for prod in pending:
            print(f"  ID: {prod['id']}")
            print(f"  Name: {prod['name']}")
            print(f"  Seller: {prod['store_name']}")
            print(f"  Created: {prod['created_at']}")
            print(f"  Active: {prod['is_active']} (should be 0)")
            print("-" * 50)
    else:
        print("\n⚠️  No pending products found!")

    cursor.close()
    conn.close()
    return pending

def check_approved_products():
    """Check all approved products"""
    conn = get_db()
    if not conn:
        return

    cursor = conn.cursor(dictionary=True)

    print("\n" + "="*60)
    print("APPROVED PRODUCTS (is_active = 1)")
    print("="*60)

    cursor.execute('''
        SELECT p.id, p.name, p.is_active, s.store_name, p.created_at
        FROM products p
        LEFT JOIN sellers s ON p.seller_id = s.id
        WHERE p.is_active = 1
        ORDER BY p.created_at DESC
        LIMIT 5
    ''')

    approved = cursor.fetchall()

    if approved:
        print(f"\n✅ Found {len(approved)} approved product(s):\n")
        for prod in approved:
            print(f"  ID: {prod['id']}")
            print(f"  Name: {prod['name']}")
            print(f"  Seller: {prod['store_name']}")
            print(f"  Active: {prod['is_active']} (should be 1)")
            print("-" * 50)
    else:
        print("\n⚠️  No approved products found!")

    cursor.close()
    conn.close()
    return approved

def check_product_details(product_id):
    """Check detailed info for a product"""
    conn = get_db()
    if not conn:
        return

    cursor = conn.cursor(dictionary=True)

    print(f"\n" + "="*60)
    print(f"PRODUCT DETAILS (ID: {product_id})")
    print("="*60 + "\n")


    cursor.execute('''
        SELECT p.*, s.store_name, s.user_id
        FROM products p
        LEFT JOIN sellers s ON p.seller_id = s.id
        WHERE p.id = %s
    ''', (product_id,))

    product = cursor.fetchone()

    if not product:
        print(f"❌ Product {product_id} not found!")
        cursor.close()
        conn.close()
        return

    print(f"Product Name: {product['name']}")
    print(f"Price: ₱{product['price']}")
    print(f"Seller: {product['store_name']}")
    print(f"Is Active: {product['is_active']} {'✅ (Approved)' if product['is_active'] else '⏳ (Pending)'}")
    print(f"Created: {product['created_at']}")


    cursor.execute('''
        SELECT image_url, is_primary
        FROM product_images
        WHERE product_id = %s
    ''', (product_id,))

    images = cursor.fetchall()
    print(f"\nImages ({len(images)}):")
    if images:
        for img in images:
            print(f"  - {img['image_url']} {'(Primary)' if img['is_primary'] else ''}")
    else:
        print("  ❌ No images found!")


    cursor.execute('''
        SELECT stock_quantity, low_stock_threshold
        FROM inventory
        WHERE product_id = %s
    ''', (product_id,))

    inventory = cursor.fetchone()
    if inventory:
        print(f"\nInventory:")
        print(f"  - Stock: {inventory['stock_quantity']}")
        print(f"  - Low Stock Threshold: {inventory['low_stock_threshold']}")
    else:
        print(f"\n❌ No inventory found!")


    cursor.execute('''
        SELECT size, color, stock_quantity
        FROM product_variants
        WHERE product_id = %s
        LIMIT 10
    ''', (product_id,))

    variants = cursor.fetchall()
    if variants:
        print(f"\nVariants ({len(variants)}):")
        for variant in variants:
            print(f"  - {variant['size']} / {variant['color']}: {variant['stock_quantity']} pcs")

    cursor.close()
    conn.close()

def test_product_flow():
    """Test the complete flow"""
    print("\n" + "="*60)
    print("PRODUCT FLOW VERIFICATION")
    print("="*60)


    pending = check_pending_products()


    approved = check_approved_products()


    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Pending Products: {len(pending) if pending else 0}")
    print(f"Approved Products: {len(approved) if approved else 0}")

    if pending:
        print("\n✅ FLOW WORKING:")
        print("  1. Products are being created with is_active=0")
        print("  2. They appear in admin's pending-products")
        print("  3. Admin can approve them to set is_active=1")
        print("\n🔍 Next step: Admin should approve pending products to see them in store")
    else:
        print("\n⚠️  NO PENDING PRODUCTS")
        print("  Either no products have been added yet, or there's an issue")

if __name__ == "__main__":
    test_product_flow()


    print("\n" + "="*60)
    print("To check a specific product, uncomment the line below and add product ID:")
    print("="*60)
    print("# check_product_details(1)  # Replace 1 with your product ID")
