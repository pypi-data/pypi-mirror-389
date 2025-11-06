"""
Tests for edge cases and error handling
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from __init__ import Node, Parallel


async def test_empty_input():
    """Test handling None input"""
    @Node
    def handle_empty(x):
        return f"handled:{x}"
    
    result = await handle_empty(None)
    assert result == "handled:None"
    print("✓ test_empty_input")


async def test_numeric_data():
    """Test processing numeric data"""
    @Node
    def double(x):
        return x * 2
    
    @Node
    def add_ten(x):
        return x + 10
    
    pipeline = double | add_ten
    result = await pipeline(5)
    assert result == 20
    print("✓ test_numeric_data")


async def test_list_input():
    """Test processing list input"""
    @Node
    def process_list(items):
        return [item.upper() for item in items]
    
    result = await process_list(["a", "b", "c"])
    assert result == ["A", "B", "C"]
    print("✓ test_list_input")


async def test_dict_input():
    """Test processing dict input"""
    @Node
    def process_dict(data):
        return {k: v * 2 for k, v in data.items()}
    
    result = await process_dict({"a": 1, "b": 2})
    assert result == {"a": 2, "b": 4}
    print("✓ test_dict_input")


async def test_zero_value():
    """Test handling zero value"""
    @Node
    def process_zero(x):
        return x + 1
    
    result = await process_zero(0)
    assert result == 1
    print("✓ test_zero_value")


async def test_empty_string():
    """Test handling empty string"""
    @Node
    def process_empty_string(x):
        return f"processed:{x}"
    
    result = await process_empty_string("")
    assert result == "processed:"
    print("✓ test_empty_string")


async def test_boolean_values():
    """Test handling boolean values"""
    @Node
    def negate(x):
        return not x
    
    assert await negate(True) is False
    assert await negate(False) is True
    print("✓ test_boolean_values")


async def test_node_exception_handling():
    """Test that exceptions propagate correctly"""
    @Node
    def raises_error(x):
        raise ValueError("Test error")
    
    try:
        await raises_error("input")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert str(e) == "Test error"
    print("✓ test_node_exception_handling")


async def test_exception_marks_failed():
    """Test that exceptions can be handled and persistence state preserved"""
    captured_persistence = None

    @Node
    def capture_then_fail(x, persistence=None):
        nonlocal captured_persistence
        captured_persistence = persistence
        if persistence:
            persistence.set_status("failed", "Intentional failure")
        raise RuntimeError("Intentional failure")

    try:
        await capture_then_fail("test")
    except RuntimeError:
        pass

    if captured_persistence:
        from __init__ import Persistence
        run_data = Persistence.get_run(captured_persistence.run_id)
        assert run_data["status"] == "failed"
        assert "Intentional failure" in run_data["error"]
    print("✓ test_exception_marks_failed")


async def test_large_parallel_execution():
    """Test parallel execution with many branches"""
    @Node
    def process(x):
        return f"p{x}"
    
    # Create 10 branches
    branches = [Node(lambda x, i=i: f"b{i}({x})") for i in range(10)]
    parallel = Parallel(*branches)
    result = await parallel("x")
    
    assert len(result) == 10
    print("✓ test_large_parallel_execution")


async def test_deep_pipeline():
    """Test deeply nested pipeline"""
    @Node
    def step(x):
        return x + 1
    
    # Create a pipeline with 20 steps
    pipeline = step
    for _ in range(19):
        pipeline = pipeline | step
    
    result = await pipeline(0)
    assert result == 20
    print("✓ test_deep_pipeline")


async def test_node_without_return():
    """Test node that doesn't explicitly return"""
    @Node
    def no_return(x):
        pass  # Implicitly returns None
    
    result = await no_return("input")
    assert result is None
    print("✓ test_node_without_return")


async def test_parallel_with_different_return_types():
    """Test parallel with branches returning different types"""
    @Node
    def return_string(x):
        return "string"
    
    @Node
    def return_int(x):
        return 42
    
    @Node
    def return_list(x):
        return [1, 2, 3]
    
    parallel = Parallel(return_string, return_int, return_list)
    result = await parallel("input")
    assert result == ["string", 42, [1, 2, 3]]
    print("✓ test_parallel_with_different_return_types")


async def test_node_with_varargs():
    """Test node with *args to accept any number of arguments"""
    @Node
    def varargs(*args):
        return f"received_{len(args)}_args"
    
    result = await varargs("arg1")
    assert result == "received_1_args"
    print("✓ test_node_with_varargs")


async def test_shared_and_persistence_together():
    """Test using both shared and persistence in same node"""
    @Node
    def use_both(x, shared=None, persistence=None):
        if shared is not None:
            shared['shared_key'] = "shared_value"
        if persistence:
            persistence.save("persist_key", "persist_value")
        return x
    
    @Node
    def verify_both(x, shared=None, persistence=None):
        shared_val = shared.get('shared_key') if shared is not None else "no_shared"
        persist_val = persistence.get("persist_key") if persistence else "no_persist"
        return f"{shared_val}_{persist_val}"
    
    shared_dict = {}
    pipeline = use_both | verify_both
    result = await pipeline("input", shared=shared_dict)
    # Should have both shared and persistence values
    assert "persist_value" in result
    assert shared_dict.get('shared_key') == "shared_value"
    print("✓ test_shared_and_persistence_together")


async def test_unicode_strings():
    """Test handling unicode strings"""
    @Node
    def process_unicode(x):
        return f"processed:{x}"
    
    result = await process_unicode("héllo 世界 🌍")
    assert result == "processed:héllo 世界 🌍"
    print("✓ test_unicode_strings")


async def test_very_long_string():
    """Test handling very long strings"""
    @Node
    def process_long(x):
        return len(x)
    
    long_string = "a" * 100000
    result = await process_long(long_string)
    assert result == 100000
    print("✓ test_very_long_string")


async def test_nested_data_structures():
    """Test handling nested data structures"""
    @Node
    def process_nested(data):
        return data['a']['b']['c']
    
    result = await process_nested({"a": {"b": {"c": "value"}}})
    assert result == "value"
    print("✓ test_nested_data_structures")


async def run_all():
    """Run all edge case tests"""
    tests = [
        test_empty_input,
        test_numeric_data,
        test_list_input,
        test_dict_input,
        test_zero_value,
        test_empty_string,
        test_boolean_values,
        test_node_exception_handling,
        test_exception_marks_failed,
        test_large_parallel_execution,
        test_deep_pipeline,
        test_node_without_return,
        test_parallel_with_different_return_types,
        test_node_with_varargs,
        test_shared_and_persistence_together,
        test_unicode_strings,
        test_very_long_string,
        test_nested_data_structures,
    ]
    
    for test in tests:
        await test()
    
    print(f"\n✅ All {len(tests)} edge case tests passed")


if __name__ == "__main__":
    asyncio.run(run_all())
