import requests
import json

# Test getting user orders (need to be logged in)
url_orders = "http://192.168.1.14:5000/api/my-orders"

# First, let's see what orders are available
response = requests.get(url_orders)
print(f"API Response Status: {response.status_code}")

try:
    data = response.json()
    print("Orders data:")
    print(json.dumps(data, indent=2, default=str)[:2000])
except:
    print("Response text:", response.text[:500])
