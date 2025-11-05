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
    2. Start tunnel client
    3. That's it!
    """
    try:
        print("🔌 Node Connection: Starting simplified tunnel...")
        
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
                print("   ⚠️  No auth token found. Tunnel will not start.")
                print("   ⚠️  Please set AUTH_TOKEN env var or ensure last_auth.json exists")
                return False
        
        if not auth_token:
            print("   ⚠️  No auth token available. Tunnel will not start.")
            return False
        
        # Import and start tunnel client
        base_be = Path(__file__).parent.parent.parent.parent / "aurica-base-be"
        if str(base_be) not in sys.path:
            sys.path.insert(0, str(base_be))
        
        from src.simple_tunnel_client import start_tunnel
        
        # Get cloud URL
        cloud_url = os.getenv("CLOUD_URL", "https://api.oneaurica.com")
        local_url = f"http://localhost:{os.getenv('PORT', '8000')}"
        
        # Start tunnel in background
        await start_tunnel(
            auth_token=auth_token,
            cloud_url=cloud_url,
            local_url=local_url
        )
        
        print("✅ Node connection started")
        print(f"   🔗 Connecting to: {cloud_url}")
        print(f"   🏠 Local server: {local_url}")
        print("   📡 Tunnel will auto-connect and proxy requests")
        
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
    print("✅ Node Connection Manager: Shutdown complete")
