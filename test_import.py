import sys
sys.path.insert(0, 'app')

try:
    from app.routers.auth.auth_routes import get_me
    print("✅ /me endpoint fix imported successfully")
    print("✅ The fix is ready to test")
except Exception as e:
    print(f"❌ Import failed: {e}") 