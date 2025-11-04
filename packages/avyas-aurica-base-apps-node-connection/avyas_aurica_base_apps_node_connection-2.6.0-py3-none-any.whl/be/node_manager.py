"""
Node Manager - Core functionality for node connection management

This module handles:
1. Loading authorized users from config
2. Registering this node with API server at startup
3. NO active tunnel - just registration
4. Tunnel is established on-demand when authorized user logs into chat-app
"""
import os
import time
import logging
import asyncio
import httpx
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class NodeConfig:
    """Node configuration"""
    api_domain: str
    authorized_users: List[str]
    node_name: str
    capabilities: List[str]
    max_concurrent_users: int = 5
    auto_reconnect: bool = True
    heartbeat_interval: int = 60
    connection_timeout: int = 30
    max_retry_attempts: int = 3
    retry_delay: int = 5


class NodeConnectionManager:
    """Manages node registration with API domain (no active tunnel yet)"""
    
    def __init__(self, config: NodeConfig):
        self.config = config
        self.node_id = os.environ.get("NODE_ID", "node-" + str(int(time.time())))
        self.registered = False
        self.registered_at: Optional[datetime] = None
        self.local_url = f"http://localhost:{os.environ.get('PORT', '8000')}"
        self._startup_called = False
        self._heartbeat_task: Optional[asyncio.Task] = None
        
    async def startup(self):
        """Startup routine - register this node with API server"""
        logger.info(f"🚀 Starting node registration for node {self.node_id}")
        logger.info(f"📋 Authorized users: {', '.join(self.config.authorized_users)}")
        
        # Register with API domain
        success = await self.register_with_api()
        if success:
            logger.info("✅ Node successfully registered with API domain")
            self.registered_at = datetime.utcnow()
            self.registered = True
            self._startup_called = True
            logger.info(f"🔗 Local URL: {self.local_url}")
            logger.info("⏸️  No active tunnel yet - will connect when user logs in")
            
            # Start heartbeat to keep registration alive
            if self.config.auto_reconnect:
                self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        else:
            logger.warning("⚠️  Failed to register with API domain (will retry)")
            
        return success
    
    async def shutdown(self):
        """Shutdown routine - unregister from API"""
        logger.info("🛑 Shutting down node connection manager")
        
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # Unregister from API
        await self.unregister_from_api()
        
        self.registered = False
    
    async def register_with_api(self) -> bool:
        """Register this node with API domain"""
        try:
            logger.info(f"📡 Registering node with API domain: {self.config.api_domain}")
            
            registration_data = {
                "node_id": self.node_id,
                "node_url": self.local_url,
                "node_name": self.config.node_name,
                "authorized_users": self.config.authorized_users,
                "capabilities": self.config.capabilities,
                "max_concurrent_users": self.config.max_concurrent_users,
                "connection_type": "local",
                "status": "available",
                "registered_at": datetime.utcnow().isoformat(),
                "last_heartbeat": datetime.utcnow().isoformat()
            }
            
            # In development, we'll store locally
            # In production, this would POST to API server
            is_dev = os.environ.get("ENVIRONMENT", "development") == "development"
            
            if is_dev:
                logger.info("🔧 Development mode - storing registration locally")
                self._store_registration_locally(registration_data)
                return True
            else:
                # POST to API server
                async with httpx.AsyncClient(timeout=self.config.connection_timeout) as client:
                    response = await client.post(
                        f"{self.config.api_domain}/api/node-connection/register-node",
                        json=registration_data
                    )
                    
                    if response.status_code == 200:
                        logger.info("✅ Node registered successfully with API")
                        return True
                    else:
                        logger.error(f"❌ Failed to register: {response.status_code} - {response.text}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Error registering node: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _store_registration_locally(self, registration_data: Dict):
        """Store registration locally for development"""
        try:
            # Store for each authorized user
            app_dir = Path(__file__).parent.parent
            registry_dir = app_dir / "data" / "nodes"
            registry_dir.mkdir(parents=True, exist_ok=True)
            
            # Load existing registry
            registry_file = registry_dir / "registry.json"
            if registry_file.exists():
                with open(registry_file, 'r') as f:
                    registry = json.load(f)
            else:
                registry = {}
            
            # Register for each authorized user
            for user_id in self.config.authorized_users:
                if user_id not in registry:
                    registry[user_id] = []
                
                # Remove any existing registration for this node
                registry[user_id] = [n for n in registry[user_id] if n.get("node_id") != self.node_id]
                
                # Add new registration
                registry[user_id].append(registration_data)
            
            # Save registry
            with open(registry_file, 'w') as f:
                json.dump(registry, f, indent=2)
            
            logger.info(f"✅ Registration stored locally for {len(self.config.authorized_users)} users")
            
        except Exception as e:
            logger.error(f"❌ Error storing registration: {e}")
    
    async def unregister_from_api(self):
        """Unregister this node from API domain"""
        try:
            logger.info("📡 Unregistering node from API domain")
            
            is_dev = os.environ.get("ENVIRONMENT", "development") == "development"
            
            if is_dev:
                # Remove from local registry
                app_dir = Path(__file__).parent.parent
                registry_file = app_dir / "data" / "nodes" / "registry.json"
                
                if registry_file.exists():
                    with open(registry_file, 'r') as f:
                        registry = json.load(f)
                    
                    # Remove this node from all users
                    for user_id in registry:
                        registry[user_id] = [n for n in registry[user_id] if n.get("node_id") != self.node_id]
                    
                    with open(registry_file, 'w') as f:
                        json.dump(registry, f, indent=2)
                    
                    logger.info("✅ Node unregistered locally")
            else:
                # POST to API server
                async with httpx.AsyncClient(timeout=self.config.connection_timeout) as client:
                    await client.post(
                        f"{self.config.api_domain}/api/node-connection/unregister-node",
                        json={"node_id": self.node_id}
                    )
                    
        except Exception as e:
            logger.error(f"❌ Error unregistering node: {e}")
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats to keep registration alive"""
        while True:
            try:
                await asyncio.sleep(self.config.heartbeat_interval)
                
                if self.registered:
                    await self._send_heartbeat()
                else:
                    # Try to re-register
                    await self.register_with_api()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error in heartbeat loop: {e}")
    
    async def _send_heartbeat(self):
        """Send heartbeat to update last_seen timestamp"""
        try:
            is_dev = os.environ.get("ENVIRONMENT", "development") == "development"
            
            if is_dev:
                # Update local registry
                app_dir = Path(__file__).parent.parent
                registry_file = app_dir / "data" / "nodes" / "registry.json"
                
                if registry_file.exists():
                    with open(registry_file, 'r') as f:
                        registry = json.load(f)
                    
                    # Update last_heartbeat for this node
                    for user_id in registry:
                        for node in registry[user_id]:
                            if node.get("node_id") == self.node_id:
                                node["last_heartbeat"] = datetime.utcnow().isoformat()
                    
                    with open(registry_file, 'w') as f:
                        json.dump(registry, f, indent=2)
            else:
                # POST to API server
                async with httpx.AsyncClient(timeout=self.config.connection_timeout) as client:
                    await client.post(
                        f"{self.config.api_domain}/api/node-connection/heartbeat",
                        json={"node_id": self.node_id}
                    )
                    
        except Exception as e:
            logger.error(f"❌ Error sending heartbeat: {e}")
    
    async def reconnect(self) -> bool:
        """Re-register with API domain"""
        logger.info("🔄 Re-registering node...")
        return await self.register_with_api()
    
    async def ensure_connected(self):
        """Ensure the node is registered, call startup if needed"""
        if not self._startup_called or not self.registered:
            logger.info("Node not registered, calling startup...")
            await self.startup()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current node status"""
        uptime = 0
        if self.registered_at:
            uptime = int((datetime.utcnow() - self.registered_at).total_seconds())
        
        return {
            "node_id": self.node_id,
            "registered": self.registered,
            "local_url": self.local_url,
            "api_domain": self.config.api_domain,
            "registered_at": self.registered_at.isoformat() if self.registered_at else None,
            "uptime_seconds": uptime,
            "authorized_users": self.config.authorized_users,
            "node_name": self.config.node_name,
            "capabilities": self.config.capabilities,
            "max_concurrent_users": self.config.max_concurrent_users,
            "auto_reconnect": self.config.auto_reconnect,
            "heartbeat_interval": self.config.heartbeat_interval
        }
    
    def get_connection_details(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get connection details for a specific user (if authorized)"""
        if user_id not in self.config.authorized_users:
            logger.warning(f"⚠️  User {user_id} is not authorized to access this node")
            return None
        
        if self.registered:
            uptime = int((datetime.utcnow() - self.registered_at).total_seconds())
            
            return {
                "user_id": user_id,
                "node_id": self.node_id,
                "node_name": self.config.node_name,
                "local_url": self.local_url,
                "api_domain": self.config.api_domain,
                "registered_at": self.registered_at.isoformat(),
                "last_seen": datetime.utcnow().isoformat(),
                "status": "registered",
                "uptime_seconds": uptime,
                "capabilities": self.config.capabilities,
                "tunnel_status": "not_connected",
                "message": "Node is registered. Tunnel will be established when you access chat-app."
            }
        
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


def load_authorized_users_config() -> Dict[str, Any]:
    """Load authorized users configuration from JSON file"""
    try:
        config_file = Path(__file__).parent / "authorized_users.json"
        
        if not config_file.exists():
            logger.warning(f"⚠️  Config file not found: {config_file}")
            
            # Create default config
            default_config = {
                "authorized_users": [],
                "node_name": "API Domain Node",
                "capabilities": [],
                "max_concurrent_users": 0
            }
            
            # Try to create the file, but don't fail if we can't (production)
            try:
                logger.info("Attempting to create default configuration...")
                with open(config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
                logger.info(f"✅ Created default config at {config_file}")
            except (PermissionError, OSError) as e:
                logger.warning(f"⚠️  Could not create config file (read-only filesystem?): {e}")
                logger.info("   Using in-memory default configuration")
            
            return default_config
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        logger.info(f"✅ Loaded authorized users config from {config_file}")
        return config
        
    except Exception as e:
        logger.error(f"❌ Error loading config: {e}")
        import traceback
        traceback.print_exc()
        # Return minimal default (API domain mode)
        return {
            "authorized_users": [],
            "node_name": "API Domain Node",
            "capabilities": [],
            "max_concurrent_users": 0
        }


def get_node_manager() -> NodeConnectionManager:
    """Get global node manager instance"""
    global _manager
    if _manager is None:
        # Load authorized users config
        user_config = load_authorized_users_config()
        
        # Use existing AUTH_SERVER_DOMAIN instead of separate API_DOMAIN
        auth_server = os.environ.get("AUTH_SERVER_DOMAIN", "api.oneaurica.com")
        api_domain = f"https://{auth_server}" if not auth_server.startswith("http") else auth_server
        
        config = NodeConfig(
            api_domain=api_domain,
            authorized_users=user_config.get("authorized_users", []),
            node_name=user_config.get("node_name", "Execution Node"),
            capabilities=user_config.get("capabilities", []),
            max_concurrent_users=user_config.get("max_concurrent_users", 5),
            auto_reconnect=os.environ.get("AUTO_RECONNECT", "true").lower() == "true",
            heartbeat_interval=int(os.environ.get("HEARTBEAT_INTERVAL", "60")),
            connection_timeout=int(os.environ.get("CONNECTION_TIMEOUT", "30"))
        )
        _manager = NodeConnectionManager(config)
    return _manager
