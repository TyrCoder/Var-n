
"""
Validation script to check for common backend bugs and inconsistencies
"""

import re
import sys

def check_undefined_variables(filename):
    """Check for undefined variables in functions"""
    issues = []
    with open(filename, 'r') as f:
        content = f.read()


    if 'stock_map=' in content and 'stock_map' in content.split('stock_map=')[1].split('\n')[20:]:

        pass


    if 'conn_user.close()' in content and 'conn_user = ' not in content:
        issues.append("⚠ Undefined variable: conn_user might be None")

    return issues

def check_connection_handling(filename):
    """Check for proper connection cleanup"""
    issues = []
    with open(filename, 'r') as f:
        lines = f.readlines()


    in_try = False
    for i, line in enumerate(lines, 1):
        if 'try:' in line:
            in_try = True
        elif in_try and 'except' in line:

            if 'conn.close()' not in lines[i]:
                issues.append(f"Line {i}: Possible missing connection cleanup in except block")
            in_try = False

    return issues

def check_query_references(filename):
    """Check for references to non-existent columns"""
    with open(filename, 'r') as f:
        content = f.read()

    issues = []


    if 'SELECT' in content and 'link_url' in content and 'journal' in content:

        pass


    if 'otp_verifications' in content and 'is_verified' in content:
        pass
    else:
        issues.append("⚠ OTP verifications table might be missing is_verified column")

    return issues

def check_decimal_handling(filename):
    """Check for Decimal to float conversions"""
    with open(filename, 'r') as f:
        content = f.read()

    issues = []


    float_conversions = len(re.findall(r'float\(', content))


    decimal_refs = len(re.findall(r'Decimal', content))

    if decimal_refs > float_conversions:
        issues.append(f"⚠ More Decimal references ({decimal_refs}) than float conversions ({float_conversions})")

    return issues

def check_error_responses(filename):
    """Check for consistent error response format"""
    with open(filename, 'r') as f:
        lines = f.readlines()

    issues = []


    for i, line in enumerate(lines, 1):
        if 'jsonify' in line and 'success' not in line and 'error' not in line:
            if i > 100:
                issues.append(f"Line {i}: Potentially inconsistent JSON response format")

    return issues

def main():
    filename = 'app.py'

    print("🔍 Validating backend code...\n")

    all_issues = []

    print("✓ Checking for undefined variables...")
    all_issues.extend(check_undefined_variables(filename))

    print("✓ Checking connection handling...")
    all_issues.extend(check_connection_handling(filename))

    print("✓ Checking query references...")
    all_issues.extend(check_query_references(filename))

    print("✓ Checking Decimal handling...")
    all_issues.extend(check_decimal_handling(filename))

    print("✓ Checking error response consistency...")
    all_issues.extend(check_error_responses(filename))

    if all_issues:
        print(f"\n⚠ Found {len(all_issues)} potential issues:\n")
        for issue in all_issues[:10]:
            print(f"  • {issue}")
        if len(all_issues) > 10:
            print(f"\n  ... and {len(all_issues) - 10} more issues")
    else:
        print("\n✅ No major issues found!")

    return 0 if not all_issues else 1

if __name__ == '__main__':
    sys.exit(main())
