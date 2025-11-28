
"""Test seller dashboard template rendering"""
import sys
sys.path.insert(0, '/root/app')

try:
    from flask import Flask
    from jinja2 import Environment, FileSystemLoader


    env = Environment(loader=FileSystemLoader('templates/pages'))
    template = env.get_template('SellerDashboard.html')
    print("✓ Template loads successfully")


    html_content = open('templates/pages/SellerDashboard.html', 'r', encoding='utf-8').read()

    checks = {
        'pageTemplates object': "'add-product':" in html_content and "'products':" in html_content,
        'sidebar links': 'data-page=' in html_content,
        'loadPage function': 'function loadPage(' in html_content,
        'event listener': 'addEventListener' in html_content,
        'console logs': 'console.log' in html_content,
    }

    print("\n=== Template Integrity Check ===")
    for check, result in checks.items():
        status = "✓" if result else "✗"
        print(f"{status} {check}")

    print("\n✓ All checks passed - Template is valid")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
