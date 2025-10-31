#!/usr/bin/env python3
"""
Test script to verify all imports work without circular dependencies.
"""
import sys
print("Testing imports...")

try:
    print("1. Testing config...")
    from ag_ui_gateway.config import settings
    print("   ✅ Config OK")
    
    print("2. Testing database...")
    from ag_ui_gateway import database
    print("   ✅ Database OK")
    
    print("3. Testing auth...")
    from ag_ui_gateway.auth import tokens, flow_auth
    print("   ✅ Auth OK")
    
    print("4. Testing adapters...")
    from ag_ui_gateway.adapters import llm_adapter, task_adapter, catalog_adapter, command_adapter, profile_adapter
    print("   ✅ Adapters OK")
    
    print("5. Testing API...")
    from ag_ui_gateway.api import auth, catalog, profile, files, health
    print("   ✅ API OK")
    
    print("6. Testing WebSocket...")
    from ag_ui_gateway.websocket import chat
    print("   ✅ WebSocket OK")
    
    print("7. Testing main...")
    from ag_ui_gateway import main
    print("   ✅ Main OK")
    
    print("\n🎉 All imports successful!")
    print("No circular dependencies detected.")
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

