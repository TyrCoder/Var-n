
"""
Simple Flask app runner with error reporting
"""
import sys
import os


sys.path.insert(0, os.path.dirname(__file__))

try:
    print("[*] Loading environment variables...")
    from dotenv import load_dotenv
    load_dotenv()
    print("[✓] Environment loaded")

    print("[*] Importing Flask app...")
    from app import app
    print("[✓] App imported successfully")

    print("\n" + "="*60)
    print("🚀 STARTING FLASK APPLICATION")
    print("="*60)
    print("\n📍 Server running at:")
    print("   • Local:   http://localhost:5000")
    print("   • Network: http://0.0.0.0:5000")
    print("\n💡 Press CTRL+C to stop the server")
    print("\n📚 Features:")
    print("   • Database will initialize on first request")
    print("   • Check http://localhost:5000 to get started")
    print("="*60 + "\n")

    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

except ImportError as e:
    print(f"\n❌ IMPORT ERROR: {e}")
    print("\nMissing package detected. Please install dependencies:")
    print("  pip install -r requirements.txt")
    sys.exit(1)

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
