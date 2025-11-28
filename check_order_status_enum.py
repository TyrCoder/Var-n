import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='varon'
)

cursor = conn.cursor()
cursor.execute("SHOW COLUMNS FROM orders LIKE 'order_status'")
result = cursor.fetchone()

print("Current order_status ENUM values:")
print(result[1])

cursor.close()
conn.close()
