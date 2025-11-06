"""
Comprehensive tests for the Flux agentic framework
Tests sequential execution, parallel execution, and combinations
"""
import asyncio
import sys
from __init__ import Node, Parallel, Persistence


async def test_single_node():
    """Test 1: Single node execution"""
    print("\n=== Test 1: Single Node ===")
    
    @Node
    def single(x):
        print(f"  single node processing: {x}")
        return f"processed_{x}"
    
    result = await single("input")
    assert result == "processed_input", f"Expected 'processed_input', got {result}"
    print(f"✓ Result: {result}")


async def test_sequential_two_nodes():
    """Test 2: Two nodes in sequence"""
    print("\n=== Test 2: Sequential (2 nodes) ===")
    
    @Node
    def step1(x):
        print(f"  step1: {x}")
        return f"s1({x})"
    
    @Node
    def step2(x):
        print(f"  step2: {x}")
        return f"s2({x})"
    
    pipeline = step1 | step2
    result = await pipeline("start")
    assert result == "s2(s1(start))", f"Expected 's2(s1(start))', got {result}"
    print(f"✓ Result: {result}")


async def test_sequential_three_nodes():
    """Test 3: Three nodes in sequence"""
    print("\n=== Test 3: Sequential (3 nodes) ===")
    
    @Node
    def a(x):
        print(f"  a: {x}")
        return f"a({x})"
    
    @Node
    def b(x):
        print(f"  b: {x}")
        return f"b({x})"
    
    @Node
    def c(x):
        print(f"  c: {x}")
        return f"c({x})"
    
    pipeline = a | b | c
    result = await pipeline("x")
    assert result == "c(b(a(x)))", f"Expected 'c(b(a(x)))', got {result}"
    print(f"✓ Result: {result}")


async def test_parallel_two_branches():
    """Test 4: Two branches in parallel"""
    print("\n=== Test 4: Parallel (2 branches) ===")
    
    @Node
    def branch_a(x):
        print(f"  branch_a: {x}")
        return f"a({x})"
    
    @Node
    def branch_b(x):
        print(f"  branch_b: {x}")
        return f"b({x})"
    
    parallel = Parallel(branch_a, branch_b)
    result = await parallel("input")
    assert result == ["a(input)", "b(input)"], f"Expected ['a(input)', 'b(input)'], got {result}"
    print(f"✓ Result: {result}")


async def test_parallel_three_branches():
    """Test 5: Three branches in parallel"""
    print("\n=== Test 5: Parallel (3 branches) ===")
    
    @Node
    def p1(x):
        print(f"  p1: {x}")
        return f"p1({x})"
    
    @Node
    def p2(x):
        print(f"  p2: {x}")
        return f"p2({x})"
    
    @Node
    def p3(x):
        print(f"  p3: {x}")
        return f"p3({x})"
    
    parallel = Parallel(p1, p2, p3)
    result = await parallel("data")
    assert result == ["p1(data)", "p2(data)", "p3(data)"], f"Unexpected result: {result}"
    print(f"✓ Result: {result}")


async def test_sequential_then_parallel():
    """Test 6: Sequential pipeline feeding into parallel branches"""
    print("\n=== Test 6: Sequential → Parallel ===")
    
    @Node
    def prep(x):
        print(f"  prep: {x}")
        return f"prep({x})"
    
    @Node
    def process_a(x):
        print(f"  process_a: {x}")
        return f"a({x})"
    
    @Node
    def process_b(x):
        print(f"  process_b: {x}")
        return f"b({x})"
    
    pipeline = prep | Parallel(process_a, process_b)
    result = await pipeline("raw")
    assert result == ["a(prep(raw))", "b(prep(raw))"], f"Unexpected result: {result}"
    print(f"✓ Result: {result}")


async def test_parallel_then_sequential():
    """Test 7: Parallel branches feeding into sequential processing"""
    print("\n=== Test 7: Parallel → Sequential ===")
    
    @Node
    def source_a(x):
        print(f"  source_a: {x}")
        return f"a({x})"
    
    @Node
    def source_b(x):
        print(f"  source_b: {x}")
        return f"b({x})"
    
    @Node
    def combine(results):
        print(f"  combine: {results}")
        return " + ".join(results)
    
    pipeline = Parallel(source_a, source_b) | combine
    result = await pipeline("input")
    assert result == "a(input) + b(input)", f"Expected 'a(input) + b(input)', got {result}"
    print(f"✓ Result: {result}")


