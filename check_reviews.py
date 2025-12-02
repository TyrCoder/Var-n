import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    database='varon'
)

cursor = conn.cursor(dictionary=True)

# Check total reviews
cursor.execute('SELECT COUNT(*) as count FROM reviews')
result = cursor.fetchone()
print(f'Total reviews in database: {result["count"]}')

# Get sample reviews
cursor.execute('''
    SELECT id, product_id, rating, title, comment, is_approved, user_id, created_at 
    FROM reviews 
    LIMIT 5
''')
results = cursor.fetchall()
print('\nSample reviews:')
for r in results:
    print(r)

# Check rider ratings
cursor.execute('SELECT COUNT(*) as count FROM rider_ratings')
result = cursor.fetchone()
print(f'\n\nTotal rider ratings in database: {result["count"]}')

# Get sample rider ratings
cursor.execute('''
    SELECT id, rider_id, rating, comment, user_id, created_at 
    FROM rider_ratings 
    LIMIT 5
''')
results = cursor.fetchall()
print('\nSample rider ratings:')
for r in results:
    print(r)

conn.close()
