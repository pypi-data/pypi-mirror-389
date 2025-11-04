"""
Node Connection API endpoints
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Dict, Any, Optional
from pydantic import BaseModel
import logging
import sys
from pathlib import Path

# Add app directory to path for imports
node_be_dir = Path(__file__).parent.parent
if str(node_be_dir) not in sys.path:
    sys.path.insert(0, str(node_be_dir))

from node_manager import get_node_manager
from node_registry import get_registry

logger = logging.getLogger(__name__)

router = APIRouter()


class NodeConfigUpdate(BaseModel):
    """Node configuration update request"""
    api_domain: Optional[str] = None
    auto_reconnect: Optional[bool] = None
    heartbeat_interval: Optional[int] = None
    connection_timeout: Optional[int] = None


@router.get("/health")
async def health_check():
    """Health check endpoint (public)"""
    return {
        "status": "healthy",
        "service": "node-connection",
        "version": "1.0.0"
    }


@router.get("/status")
async def get_status(request: Request):
    """Get current node connection status"""
    try:
        manager = get_node_manager()
        
        # Ensure the node is connected (auto-startup if needed)
        await manager.ensure_connected()
        
        status = manager.get_status()
        
        return {
            "success": True,
            "status": status
        }
    except Exception as e:
        logger.error(f"Error getting node status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connection-details")
async def get_connection_details(request: Request):
    """Get connection details for authenticated user"""
    try:
        # Get user from request (set by auth middleware)
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        user_id = user.get("user_id") or user.get("sub") or user.get("username", "unknown")
        
        manager = get_node_manager()
        
        # Ensure the node is connected (auto-startup if needed)
        await manager.ensure_connected()
        
        details = manager.get_connection_details(user_id)
        
        if not details:
            raise HTTPException(status_code=503, detail="Node not connected")
        
        return {
            "success": True,
            "connection_details": details
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting connection details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reconnect")
async def reconnect_node(request: Request):
    """Reconnect to API domain"""
    try:
        manager = get_node_manager()
        success = await manager.reconnect()
        
        if success:
            return {
                "success": True,
                "message": "Successfully reconnected to API domain",
                "status": manager.get_status()
            }
        else:
            raise HTTPException(status_code=503, detail="Failed to reconnect")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reconnecting node: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config")
async def update_config(config_update: NodeConfigUpdate, request: Request):
    """Update node configuration"""
    try:
        manager = get_node_manager()
        
        # Convert to dict, excluding None values
        updates = config_update.dict(exclude_none=True)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No configuration updates provided")
        
        updated_config = manager.update_config(updates)
        
        return {
            "success": True,
            "message": "Configuration updated successfully",
            "config": updated_config
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restart")
async def restart_node(request: Request):
    """
    Restart this specific node connection (CLIENT-SIDE ONLY)
    
    IMPORTANT: This only resets this particular node's connection state and reconnects.
    It NEVER restarts the server process. Each node can be restarted independently.
    Safe for production use.
    """
    try:
        logger.info("Node connection restart requested by user")
        
        manager = get_node_manager()
        
        # Reset connection state for this node (client-side only)
        logger.info(f"Resetting connection state for node {manager.node_id}...")
        manager.connected = False
        manager.connected_at = None
        manager.user_connections.clear()
        manager._startup_called = False
        
        # Reconnect this node
        logger.info("Reconnecting node to API domain...")
        success = await manager.reconnect()
        
        if success:
            logger.info(f"Node {manager.node_id} successfully restarted")
            return {
                "success": True,
                "message": f"Node {manager.node_id} connection restarted successfully",
                "status": manager.get_status()
            }
        else:
            raise HTTPException(
                status_code=503, 
                detail="Failed to reconnect after restart"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restarting node connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/execution-node-status")
async def get_execution_node_status(request: Request):
    """
    Get the status of the user's local execution node.
    
    This endpoint checks the digital-twin discovery service to find
    the user's execution node and fetch its status remotely.
    """
    try:
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        user_id = user.get("user_id") or user.get("sub") or user.get("username", "unknown")
        
        # Try to discover the execution node
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Check discovery service
                base_url = str(request.base_url).rstrip('/')
                discovery_url = f"{base_url}/digital-twin/api/direct_connection/discover/{user_id}"
                
                logger.info(f"Checking discovery service for user {user_id}: {discovery_url}")
                
                discovery_response = await client.get(discovery_url)
                
                if discovery_response.status_code == 200:
                    discovery_data = discovery_response.json()
                    
                    if discovery_data.get("found"):
                        # Node is registered, try to get its status
                        node_url = discovery_data.get("local_url", "").rstrip('/')
                        
                        try:
                            # Try to reach the execution node's status endpoint
                            node_status_url = f"{node_url}/node-connection/api/node/status"
                            
                            # Get auth token to authenticate with execution node
                            auth_token = request.headers.get("authorization", "")
                            
                            node_response = await client.get(
                                node_status_url,
                                headers={"Authorization": auth_token} if auth_token else {},
                                timeout=5.0
                            )
                            
                            if node_response.status_code == 200:
                                node_data = node_response.json()
                                return {
                                    "success": True,
                                    "execution_node_found": True,
                                    "execution_node_reachable": True,
                                    "execution_node_url": node_url,
                                    "status": node_data.get("status", {}),
                                    "message": "Your execution node is online and reachable"
                                }
                            else:
                                # Registered but not reachable
                                return {
                                    "success": True,
                                    "execution_node_found": True,
                                    "execution_node_reachable": False,
                                    "execution_node_url": node_url,
                                    "status": None,
                                    "message": "Your execution node is registered but not currently reachable"
                                }
                        except Exception as e:
                            logger.warning(f"Could not reach execution node: {e}")
                            return {
                                "success": True,
                                "execution_node_found": True,
                                "execution_node_reachable": False,
                                "execution_node_url": node_url,
                                "status": None,
                                "message": "Your execution node is registered but not currently reachable"
                            }
                    else:
                        # Not registered
                        return {
                            "success": True,
                            "execution_node_found": False,
                            "execution_node_reachable": False,
                            "status": None,
                            "message": "Your execution node is not currently registered. Start your local server to register."
                        }
                else:
                    # Discovery service not available
                    return {
                        "success": True,
                        "execution_node_found": False,
                        "execution_node_reachable": False,
                        "status": None,
                        "message": "Discovery service unavailable. Cannot check execution node status."
                    }
        except Exception as e:
            logger.error(f"Error checking execution node: {e}")
            return {
                "success": True,
                "execution_node_found": False,
                "execution_node_reachable": False,
                "status": None,
                "message": f"Error checking execution node: {str(e)}"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in execution node status check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/register")
async def register_node(request: Request):
    """
    Register an execution node with the API domain.
    
    This endpoint is called by execution nodes at startup to register
    themselves so they can be discovered and managed remotely.
    """
    try:
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        user_id = user.get("user_id") or user.get("sub") or user.get("username", "unknown")
        
        # Get request body
        body = await request.json()
        
        node_id = body.get("node_id")
        node_url = body.get("node_url")
        
        if not node_id or not node_url:
            raise HTTPException(status_code=400, detail="node_id and node_url are required")
        
        # Register in registry
        registry = get_registry()
        
        node_data = {
            "node_id": node_id,
            "node_url": node_url,
            "connection_type": body.get("connection_type", "execution"),
            "capabilities": body.get("capabilities", []),
            "version": body.get("version", "1.0.0")
        }
        
        registered_node = registry.register_node(user_id, node_data)
        
        logger.info(f"✅ Registered node {node_id} for user {user_id}")
        
        return {
            "success": True,
            "message": "Node registered successfully",
            "node": registered_node
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering node: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/heartbeat")
async def node_heartbeat(request: Request):
    """
    Heartbeat endpoint for nodes to maintain their registration.
    
    Nodes should call this periodically (e.g., every 60 seconds) to
    indicate they're still online.
    """
    try:
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        user_id = user.get("user_id") or user.get("sub") or user.get("username", "unknown")
        
        body = await request.json()
        node_id = body.get("node_id")
        
        if not node_id:
            raise HTTPException(status_code=400, detail="node_id is required")
        
        registry = get_registry()
        success = registry.update_node_heartbeat(user_id, node_id)
        
        if success:
            return {
                "success": True,
                "message": "Heartbeat received"
            }
        else:
            raise HTTPException(status_code=404, detail="Node not registered")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing heartbeat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_user_nodes(request: Request):
    """
    List all nodes registered by the authenticated user.
    
    Returns information about all execution nodes owned by this user,
    including their status (online/offline).
    
    This now queries the digital-twin discovery service for registered nodes.
    """
    try:
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        user_id = user.get("user_id") or user.get("sub") or user.get("username", "unknown")
        
        # Query the digital-twin discovery service for all registered execution nodes
        import httpx
        
        nodes = []
        
        try:
            # Get base URL (could be local or remote)
            base_url = str(request.base_url).rstrip('/')
            list_url = f"{base_url}/digital-twin/api/direct_connection/list"
            
            # Get auth token from request to pass through
            auth_token = request.headers.get("authorization", "")
            headers = {}
            if auth_token:
                headers["Authorization"] = auth_token
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(list_url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    all_nodes = data.get("nodes", [])
                    
                    # Filter to only this user's nodes
                    for node in all_nodes:
                        if node.get("user_id") == user_id:
                            nodes.append({
                                "node_id": node.get("node_id"),
                                "node_url": node.get("local_url"),
                                "connection_type": "execution",
                                "status": "online",  # If it's in the list, it's online
                                "last_seen": node.get("last_seen"),
                                "registered_at": node.get("last_seen"),
                                "capabilities": []
                            })
                    
                    logger.info(f"Found {len(nodes)} registered execution nodes for user {user_id}")
                else:
                    logger.warning(f"Discovery service returned {response.status_code}")
                    
        except Exception as e:
            logger.warning(f"Could not query discovery service: {e}")
            # Fallback to local registry
            registry = get_registry()
            nodes = registry.get_user_nodes(user_id)
        
        return {
            "success": True,
            "nodes": nodes,
            "count": len(nodes)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing nodes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simple-test")
async def simple_test():
    """Super simple test"""
    return {"test": "works"}


class SelfRegisterRequest(BaseModel):
    """Request body for self-registration"""
    auth_token: Optional[str] = None


@router.post("/self-register-with-api-domain")
async def self_register_with_api_domain(body: Optional[SelfRegisterRequest] = None):
    """
    Register this execution node with the API domain.
    
    This endpoint is called from the local node's frontend to register
    itself with the production API domain, making it visible in the
    node manager on the API domain.
    """
    try:
        # Get current node info
        manager = get_node_manager()
        await manager.ensure_connected()
        status = manager.get_status()
        
        # Get the API domain to register with
        api_domain = manager.config.api_domain
        
        # Check if we're on the API domain itself
        if "localhost" in api_domain or "127.0.0.1" in api_domain:
            return {
                "success": False,
                "message": "Cannot register: Running on API domain itself",
                "is_api_domain": True
            }
        
        # Use localhost as node URL since we're registering from local node
        node_url = "http://localhost:8000"
        
        # Get auth token from body
        auth_token = body.auth_token if body else None
        
        if not auth_token:
            return {
                "success": False,
                "message": "No auth token provided",
                "note": "Frontend needs to pass auth_token in request body"
            }
        
        logger.info(f"🔗 Attempting to register node {status['node_id']} with {api_domain}")
        
        # Register with API domain
        import httpx
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            register_url = f"{api_domain}/node-connection/api/node/register"
            
            logger.info(f"🔗 Registering node {status['node_id']} with {register_url}")
            
            response = await client.post(
                register_url,
                json={
                    "node_id": status['node_id'],
                    "node_url": node_url,
                    "connection_type": status.get('connection_type', 'execution'),
                    "capabilities": ["chat", "digital-twin", "node-connection"],
                    "version": "2.2.0"
                },
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            logger.info(f"📊 Registration response: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Successfully registered node with API domain")
                return {
                    "success": True,
                    "message": "Node registered with API domain successfully",
                    "node": result.get("node", {}),
                    "api_domain": api_domain
                }
            elif response.status_code == 404:
                logger.warning(f"⚠️  Registration endpoint not found on API domain")
                return {
                    "success": False,
                    "message": "Registration endpoint not available on API domain",
                    "status_code": 404,
                    "note": "The API domain needs to be updated with the latest node-connection app that includes the /register endpoint. Please deploy the updated app to the API domain."
                }
            else:
                error_msg = f"Registration failed: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get("detail", error_msg)
                    logger.error(f"❌ Registration failed: {error_msg}")
                except:
                    pass
                
                return {
                    "success": False,
                    "message": error_msg,
                    "status_code": response.status_code
                }
                
    except Exception as e:
        logger.error(f"❌ Error in self-register: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))




@router.get("/test_endpoint")
async def test_endpoint():
    """Test endpoint to verify routing works"""
    return {"message": "Test endpoint works!", "timestamp": "now"}


@router.post("/register-execution-node")
async def register_execution_node_manually(request: Request):
    """
    Manually register this local execution node with the API domain.
    
    This uses the Digital Twin's auto-register mechanism to register
    the node with the discovery service.
    
    Can be called from the UI when user clicks "Register with API" button.
    """
    try:
        # Get user from auth
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        user_id = user.get("user_id") or user.get("sub") or user.get("username", "unknown")
        
        # Get auth token
        auth_token = request.headers.get("authorization", "").replace("Bearer ", "")
        if not auth_token:
            raise HTTPException(status_code=401, detail="No auth token provided")
        
        logger.info(f"Manual registration requested by user {user_id}")
        
        # Import Digital Twin's auto-register
        import sys
        from pathlib import Path
        dt_path = Path(__file__).parent.parent.parent.parent / "digital-twin" / "be"
        if str(dt_path) not in sys.path:
            sys.path.insert(0, str(dt_path))
        
        from auto_register import register_execution_node
        
        # Register the node
        logger.info(f"Calling Digital Twin auto-register for user {user_id}...")
        success = await register_execution_node(user_id, auth_token)
        
        if success:
            logger.info(f"✅ Execution node registered successfully!")
            return {
                "success": True,
                "message": "Execution node registered with API domain successfully",
                "user_id": user_id,
                "note": "Your local node is now discoverable for P2P connections"
            }
        else:
            logger.warning(f"⚠️  Registration returned False - check logs above for details")
            return {
                "success": False,
                "message": "Registration failed",
                "note": "The cloud API (api.oneaurica.com) might not have the digital-twin app installed with the direct_connection endpoints. Check server logs for details.",
                "suggestion": "Deploy the digital-twin app to api.oneaurica.com or verify the /digital-twin/api/direct_connection/register endpoint exists"
            }
            
    except Exception as e:
        logger.error(f"❌ Error in manual registration: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


