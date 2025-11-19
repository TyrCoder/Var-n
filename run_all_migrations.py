"""
Master migration script to run all database migrations
Run this with: python run_all_migrations.py
This script is idempotent - it's safe to run multiple times
"""
import mysql.connector
from mysql.connector import Error
import os
import sys

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Add your password here if needed
    'database': 'varon'
}

MIGRATIONS_DIR = 'migrations'

def run_all_migrations():
    """Run all SQL migration files in the migrations directory"""
    try:
        # Connect to database
        conn = mysql.connector.connect(**DB_CONFIG)
        
        if conn.is_connected():
            cursor = conn.cursor()
            print("Connected to database successfully!")
            print(f"Database: {DB_CONFIG['database']}\n")
            print("=" * 60)
            
            # Get all SQL migration files
            migration_files = sorted([
                f for f in os.listdir(MIGRATIONS_DIR) 
                if f.endswith('.sql')
            ])
            
            if not migration_files:
                print("⚠ No migration files found in migrations/ directory")
                cursor.close()
                conn.close()
                return
            
            print(f"Found {len(migration_files)} migration file(s):\n")
            for f in migration_files:
                print(f"  • {f}")
            
            print("\n" + "=" * 60)
            print("Running migrations...\n")
            
            # Run each migration file
            successful = 0
            failed = 0
            skipped = 0
            
            for migration_file in migration_files:
                migration_path = os.path.join(MIGRATIONS_DIR, migration_file)
                
                try:
                    print(f"Executing: {migration_file}...", end=" ")
                    
                    # Read the SQL file
                    with open(migration_path, 'r', encoding='utf-8') as f:
                        sql_content = f.read()
                    
                    # Split by semicolon and execute each statement
                    statements = [s.strip() for s in sql_content.split(';') if s.strip()]
                    
                    statement_results = []
                    for statement in statements:
                        if statement.strip():
                            try:
                                cursor.execute(statement)
                                statement_results.append(True)
                            except Error as e:
                                # Skip duplicate key and already exists errors
                                if "1061" in str(e) or "Duplicate key" in str(e) or "already exists" in str(e):
                                    statement_results.append(None)  # Mark as skipped
                                else:
                                    raise  # Re-raise other errors
                    
                    conn.commit()
                    
                    # Check if any statements actually executed
                    if all(r is None for r in statement_results):
                        print("⊘ Skipped (already applied)")
                        skipped += 1
                    else:
                        print("✓ Success")
                        successful += 1
                    
                except Error as e:
                    if "Unread result found" in str(e):
                        # Fetch remaining results to clear the buffer
                        try:
                            while cursor.nextset():
                                pass
                        except:
                            pass
                        print("✓ Success (with warnings)")
                        successful += 1
                    else:
                        print(f"✗ Failed")
                        print(f"    Error: {str(e)}")
                        failed += 1
                        conn.rollback()
                
                except Exception as e:
                    print(f"✗ Failed")
                    print(f"    Error: {str(e)}")
                    failed += 1
            
            print("\n" + "=" * 60)
            print(f"Migration Summary:")
            print(f"  Successful: {successful}")
            print(f"  Skipped (already applied): {skipped}")
            print(f"  Failed: {failed}")
            print(f"  Total: {successful + failed + skipped}")
            print("=" * 60)
            
            # Verify database schema
            print("\nVerifying database schema...")
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"\nTables in database '{DB_CONFIG['database']}':")
            for table in sorted(tables):
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                count = cursor.fetchone()[0]
                print(f"  • {table[0]:30s} ({count:6d} rows)")
            
            cursor.close()
            conn.close()
            
            if failed == 0:
                print("\n✓ All migrations completed successfully!")
                return True
            else:
                print(f"\n⚠ {failed} migration(s) failed. Please review the errors above.")
                return False
            
    except Error as e:
        print(f"Database connection error: {str(e)}")
        return False
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_all_migrations()
    sys.exit(0 if success else 1)
