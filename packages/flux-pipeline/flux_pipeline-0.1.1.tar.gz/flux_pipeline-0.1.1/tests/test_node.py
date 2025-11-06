"""
Tests for Node class functionality
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from __init__ import Node


async def test_single_node_sync():
    """Test basic synchronous node execution"""
    @Node
    def process(x):
        return f"processed_{x}"
    
    result = await process("input")
    assert result == "processed_input"
    print("✓ test_single_node_sync")


async def test_single_node_async():
    """Test basic asynchronous node execution"""
    @Node
    async def async_process(x):
        await asyncio.sleep(0.001)
        return f"async_{x}"
    
    result = await async_process("input")
    assert result == "async_input"
    print("✓ test_single_node_async")


async def test_node_name_attribute():
    """Test that nodes capture function name"""
    @Node
    def my_function(x):
        return x
    
    assert my_function.name == "my_function"
    print("✓ test_node_name_attribute")


async def test_node_accepts_shared():
    """Test node detection of shared parameter"""
    @Node
    def with_shared(x, shared=None):
        return x
    
    @Node
    def without_shared(x):
        return x
    
    assert with_shared.accepts_shared is True
    assert without_shared.accepts_shared is False
    print("✓ test_node_accepts_shared")


async def test_node_accepts_persistence():
    """Test node detection of persistence parameter"""
    @Node
    def with_persistence(x, persistence=None):
        return x
    
    @Node
    def without_persistence(x):
        return x
    
    assert with_persistence.accepts_persistence is True
    assert without_persistence.accepts_persistence is False
    print("✓ test_node_accepts_persistence")


async def test_node_with_multiple_args():
    """Test node with multiple arguments"""
    @Node
    def multi_arg(a, b, c=10):
        return a + b + c
    
    result = await multi_arg(5, 3)
    assert result == 18
    print("✓ test_node_with_multiple_args")


async def test_node_with_kwargs():
    """Test node with keyword arguments"""
    @Node
    def with_kwargs(x, **kwargs):
        print("inner kwargs:", kwargs)
        return f"{x}_{kwargs.get('extra', 'none')}"
    
    result = await with_kwargs("test", extra="data")
    print("result:", result)

    assert result == "test_data"
    print("✓ test_node_with_kwargs")


async def test_node_is_async_detection():
    """Test correct detection of async vs sync functions"""
    @Node
    def sync_func(x):
        return x
    
    @Node
    async def async_func(x):
        return x
    
    assert sync_func.is_async is False
    assert async_func.is_async is True
    print("✓ test_node_is_async_detection")


async def run_all():
    """Run all node tests"""
    tests = [
        test_single_node_sync,
        test_single_node_async,
        test_node_name_attribute,
        test_node_accepts_shared,
        test_node_accepts_persistence,
        test_node_with_multiple_args,
        test_node_with_kwargs,
        test_node_is_async_detection,
    ]
    
    for test in tests:
        await test()
    
    print(f"\n✅ All {len(tests)} node tests passed")


if __name__ == "__main__":
    asyncio.run(run_all())
