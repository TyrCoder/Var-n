"""
Test the cart API endpoints
"""
import requests
import json

BASE_URL = 'http://192.168.1.14:5000'

# Test without login - should fail
print("Testing cart API without login...")
response = requests.get(f'{BASE_URL}/api/cart/get')
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
print()

# Note: To test with login, you need to have an active session
# This would require setting up cookies from a login request
print("Note: Full test requires authenticated session.")
print("Please test by:")
print("1. Login to the app")
print("2. Add an item to cart")
print("3. Check browser console for API response")
print("4. Open browser DevTools > Network > XHR and look for /api/cart/get response")
