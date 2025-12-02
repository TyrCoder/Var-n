#!/usr/bin/env python
"""
Test script to verify reviews system is working correctly
Creates test data and verifies API responses
"""
import mysql.connector
import requests
import json

print("=" * 70)
print("REVIEWS SYSTEM TEST")
print("=" * 70)

# Connect to database
try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        database='varon'
    )
    cursor = conn.cursor(dictionary=True)
    print("\n✓ Connected to database")
except Exception as e:
    print(f"\n✗ Database connection failed: {e}")
    exit(1)

# Check if rider_ratings table exists
try:
    cursor.execute("SHOW TABLES LIKE 'rider_ratings'")
    if cursor.fetchone():
        print("✓ rider_ratings table exists")
    else:
        print("✗ rider_ratings table NOT found")
except Exception as e:
    print(f"✗ Error checking rider_ratings table: {e}")

# Check if reviews table exists and has data
try:
    cursor.execute("SELECT COUNT(*) as cnt FROM reviews")
    count = cursor.fetchone()['cnt']
    print(f"✓ reviews table has {count} reviews")
except Exception as e:
    print(f"✗ Error checking reviews table: {e}")

# Check if rider_ratings table has data
try:
    cursor.execute("SELECT COUNT(*) as cnt FROM rider_ratings")
    count = cursor.fetchone()['cnt']
    print(f"✓ rider_ratings table has {count} ratings")
except Exception as e:
    print(f"✗ Error checking rider_ratings table data: {e}")

# Get sample delivered order
print("\nLooking for test data...")
try:
    cursor.execute('''
        SELECT o.id, o.user_id, oi.product_id, s.rider_id
        FROM orders o
        LEFT JOIN order_items oi ON o.id = oi.order_id
        LEFT JOIN shipments s ON o.id = s.order_id
        WHERE o.order_status = "delivered"
        LIMIT 1
    ''')
    result = cursor.fetchone()
    
    if result:
        order_id, user_id, product_id, rider_id = result['id'], result['user_id'], result['product_id'], result['rider_id']
        print(f"✓ Found delivered order: #{order_id}")
        print(f"  - User ID: {user_id}")
        print(f"  - Product ID: {product_id}")
        print(f"  - Rider ID: {rider_id}")
        
        # Check if a review already exists
        cursor.execute('''
            SELECT id FROM reviews
            WHERE order_id = %s AND user_id = %s AND product_id = %s
        ''', (order_id, user_id, product_id))
        
        if cursor.fetchone():
            print("  - Review already exists for this order")
        else:
            print("  - No review yet for this order")
            # Create test review
            try:
                cursor.execute('''
                    INSERT INTO reviews (product_id, user_id, order_id, rating, title, comment, is_verified_purchase, is_approved)
                    VALUES (%s, %s, %s, 5, "Excellent product!", "Great quality and fast delivery. Highly recommended!", 1, 1)
                ''', (product_id, user_id, order_id))
                conn.commit()
                print("  ✓ Created test review with 5-star rating")
            except Exception as e:
                print(f"  ✗ Failed to create review: {e}")
        
        # Check if rider rating exists
        if rider_id:
            cursor.execute('''
                SELECT id FROM rider_ratings
                WHERE order_id = %s AND user_id = %s AND rider_id = %s
            ''', (order_id, user_id, rider_id))
            
            if cursor.fetchone():
                print("  - Rider rating already exists for this order")
            else:
                print("  - No rider rating yet for this order")
                # Create test rider rating
                try:
                    cursor.execute('''
                        INSERT INTO rider_ratings (rider_id, user_id, order_id, rating, comment)
                        VALUES (%s, %s, %s, 5, "Excellent delivery service! Professional and courteous.")
                    ''', (rider_id, user_id, order_id))
                    conn.commit()
                    print("  ✓ Created test rider rating with 5-star rating")
                except Exception as e:
                    print(f"  ✗ Failed to create rider rating: {e}")
    else:
        print("✗ No delivered orders found to create test data")
except Exception as e:
    print(f"✗ Error: {e}")

# Now test the APIs
print("\n" + "=" * 70)
print("TESTING APIS")
print("=" * 70)

# Test product reviews API
try:
    response = requests.get("http://192.168.1.14:5000/api/product-reviews/5", timeout=5)
    data = response.json()
    print(f"\n✓ Product Reviews API (product 5):")
    print(f"  Status: {response.status_code}")
    print(f"  Success: {data.get('success')}")
    print(f"  Review Count: {data.get('count')}")
    
    if data.get('reviews'):
        review = data['reviews'][0]
        print(f"  First Review:")
        print(f"    - Rating: {review.get('rating')}")
        print(f"    - Title: {review.get('title')}")
        print(f"    - Comment: {review.get('comment')[:50] if review.get('comment') else 'N/A'}...")
        print(f"    - Author: {review.get('first_name')} {review.get('last_name')}")
except Exception as e:
    print(f"\n✗ Error testing product reviews API: {e}")

# Test rider reviews API (if we found a rider)
if rider_id:
    try:
        response = requests.get(f"http://192.168.1.14:5000/api/rider/{rider_id}/reviews", timeout=5)
        data = response.json()
        print(f"\n✓ Rider Reviews API (rider {rider_id}):")
        print(f"  Status: {response.status_code}")
        print(f"  Success: {data.get('success')}")
        
        if data.get('rider'):
            print(f"  Rider Info:")
            print(f"    - Name: {data['rider'].get('name')}")
            print(f"    - Overall Rating: {data['rider'].get('overall_rating')}")
            print(f"    - Total Ratings: {data['rider'].get('total_ratings')}")
        
        if data.get('reviews'):
            review = data['reviews'][0]
            print(f"  First Review:")
            print(f"    - Rating: {review.get('rating')}")
            print(f"    - Comment: {review.get('comment')[:50] if review.get('comment') else 'N/A'}...")
            print(f"    - Customer: {review.get('customer_name')}")
    except Exception as e:
        print(f"\n✗ Error testing rider reviews API: {e}")

conn.close()
print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
