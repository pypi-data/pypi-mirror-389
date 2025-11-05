"""
Simple Startup handler for node-connection app
Automatically called when the app is loaded
"""

import asyncio
import os
import logging
from pathlib import Path
import json
import sys

logger = logging.getLogger(__name__)


async def startup():
    """
    Start node connection on app startup.
    
    1. Load auth token from last_auth.json
    2. Start P2P node client (registration + heartbeat)
    3. That's it!
    """
    try:
        print("🔌 Node Connection: Starting P2P node registration...")
        
        # Get auth token from environment or last_auth.json
        auth_token = os.getenv("AUTH_TOKEN")
        
        if not auth_token:
            # Try to load from last_auth.json
            auth_file = Path(__file__).parent.parent.parent.parent / "aurica-base-be" / "data" / "last_auth.json"
            
            if auth_file.exists():
                with open(auth_file, 'r') as f:
                    auth_data = json.load(f)
                    auth_token = auth_data.get("auth_token") or auth_data.get("access_token")
                    print("   📋 Loaded auth token from last_auth.json")
            else:
                print("   ⚠️  No auth token found. Node will not register.")
                print("   ⚠️  Please set AUTH_TOKEN env var or ensure last_auth.json exists")
                return False
        
        if not auth_token:
            print("   ⚠️  No auth token available. Node will not register.")
            return False
        
        # Import and start P2P client
        base_be = Path(__file__).parent.parent.parent.parent / "aurica-base-be"
        if str(base_be) not in sys.path:
            sys.path.insert(0, str(base_be))
        
        from src.p2p_node_client import start_p2p_client
        from src.simple_tunnel_client import start_tunnel
        
        # Get configuration
        cloud_url = os.getenv("CLOUD_URL", "https://api.oneaurica.com")
        local_port = int(os.getenv("PORT", "8000"))
        local_ip = os.getenv("LOCAL_IP", "localhost")
        local_url = f"http://{local_ip}:{local_port}"
        
        # Start P2P client in background (for P2P connections)
        await start_p2p_client(
            auth_token=auth_token,
            cloud_url=cloud_url,
            local_port=local_port,
            local_ip=local_ip
        )
        
        # Start Tunnel client in background (for cloud proxying)
        await start_tunnel(
            auth_token=auth_token,
            cloud_url=cloud_url,
            local_url=local_url
        )
        
        print("✅ Node connection started with dual mode")
        print(f"   🔗 Cloud: {cloud_url}")
        print(f"   🏠 Local: {local_url}")
        print("   📡 P2P: Registered for direct browser connections")
        print("   🌐 Tunnel: Connected for cloud-proxied requests")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to start node connection: {e}")
        import traceback
        traceback.print_exc()
        return False


async def shutdown():
    """
    Shutdown routine - called when app is unloaded
    """
    print("🔌 Node Connection Manager: Shutting down...")
    
    try:
        # Unregister from cloud
        base_be = Path(__file__).parent.parent.parent.parent / "aurica-base-be"
        if str(base_be) not in sys.path:
            sys.path.insert(0, str(base_be))
        
        from src.p2p_node_client import stop_p2p_client
        from src.simple_tunnel_client import stop_tunnel
        
        await stop_p2p_client()
        await stop_tunnel()
        
        print("✅ Node disconnected (P2P and Tunnel)")
    except Exception as e:
        print(f"⚠️ Error during shutdown: {e}")
    
    print("✅ Node Connection Manager: Shutdown complete")
