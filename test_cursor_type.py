import pymysql


conn1 = pymysql.connect(
    host='localhost'
    user='root'
    password=''
    database='varon'
)

cursor1 = conn1.cursor()
cursor1.execute("SELECT id, name FROM users LIMIT 1")
result1 = cursor1.fetchone()
print(f"With cursorclass in connect: {type(result1)} = {result1}")
cursor1.close()
conn1.close()


conn2 = pymysql.connect(
    host='localhost'
    user='root'
    password=''
    database='varon'
)

cursor2 = conn2.cursor(dictionary=True)
cursor2.execute("SELECT id, name FROM users LIMIT 1")
result2 = cursor2.fetchone()
print(f"With explicit DictCursor: {type(result2)} = {result2}")
cursor2.close()
conn2.close()
