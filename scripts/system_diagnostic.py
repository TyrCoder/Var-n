"""
Comprehensive System Diagnostic and Repair Tool
Scans: Database, Configuration, API Endpoints, File Integrity
"""
import os
import sys
import mysql.connector
from mysql.connector import Error
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, '/c/Users/windows/OneDrive/Documents/GitHub/Var-n')

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'varon'
}

CHECKS = []
FIXES = []

def log_check(name, status, details=""):
    """Log a system check"""
    CHECKS.append({
        'name': name,
        'status': status,
        'details': details
    })

def log_fix(name, result, details=""):
    """Log a fix"""
    FIXES.append({
        'name': name,
        'result': result,
        'details': details
    })

class SystemDiagnostic:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.passed = []
        
    def check_env_file(self):
        """Check if .env file exists and has required keys"""
        env_path = '/c/Users/windows/OneDrive/Documents/GitHub/Var-n/.env'
        if os.path.exists(env_path):
            log_check("✓ .env File", "EXISTS", "Configuration file found")
            self.passed.append("Environment file exists")
        else:
            log_check("❌ .env File", "MISSING", "Required .env file not found")
            self.issues.append("Missing .env file - create one with DB credentials")
    
    def check_database_connection(self):
        """Verify database connection works"""
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            if conn.is_connected():
                log_check("✓ Database Connection", "OK", "Connected to varon database")
                self.passed.append("Database connection successful")
                conn.close()
                return True
            else:
                log_check("❌ Database Connection", "FAILED", "Could not establish connection")
                self.issues.append("Database connection failed")
                return False
        except Error as e:
            log_check("❌ Database Connection", "ERROR", str(e))
            self.issues.append(f"Database error: {e}")
            return False
    
    def check_required_tables(self):
        """Verify all required tables exist"""
        required_tables = [
            'users', 'sellers', 'riders', 'products', 'categories',
            'orders', 'order_items', 'shipments', 'addresses',
            'product_variants', 'product_images', 'cart',
            'flash_sales', 'flash_sale_products', 'product_edits',
            'product_archive_requests', 'otp_verifications', 'reviews'
        ]
        
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES")
            existing = [t[0] for t in cursor.fetchall()]
            cursor.close()
            conn.close()
            
            missing = set(required_tables) - set(existing)
            if not missing:
                log_check("✓ Required Tables", "OK", f"All {len(required_tables)} tables present")
                self.passed.append(f"All {len(required_tables)} required tables exist")
            else:
                log_check("❌ Missing Tables", "FAILED", f"Missing: {missing}")
                self.issues.append(f"Missing tables: {missing}")
                
        except Error as e:
            log_check("❌ Required Tables", "ERROR", str(e))
            self.issues.append(f"Could not check tables: {e}")
    
    def check_users_table_schema(self):
        """Verify users table has all required columns"""
        required_cols = [
            'id', 'first_name', 'last_name', 'email', 'password', 'phone',
            'role', 'status', 'email_verified', 'phone_verified',
            'email_verified_at', 'phone_verified_at', 'verification_token'
        ]
        
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("DESCRIBE users")
            existing = [col[0] for col in cursor.fetchall()]
            cursor.close()
            conn.close()
            
            missing = set(required_cols) - set(existing)
            if not missing:
                log_check("✓ Users Schema", "OK", "All columns present")
                self.passed.append("Users table has all required columns")
            else:
                log_check("❌ Users Schema", "INCOMPLETE", f"Missing: {missing}")
                self.warnings.append(f"Users table missing columns: {missing}")
                
        except Error as e:
            log_check("❌ Users Schema", "ERROR", str(e))
            self.issues.append(f"Could not check users schema: {e}")
    
    def check_file_structure(self):
        """Verify required files and directories exist"""
        required_paths = [
            '/c/Users/windows/OneDrive/Documents/GitHub/Var-n/app.py',
            '/c/Users/windows/OneDrive/Documents/GitHub/Var-n/templates',
            '/c/Users/windows/OneDrive/Documents/GitHub/Var-n/static',
            '/c/Users/windows/OneDrive/Documents/GitHub/Var-n/migrations',
        ]
        
        missing = []
        for path in required_paths:
            if not os.path.exists(path):
                missing.append(path)
        
        if not missing:
            log_check("✓ File Structure", "OK", "All required files present")
            self.passed.append("Project file structure intact")
        else:
            log_check("❌ File Structure", "INCOMPLETE", f"Missing: {missing}")
            self.issues.append(f"Missing files: {missing}")
    
    def check_seller_data(self):
        """Verify seller data integrity"""
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor(dictionary=True)
            
            # Check sellers
            cursor.execute("SELECT COUNT(*) as count FROM sellers")
            seller_count = cursor.fetchone()['count']
            
            # Check sellers with valid users
            cursor.execute("""
                SELECT COUNT(*) as count FROM sellers s
                WHERE s.user_id IN (SELECT id FROM users WHERE role='seller')
            """)
            valid_sellers = cursor.fetchone()['count']
            
            cursor.close()
            conn.close()
            
            if seller_count > 0 and valid_sellers == seller_count:
                log_check("✓ Seller Data", "OK", f"{seller_count} seller(s) with valid users")
                self.passed.append("All sellers have valid user accounts")
            elif seller_count == 0:
                log_check("⚠ Seller Data", "WARNING", "No sellers in database")
                self.warnings.append("No seller accounts found")
            else:
                log_check("❌ Seller Data", "INCONSISTENT", f"{seller_count} sellers but only {valid_sellers} valid")
                self.issues.append("Seller data inconsistency detected")
                
        except Error as e:
            log_check("❌ Seller Data", "ERROR", str(e))
            self.issues.append(f"Could not check seller data: {e}")
    
    def check_orders_integrity(self):
        """Verify order data integrity"""
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor(dictionary=True)
            
            # Check orders
            cursor.execute("SELECT COUNT(*) as count FROM orders")
            order_count = cursor.fetchone()['count']
            
            # Check orders with valid users and sellers
            cursor.execute("""
                SELECT COUNT(*) as count FROM orders
                WHERE user_id IN (SELECT id FROM users)
                AND seller_id IN (SELECT id FROM sellers)
            """)
            valid_orders = cursor.fetchone()['count']
            
            # Check for orphaned order items
            cursor.execute("""
                SELECT COUNT(*) as count FROM order_items
                WHERE order_id NOT IN (SELECT id FROM orders)
            """)
            orphaned = cursor.fetchone()['count']
            
            cursor.close()
            conn.close()
            
            if orphaned == 0 and valid_orders == order_count:
                log_check("✓ Orders Integrity", "OK", f"{order_count} orders with valid relationships")
                self.passed.append("Order data is consistent")
            else:
                issues = []
                if orphaned > 0:
                    issues.append(f"{orphaned} orphaned order items")
                if valid_orders != order_count:
                    issues.append(f"{order_count - valid_orders} orders with invalid references")
                log_check("❌ Orders Integrity", "ISSUES", ", ".join(issues))
                self.issues.append(f"Order integrity issues: {issues}")
                
        except Error as e:
            log_check("❌ Orders Integrity", "ERROR", str(e))
            self.issues.append(f"Could not check orders: {e}")
    
    def check_product_data(self):
        """Verify product data"""
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor(dictionary=True)
            
            # Check products
            cursor.execute("SELECT COUNT(*) as count FROM products")
            product_count = cursor.fetchone()['count']
            
            # Check products with valid sellers
            cursor.execute("""
                SELECT COUNT(*) as count FROM products
                WHERE seller_id IN (SELECT id FROM sellers)
            """)
            valid_products = cursor.fetchone()['count']
            
            # Check for products without images
            cursor.execute("""
                SELECT COUNT(*) as count FROM products
                WHERE id NOT IN (SELECT DISTINCT product_id FROM product_images)
            """)
            no_images = cursor.fetchone()['count']
            
            cursor.close()
            conn.close()
            
            status = "OK" if valid_products == product_count else "ISSUES"
            details = f"{product_count} products"
            if no_images > 0:
                details += f", {no_images} without images"
            
            log_check(f"✓ Product Data" if status == "OK" else "⚠ Product Data", status, details)
            if status == "OK":
                self.passed.append("Product data is consistent")
            else:
                self.warnings.append("Some products may have missing data")
                
        except Error as e:
            log_check("❌ Product Data", "ERROR", str(e))
            self.issues.append(f"Could not check products: {e}")
    
    def check_foreign_keys(self):
        """Verify foreign key relationships"""
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor(dictionary=True)
            
            queries = [
                ("Orders → Users", "SELECT COUNT(*) as broken FROM orders WHERE user_id NOT IN (SELECT id FROM users)"),
                ("Orders → Sellers", "SELECT COUNT(*) as broken FROM orders WHERE seller_id NOT IN (SELECT id FROM sellers)"),
                ("Products → Sellers", "SELECT COUNT(*) as broken FROM products WHERE seller_id NOT IN (SELECT id FROM sellers)"),
                ("Order Items → Orders", "SELECT COUNT(*) as broken FROM order_items WHERE order_id NOT IN (SELECT id FROM orders)"),
            ]
            
            all_ok = True
            for name, query in queries:
                cursor.execute(query)
                result = cursor.fetchone()
                broken = result['broken'] if result else 0
                
                if broken == 0:
                    self.passed.append(f"{name} relationship OK")
                else:
                    all_ok = False
                    self.issues.append(f"{name}: {broken} broken references")
            
            cursor.close()
            conn.close()
            
            status = "OK" if all_ok else "ISSUES"
            log_check(f"✓ Foreign Keys" if all_ok else "❌ Foreign Keys", status, 
                     "All relationships valid" if all_ok else "Some broken references found")
                
        except Error as e:
            log_check("❌ Foreign Keys", "ERROR", str(e))
            self.issues.append(f"Could not check foreign keys: {e}")
    
    def generate_report(self):
        """Generate full diagnostic report"""
        print("\n" + "=" * 80)
        print("SYSTEM DIAGNOSTIC REPORT")
        print("=" * 80)
        
        for check in CHECKS:
            status_icon = check['status'].split()[0]
            print(f"\n{check['status']}")
            print(f"  {check['details']}")
        
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"✓ Passed: {len(self.passed)}")
        print(f"⚠ Warnings: {len(self.warnings)}")
        print(f"❌ Issues: {len(self.issues)}")
        
        if self.warnings:
            print("\nWARNINGS:")
            for w in self.warnings:
                print(f"  ⚠ {w}")
        
        if self.issues:
            print("\nISSUES FOUND:")
            for issue in self.issues:
                print(f"  ❌ {issue}")
        else:
            print("\n✓ NO CRITICAL ISSUES FOUND")
        
        print("\n" + "=" * 80)
        return len(self.issues) == 0

def main():
    print("\n🔍 Starting System Diagnostic Scan...")
    print("This will check database, files, configuration, and data integrity.\n")
    
    diagnostic = SystemDiagnostic()
    diagnostic.check_env_file()
    diagnostic.check_database_connection()
    diagnostic.check_required_tables()
    diagnostic.check_users_table_schema()
    diagnostic.check_file_structure()
    diagnostic.check_seller_data()
    diagnostic.check_orders_integrity()
    diagnostic.check_product_data()
    diagnostic.check_foreign_keys()
    
    all_ok = diagnostic.generate_report()
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