async def test_complex_pipeline():
    """Test 8: Complex pipeline with nested sequential and parallel"""
    print("\n=== Test 8: Complex Pipeline ===")
    print("  Structure: (seq1, seq2) → parallel → concat → final")
    
    @Node
    def f1(x):
        print(f"  f1: {x}")
        return f"f1({x})"
    
    @Node
    def f2(x):
        print(f"  f2: {x}")
        return f"f2({x})"
    
    @Node
    def f3(x):
        print(f"  f3: {x}")
        return f"f3({x})"
    
    @Node
    def concat(lst):
        result = " + ".join(lst)
        print(f"  concat: {lst} → {result}")
        return result
    
    @Node
    def final(x):
        print(f"  final: {x}")
        return f"final({x})"
    
    # Sequential branches
    seq1 = f1 | f2
    seq2 = f3
    
    # Parallel execution
    parallel = Parallel(seq1, seq2)
    
    # Complete pipeline
    pipeline = parallel | concat | final
    
    result = await pipeline("start")
    expected = "final(f2(f1(start)) + f3(start))"
    assert result == expected, f"Expected '{expected}', got {result}"
    print(f"✓ Result: {result}")


async def test_shared_state():
    """Test 9: Shared state across nodes"""
    print("\n=== Test 9: Shared State ===")
    
    @Node
    def writer(x, shared=None):
        if shared is not None:
            shared['value'] = x
        print(f"  writer: wrote '{x}' to shared")
        return x
    
    @Node
    def reader(x, shared=None):
        stored = shared.get('value', 'none') if shared else 'none'
        print(f"  reader: read '{stored}' from shared")
        return f"read:{stored}"
    
    shared_dict = {}
    pipeline = writer | reader
    result = await pipeline("test_data", shared=shared_dict)
    
    assert shared_dict['value'] == "test_data", f"Shared state not updated"
    assert result == "read:test_data", f"Expected 'read:test_data', got {result}"
    print(f"✓ Result: {result}, Shared: {shared_dict}")


async def test_parallel_with_shared_state():
    """Test 10: Parallel branches with shared state"""
    print("\n=== Test 10: Parallel with Shared State ===")
    
    @Node
    def increment_a(x, shared=None):
        if shared is not None:
            shared['count'] = shared.get('count', 0) + 1
        print(f"  increment_a: count = {shared.get('count', 0)}")
        return f"a{shared.get('count', 0)}"
    
    @Node
    def increment_b(x, shared=None):
        if shared is not None:
            shared['count'] = shared.get('count', 0) + 1
        print(f"  increment_b: count = {shared.get('count', 0)}")
        return f"b{shared.get('count', 0)}"
    
    shared_dict = {'count': 0}
    parallel = Parallel(increment_a, increment_b)
    result = await parallel("x", shared=shared_dict)
    
    # Both should increment, final count should be 2 (may vary due to race)
    print(f"✓ Result: {result}, Final count: {shared_dict['count']}")
    assert shared_dict['count'] == 2, f"Expected count=2, got {shared_dict['count']}"


async def test_empty_input():
    """Test 11: Handling empty/None inputs"""
    print("\n=== Test 11: Empty Input ===")
    
    @Node
    def handle_empty(x):
        print(f"  handle_empty: {x}")
        return f"handled:{x}"
    
    result = await handle_empty(None)
    assert result == "handled:None", f"Expected 'handled:None', got {result}"
    print(f"✓ Result: {result}")


async def test_numeric_data():
    """Test 12: Processing numeric data"""
    print("\n=== Test 12: Numeric Data ===")
    
    @Node
    def double(x):
        print(f"  double: {x}")
        return x * 2
    
    @Node
    def add_ten(x):
        print(f"  add_ten: {x}")
        return x + 10
    
    pipeline = double | add_ten
    result = await pipeline(5)
    assert result == 20, f"Expected 20, got {result}"
    print(f"✓ Result: {result}")


async def test_persistence_basic():
    """Test 13: Basic persistence save and get"""
    print("\n=== Test 13: Persistence Basic ===")
    
    @Node
    def writer(x, persistence=None):
        if persistence:
            persistence.save("my_key", f"saved:{x}")
        print(f"  writer: saved data")
        return x
    
    @Node
    def reader(x, persistence=None):
        if persistence:
            value = persistence.get("my_key", "not_found")
            print(f"  reader: retrieved '{value}'")
            return value
        return "no_persistence"
    
    pipeline = writer | reader
    result = await pipeline("test_value")
    assert result == "saved:test_value", f"Expected 'saved:test_value', got {result}"
    print(f"✓ Result: {result}")


