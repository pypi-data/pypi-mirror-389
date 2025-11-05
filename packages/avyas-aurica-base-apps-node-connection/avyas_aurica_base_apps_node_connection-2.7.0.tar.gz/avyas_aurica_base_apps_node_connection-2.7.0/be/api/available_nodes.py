"""
Node availability and tunnel management endpoints
"""
from fastapi import APIRouter, HTTPException, Request
from typing import Dict, List, Optional
from pydantic import BaseModel
import logging
import sys
from pathlib import Path

# Add app directory to path for imports
node_be_dir = Path(__file__).parent.parent
if str(node_be_dir) not in sys.path:
    sys.path.insert(0, str(node_be_dir))

from node_registry import get_registry
from tunnel_manager import get_tunnel_manager

logger = logging.getLogger(__name__)

router = APIRouter()


class TunnelRequest(BaseModel):
    """Request to establish tunnel to a node"""
    node_id: str


@router.get("/my-nodes")
async def get_my_available_nodes(request: Request):
    """
    Get list of execution nodes available to the authenticated user.
    
    This checks which nodes have registered with this user in their
    authorized_users list.
    """
    try:
        # Get user from request (set by auth middleware)
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        user_id = user.get("user_id") or user.get("sub") or user.get("username", "unknown")
        
        logger.info(f"🔍 Fetching available nodes for user: {user_id}")
        
        # Get registry
        registry = get_registry()
        registry.load_registry()
        
        # Get user's nodes
        user_nodes = registry.get_user_nodes(user_id)
        
        if not user_nodes:
            return {
                "success": True,
                "nodes": [],
                "count": 0,
                "message": "No execution nodes available. Start your local server to register a node."
            }
        
        # Check tunnel status for each node
        tunnel_mgr = get_tunnel_manager()
        
        nodes_with_status = []
        for node in user_nodes:
            node_id = node.get("node_id")
            tunnel_status = await tunnel_mgr.get_tunnel_status(user_id, node_id)
            
            nodes_with_status.append({
                **node,
                "tunnel_connected": tunnel_status.get("connected", False),
                "tunnel_status": tunnel_status.get("status", "not_connected")
            })
        
        return {
            "success": True,
            "nodes": nodes_with_status,
            "count": len(nodes_with_status),
            "message": f"Found {len(nodes_with_status)} available node(s)"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching available nodes: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connect-tunnel")
async def connect_tunnel(tunnel_request: TunnelRequest, request: Request):
    """
    Establish tunnel connection to a specific execution node.
    
    This is called when user accesses chat-app and needs to connect
    to their execution node.
    """
    try:
        # Get user from request (set by auth middleware)
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        user_id = user.get("user_id") or user.get("sub") or user.get("username", "unknown")
        node_id = tunnel_request.node_id
        
        logger.info(f"🔌 Tunnel connection requested: user={user_id}, node={node_id}")
        
        # Verify user has access to this node
        registry = get_registry()
        registry.load_registry()
        
        user_nodes = registry.get_user_nodes(user_id)
        node_info = next((n for n in user_nodes if n.get("node_id") == node_id), None)
        
        if not node_info:
            raise HTTPException(
                status_code=403, 
                detail=f"You don't have access to node {node_id}"
            )
        
        # Get auth token from request
        auth_token = request.headers.get("authorization", "").replace("Bearer ", "")
        if not auth_token:
            raise HTTPException(status_code=401, detail="No authentication token provided")
        
        # Establish tunnel
        tunnel_mgr = get_tunnel_manager()
        
        # Use cloud URL from environment or default
        import os
        cloud_url = os.getenv("CLOUD_URL", "https://api.oneaurica.com")
        
        success = await tunnel_mgr.start_tunnel(
            user_id=user_id,
            node_id=node_id,
            auth_token=auth_token,
            cloud_url=cloud_url
        )
        
        if success:
            return {
                "success": True,
                "message": f"Tunnel established to node {node_id}",
                "node_id": node_id,
                "node_name": node_info.get("node_name"),
                "node_url": node_info.get("node_url")
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to establish tunnel connection"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error connecting tunnel: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/disconnect-tunnel")
async def disconnect_tunnel(tunnel_request: TunnelRequest, request: Request):
    """
    Disconnect tunnel from a specific execution node.
    """
    try:
        # Get user from request (set by auth middleware)
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        user_id = user.get("user_id") or user.get("sub") or user.get("username", "unknown")
        node_id = tunnel_request.node_id
        
        logger.info(f"🔌 Tunnel disconnection requested: user={user_id}, node={node_id}")
        
        # Disconnect tunnel
        tunnel_mgr = get_tunnel_manager()
        await tunnel_mgr.stop_tunnel(user_id, node_id)
        
        return {
            "success": True,
            "message": f"Tunnel disconnected from node {node_id}",
            "node_id": node_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error disconnecting tunnel: {e}")
        raise HTTPException(status_code=500, detail=str(e))
