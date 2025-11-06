"""
Simple Node Connection API - P2P Approach

Endpoints:
1. GET /api/status - Get node registration status
2. POST /api/reconnect - Re-register node with cloud
3. POST /api/disconnect - Unregister node from cloud

Note: This uses P2P registration approach, not persistent tunneling.
The cloud server only stores connection info for browser handshake.
"""
from fastapi import APIRouter, Request, HTTPException
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter()

# Import P2P client
base_be = Path(__file__).parent.parent.parent.parent.parent / "aurica-base-be"
if str(base_be) not in sys.path:
    sys.path.insert(0, str(base_be))

from src.p2p_node_client import get_p2p_client_status, stop_p2p_client, start_p2p_client


@router.get("/status")
async def get_status(request: Request):
    """
    Get node registration status.
    
    Returns:
        {
            "registered": bool,
            "cloud_url": str,
            "local_url": str,
            "node_id": str,
            "user_id": str
        }
    """
    try:
        # Get user from auth middleware
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        user_id = user.get("user_id") or user.get("sub") or user.get("username", "unknown")
        
        status = get_p2p_client_status()
        
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
    Re-register node with cloud.
    
    Stops current registration and starts a new one.
    """
    try:
        # Get user from auth middleware
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        user_id = user.get("user_id") or user.get("sub") or user.get("username", "unknown")
        
        logger.info(f"🔄 Re-registration requested by {user_id}")
        
        # Get auth token from request
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="No auth token")
        
        auth_token = auth_header.replace("Bearer ", "")
        
        # Stop current client
        await stop_p2p_client()
        
        # Start new client
        import os
        cloud_url = os.getenv("CLOUD_URL", "https://api.oneaurica.com")
        local_port = int(os.getenv("PORT", "8000"))
        local_ip = os.getenv("LOCAL_IP", "localhost")
        
        await start_p2p_client(
            auth_token=auth_token,
            cloud_url=cloud_url,
            local_port=local_port,
            local_ip=local_ip
        )
        
        logger.info(f"✅ Node re-registered for {user_id}")
        
        return {
            "success": True,
            "message": "Node re-registering..."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reconnecting: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/disconnect")
async def disconnect(request: Request):
    """
    Unregister node from cloud.
    """
    try:
        # Get user from auth middleware
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        user_id = user.get("user_id") or user.get("sub") or user.get("username", "unknown")
        
        logger.info(f"🔌 Unregister requested by {user_id}")
        
        await stop_p2p_client()
        
        return {
            "success": True,
            "message": "Node unregistered"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting: {e}")
        raise HTTPException(status_code=500, detail=str(e))
