import mysql.connector
import sys
import os

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'varon'
}

def run_migration(sql_file_path):
    """Run a SQL migration file"""
    try:
        if not os.path.exists(sql_file_path):
            print(f"Migration file not found: {sql_file_path}")
            return False
        
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        statements = [s.strip() for s in sql_content.split(';') if s.strip()]
        
        for statement in statements:
            if statement:
                try:
                    cursor.execute(statement)
                    print(f"✓ Executed: {statement[:80]}...")
                except Exception as e:
                    print(f"✗ Error: {str(e)}")
                    print(f"  Statement: {statement[:100]}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"\n✓ Migration completed successfully: {os.path.basename(sql_file_path)}")
        return True
        
    except Exception as e:
        print(f"✗ Migration failed: {str(e)}")
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python run_single_migration.py <migration_file.sql>")
        print("\nExample:")
        print("  python run_single_migration.py migrations/add_otp_verification.sql")
        sys.exit(1)
    
    migration_file = sys.argv[1]
    success = run_migration(migration_file)
    sys.exit(0 if success else 1)
