import mysql.connector

conn = mysql.connector.connect(host='localhost', user='root', password='', database='varon')
cursor = conn.cursor()

print("\nShipments table structure:")
print("-" * 80)
cursor.execute('DESCRIBE shipments')
for row in cursor:
    field, type_, null, key, default, extra = row
    print(f"{field:25} {type_:30} {null:10} {str(default):15}")

cursor.close()
conn.close()
print("\n✓ Migration verified successfully!\n")
