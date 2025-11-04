"""
Machine Management API - Endpoints for registering and managing user machines.

Provides APIs for:
- Listing user's machines
- Registering new machines
- Getting machine details
- Updating machine settings
- Deleting machines
- Testing machine connections
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import sys
from pathlib import Path
import logging

# Add parent directories to path for imports
_be_dir = Path(__file__).parent.parent
_base_dir = _be_dir.parent.parent.parent / "aurica-base-be" / "src"
if str(_base_dir) not in sys.path:
    sys.path.insert(0, str(_base_dir))
if str(_be_dir) not in sys.path:
    sys.path.insert(0, str(_be_dir))

# Import auth decorator
from auth_decorators import require_auth

# Import machine registry
from machine_registry import get_machine_registry

logger = logging.getLogger(__name__)
router = APIRouter()


# Request/Response Models

class ConnectionDetails(BaseModel):
    """Connection details for a machine."""
    url: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    ssh_key: Optional[str] = None
    additional: Optional[Dict[str, Any]] = None


class MachineMetadata(BaseModel):
    """Machine metadata."""
    os: Optional[str] = None
    hostname: Optional[str] = None
    ip: Optional[str] = None
    capabilities: Optional[List[str]] = None
    additional: Optional[Dict[str, Any]] = None


class RegisterMachineRequest(BaseModel):
    """Request to register a new machine."""
    name: str = Field(..., description="Human-readable machine name")
    connection_type: str = Field(..., description="Connection type: local, ssh, or tunnel")
    connection: ConnectionDetails = Field(..., description="Connection details")
    metadata: Optional[MachineMetadata] = Field(None, description="Optional machine metadata")
    access_level: Optional[str] = Field("full", description="Access level: full, read-only, restricted")
    allowed_apps: Optional[List[str]] = Field(["*"], description="Allowed apps (* for all)")


class UpdateMachineRequest(BaseModel):
    """Request to update machine details."""
    name: Optional[str] = None
    status: Optional[str] = None
    access_level: Optional[str] = None
    allowed_apps: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class MachineResponse(BaseModel):
    """Machine information response."""
    machine_id: str
    name: str
    connection_type: str
    status: str
    registered_at: str
    last_seen: str
    access_level: str
    allowed_apps: List[str]


class MachineDetailResponse(MachineResponse):
    """Detailed machine information response."""
    connection: Dict[str, Any]
    metadata: Dict[str, Any]
    connection_token: Optional[str] = None


class RegisterMachineResponse(BaseModel):
    """Response after successful machine registration."""
    machine_id: str
    status: str
    connection_token: str
    machine: MachineDetailResponse


# API Endpoints

@router.get("/api/machines", response_model=Dict[str, List[Dict[str, Any]]])
async def list_machines(user: Dict = Depends(require_auth)):
    """
    List all machines registered to the authenticated user.
    
    Returns:
        List of machines with summary information
    """
    try:
        user_id = user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        
        registry = get_machine_registry()
        machines = registry.get_user_machines(user_id)
        
        logger.info(f"📋 Listed {len(machines)} machines for user {user_id}")
        
        return {
            "machines": machines,
            "count": len(machines)
        }
    except Exception as e:
        logger.error(f"❌ Error listing machines: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list machines: {str(e)}")


@router.post("/api/machines/register", response_model=RegisterMachineResponse)
async def register_machine(
    request: RegisterMachineRequest,
    user: Dict = Depends(require_auth)
):
    """
    Register a new machine to the authenticated user's account.
    
    Args:
        request: Machine registration details
        
    Returns:
        Registered machine information with connection token
    """
    try:
        user_id = user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        
        # Validate connection type
        valid_types = ["local", "ssh", "tunnel"]
        if request.connection_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid connection_type. Must be one of: {', '.join(valid_types)}"
            )
        
        # Build machine data
        machine_data = {
            "name": request.name,
            "connection_type": request.connection_type,
            "connection": request.connection.dict(exclude_none=True),
            "metadata": request.metadata.dict(exclude_none=True) if request.metadata else {},
            "access_level": request.access_level,
            "allowed_apps": request.allowed_apps
        }
        
        # Register machine
        registry = get_machine_registry()
        result = registry.register_machine(user_id, machine_data)
        
        logger.info(f"✅ Registered machine {result['machine_id']} for user {user_id}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error registering machine: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to register machine: {str(e)}")


@router.get("/api/machines/{machine_id}", response_model=MachineDetailResponse)
async def get_machine(
    machine_id: str,
    user: Dict = Depends(require_auth)
):
    """
    Get detailed information about a specific machine.
    
    Args:
        machine_id: Machine ID
        
    Returns:
        Detailed machine information
    """
    try:
        user_id = user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        
        registry = get_machine_registry()
        machine = registry.get_machine(user_id, machine_id)
        
        if not machine:
            raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
        
        logger.info(f"📋 Retrieved machine {machine_id} for user {user_id}")
        
        return machine
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting machine: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get machine: {str(e)}")


@router.put("/api/machines/{machine_id}", response_model=MachineDetailResponse)
async def update_machine(
    machine_id: str,
    request: UpdateMachineRequest,
    user: Dict = Depends(require_auth)
):
    """
    Update machine settings.
    
    Args:
        machine_id: Machine ID
        request: Fields to update
        
    Returns:
        Updated machine information
    """
    try:
        user_id = user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        
        # Build updates dict (exclude None values)
        updates = request.dict(exclude_none=True)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        registry = get_machine_registry()
        machine = registry.update_machine(user_id, machine_id, updates)
        
        if not machine:
            raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
        
        logger.info(f"✅ Updated machine {machine_id} for user {user_id}")
        
        return machine
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating machine: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update machine: {str(e)}")


@router.delete("/api/machines/{machine_id}")
async def delete_machine(
    machine_id: str,
    user: Dict = Depends(require_auth)
):
    """
    Delete/unregister a machine.
    
    Args:
        machine_id: Machine ID
        
    Returns:
        Deletion status
    """
    try:
        user_id = user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        
        registry = get_machine_registry()
        success = registry.delete_machine(user_id, machine_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
        
        logger.info(f"✅ Deleted machine {machine_id} for user {user_id}")
        
        return {
            "status": "deleted",
            "machine_id": machine_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting machine: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete machine: {str(e)}")


@router.post("/api/machines/{machine_id}/heartbeat")
async def machine_heartbeat(
    machine_id: str,
    connection_token: str
):
    """
    Machine heartbeat endpoint (called by machines to update last_seen).
    
    This endpoint does NOT require user JWT auth - it uses the machine's connection_token.
    
    Args:
        machine_id: Machine ID
        connection_token: Machine's connection token
        
    Returns:
        Status
    """
    try:
        registry = get_machine_registry()
        
        # Verify token
        machine = registry.get_machine_by_token(connection_token)
        if not machine or machine.get("machine_id") != machine_id:
            raise HTTPException(status_code=401, detail="Invalid connection token")
        
        # Update last_seen
        user_id = machine.get("user_id")
        success = registry.update_last_seen(user_id, machine_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Machine not found")
        
        return {
            "status": "ok",
            "machine_id": machine_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error processing heartbeat: {e}")
        raise HTTPException(status_code=500, detail=f"Heartbeat failed: {str(e)}")


@router.post("/api/machines/{machine_id}/test")
async def test_machine_connection(
    machine_id: str,
    user: Dict = Depends(require_auth)
):
    """
    Test connection to a machine.
    
    Args:
        machine_id: Machine ID
        
    Returns:
        Connection test result
    """
    try:
        user_id = user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        
        registry = get_machine_registry()
        machine = registry.get_machine(user_id, machine_id)
        
        if not machine:
            raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
        
        # TODO: Implement actual connection testing based on connection_type
        # For now, just return status
        
        return {
            "status": "connected" if machine.get("status") == "active" else "offline",
            "machine_id": machine_id,
            "last_seen": machine.get("last_seen"),
            "latency_ms": None  # TODO: Implement actual latency check
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error testing machine connection: {e}")
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")
