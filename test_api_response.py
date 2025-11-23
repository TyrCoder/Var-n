import requests
import json

print("Testing API response...")
response = requests.get('http://localhost:5000/api/products?limit=4')
print(f"\nStatus Code: {response.status_code}")
print(f"\nResponse Headers:")
print(f"  Content-Type: {response.headers.get('Content-Type')}")

data = response.json()
print(f"\nSuccess: {data.get('success')}")
print(f"Number of products: {len(data.get('products', []))}")

print("\n" + "="*80)
print("Product Details:")
print("="*80)
for product in data.get('products', [])[:2]:
    print(f"\nProduct ID: {product.get('id')}")
    print(f"Name: {product.get('name')}")
    print(f"Price: {product.get('price')}")
    print(f"Image URL: {product.get('image_url')}")
    print(f"Colors: {product.get('colors', [])}")
    
    # Test if image is accessible
    if product.get('image_url'):
        img_url = f"http://localhost:5000{product.get('image_url')}"
        img_response = requests.get(img_url)
        print(f"Image Status: {img_response.status_code}")
        if img_response.status_code == 200:
            print(f"Image Size: {len(img_response.content)} bytes")
            print(f"Image Content-Type: {img_response.headers.get('Content-Type')}")
        else:
            print(f"IMAGE NOT ACCESSIBLE!")

print("\n" + "="*80)
print("Full JSON Response (first product):")
print("="*80)
if data.get('products'):
    print(json.dumps(data['products'][0], indent=2))
