"""
migrate_db.py

Simple helper to run SQL files from the `migrations/` folder against your local MySQL
server. Reads credentials from a `.env` file (HOST, USER, PASSWORD, DB_NAME) or from
environment variables.

Usage (PowerShell):

  pip install -r requirements.txt
  python migrate_db.py

This script will:
 - connect to MySQL server
 - create the database if it doesn't exist
 - execute all .sql files in `migrations/` in alphanumeric order

Note: SQL files are executed using mysql-connector's multi-statement execution.
If you have complex procedures/delimiters, review those files first.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

try:
    import mysql.connector
    from mysql.connector import errorcode
except Exception as e:
    print("Missing dependency: mysql-connector-python. Install with: pip install mysql-connector-python")
    raise


env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
DB_NAME = os.environ.get('DB_NAME', 'varon')
MIGRATIONS_DIR = Path(__file__).parent / 'migrations'

print(f"Using DB host={DB_HOST!s} user={DB_USER!s} db={DB_NAME!s}")

if not MIGRATIONS_DIR.exists() or not MIGRATIONS_DIR.is_dir():
    print(f"Migrations folder not found: {MIGRATIONS_DIR}")
    sys.exit(1)


try:
    cnx = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD)
    cnx.autocommit = True
    cursor = cnx.cursor()
except mysql.connector.Error as err:
    print(f"[ERROR] Could not connect to MySQL server: {err}")
    sys.exit(1)

try:

    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    print(f"Database `{DB_NAME}` ensured.")

    cnx.database = DB_NAME
except mysql.connector.Error as err:
    print(f"[ERROR] Failed creating or switching to database {DB_NAME}: {err}")
    cursor.close()
    cnx.close()
    sys.exit(1)


sql_files = sorted([p for p in MIGRATIONS_DIR.iterdir() if p.suffix.lower() == '.sql'])
if not sql_files:
    print("No .sql files found in migrations/ folder. Nothing to do.")
    cursor.close()
    cnx.close()
    sys.exit(0)

print(f"Found {len(sql_files)} migration files. Executing in order...")

for sql_file in sql_files:
    print(f"\n--- Running: {sql_file.name} ---")
    sql_text = sql_file.read_text(encoding='utf-8')
    try:

        for result in cursor.execute(sql_text, multi=True):

            try:
                affected = result.rowcount
                if affected is None:
                    affected = 0
                print(f"  Statement OK, affected rows: {affected}")
            except Exception:
                pass
        print(f"{sql_file.name}: OK")
    except mysql.connector.Error as err:
        print(f"{sql_file.name}: ERROR -> {err}")

        cursor.close()
        cnx.close()
        sys.exit(1)

print("\nAll migrations executed successfully.")
cursor.close()
cnx.close()

print("Done.")
