import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    database='varon'
)

cursor = conn.cursor(dictionary=True)

# Check all reviews
cursor.execute('SELECT COUNT(*) as count FROM reviews')
result = cursor.fetchone()
total_reviews = result["count"]
print(f'Total reviews in database: {total_reviews}')

if total_reviews > 0:
    # Get sample reviews with all details
    cursor.execute('''
        SELECT id, product_id, user_id, rating, title, comment, is_approved, created_at 
        FROM reviews 
        LIMIT 10
    ''')
    results = cursor.fetchall()
    print('\nAll reviews:')
    for r in results:
        print(f"  ID: {r['id']}, Product: {r['product_id']}, Rating: {r['rating']}, Approved: {r['is_approved']}, Comment: {r['comment'][:50] if r['comment'] else 'None'}")

# Check all rider ratings
cursor.execute('SELECT COUNT(*) as count FROM rider_ratings')
result = cursor.fetchone()
total_ratings = result["count"]
print(f'\n\nTotal rider ratings in database: {total_ratings}')

if total_ratings > 0:
    # Get sample rider ratings
    cursor.execute('''
        SELECT id, rider_id, user_id, rating, comment, created_at 
        FROM rider_ratings 
        LIMIT 10
    ''')
    results = cursor.fetchall()
    print('\nAll rider ratings:')
    for r in results:
        print(f"  ID: {r['id']}, Rider: {r['rider_id']}, Rating: {r['rating']}, Comment: {r['comment'][:50] if r['comment'] else 'None'}")

conn.close()
