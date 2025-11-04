"""
Tunnel Manager - Manages WebSocket tunnel connections for execution nodes

This module ensures tunnels stay connected and auto-reconnect if they fail.
"""
import asyncio
import logging
from typing import Optional, Dict
from datetime import datetime
from pathlib import Path
import sys

# Import tunnel client
base_be = Path(__file__).parent.parent.parent.parent / "aurica-base-be"
if str(base_be) not in sys.path:
    sys.path.insert(0, str(base_be))

from src.tunnel_client import TunnelClient

logger = logging.getLogger(__name__)


class TunnelConnectionManager:
    """
    Manages tunnel connections for execution nodes.
    
    Ensures tunnels stay connected and restart if they fail.
    Supports multiple nodes per user using composite key: user_id:node_id
    """
    
    def __init__(self):
        self._tunnels: Dict[str, TunnelClient] = {}  # key: user_id:node_id
        self._tunnel_tasks: Dict[str, asyncio.Task] = {}  # key: user_id:node_id
        self._monitor_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start_tunnel(self, user_id: str, node_id: str, auth_token: str, cloud_url: str = None) -> bool:
        """
        Start a tunnel connection for a user to a specific node.
        
        Args:
            user_id: User ID
            node_id: Node ID to connect to
            auth_token: JWT authentication token
            cloud_url: Cloud WebSocket URL (defaults to wss://api.oneaurica.com)
        
        Returns:
            True if tunnel started successfully
        """
        try:
            tunnel_key = f"{user_id}:{node_id}"
            
            # Stop existing tunnel for this user:node if any
            await self.stop_tunnel(user_id, node_id)
            
            # Prepare cloud URL
            if not cloud_url:
                import os
                cloud_url = os.getenv("CLOUD_URL", "https://api.oneaurica.com")
                cloud_url = cloud_url.replace("https://", "wss://").replace("http://", "ws://")
            
            logger.info(f"🔌 Starting tunnel for user {user_id} to node {node_id} via {cloud_url}")
            
            # Create tunnel client
            client = TunnelClient(
                user_id=user_id,
                auth_token=auth_token,
                cloud_url=cloud_url,
                auto_reconnect=True,
                reconnect_delay=5
            )
            
            # Store client
            self._tunnels[tunnel_key] = client
            
            # Start tunnel in background
            task = asyncio.create_task(client.connect())
            self._tunnel_tasks[tunnel_key] = task
            
            # Start monitoring if not already running
            if not self._running:
                self._running = True
                self._monitor_task = asyncio.create_task(self._monitor_tunnels())
            
            logger.info(f"✅ Tunnel task started for {tunnel_key}")
            
            # Wait a bit to ensure connection is established
            await asyncio.sleep(2)
            
            if client.connected:
                logger.info(f"✅ Tunnel successfully connected for {tunnel_key}")
                return True
            else:
                logger.warning(f"⚠️  Tunnel task started but not yet connected for {tunnel_key}")
                return True  # Task is running, connection will establish shortly
            
        except Exception as e:
            logger.error(f"❌ Failed to start tunnel for {user_id}:{node_id}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def stop_tunnel(self, user_id: str, node_id: str = None):
        """Stop tunnel for a user (optionally for specific node)"""
        if node_id:
            tunnel_key = f"{user_id}:{node_id}"
            if tunnel_key in self._tunnels:
                logger.info(f"🔌 Stopping tunnel for {tunnel_key}")
                
                # Stop the client
                client = self._tunnels[tunnel_key]
                await client.disconnect()
                
                # Cancel the task
                if tunnel_key in self._tunnel_tasks:
                    task = self._tunnel_tasks[tunnel_key]
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                    del self._tunnel_tasks[tunnel_key]
                
                del self._tunnels[tunnel_key]
                logger.info(f"✅ Tunnel stopped for {tunnel_key}")
        else:
            # Stop all tunnels for this user
            keys_to_remove = [k for k in self._tunnels.keys() if k.startswith(f"{user_id}:")]
            for tunnel_key in keys_to_remove:
                logger.info(f"🔌 Stopping tunnel for {tunnel_key}")
                
                client = self._tunnels[tunnel_key]
                await client.disconnect()
                
                if tunnel_key in self._tunnel_tasks:
                    task = self._tunnel_tasks[tunnel_key]
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                    del self._tunnel_tasks[tunnel_key]
                
                del self._tunnels[tunnel_key]
                logger.info(f"✅ Tunnel stopped for {tunnel_key}")
    
    async def get_tunnel_status(self, user_id: str, node_id: str = None) -> Dict:
        """Get status of tunnel for a user (optionally for specific node)"""
        if node_id:
            tunnel_key = f"{user_id}:{node_id}"
            if tunnel_key not in self._tunnels:
                return {
                    "connected": False,
                    "exists": False,
                    "status": "not_connected",
                    "message": "No tunnel connection for this node"
                }
            
            client = self._tunnels[tunnel_key]
            task = self._tunnel_tasks.get(tunnel_key)
            
            return {
                "connected": client.connected,
                "exists": True,
                "status": "connected" if client.connected else "connecting",
                "user_id": user_id,
                "node_id": node_id,
                "cloud_url": client.cloud_url,
                "auto_reconnect": client.auto_reconnect,
                "task_running": task is not None and not task.done() if task else False,
                "message": "Tunnel is active" if client.connected else "Tunnel exists but not connected"
            }
        else:
            # Get status of all tunnels for this user
            user_tunnels = {k: v for k, v in self._tunnels.items() if k.startswith(f"{user_id}:")}
            
            if not user_tunnels:
                return {
                    "connected": False,
                    "exists": False,
                    "status": "not_connected",
                    "message": "No tunnel connections for this user"
                }
            
            # Return summary
            connected_count = sum(1 for c in user_tunnels.values() if c.connected)
            return {
                "connected": connected_count > 0,
                "exists": True,
                "status": "connected" if connected_count > 0 else "disconnected",
                "user_id": user_id,
                "total_tunnels": len(user_tunnels),
                "connected_tunnels": connected_count,
                "message": f"{connected_count}/{len(user_tunnels)} tunnels connected"
            }
    
    async def _monitor_tunnels(self):
        """
        Background task to monitor tunnels and restart if needed.
        
        Checks every 30 seconds if tunnel tasks have died unexpectedly.
        """
        logger.info("👁️  Starting tunnel monitor")
        
        try:
            while self._running:
                await asyncio.sleep(30)
                
                # Check each tunnel
                for user_id in list(self._tunnel_tasks.keys()):
                    task = self._tunnel_tasks.get(user_id)
                    client = self._tunnels.get(user_id)
                    
                    if not task or not client:
                        continue
                    
                    # Check if task has died
                    if task.done():
                        logger.warning(f"⚠️  Tunnel task for {user_id} has died. Checking exception...")
                        
                        try:
                            # Get exception if any
                            exception = task.exception()
                            if exception:
                                logger.error(f"❌ Tunnel task died with exception: {exception}")
                        except Exception as e:
                            logger.error(f"❌ Error checking task exception: {e}")
                        
                        # Remove dead task
                        del self._tunnel_tasks[user_id]
                        
                        # If client still wants to reconnect, restart the task
                        if client.auto_reconnect and client.should_run:
                            logger.info(f"🔄 Restarting tunnel task for {user_id}")
                            task = asyncio.create_task(client.connect())
                            self._tunnel_tasks[user_id] = task
                    
                    # Log status
                    elif client.connected:
                        logger.debug(f"✅ Tunnel for {user_id}: Connected")
                    else:
                        logger.debug(f"⏳ Tunnel for {user_id}: Connecting...")
        
        except asyncio.CancelledError:
            logger.info("👁️  Tunnel monitor stopped")
        except Exception as e:
            logger.error(f"❌ Error in tunnel monitor: {e}")
            import traceback
            traceback.print_exc()
    
    async def shutdown(self):
        """Shutdown all tunnels"""
        logger.info("🔌 Shutting down tunnel manager...")
        
        self._running = False
        
        # Stop monitor
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        # Stop all tunnels
        for user_id in list(self._tunnels.keys()):
            await self.stop_tunnel(user_id)
        
        logger.info("✅ Tunnel manager shutdown complete")


# Global instance
_tunnel_manager: Optional[TunnelConnectionManager] = None


def get_tunnel_manager() -> TunnelConnectionManager:
    """Get the global tunnel manager instance"""
    global _tunnel_manager
    if _tunnel_manager is None:
        _tunnel_manager = TunnelConnectionManager()
    return _tunnel_manager