async def test_persistence_run_id():
    """Test 14: Each run gets unique run_id"""
    print("\n=== Test 14: Persistence Run ID ===")
    
    run_ids = []
    
    @Node
    def capture_run_id(x, persistence=None):
        if persistence:
            run_ids.append(persistence.run_id)
            print(f"  Run ID: {persistence.run_id[:8]}...")
        return x
    
    # Run pipeline twice
    await capture_run_id("run1")
    await capture_run_id("run2")
    
    assert len(run_ids) == 2, f"Expected 2 run_ids, got {len(run_ids)}"
    assert run_ids[0] != run_ids[1], "Run IDs should be different"
    print(f"✓ Generated unique run_ids")


async def test_persistence_history():
    """Test 15: Automatic history tracking"""
    print("\n=== Test 15: Persistence History ===")
    
    captured_persistence = None
    
    @Node
    def step1(x, persistence=None):
        nonlocal captured_persistence
        captured_persistence = persistence
        print(f"  step1: {x}")
        return f"s1({x})"
    
    @Node
    def step2(x):
        print(f"  step2: {x}")
        return f"s2({x})"
    
    pipeline = step1 | step2
    result = await pipeline("start")
    
    # Check history was recorded
    assert captured_persistence is not None, "Persistence should be created"
    history = captured_persistence.get_history()
    assert len(history) > 0, "History should contain entries"
    
    print(f"✓ History entries: {len(history)}")
    for entry in history:
        print(f"  - {entry['node_name']}: {entry['duration']:.4f}s")


async def test_persistence_parallel():
    """Test 16: Persistence shared across parallel branches"""
    print("\n=== Test 16: Persistence in Parallel ===")
    
    @Node
    def branch_a(x, persistence=None):
        if persistence:
            persistence.save("branch_a", "executed")
        print(f"  branch_a: executed")
        return "a_result"
    
    @Node
    def branch_b(x, persistence=None):
        if persistence:
            persistence.save("branch_b", "executed")
            # Check if can see branch_a data (may not be there due to timing)
            a_data = persistence.get("branch_a")
            print(f"  branch_b: executed, branch_a={a_data}")
        return "b_result"
    
    @Node
    def combiner(results, persistence=None):
        if persistence:
            a_data = persistence.get("branch_a", "missing")
            b_data = persistence.get("branch_b", "missing")
            print(f"  combiner: branch_a={a_data}, branch_b={b_data}")
        return results
    
    pipeline = Parallel(branch_a, branch_b) | combiner
    result = await pipeline("input")
    
    assert result == ["a_result", "b_result"], f"Expected parallel results, got {result}"
    print(f"✓ Result: {result}")


async def test_persistence_global_tracking():
    """Test 17: Global tracking of all runs"""
    print("\n=== Test 17: Global Run Tracking ===")
    
    initial_count = len(Persistence.list_runs())
    
    @Node
    def simple(x):
        return f"processed:{x}"
    
    # Run pipeline multiple times
    await simple("run1")
    await simple("run2")
    await simple("run3")
    
    final_count = len(Persistence.list_runs())
    new_runs = final_count - initial_count
    
    assert new_runs == 3, f"Expected 3 new runs, got {new_runs}"
    print(f"✓ Tracked {new_runs} new runs")
    
    # Verify we can retrieve run data
    all_runs = Persistence.list_runs()
    for run_id, run_data in list(all_runs.items())[-3:]:
        print(f"  Run {run_id[:8]}...: {run_data['status']}, {len(run_data['history'])} history entries")


async def test_persistence_with_custom_storage():
    """Test 18: Persistence with custom storage"""
    print("\n=== Test 18: Custom Storage ===")
    
    # Simple in-memory storage
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
    
    # Check that custom storage was used
    assert len(storage.data) > 0, "Custom storage should have data"
    print(f"✓ Custom storage entries: {len(storage.data)}")
    for key in storage.data.keys():
        print(f"  - {key}")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("FLUX FRAMEWORK TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_single_node,
        test_sequential_two_nodes,
        test_sequential_three_nodes,
        test_parallel_two_branches,
        test_parallel_three_branches,
        test_sequential_then_parallel,
        test_parallel_then_sequential,
        test_complex_pipeline,
        test_shared_state,
        test_parallel_with_shared_state,
        test_empty_input,
        test_numeric_data,
        test_persistence_basic,
        test_persistence_run_id,
        test_persistence_history,
        test_persistence_parallel,
        test_persistence_global_tracking,
        test_persistence_with_custom_storage,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"✗ FAILED: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
