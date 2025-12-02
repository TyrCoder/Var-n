import requests
import json

# Test getting product reviews
product_id = 5
url = f"http://192.168.1.14:5000/api/product-reviews/{product_id}"

response = requests.get(url)
data = response.json()

print(f"API Response Status: {response.status_code}")
print(f"Response Data:")
print(json.dumps(data, indent=2, default=str))
