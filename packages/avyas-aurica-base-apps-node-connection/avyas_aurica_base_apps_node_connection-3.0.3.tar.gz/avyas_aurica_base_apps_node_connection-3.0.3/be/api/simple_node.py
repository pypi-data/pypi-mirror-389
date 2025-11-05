"""
Simple Node Connection API

Just 3 endpoints:
1. GET /api/status - Get connection status
2. POST /api/reconnect - Reconnect tunnel
3. POST /api/disconnect - Disconnect tunnel
"""
from fastapi import APIRouter, Request, HTTPException
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter()

# Import tunnel client
base_be = Path(__file__).parent.parent.parent.parent.parent / "aurica-base-be"
if str(base_be) not in sys.path:
    sys.path.insert(0, str(base_be))

from src.simple_tunnel_client import get_tunnel_status, stop_tunnel, start_tunnel


@router.get("/status")
async def get_status(request: Request):
    """
    Get tunnel connection status.
    
    Returns:
        {
            "connected": bool,
            "cloud_url": str,
            "local_url": str,
            "user_id": str
        }
    """
    try:
        # Get user from auth middleware
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        user_id = user.get("user_id") or user.get("sub") or user.get("username", "unknown")
        
        status = get_tunnel_status()
        
        return {
            "success": True,
            "user_id": user_id,
            **status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reconnect")
async def reconnect(request: Request):
    """
    Reconnect tunnel.
    
    Stops current connection and starts a new one.
    """
    try:
        # Get user from auth middleware
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        user_id = user.get("user_id") or user.get("sub") or user.get("username", "unknown")
        
        logger.info(f"🔄 Reconnect requested by {user_id}")
        
        # Get auth token from request
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="No auth token")
        
        auth_token = auth_header.replace("Bearer ", "")
        
        # Stop current tunnel
        await stop_tunnel()
        
        # Start new tunnel
        import os
        cloud_url = os.getenv("CLOUD_URL", "https://api.oneaurica.com")
        local_url = f"http://localhost:{os.getenv('PORT', '8000')}"
        
        await start_tunnel(
            auth_token=auth_token,
            cloud_url=cloud_url,
            local_url=local_url
        )
        
        logger.info(f"✅ Tunnel reconnected for {user_id}")
        
        return {
            "success": True,
            "message": "Tunnel reconnecting..."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reconnecting: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/disconnect")
async def disconnect(request: Request):
    """
    Disconnect tunnel.
    """
    try:
        # Get user from auth middleware
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        user_id = user.get("user_id") or user.get("sub") or user.get("username", "unknown")
        
        logger.info(f"🔌 Disconnect requested by {user_id}")
        
        await stop_tunnel()
        
        return {
            "success": True,
            "message": "Tunnel disconnected"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting: {e}")
        raise HTTPException(status_code=500, detail=str(e))
