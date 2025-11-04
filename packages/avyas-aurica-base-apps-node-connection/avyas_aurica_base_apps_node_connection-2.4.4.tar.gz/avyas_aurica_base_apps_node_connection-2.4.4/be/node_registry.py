"""
Node Registry - Manages registration and tracking of multiple execution nodes.

This module provides persistent storage for node registrations, allowing
the API domain to track all connected execution nodes and their status.
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class NodeRegistry:
    """Manages registration and tracking of multiple execution nodes."""
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize node registry.
        
        Args:
            storage_dir: Directory for storing node data. Defaults to data/nodes in app directory.
        """
        if storage_dir is None:
            app_dir = Path(__file__).parent.parent
            storage_dir = app_dir / "data" / "nodes"
        
        self.storage_dir = Path(storage_dir)
        self.nodes_file = self.storage_dir / "registry.json"
        
        # Create directories if they don't exist
        self._initialize_storage()
        
        # In-memory cache
        self._nodes_cache: Dict = {}
        self._cache_loaded = False
    
    def _initialize_storage(self):
        """Create storage directories if they don't exist."""
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            
            if not self.nodes_file.exists():
                self._save_json(self.nodes_file, {})
                logger.info(f"✅ Created node registry at {self.nodes_file}")
            
            logger.info(f"✅ Node registry initialized at {self.storage_dir}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize node registry: {e}")
            raise
    
    def _load_json(self, file_path: Path) -> Dict:
        """Load JSON data from file."""
        try:
            if not file_path.exists():
                return {}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ Error loading {file_path}: {e}")
            return {}
    
    def _save_json(self, file_path: Path, data: Dict):
        """Save JSON data to file."""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ Error saving {file_path}: {e}")
            raise
    
    def load_registry(self):
        """Load all node registrations from disk."""
        if self._cache_loaded:
            return
        
        logger.info("📂 Loading node registry...")
        self._nodes_cache = self._load_json(self.nodes_file)
        self._cache_loaded = True
        logger.info(f"✅ Loaded {len(self._nodes_cache)} registered nodes")
    
    def register_node(self, user_id: str, node_data: Dict) -> Dict:
        """
        Register or update a node.
        
        Args:
            user_id: User ID who owns this node
            node_data: Node information including:
                - node_id: Unique node identifier
                - node_url: URL where node can be reached
                - connection_type: 'local' or 'remote'
                - capabilities: List of capabilities
                
        Returns:
            Updated node data with registration timestamp
        """
        self.load_registry()
        
        node_id = node_data.get("node_id")
        if not node_id:
            raise ValueError("node_id is required")
        
        # Create composite key: user_id:node_id
        registry_key = f"{user_id}:{node_id}"
        
        # Add registration metadata
        now = datetime.utcnow().isoformat()
        node_data["user_id"] = user_id
        node_data["registered_at"] = now
        node_data["last_seen"] = now
        node_data["status"] = "online"
        
        # Store in cache and persist
        self._nodes_cache[registry_key] = node_data
        self._save_json(self.nodes_file, self._nodes_cache)
        
        logger.info(f"✅ Registered node {node_id} for user {user_id}")
        return node_data
    
    def update_node_heartbeat(self, user_id: str, node_id: str) -> bool:
        """Update node's last_seen timestamp."""
        self.load_registry()
        
        registry_key = f"{user_id}:{node_id}"
        
        if registry_key in self._nodes_cache:
            self._nodes_cache[registry_key]["last_seen"] = datetime.utcnow().isoformat()
            self._nodes_cache[registry_key]["status"] = "online"
            self._save_json(self.nodes_file, self._nodes_cache)
            return True
        
        return False
    
    def get_user_nodes(self, user_id: str) -> List[Dict]:
        """Get all nodes registered by a user."""
        self.load_registry()
        
        user_nodes = []
        for key, node_data in self._nodes_cache.items():
            if key.startswith(f"{user_id}:"):
                # Check if node is still online (last seen within 5 minutes)
                last_seen = datetime.fromisoformat(node_data["last_seen"])
                if datetime.utcnow() - last_seen > timedelta(minutes=5):
                    node_data["status"] = "offline"
                
                user_nodes.append(node_data)
        
        # Sort by last_seen (most recent first)
        user_nodes.sort(key=lambda x: x["last_seen"], reverse=True)
        
        return user_nodes
    
    def get_node(self, user_id: str, node_id: str) -> Optional[Dict]:
        """Get a specific node."""
        self.load_registry()
        
        registry_key = f"{user_id}:{node_id}"
        node_data = self._nodes_cache.get(registry_key)
        
        if node_data:
            # Update status based on last_seen
            last_seen = datetime.fromisoformat(node_data["last_seen"])
            if datetime.utcnow() - last_seen > timedelta(minutes=5):
                node_data["status"] = "offline"
            else:
                node_data["status"] = "online"
        
        return node_data
    
    def unregister_node(self, user_id: str, node_id: str) -> bool:
        """Unregister a node."""
        self.load_registry()
        
        registry_key = f"{user_id}:{node_id}"
        
        if registry_key in self._nodes_cache:
            del self._nodes_cache[registry_key]
            self._save_json(self.nodes_file, self._nodes_cache)
            logger.info(f"🗑️  Unregistered node {node_id} for user {user_id}")
            return True
        
        return False
    
    def get_stats(self) -> Dict:
        """Get registry statistics."""
        self.load_registry()
        
        total_nodes = len(self._nodes_cache)
        online_nodes = sum(1 for n in self._nodes_cache.values() 
                          if datetime.utcnow() - datetime.fromisoformat(n["last_seen"]) <= timedelta(minutes=5))
        
        return {
            "total_nodes": total_nodes,
            "online_nodes": online_nodes,
            "offline_nodes": total_nodes - online_nodes
        }


# Global registry instance
_registry: Optional[NodeRegistry] = None


def get_registry() -> NodeRegistry:
    """Get the global node registry instance."""
    global _registry
    if _registry is None:
        _registry = NodeRegistry()
    return _registry


def initialize_registry(storage_dir: Optional[Path] = None):
    """Initialize the global registry instance with custom directory."""
    global _registry
    _registry = NodeRegistry(storage_dir)
    return _registry
