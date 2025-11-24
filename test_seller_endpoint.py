#!/usr/bin/env python
"""Test script to verify seller products endpoint"""

import requests
import json
from flask import session

# Start the app in test mode
import sys
sys.path.insert(0, '/c/Users/razeel/Documents/GitHub/Var-n')

from app import app

# Create a test client
client = app.test_client()

# Test the endpoint without authentication first
print("Test 1: No authentication")
response = client.get('/seller/products')
print(f"Status: {response.status_code}")
print(f"Data: {response.get_json()}")

print("\n" + "="*50 + "\n")

# Test with authentication - create a session
print("Test 2: With mock session")
with client:
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['role'] = 'seller'
        sess['user_id'] = 18  # User ID for seller 1
    
    response = client.get('/seller/products')
    print(f"Status: {response.status_code}")
    data = response.get_json()
    print(f"Response structure: {json.dumps(data, indent=2, default=str)}")
    
    if data.get('products'):
        print(f"\nFound {len(data['products'])} products")
        for p in data['products'][:2]:
            print(f"  - {p.get('name')}: is_active={p.get('is_active')}, stock={p.get('stock')}")
