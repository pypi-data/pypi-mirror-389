"""
Tests for Parallel class functionality
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from __init__ import Node, Parallel


async def test_parallel_two_branches():
    """Test parallel execution with two branches"""
    @Node
    def branch_a(x):
        return f"a({x})"
    
    @Node
    def branch_b(x):
        return f"b({x})"
    
    parallel = Parallel(branch_a, branch_b)
    result = await parallel("input")
    assert result == ["a(input)", "b(input)"]
    print("✓ test_parallel_two_branches")


async def test_parallel_three_branches():
    """Test parallel execution with three branches"""
    @Node
    def p1(x):
        return f"p1({x})"
    
    @Node
    def p2(x):
        return f"p2({x})"
    
    @Node
    def p3(x):
        return f"p3({x})"
    
    parallel = Parallel(p1, p2, p3)
    result = await parallel("data")
    assert result == ["p1(data)", "p2(data)", "p3(data)"]
    print("✓ test_parallel_three_branches")


async def test_parallel_with_async_branches():
    """Test parallel with async functions"""
    @Node
    async def async_a(x):
        await asyncio.sleep(0.001)
        return f"a({x})"
    
    @Node
    async def async_b(x):
        await asyncio.sleep(0.001)
        return f"b({x})"
    
    parallel = Parallel(async_a, async_b)
    result = await parallel("input")
    assert result == ["a(input)", "b(input)"]
    print("✓ test_parallel_with_async_branches")


async def test_parallel_with_shared_state():
    """Test parallel branches accessing shared state"""
    @Node
    def increment_a(x, shared=None):
        if shared is not None:
            shared['count'] = shared.get('count', 0) + 1
        return f"a{shared.get('count', 0)}"
    
    @Node
    def increment_b(x, shared=None):
        if shared is not None:
            shared['count'] = shared.get('count', 0) + 1
        return f"b{shared.get('count', 0)}"
    
    shared_dict = {'count': 0}
    parallel = Parallel(increment_a, increment_b)
    result = await parallel("x", shared=shared_dict)
    
    assert shared_dict['count'] == 2
    print("✓ test_parallel_with_shared_state")


async def test_parallel_name_attribute():
    """Test that Parallel has correct name"""
    @Node
    def a(x):
        return x
    
    @Node
    def b(x):
        return x
    
    parallel = Parallel(a, b)
    assert parallel.name == "Parallel"
    print("✓ test_parallel_name_attribute")


async def test_parallel_is_async():
    """Test that Parallel is marked as async"""
    @Node
    def a(x):
        return x
    
    parallel = Parallel(a)
    assert parallel.is_async is True
    print("✓ test_parallel_is_async")


async def test_parallel_single_branch():
    """Test parallel with single branch"""
    @Node
    def single(x):
        return f"s({x})"
    
    parallel = Parallel(single)
    result = await parallel("input")
    assert result == ["s(input)"]
    print("✓ test_parallel_single_branch")


async def test_parallel_order_preserved():
    """Test that parallel results maintain branch order"""
    @Node
    async def slow(x):
        await asyncio.sleep(0.02)
        return "slow"
    
    @Node
    async def fast(x):
        await asyncio.sleep(0.001)
        return "fast"
    
    parallel = Parallel(slow, fast)
    result = await parallel("x")
    # Even though fast completes first, order should match branch order
    assert result == ["slow", "fast"]
    print("✓ test_parallel_order_preserved")


async def run_all():
    """Run all parallel tests"""
    tests = [
        test_parallel_two_branches,
        test_parallel_three_branches,
        test_parallel_with_async_branches,
        test_parallel_with_shared_state,
        test_parallel_name_attribute,
        test_parallel_is_async,
        test_parallel_single_branch,
        test_parallel_order_preserved,
    ]
    
    for test in tests:
        await test()
    
    print(f"\n✅ All {len(tests)} parallel tests passed")


if __name__ == "__main__":
    asyncio.run(run_all())
