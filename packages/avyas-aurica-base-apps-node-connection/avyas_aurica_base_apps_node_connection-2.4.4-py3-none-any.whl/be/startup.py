"""
Startup handler for node-connection app
This module is automatically called when the app is loaded
"""
import asyncio
from pathlib import Path
import sys
import os

# Add app directory to path for imports
node_be_dir = Path(__file__).parent
if str(node_be_dir) not in sys.path:
    sys.path.insert(0, str(node_be_dir))

from node_manager import get_node_manager
from node_registry import initialize_registry, get_registry


async def startup():
    """
    Startup routine - called when app is loaded
    
    1. Initializes node registry (for API domain)
    2. Connects to API domain and establishes connection
    3. Registers this node with the API domain (if execution node)
    """
    print("🔌 Node Connection Manager: Starting up...")
    
    try:
        # Initialize registry
        registry = initialize_registry()
        print("✅ Node registry initialized")
        
        # Initialize node manager
        manager = get_node_manager()
        success = await manager.startup()
        
        if success:
            print("✅ Node Connection Manager: Successfully connected to API domain")
            status = manager.get_status()
            print(f"   📍 Node ID: {status['node_id']}")
            print(f"   🌐 API Domain: {status['api_domain']}")
            print(f"   🟢 Status: {'Connected' if status['connected'] else 'Disconnected'}")
            print("   🔐 Using existing JWT authentication system")
            
            # If this is an execution node (not the API domain itself), register it
            await register_with_api_domain(manager)
        else:
            print("⚠️  Node Connection Manager: Failed to connect to API domain")
        
        return success
    except Exception as e:
        print(f"❌ Error during startup: {e}")
        import traceback
        traceback.print_exc()
        return False


async def register_with_api_domain(manager):
    """
    Register this execution node with the API domain.
    
    This sends node connection details to the API domain so it can
    be discovered and managed remotely.
    
    Note: Full registration happens when user authenticates.
    This just establishes initial connection capability.
    """
    import httpx
    
    # Check if we're running as an execution node (not the API domain)
    api_domain = manager.config.api_domain
    status = manager.get_status()
    node_id = status['node_id']
    
    # Determine current host
    current_host = os.environ.get("HOST", "localhost")
    current_port = os.environ.get("PORT", "8000")
    
    # Check if we're running on the production API domain
    is_production_api = "api.oneaurica.com" in current_host or "oneaurica.com" in os.environ.get("HOSTNAME", "")
    
    # If we ARE the production API domain, skip self-registration
    if is_production_api:
        print(f"   ℹ️  Running on production API domain - skipping self-registration")
        return
    
    # This is an execution node (localhost or other remote node)
    print(f"   📡 Execution node detected (not API domain)")
    print(f"      Will register with API domain when user authenticates")
    print(f"      Node will be available at: http://localhost:{current_port}")
    
    # Try to auto-register using Digital Twin's mechanism
    try:
        # Import the Digital Twin auto-register module
        from pathlib import Path
        dt_path = Path(__file__).parent.parent.parent / "digital-twin" / "be"
        if str(dt_path) not in sys.path:
            sys.path.insert(0, str(dt_path))
        
        from auto_register import register_execution_node
        
        # Check if we have a stored auth token (from previous login)
        auth_token = os.environ.get("AURICA_AUTH_TOKEN")
        user_id = os.environ.get("AURICA_USER_ID")
        
        if auth_token and user_id:
            print(f"   🔐 Found stored credentials for user {user_id}")
            print(f"   🔄 Auto-registering execution node...")
            success = await register_execution_node(user_id, auth_token)
            if success:
                print(f"   ✅ Execution node auto-registered!")
            else:
                print(f"   ⚠️  Auto-registration failed - will retry on user login")
        else:
            print(f"   ℹ️  No stored credentials - node will register on first user login")
            
    except Exception as e:
        print(f"   ⚠️  Could not auto-register: {e}")
        print(f"      Node will be registered when user logs in")


async def shutdown():
    """
    Shutdown routine - called when app is unloaded
    """
    print("🔌 Node Connection Manager: Shutting down...")
    
    manager = get_node_manager()
    await manager.shutdown()
    
    print("✅ Node Connection Manager: Shutdown complete")


# For backward compatibility - export the manager
def get_manager():
    """Get the global node manager instance"""
    return get_node_manager()
