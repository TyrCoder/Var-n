"""
Test script to verify Flask routes are correctly registered
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Direct import
from app import app

print("\n" + "=" * 80)
print("FLASK ROUTES DIAGNOSTIC")
print("=" * 80)

print("\nAll registered routes:")
print("-" * 80)

routes = []
for rule in app.url_map.iter_rules():
    routes.append({
        'rule': rule.rule,
        'endpoint': rule.endpoint,
        'methods': list(rule.methods - {'HEAD', 'OPTIONS'})
    })

# Sort by rule
routes.sort(key=lambda x: x['rule'])

# Filter for signup routes
signup_routes = [r for r in routes if 'signup' in r['rule'].lower()]

print("\nSignup-related routes:")
print("-" * 80)
for route in signup_routes:
    print(f"Route: {route['rule']:<30} Endpoint: {route['endpoint']:<25} Methods: {route['methods']}")

print("\n" + "=" * 80)
print("Testing url_for():")
print("=" * 80)

with app.app_context():
    from flask import url_for
    
    print(f"\nurl_for('signup_seller'): {url_for('signup_seller')}")
    print(f"url_for('signup_rider'): {url_for('signup_rider')}")
    print(f"url_for('signup'): {url_for('signup')}")

print("\n" + "=" * 80)
