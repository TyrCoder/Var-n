
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

try:
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

    cursor = conn.cursor()
    cursor.execute('SHOW TABLES')

    print('✅ Database connection successful!')
    print('\nTables in varon database:')
    for table in cursor:
        print(f'  - {table[0]}')

    cursor.close()
    conn.close()

except Exception as e:
    print(f'❌ Error: {e}')
