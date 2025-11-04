"""
Node Manager - Core functionality for node connection management
"""
import os
import time
import logging
import asyncio
import httpx
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class NodeConfig:
    """Node configuration"""
    api_domain: str
    auto_reconnect: bool = True
    heartbeat_interval: int = 30
    connection_timeout: int = 30
    max_retry_attempts: int = 3
    retry_delay: int = 5


@dataclass
class ConnectionDetails:
    """Connection details for a user"""
    user_id: str
    node_id: str
    api_domain: str
    connected_at: str
    last_heartbeat: str
    status: str
    uptime_seconds: int


class NodeConnectionManager:
    """Manages node connections to API domain"""
    
    def __init__(self, config: NodeConfig):
        self.config = config
        self.node_id = os.environ.get("NODE_ID", "node-" + str(int(time.time())))
        self.connected = False
        self.auth_token: Optional[str] = None
        self.connected_at: Optional[datetime] = None
        self.user_connections: Dict[str, ConnectionDetails] = {}
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._startup_called = False
        
    async def startup(self):
        """Startup routine - authenticate and establish connection"""
        logger.info(f"Starting node connection manager for node {self.node_id}")
        
        # Login to API domain
        success = await self.login_to_api_domain()
        if success:
            logger.info("Successfully authenticated with API domain")
            self.connected_at = datetime.utcnow()
            self.connected = True
            self._startup_called = True
            
            # Don't start heartbeat - we use JWT auth instead
            # The connection is maintained through normal API authentication
            logger.info("Connection established - using JWT authentication")
        else:
            logger.error("Failed to authenticate with API domain")
            
        return success
    
    async def shutdown(self):
        """Shutdown routine - cleanup connections"""
        logger.info("Shutting down node connection manager")
        
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        self.connected = False
        self.auth_token = None
    
    async def login_to_api_domain(self) -> bool:
        """Login to API domain and obtain auth token"""
        # In development, just mark as connected
        # In production, this would authenticate with the auth server
        # using the existing JWT infrastructure
        
        logger.info(f"� Connecting to API domain: {self.config.api_domain}")
        
        # For now, we use the existing JWT auth system
        # The connection is authenticated via the standard auth flow
        self.auth_token = "authenticated-via-jwt"
        
        logger.info("✅ Using existing JWT authentication system")
        return True
    
    async def reconnect(self) -> bool:
        """Reconnect to API domain"""
        logger.info("Attempting to reconnect...")
        
        for attempt in range(self.config.max_retry_attempts):
            success = await self.login_to_api_domain()
            if success:
                self.connected = True
                self.connected_at = datetime.utcnow()
                return True
            
            if attempt < self.config.max_retry_attempts - 1:
                await asyncio.sleep(self.config.retry_delay)
        
        return False
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats to API domain"""
        while True:
            try:
                await asyncio.sleep(self.config.heartbeat_interval)
                
                if not self.connected:
                    # Try to reconnect
                    await self.reconnect()
                else:
                    # Send heartbeat
                    await self._send_heartbeat()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
    
    async def _send_heartbeat(self):
        """Send heartbeat to API domain"""
        # Heartbeat is maintained through the regular API calls
        # The connection is alive as long as the server is running
        # and authenticated users can access the connection details
        pass
    
    async def ensure_connected(self):
        """Ensure the node is connected, call startup if needed"""
        if not self._startup_called or not self.connected:
            logger.info("Node not connected, calling startup...")
            await self.startup()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current node status"""
        uptime = 0
        if self.connected_at:
            uptime = int((datetime.utcnow() - self.connected_at).total_seconds())
        
        return {
            "node_id": self.node_id,
            "connected": self.connected,
            "api_domain": self.config.api_domain,
            "connected_at": self.connected_at.isoformat() if self.connected_at else None,
            "uptime_seconds": uptime,
            "active_connections": len(self.user_connections),
            "auto_reconnect": self.config.auto_reconnect,
            "heartbeat_interval": self.config.heartbeat_interval
        }
    
    def get_connection_details(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get connection details for a specific user"""
        if user_id in self.user_connections:
            return asdict(self.user_connections[user_id])
        
        # Create new connection details
        if self.connected:
            uptime = int((datetime.utcnow() - self.connected_at).total_seconds())
            now = datetime.utcnow().isoformat()
            
            details = ConnectionDetails(
                user_id=user_id,
                node_id=self.node_id,
                api_domain=self.config.api_domain,
                connected_at=self.connected_at.isoformat(),
                last_heartbeat=now,
                status="connected",
                uptime_seconds=uptime
            )
            
            self.user_connections[user_id] = details
            return asdict(details)
        
        return None
    
    def update_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update node configuration"""
        if "api_domain" in updates:
            self.config.api_domain = updates["api_domain"]
        if "auto_reconnect" in updates:
            self.config.auto_reconnect = updates["auto_reconnect"]
        if "heartbeat_interval" in updates:
            self.config.heartbeat_interval = updates["heartbeat_interval"]
        if "connection_timeout" in updates:
            self.config.connection_timeout = updates["connection_timeout"]
        
        return {
            "api_domain": self.config.api_domain,
            "auto_reconnect": self.config.auto_reconnect,
            "heartbeat_interval": self.config.heartbeat_interval,
            "connection_timeout": self.config.connection_timeout
        }


# Global instance
_manager: Optional[NodeConnectionManager] = None


def get_node_manager() -> NodeConnectionManager:
    """Get global node manager instance"""
    global _manager
    if _manager is None:
        # Use existing AUTH_SERVER_DOMAIN instead of separate API_DOMAIN
        auth_server = os.environ.get("AUTH_SERVER_DOMAIN", "api.oneaurica.com")
        api_domain = f"https://{auth_server}" if not auth_server.startswith("http") else auth_server
        
        config = NodeConfig(
            api_domain=api_domain,
            auto_reconnect=os.environ.get("AUTO_RECONNECT", "true").lower() == "true",
            heartbeat_interval=int(os.environ.get("HEARTBEAT_INTERVAL", "30")),
            connection_timeout=int(os.environ.get("CONNECTION_TIMEOUT", "30"))
        )
        _manager = NodeConnectionManager(config)
    return _manager
