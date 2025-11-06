"""
Tests for Persistence class and state management
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from __init__ import Node, Parallel, Persistence, _GLOBAL_PERSISTENCE_STORE


async def test_persistence_auto_creation():
    """Test that persistence is automatically created"""
    captured_persistence = None
    
    @Node
    def capture(x, persistence=None):
        nonlocal captured_persistence
        captured_persistence = persistence
        return x
    
    result = await capture("test")
    assert captured_persistence is not None
    assert hasattr(captured_persistence, 'run_id')
    print("✓ test_persistence_auto_creation")


async def test_persistence_save_get():
    """Test basic save and get operations"""
    @Node
    def writer(x, persistence=None):
        if persistence:
            persistence.save("my_key", f"saved:{x}")
        return x
    
    @Node
    def reader(x, persistence=None):
        if persistence:
            value = persistence.get("my_key", "not_found")
            return value
        return "no_persistence"
    
    pipeline = writer | reader
    result = await pipeline("test_value")
    assert result == "saved:test_value"
    print("✓ test_persistence_save_get")


async def test_persistence_unique_run_id():
    """Test that each run gets unique run_id"""
    run_ids = []
    
    @Node
    def capture_run_id(x, persistence=None):
        if persistence:
            run_ids.append(persistence.run_id)
        return x
    
    await capture_run_id("run1")
    await capture_run_id("run2")
    
    assert len(run_ids) == 2
    assert run_ids[0] != run_ids[1]
    print("✓ test_persistence_unique_run_id")


async def test_persistence_history_tracking():
    """Test automatic history tracking"""
    captured_persistence = None
    
    @Node
    def step1(x, persistence=None):
        nonlocal captured_persistence
        captured_persistence = persistence
        return f"s1({x})"
    
    @Node
    def step2(x):
        return f"s2({x})"
    
    pipeline = step1 | step2
    result = await pipeline("start")
    
    assert captured_persistence is not None
    history = captured_persistence.get_history()
    assert len(history) > 0
    
    # Check history entry structure
    entry = history[0]
    assert "run_id" in entry
    assert "node_name" in entry
    assert "timestamp" in entry
    assert "duration" in entry
    assert "input" in entry
    assert "output" in entry
    print("✓ test_persistence_history_tracking")


async def test_persistence_in_parallel():
    """Test persistence shared across parallel branches"""
    @Node
    def branch_a(x, persistence=None):
        if persistence:
            persistence.save("branch_a", "executed")
        return "a_result"
    
    @Node
    def branch_b(x, persistence=None):
        if persistence:
            persistence.save("branch_b", "executed")
        return "b_result"
    
    @Node
    def combiner(results, persistence=None):
        if persistence:
            a_data = persistence.get("branch_a", "missing")
            b_data = persistence.get("branch_b", "missing")
            assert a_data == "executed"
            assert b_data == "executed"
        return results
    
    pipeline = Parallel(branch_a, branch_b) | combiner
    result = await pipeline("input")
    assert result == ["a_result", "b_result"]
    print("✓ test_persistence_in_parallel")


async def test_persistence_global_tracking():
    """Test global tracking of all runs"""
    initial_count = len(_GLOBAL_PERSISTENCE_STORE["runs"])
    
    @Node
    def simple(x):
        return f"processed:{x}"
    
    await simple("run1")
    await simple("run2")
    await simple("run3")
    
    final_count = len(_GLOBAL_PERSISTENCE_STORE["runs"])
    new_runs = final_count - initial_count
    
    assert new_runs == 3
    print("✓ test_persistence_global_tracking")


async def test_persistence_get_run():
    """Test retrieving specific run data"""
    captured_run_id = None
    
    @Node
    def capture(x, persistence=None):
        nonlocal captured_run_id
        if persistence:
            captured_run_id = persistence.run_id
        return x
    
    await capture("test")
    
    assert captured_run_id is not None
    run_data = Persistence.get_run(captured_run_id)
    assert run_data is not None
    assert "kv" in run_data
    assert "history" in run_data
    assert "status" in run_data
    print("✓ test_persistence_get_run")


async def test_persistence_list_runs():
    """Test listing all runs"""
    all_runs = Persistence.list_runs()
    assert isinstance(all_runs, dict)
    assert len(all_runs) > 0
    print("✓ test_persistence_list_runs")


async def test_persistence_delete():
    """Test delete operation"""
    @Node
    def test_delete(x, persistence=None):
        if persistence:
            persistence.save("temp_key", "temp_value")
            assert persistence.get("temp_key") == "temp_value"
            deleted = persistence.delete("temp_key")
            assert deleted is True
            assert persistence.get("temp_key") is None
        return x
    
    await test_delete("test")
    print("✓ test_persistence_delete")


async def test_persistence_get_with_default():
    """Test get with default value"""
    @Node
    def test_default(x, persistence=None):
        if persistence:
            value = persistence.get("nonexistent", "default_value")
            assert value == "default_value"
        return x
    
    await test_default("test")
    print("✓ test_persistence_get_with_default")


async def test_persistence_mark_complete():
    """Test marking run as complete"""
    captured_persistence = None

    @Node
    def capture(x, persistence=None):
        nonlocal captured_persistence
        captured_persistence = persistence
        return x

    await capture("test")

    captured_persistence.set_status("complete")
    run_data = Persistence.get_run(captured_persistence.run_id)
    assert run_data["status"] == "complete"
    assert "completed_at" in run_data
    print("✓ test_persistence_mark_complete")


async def test_persistence_mark_failed():
    """Test marking run as failed"""
    captured_persistence = None

    @Node
    def capture(x, persistence=None):
        nonlocal captured_persistence
        captured_persistence = persistence
        return x

    await capture("test")

    captured_persistence.set_status("failed", "Test error")
    run_data = Persistence.get_run(captured_persistence.run_id)
    assert run_data["status"] == "failed"
    assert run_data["error"] == "Test error"
    assert "failed_at" in run_data
    print("✓ test_persistence_mark_failed")


async def test_persistence_with_custom_storage():
    """Test persistence with custom storage backend"""
    class CustomStorage:
        def __init__(self):
            self.data = {}
        
        def save(self, key, value):
            self.data[key] = value
        
        def get(self, key):
            return self.data.get(key)
        
        def delete(self, key):
            if key in self.data:
                del self.data[key]
                return True
            return False
        
        def __call__(self, key, value):
            self.save(key, value)
    
    storage = CustomStorage()
    
    @Node
    def saver(x, persistence=None):
        if persistence:
            persistence.save("custom_key", x)
        return x
    
    result = await saver("test_data", storage=storage)
    
    # Custom storage should have received the save calls
    assert len(storage.data) > 0
    print("✓ test_persistence_with_custom_storage")


async def test_persistence_with_observability():
    """Test persistence with observability hook"""
    observations = []
    
    class CustomObservability:
        def __call__(self, action, key, value):
            observations.append({"action": action, "key": key, "value": value})
    
    observability = CustomObservability()
    
    @Node
    def tracked(x, persistence=None):
        if persistence:
            persistence.save("tracked_key", x)
        return x
    
    await tracked("test_data", observability=observability)
    
    # Should have observed the save and node_execution
    assert len(observations) > 0
    assert any(obs["action"] == "save" for obs in observations)
    print("✓ test_persistence_with_observability")


async def test_persistence_propagation():
    """Test that persistence propagates through entire pipeline"""
    captured_ids = []
    
    @Node
    def capture1(x, persistence=None):
        if persistence:
            captured_ids.append(persistence.run_id)
        return x
    
    @Node
    def capture2(x, persistence=None):
        if persistence:
            captured_ids.append(persistence.run_id)
        return x
    
    @Node
    def capture3(x, persistence=None):
        if persistence:
            captured_ids.append(persistence.run_id)
        return x
    
    pipeline = capture1 | capture2 | capture3
    await pipeline("test")
    
    # All nodes should see the same run_id
    assert len(captured_ids) == 3
    assert captured_ids[0] == captured_ids[1] == captured_ids[2]
    print("✓ test_persistence_propagation")


async def run_all():
    """Run all persistence tests"""
    tests = [
        test_persistence_auto_creation,
        test_persistence_save_get,
        test_persistence_unique_run_id,
        test_persistence_history_tracking,
        test_persistence_in_parallel,
        test_persistence_global_tracking,
        test_persistence_get_run,
        test_persistence_list_runs,
        test_persistence_delete,
        test_persistence_get_with_default,
        test_persistence_mark_complete,
        test_persistence_mark_failed,
        test_persistence_with_custom_storage,
        test_persistence_with_observability,
        test_persistence_propagation,
    ]
    
    for test in tests:
        await test()
    
    print(f"\n✅ All {len(tests)} persistence tests passed")


if __name__ == "__main__":
    asyncio.run(run_all())
