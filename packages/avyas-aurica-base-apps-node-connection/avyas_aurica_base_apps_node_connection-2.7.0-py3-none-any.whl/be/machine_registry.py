"""
Machine Registry - Manages user machines and their registrations.

This module provides storage and management for machines registered to user accounts.
Each user can have multiple machines (local, SSH, tunnel-based) that they can access
through their Digital Twin.
"""
import json
import os
import secrets
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MachineRegistry:
    """Manages registration and tracking of user machines."""
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize machine registry.
        
        Args:
            storage_dir: Directory for storing machine data. Defaults to data/machines in app directory.
        """
        if storage_dir is None:
            app_dir = Path(__file__).parent.parent
            storage_dir = app_dir / "data" / "machines"
        
        self.storage_dir = Path(storage_dir)
        
        # Create directories if they don't exist
        self._initialize_storage()
    
    def _initialize_storage(self):
        """Create storage directories if they don't exist."""
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Machine registry initialized at {self.storage_dir}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize machine registry: {e}")
            raise
    
    def _get_user_dir(self, user_id: str) -> Path:
        """Get directory for user's machines."""
        user_dir = self.storage_dir / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir
    
    def _get_machines_file(self, user_id: str) -> Path:
        """Get machines list file for user."""
        return self._get_user_dir(user_id) / "machines.json"
    
    def _get_machine_file(self, user_id: str, machine_id: str) -> Path:
        """Get individual machine details file."""
        return self._get_user_dir(user_id) / f"machine_{machine_id}.json"
    
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
    
    def _generate_machine_id(self) -> str:
        """Generate unique machine ID."""
        return f"mach_{secrets.token_urlsafe(12)}"
    
    def _generate_connection_token(self) -> str:
        """Generate secure connection token for machine."""
        return f"mach_token_{secrets.token_urlsafe(32)}"
    
    def register_machine(self, user_id: str, machine_data: Dict) -> Dict:
        """
        Register a new machine for user.
        
        Args:
            user_id: User ID who owns this machine
            machine_data: Machine information including:
                - name: Human-readable name
                - connection_type: 'local', 'ssh', or 'tunnel'
                - connection: Connection details (type-specific)
                - metadata: Optional machine metadata
                
        Returns:
            dict: Registered machine with machine_id and connection_token
        """
        # Generate IDs
        machine_id = self._generate_machine_id()
        connection_token = self._generate_connection_token()
        
        # Build complete machine record
        machine = {
            "machine_id": machine_id,
            "user_id": user_id,
            "name": machine_data.get("name", "Unnamed Machine"),
            "connection_type": machine_data.get("connection_type", "local"),
            "status": "active",
            "registered_at": datetime.utcnow().isoformat(),
            "last_seen": datetime.utcnow().isoformat(),
            "connection": machine_data.get("connection", {}),
            "metadata": machine_data.get("metadata", {}),
            "access_level": machine_data.get("access_level", "full"),
            "allowed_apps": machine_data.get("allowed_apps", ["*"]),
            "connection_token": connection_token
        }
        
        # Save machine details
        machine_file = self._get_machine_file(user_id, machine_id)
        self._save_json(machine_file, machine)
        
        # Update machines list
        machines_file = self._get_machines_file(user_id)
        machines_list = self._load_json(machines_file)
        
        if "machines" not in machines_list:
            machines_list["machines"] = []
        
        # Add to list (summary only)
        machines_list["machines"].append({
            "machine_id": machine_id,
            "name": machine["name"],
            "connection_type": machine["connection_type"],
            "status": machine["status"],
            "registered_at": machine["registered_at"]
        })
        
        self._save_json(machines_file, machines_list)
        
        logger.info(f"✅ Registered machine {machine_id} for user {user_id}")
        
        return {
            "machine_id": machine_id,
            "status": "registered",
            "connection_token": connection_token,
            "machine": machine
        }
    
    def get_user_machines(self, user_id: str) -> List[Dict]:
        """
        Get all machines for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            list: List of user's machines (summary info)
        """
        machines_file = self._get_machines_file(user_id)
        machines_list = self._load_json(machines_file)
        return machines_list.get("machines", [])
    
    def get_machine(self, user_id: str, machine_id: str) -> Optional[Dict]:
        """
        Get specific machine details.
        
        Args:
            user_id: User ID (for authorization)
            machine_id: Machine ID
            
        Returns:
            dict: Machine details or None if not found
        """
        machine_file = self._get_machine_file(user_id, machine_id)
        
        if not machine_file.exists():
            logger.warning(f"Machine {machine_id} not found for user {user_id}")
            return None
        
        machine = self._load_json(machine_file)
        
        # Verify ownership
        if machine.get("user_id") != user_id:
            logger.warning(f"Access denied: Machine {machine_id} does not belong to user {user_id}")
            return None
        
        return machine
    
    def update_machine(self, user_id: str, machine_id: str, updates: Dict) -> Optional[Dict]:
        """
        Update machine details.
        
        Args:
            user_id: User ID (for authorization)
            machine_id: Machine ID
            updates: Fields to update
            
        Returns:
            dict: Updated machine or None if not found
        """
        machine = self.get_machine(user_id, machine_id)
        if not machine:
            return None
        
        # Update allowed fields
        allowed_updates = ["name", "status", "access_level", "allowed_apps", "metadata"]
        for key in allowed_updates:
            if key in updates:
                machine[key] = updates[key]
        
        machine["updated_at"] = datetime.utcnow().isoformat()
        
        # Save updated machine
        machine_file = self._get_machine_file(user_id, machine_id)
        self._save_json(machine_file, machine)
        
        # Update machines list summary
        self._update_machines_list_entry(user_id, machine_id, {
            "name": machine["name"],
            "status": machine["status"]
        })
        
        logger.info(f"✅ Updated machine {machine_id} for user {user_id}")
        return machine
    
    def delete_machine(self, user_id: str, machine_id: str) -> bool:
        """
        Delete/unregister a machine.
        
        Args:
            user_id: User ID (for authorization)
            machine_id: Machine ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        # Verify machine exists and belongs to user
        machine = self.get_machine(user_id, machine_id)
        if not machine:
            return False
        
        # Delete machine file
        machine_file = self._get_machine_file(user_id, machine_id)
        try:
            machine_file.unlink()
        except Exception as e:
            logger.error(f"Error deleting machine file: {e}")
            return False
        
        # Remove from machines list
        machines_file = self._get_machines_file(user_id)
        machines_list = self._load_json(machines_file)
        
        if "machines" in machines_list:
            machines_list["machines"] = [
                m for m in machines_list["machines"]
                if m["machine_id"] != machine_id
            ]
            self._save_json(machines_file, machines_list)
        
        logger.info(f"✅ Deleted machine {machine_id} for user {user_id}")
        return True
    
    def update_last_seen(self, user_id: str, machine_id: str) -> bool:
        """
        Update machine's last_seen timestamp.
        
        Args:
            user_id: User ID
            machine_id: Machine ID
            
        Returns:
            bool: True if updated, False if not found
        """
        machine = self.get_machine(user_id, machine_id)
        if not machine:
            return False
        
        machine["last_seen"] = datetime.utcnow().isoformat()
        
        machine_file = self._get_machine_file(user_id, machine_id)
        self._save_json(machine_file, machine)
        
        return True
    
    def _update_machines_list_entry(self, user_id: str, machine_id: str, updates: Dict):
        """Update machine entry in machines list."""
        machines_file = self._get_machines_file(user_id)
        machines_list = self._load_json(machines_file)
        
        if "machines" in machines_list:
            for machine in machines_list["machines"]:
                if machine["machine_id"] == machine_id:
                    machine.update(updates)
                    break
            
            self._save_json(machines_file, machines_list)
    
    def get_machine_by_token(self, connection_token: str) -> Optional[Dict]:
        """
        Find machine by connection token.
        
        Args:
            connection_token: Connection token to search for
            
        Returns:
            dict: Machine details or None if not found
        """
        # Search through all users and machines
        for user_dir in self.storage_dir.iterdir():
            if not user_dir.is_dir():
                continue
            
            user_id = user_dir.name
            
            for machine_file in user_dir.glob("machine_*.json"):
                machine = self._load_json(machine_file)
                if machine.get("connection_token") == connection_token:
                    return machine
        
        return None


# Global registry instance
_registry_instance = None

def get_machine_registry() -> MachineRegistry:
    """Get or create global machine registry instance."""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = MachineRegistry()
    return _registry_instance
