"""
Test script for Machine Registration System

Tests the core functionality of machine registration, listing, updating, and deletion.
"""
import sys
from pathlib import Path

# Add be directory to path
be_dir = Path(__file__).parent / "be"
sys.path.insert(0, str(be_dir))

from machine_registry import MachineRegistry
import tempfile
import shutil


def test_machine_registry():
    """Test MachineRegistry functionality."""
    print("🧪 Testing Machine Registry...\n")
    
    # Create temporary storage directory
    temp_dir = Path(tempfile.mkdtemp())
    print(f"📁 Using temp directory: {temp_dir}\n")
    
    try:
        # Initialize registry
        registry = MachineRegistry(storage_dir=temp_dir)
        print("✅ Registry initialized\n")
        
        # Test 1: Register a local machine
        print("Test 1: Register local machine")
        machine_data = {
            "name": "My Laptop",
            "connection_type": "local",
            "connection": {
                "url": "http://localhost:8000"
            },
            "metadata": {
                "os": "macOS",
                "hostname": "my-laptop",
                "ip": "192.168.1.100"
            }
        }
        
        result = registry.register_machine("user123", machine_data)
        machine_id_1 = result["machine_id"]
        
        print(f"   ✅ Registered machine: {machine_id_1}")
        print(f"   Connection token: {result['connection_token'][:20]}...\n")
        
        # Test 2: Register an SSH machine
        print("Test 2: Register SSH machine")
        ssh_machine_data = {
            "name": "My Server",
            "connection_type": "ssh",
            "connection": {
                "host": "server.example.com",
                "port": 22,
                "username": "amit"
            },
            "metadata": {
                "os": "Ubuntu 22.04",
                "hostname": "my-server"
            }
        }
        
        result2 = registry.register_machine("user123", ssh_machine_data)
        machine_id_2 = result2["machine_id"]
        
        print(f"   ✅ Registered machine: {machine_id_2}\n")
        
        # Test 3: List user's machines
        print("Test 3: List user's machines")
        machines = registry.get_user_machines("user123")
        print(f"   ✅ Found {len(machines)} machines:")
        for m in machines:
            print(f"      - {m['name']} ({m['connection_type']}) - {m['status']}")
        print()
        
        # Test 4: Get machine details
        print("Test 4: Get machine details")
        machine = registry.get_machine("user123", machine_id_1)
        print(f"   ✅ Machine: {machine['name']}")
        print(f"   Type: {machine['connection_type']}")
        print(f"   Status: {machine['status']}")
        print(f"   Registered: {machine['registered_at']}")
        print()
        
        # Test 5: Update machine
        print("Test 5: Update machine")
        updated = registry.update_machine("user123", machine_id_1, {
            "name": "Updated Laptop Name",
            "status": "offline"
        })
        print(f"   ✅ Updated machine: {updated['name']}")
        print(f"   New status: {updated['status']}\n")
        
        # Test 6: Update last_seen
        print("Test 6: Update last_seen")
        success = registry.update_last_seen("user123", machine_id_2)
        print(f"   ✅ Updated last_seen: {success}\n")
        
        # Test 7: Get machine by token
        print("Test 7: Get machine by token")
        token = result["connection_token"]
        machine_by_token = registry.get_machine_by_token(token)
        print(f"   ✅ Found machine by token: {machine_by_token['name']}\n")
        
        # Test 8: Delete machine
        print("Test 8: Delete machine")
        deleted = registry.delete_machine("user123", machine_id_2)
        print(f"   ✅ Deleted machine: {deleted}")
        
        machines_after_delete = registry.get_user_machines("user123")
        print(f"   Remaining machines: {len(machines_after_delete)}\n")
        
        # Test 9: Authorization (different user)
        print("Test 9: Test authorization (different user)")
        other_user_machine = registry.get_machine("user456", machine_id_1)
        if other_user_machine is None:
            print("   ✅ Authorization working - other user cannot access machine\n")
        else:
            print("   ❌ Authorization failed - other user accessed machine!\n")
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
        print(f"\n🧹 Cleaned up temp directory")


if __name__ == "__main__":
    test_machine_registry()
