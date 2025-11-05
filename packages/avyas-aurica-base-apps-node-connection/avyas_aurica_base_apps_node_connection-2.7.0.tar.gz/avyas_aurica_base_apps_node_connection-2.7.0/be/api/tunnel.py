"""
Tunnel status API endpoint for node-connection app
"""
from fastapi import APIRouter, Request, HTTPException
import logging
import sys
from pathlib import Path

# Add app directory to path for imports
node_be_dir = Path(__file__).parent.parent
if str(node_be_dir) not in sys.path:
    sys.path.insert(0, str(node_be_dir))

from tunnel_manager import get_tunnel_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/tunnel-status")
async def get_tunnel_status(request: Request):
    """
    Get tunnel status for the current user.
    
    This checks if there's an active tunnel connection.
    """
    try:
        # Get user from request (set by auth middleware)
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        user_id = user.get("user_id") or user.get("sub") or user.get("username", "unknown")
        
        tunnel_mgr = get_tunnel_manager()
        status = await tunnel_mgr.get_tunnel_status(user_id)
        
        return {
            "success": True,
            **status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tunnel status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/disconnect-tunnel")
async def disconnect_tunnel(request: Request):
    """
    Disconnect the tunnel for the current user.
    """
    try:
        # Get user from request (set by auth middleware)
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        user_id = user.get("user_id") or user.get("sub") or user.get("username", "unknown")
        
        logger.info(f"🔌 Disconnect tunnel requested for user {user_id}")
        
        tunnel_mgr = get_tunnel_manager()
        await tunnel_mgr.stop_tunnel(user_id)
        
        return {
            "success": True,
            "message": "Tunnel disconnected successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting tunnel: {e}")
        raise HTTPException(status_code=500, detail=str(e))
