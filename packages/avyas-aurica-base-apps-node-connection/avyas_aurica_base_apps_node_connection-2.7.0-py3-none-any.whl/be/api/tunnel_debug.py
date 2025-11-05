"""
Debug endpoint for testing tunnel connection
"""
from fastapi import APIRouter, Request
from pydantic import BaseModel
import asyncio
import os

try:
    from src.aurica_auth import protected, get_current_user
except ImportError:
    def protected(func):
        return func
    def get_current_user(request):
        return type('User', (), {"user_id": "test", "username": "test"})()

router = APIRouter()


class TunnelTestRequest(BaseModel):
    cloud_url: str = "wss://api.oneaurica.com"


@router.post("/test-tunnel")
@protected
async def test_tunnel_connection(req: TunnelTestRequest, request: Request):
    """Test tunnel connection for current user"""
    user = get_current_user(request)
    
    try:
        # Get auth token
        auth_token = request.cookies.get("auth_token") or request.headers.get("authorization", "").replace("Bearer ", "")
        
        if not auth_token:
            return {
                "success": False,
                "error": "No auth token found"
            }
        
        # Import tunnel client
        import sys
        from pathlib import Path
        base_be = Path(__file__).parent.parent.parent.parent.parent / "aurica-base-be"
        if str(base_be) not in sys.path:
            sys.path.insert(0, str(base_be))
        
        from src.tunnel_client import establish_tunnel
        
        # Start tunnel
        print(f"🔌 Testing tunnel connection for {user.username}...")
        asyncio.create_task(establish_tunnel(user.user_id, auth_token, req.cloud_url))
        
        # Give it a moment
        await asyncio.sleep(0.5)
        
        return {
            "success": True,
            "message": "Tunnel connection initiated",
            "user_id": user.user_id,
            "cloud_url": req.cloud_url
        }
        
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@router.get("/check-tunnel")
@protected
async def check_tunnel_status(request: Request):
    """Check if tunnel is connected for current user"""
    user = get_current_user(request)
    
    try:
        import sys
        from pathlib import Path
        base_be = Path(__file__).parent.parent.parent.parent.parent / "aurica-base-be"
        if str(base_be) not in sys.path:
            sys.path.insert(0, str(base_be))
        
        from src.websocket_tunnel import get_tunnel_manager
        
        tunnel_manager = get_tunnel_manager()
        tunnel = await tunnel_manager.get_tunnel(user.user_id)
        
        if tunnel:
            return {
                "connected": True,
                "stats": tunnel.get_stats()
            }
        else:
            return {
                "connected": False,
                "message": "No tunnel found for user"
            }
            
    except Exception as e:
        return {
            "connected": False,
            "error": str(e)
        }
