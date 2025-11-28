import pymysql


conn = pymysql.connect(
    host='localhost'
    user='root'
    password=''
)

cursor = conn.cursor()


print("Databases:")
cursor.execute("SHOW DATABASES")
databases = cursor.fetchall()
for db in databases:
    print(f"  - {db[0]}")


print("\nChecking varon database:")
cursor.execute("SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='varon'")
tables = cursor.fetchall()
print(f"Tables in varon: {len(tables)}")
for table in tables:
    print(f"  - {table[0]}")

cursor.close()
conn.close()
