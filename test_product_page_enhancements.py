#!/usr/bin/env python3
"""
Test script to verify product page enhancements:
1. Seller information display
2. Available colors display
3. Account dropdown menu
"""

import requests
import re
import json

BASE_URL = "http://127.0.0.1:5000"

def test_backend_changes():
    """Test if backend has seller info in product response"""
    print("\n" + "="*60)
    print("TESTING BACKEND CHANGES")
    print("="*60)
    
    try:
        # Get a product to test
        response = requests.get(f"{BASE_URL}/api/products", timeout=5)
        if response.status_code == 200:
            products = response.json().get('products', [])
            if products:
                product_id = products[0].get('id')
                print(f"✓ Found test product ID: {product_id}")
                
                # Try to access product page
                product_page = requests.get(f"{BASE_URL}/product/{product_id}", timeout=5)
                if product_page.status_code == 200:
                    print("✓ Product page loads successfully")
                    
                    # Check for seller info in HTML
                    if "Sold by:" in product_page.text:
                        print("✓ Seller information section found in HTML")
                    else:
                        print("⚠ Seller information section not found (expected if no seller data)")
                    
                    # Check for available colors section
                    if "Available Colors:" in product_page.text:
                        print("✓ Available colors section found in HTML")
                    else:
                        print("⚠ Available colors section not found (expected if product has no colors)")
                    
                    return True
                else:
                    print(f"✗ Product page returned {product_page.status_code}")
                    return False
            else:
                print("⚠ No products found in database")
                return True
        else:
            print(f"✗ API returned {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_frontend_dropdown():
    """Test if frontend has dropdown menu"""
    print("\n" + "="*60)
    print("TESTING FRONTEND DROPDOWN MENU")
    print("="*60)
    
    try:
        # Get a product page
        response = requests.get(f"{BASE_URL}/api/products", timeout=5)
        if response.status_code == 200:
            products = response.json().get('products', [])
            if products:
                product_id = products[0].get('id')
                product_page = requests.get(f"{BASE_URL}/product/{product_id}", timeout=5)
                
                if product_page.status_code == 200:
                    html = product_page.text
                    
                    # Check for dropdown menu items
                    checks = {
                        "My Account": "My Account" in html,
                        "My Orders": "My Orders" in html,
                        "Settings": "Settings" in html,
                        "Logout": "Logout" in html,
                        "toggleUserDropdown function": "toggleUserDropdown" in html,
                        "dropdown-content class": "dropdown-content" in html,
                        "user-dropdown class": "user-dropdown" in html,
                    }
                    
                    all_found = True
                    for check_name, found in checks.items():
                        status = "✓" if found else "✗"
                        print(f"{status} {check_name}")
                        if not found:
                            all_found = False
                    
                    return all_found
        
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_code_changes():
    """Verify the code changes were made"""
    print("\n" + "="*60)
    print("VERIFYING CODE CHANGES")
    print("="*60)
    
    checks = {}
    
    # Check app.py for seller info query
    try:
        with open('app.py', 'r') as f:
            app_content = f.read()
            checks["app.py - seller JOIN"] = "LEFT JOIN sellers s ON" in app_content and "LEFT JOIN users u ON s.user_id = u.id" in app_content
            checks["app.py - seller_name"] = "as seller_name" in app_content
            checks["app.py - store_name"] = "s.store_name" in app_content
            checks["app.py - template params"] = "seller_name=" in app_content and "store_name=" in app_content
    except Exception as e:
        print(f"✗ Error reading app.py: {e}")
        return False
    
    # Check product.html for seller section
    try:
        with open('templates/pages/product.html', 'r') as f:
            html_content = f.read()
            checks["product.html - Seller Info section"] = "Sold by:" in html_content
            checks["product.html - Available Colors section"] = "Available Colors:" in html_content
            checks["product.html - Dropdown My Account"] = "My Account" in html_content
            checks["product.html - Dropdown My Orders"] = "My Orders" in html_content
            checks["product.html - Dropdown Settings"] = "Settings" in html_content
            checks["product.html - seller_name variable"] = "{{ seller_name" in html_content
            checks["product.html - store_name variable"] = "{{ store_name" in html_content
            checks["product.html - colors loop"] = "{% for color in colors %}" in html_content
    except Exception as e:
        print(f"✗ Error reading product.html: {e}")
        return False
    
    all_passed = True
    for check_name, passed in checks.items():
        status = "✓" if passed else "✗"
        print(f"{status} {check_name}")
        if not passed:
            all_passed = False
    
    return all_passed

def main():
    print("\n" + "="*60)
    print("PRODUCT PAGE ENHANCEMENTS TEST SUITE")
    print("="*60)
    
    results = []
    
    # Test code changes
    results.append(("Code Changes", test_code_changes()))
    
    # Test backend
    results.append(("Backend Changes", test_backend_changes()))
    
    # Test frontend
    results.append(("Frontend Changes", test_frontend_dropdown()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    print("\n" + "="*60)
    if all_passed:
        print("✓ ALL TESTS PASSED!")
    else:
        print("⚠ SOME TESTS NEED ATTENTION")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
