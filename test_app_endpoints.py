
"""
Comprehensive test of the fixed Flask app with PyMySQL
"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_homepage():
    """Test if homepage loads"""
    print("Testing homepage...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ Homepage loaded successfully (200)")
            return True
        else:
            print(f"❌ Homepage returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Homepage test failed: {e}")
        return False

def test_products_api():
    """Test if products API works"""
    print("\nTesting /api/products...")
    try:
        response = requests.get(f"{BASE_URL}/api/products", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Products API returned 200")
            print(f"   Response: {json.dumps(data, indent=2)[:200]}")
            return True
        else:
            print(f"❌ Products API returned {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Products API test failed: {e}")
        return False

def test_login_page():
    """Test if login page loads"""
    print("\nTesting login page...")
    try:
        response = requests.get(f"{BASE_URL}/login", timeout=5)
        if response.status_code == 200:
            print("✅ Login page loaded successfully (200)")
            return True
        else:
            print(f"❌ Login page returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Login page test failed: {e}")
        return False

def test_categories_api():
    """Test if categories API works"""
    print("\nTesting /api/categories...")
    try:
        response = requests.get(f"{BASE_URL}/api/categories", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Categories API returned 200")
            print(f"   Response: {json.dumps(data, indent=2)[:200]}")
            return True
        else:
            print(f"❌ Categories API returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Categories API test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("FLASK APP VERIFICATION TESTS")
    print("=" * 60)

    results = []
    results.append(("Homepage", test_homepage()))
    results.append(("Login Page", test_login_page()))
    results.append(("Products API", test_products_api()))
    results.append(("Categories API", test_categories_api()))

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Database is working correctly!")
    else:
        print(f"\n❌ {total - passed} test(s) failed")
