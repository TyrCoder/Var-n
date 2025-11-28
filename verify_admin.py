import pymysql

conn = pymysql.connect(host='localhost', user='root', password='', database='varon')
cursor = conn.cursor(dictionary=True)

cursor.execute('SELECT id, first_name, last_name, email, role, status FROM users WHERE email = %s', ('admin@varon.com',))
user = cursor.fetchone()

print('✅ Admin User Verified:')
print(f'  ID: {user["id"]}')
print(f'  Name: {user["first_name"]} {user["last_name"]}')
print(f'  Email: {user["email"]}')
print(f'  Role: {user["role"]}')
print(f'  Status: {user["status"]}')

cursor.close()
conn.close()
