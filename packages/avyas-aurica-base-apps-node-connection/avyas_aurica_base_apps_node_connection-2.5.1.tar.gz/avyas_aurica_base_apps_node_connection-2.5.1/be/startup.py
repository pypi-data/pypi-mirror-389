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
        # Check if we're on the production API domain
        current_host = os.environ.get("HOST", "localhost")
        is_production_api = "api.oneaurica.com" in current_host or "oneaurica.com" in os.environ.get("HOSTNAME", "")
        
        # Initialize registry
        registry = initialize_registry()
        print("✅ Node registry initialized")
        
        # If we're on the API domain, we only serve as registry - don't register ourselves
        if is_production_api:
            print("   ℹ️  Running on production API domain")
            print("   📋 Serving as node registry for execution nodes")
            print("   ✅ Available endpoints:")
            print("      - GET  /node-connection/api/available_nodes/my-nodes")
            print("      - POST /node-connection/api/available_nodes/connect-tunnel")
            print("      - POST /node-connection/api/available_nodes/disconnect-tunnel")
            return True
        
        # Initialize node manager (execution node only)
        manager = get_node_manager()
        success = await manager.startup()
        
        if success:
            print("✅ Node Connection Manager: Successfully registered with API domain")
            status = manager.get_status()
            print(f"   📍 Node ID: {status['node_id']}")
            print(f"   🌐 API Domain: {status['api_domain']}")
            print(f"   🟢 Status: {'Registered' if status.get('registered') else 'Not Registered'}")
            print(f"   � Authorized Users: {', '.join(status.get('authorized_users', []))}")
            print(f"   🔗 Local URL: {status.get('local_url', 'N/A')}")
            print("   ⏸️  No active tunnel - will establish when user logs in")
            
            # If this is an execution node (not the API domain itself), register it
            await register_with_api_domain(manager)
        else:
            print("⚠️  Node Connection Manager: Failed to register with API domain")
        
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
        
        from auto_register import register_execution_node, IS_EXECUTION_NODE
        
        if not IS_EXECUTION_NODE:
            print(f"   ⏭️  Skipping tunnel - not an execution node")
            return
        
        # Schedule background task to auto-connect tunnel when user is authenticated
        print(f"   ℹ️  Scheduling auto-tunnel connection on user authentication")
        asyncio.create_task(_auto_connect_tunnel())
            
    except Exception as e:
        print(f"   ⚠️  Could not schedule auto-registration: {e}")
        print(f"      Tunnel can still be established manually")


async def _auto_connect_tunnel():
    """
    Background task that automatically establishes tunnel when user authenticates.
    Runs continuously and reconnects if tunnel drops.
    """
    from pathlib import Path
    import time
    
    # Wait for server to fully start
    await asyncio.sleep(3)
    
    try:
        # Import dependencies
        dt_path = Path(__file__).parent.parent.parent / "digital-twin" / "be"
        if str(dt_path) not in sys.path:
            sys.path.insert(0, str(dt_path))
        
        from auto_register import register_execution_node, IS_EXECUTION_NODE
        
        if not IS_EXECUTION_NODE:
            return
        
        base_be_path = Path(__file__).parent.parent.parent.parent / "aurica-base-be"
        if str(base_be_path) not in sys.path:
            sys.path.insert(0, str(base_be_path))
        
        from src.persistent_auth import load_auth_token
        
        connected_user = None
        checked_saved_token = False
        
        # Check continuously for authenticated users
        while True:
            try:
                # First, check for saved auth token (on first iteration only)
                if not checked_saved_token:
                    checked_saved_token = True
                    saved_auth = load_auth_token()
                    
                    if saved_auth:
                        user_id = saved_auth.get('user_id')
                        auth_token = saved_auth.get('auth_token')
                        
                        if user_id and auth_token:
                            print(f"🔌 Restoring tunnel from saved auth: {user_id}")
                            print(f"🔌 Auto-establishing tunnel to cloud...")
                            
                            # Use the new tunnel manager for reliable connection
                            try:
                                from tunnel_manager import get_tunnel_manager
                                tunnel_mgr = get_tunnel_manager()
                                success = await tunnel_mgr.start_tunnel(user_id, auth_token)
                                
                                if success:
                                    print(f"✅ Tunnel auto-connected from saved auth!")
                                    connected_user = user_id
                                else:
                                    print(f"⚠️  Tunnel connection failed, will retry...")
                            except Exception as e:
                                print(f"⚠️  Error establishing tunnel: {e}")
                                # Fallback to old method
                                success = await register_execution_node(user_id, auth_token)
                                if success:
                                    print(f"✅ Tunnel auto-connected from saved auth (fallback)!")
                                    connected_user = user_id
                    else:
                        print(f"ℹ️  No saved auth token found, waiting for user login...")
                
                # Also check active sessions (for fresh logins)
                from src.aurica_auth import get_session_manager
                session_manager = get_session_manager()
                
                # Check all active sessions
                if hasattr(session_manager, 'sessions') and session_manager.sessions:
                    for session_id, session_data in list(session_manager.sessions.items()):
                        if isinstance(session_data, dict):
                            user_id = session_data.get('user_id')
                            auth_token = session_data.get('token')
                            
                            if user_id and auth_token and user_id != connected_user:
                                print(f"🔌 Found authenticated user: {user_id}")
                                print(f"🔌 Auto-establishing tunnel to cloud...")
                                
                                # Use the new tunnel manager for reliable connection
                                try:
                                    from tunnel_manager import get_tunnel_manager
                                    tunnel_mgr = get_tunnel_manager()
                                    success = await tunnel_mgr.start_tunnel(user_id, auth_token)
                                    
                                    if success:
                                        print(f"✅ Tunnel auto-connected for {user_id}!")
                                        connected_user = user_id
                                        # Keep checking to maintain connection
                                    else:
                                        print(f"⚠️  Tunnel connection failed, will retry...")
                                except Exception as e:
                                    print(f"⚠️  Error establishing tunnel: {e}")
                                    # Fallback to old method
                                    success = await register_execution_node(user_id, auth_token)
                                    if success:
                                        print(f"✅ Tunnel auto-connected for {user_id} (fallback)!")
                                        connected_user = user_id
                
                # Check every 15 seconds
                await asyncio.sleep(15)
                
            except Exception as e:
                # Silently continue on errors
                await asyncio.sleep(15)
                
    except Exception as e:
        # Background task - don't crash server
        pass


async def shutdown():
    """
    Shutdown routine - called when app is unloaded
    """
    print("🔌 Node Connection Manager: Shutting down...")
    
    # Shutdown node manager
    manager = get_node_manager()
    await manager.shutdown()
    
    # Shutdown tunnel manager
    try:
        from tunnel_manager import get_tunnel_manager
        tunnel_mgr = get_tunnel_manager()
        await tunnel_mgr.shutdown()
        print("✅ Tunnel Manager: Shutdown complete")
    except Exception as e:
        print(f"⚠️  Error shutting down tunnel manager: {e}")
    
    print("✅ Node Connection Manager: Shutdown complete")


# For backward compatibility - export the manager
def get_manager():
    """Get the global node manager instance"""
    return get_node_manager()
