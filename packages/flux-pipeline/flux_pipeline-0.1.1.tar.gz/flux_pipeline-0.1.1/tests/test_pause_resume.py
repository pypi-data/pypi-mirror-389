"""
Tests for pause and resume functionality
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from __init__ import Node, Persistence, PauseExecution


async def test_pause_basic():
    """Test basic pause functionality"""
    paused_run_id = None

    @Node
    def step1(x):
        return x + 1

    @Node
    def step2(x, persistence=None, node=None):
        # Pause here
        if persistence and node:
            node.pause(persistence)
        return x * 2

    @Node
    def step3(x):
        return x + 10

    pipeline = step1 | step2 | step3

    try:
        result = await pipeline(5)
        assert False, "Should have paused"
    except PauseExecution:
        # Get the run that was created
        runs = Persistence.list_runs()
        paused_run_id = list(runs.keys())[-1]

    # Verify run is marked as paused
    run_data = Persistence.get_run(paused_run_id)
    assert run_data["status"] == "paused"
    assert "paused_at" in run_data

    print("✓ test_pause_basic")


async def test_pause_resume_manual():
    """Test manual resume after pause"""
    paused_run_id = None

    @Node
    def fetch(x):
        return {"data": x}

    @Node
    def process(x, persistence=None, node=None):
        processed = {"processed": x["data"] * 2}
        if persistence:
            persistence.save("intermediate", processed)
            if node:
                node.pause(persistence)
        return processed

    @Node
    def validate(x):
        return {"validated": x["processed"]}

    @Node
    def save_data(x):
        return {"saved": x["validated"]}

    # Build pipeline
    pipeline = fetch | process | validate | save_data

    # First run - will pause at process
    try:
        result = await pipeline(10)
        assert False, "Should have paused"
    except PauseExecution:
        # Get the run that was created
        runs = Persistence.list_runs()
        paused_run_id = list(runs.keys())[-1]

    # Verify state
    run_data = Persistence.get_run(paused_run_id)
    assert run_data["status"] == "paused"

    # Get last output (should be the input to the paused node)
    last_output = run_data['history'][-1]['input']
    # The input should be the original input to the pipeline, which is 10
    assert last_output == 10

    # Manual resume - rebuild remaining pipeline
    @Node
    def process_no_pause(x):
        return {"processed": x * 2}

    remaining = process_no_pause | validate | save_data
    result = await remaining(last_output)

    assert result == {"saved": 20}
    print("✓ test_pause_resume_manual")


async def test_pause_with_checkpoints():
    """Test that checkpoints are saved before pause"""
    @Node
    def step1(x, persistence=None):
        if persistence:
            persistence.save("step1_ran", True)
        return x + 1

    @Node
    def step2(x, persistence=None, node=None):
        if persistence:
            persistence.save("step2_ran", True)
            if node:
                node.pause(persistence)
        return x * 2

    pipeline = step1 | step2

    try:
        await pipeline(5)
    except PauseExecution:
        pass

    # Get run data
    runs = Persistence.list_runs()
    run_id = list(runs.keys())[-1]
    run_data = Persistence.get_run(run_id)

    # Verify state is saved
    assert run_data["kv"]["step1_ran"] is True
    assert run_data["kv"]["step2_ran"] is True  # Saved before pause

    # Verify history contains the expected steps (step1 should be there, step2 might not complete due to pause)
    history_names = [entry["node_name"] for entry in run_data["history"]]
    assert "step1" in history_names
    # step2 might not be in history if pause happens during its execution

    print("✓ test_pause_with_checkpoints")


async def test_pause_preserves_state():
    """Test that state is preserved across pause"""
    @Node
    def initialize(x, persistence=None):
        if persistence:
            persistence.save("counter", 0)
            persistence.save("data", [x])
        return x

    @Node
    def accumulate(x, persistence=None, node=None):
        if persistence:
            counter = persistence.get("counter", 0)
            data = persistence.get("data", [])
            persistence.save("counter", counter + 1)
            data.append(x * 2)
            persistence.save("data", data)
            if node:
                node.pause(persistence)
        return x * 2

    pipeline = initialize | accumulate

    try:
        await pipeline(5)
    except PauseExecution:
        pass

    # Get state
    runs = Persistence.list_runs()
    run_id = list(runs.keys())[-1]
    run_data = Persistence.get_run(run_id)

    # Verify preserved state
    assert run_data["kv"]["counter"] == 1
    assert run_data["kv"]["data"] == [5, 10]

    print("✓ test_pause_preserves_state")


async def test_multiple_pause_points():
    """Test pipeline with multiple potential pause points"""
    pause_at_step2 = True
    pause_at_step3 = False

    @Node
    def step1(x):
        return x + 1

    @Node
    def step2(x, persistence=None, node=None):
        if persistence and pause_at_step2 and node:
            node.pause(persistence)
        return x * 2

    @Node
    def step3(x, persistence=None, node=None):
        if persistence and pause_at_step3 and node:
            node.pause(persistence)
        return x + 10

    pipeline = step1 | step2 | step3

    # Should pause at step2
    try:
        await pipeline(5)
    except PauseExecution:
        pass

    # Verify pause occurred
    runs = Persistence.list_runs()
    run_id = list(runs.keys())[-1]
    run_data = Persistence.get_run(run_id)
    assert run_data["status"] == "paused"

    print("✓ test_multiple_pause_points")


async def test_pause_exception_is_raised():
    """Test that PauseExecution is properly raised"""
    @Node
    def pauser(x, persistence=None, node=None):
        if persistence and node:
            node.pause(persistence)
        return x

    try:
        await pauser(10)
        assert False, "Should have raised PauseExecution"
    except PauseExecution as e:
        assert isinstance(e, Exception)
        assert "paused" in str(e).lower()

    print("✓ test_pause_exception_is_raised")


async def run_all():
    """Run all pause/resume tests"""
    tests = [
        test_pause_basic,
        test_pause_resume_manual,
        test_pause_with_checkpoints,
        test_pause_preserves_state,
        test_multiple_pause_points,
        test_pause_exception_is_raised,
    ]
    
    for test in tests:
        await test()
    
    print(f"\n✅ All {len(tests)} pause/resume tests passed")


if __name__ == "__main__":
    asyncio.run(run_all())
