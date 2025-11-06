#!/usr/bin/env python3
"""
Master test runner for Flux framework
Runs all test modules and provides summary
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_node import run_all as run_node_tests
from test_parallel import run_all as run_parallel_tests
from test_pipeline import run_all as run_pipeline_tests
from test_persistence import run_all as run_persistence_tests
from test_edge_cases import run_all as run_edge_case_tests
from test_pause_resume import run_all as run_pause_resume_tests


async def main():
    """Run all test suites"""
    print("=" * 70)
    print("FLUX FRAMEWORK COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    
    test_suites = [
        ("Node Tests", run_node_tests),
        ("Parallel Tests", run_parallel_tests),
        ("Pipeline Tests", run_pipeline_tests),
        ("Persistence Tests", run_persistence_tests),
        ("Edge Case Tests", run_edge_case_tests),
        ("Pause/Resume Tests", run_pause_resume_tests),
    ]
    
    total_passed = 0
    total_failed = 0
    
    for suite_name, suite_func in test_suites:
        print(f"\n{'=' * 70}")
        print(f"{suite_name}")
        print("=" * 70)
        try:
            await suite_func()
            # Count tests (assuming each suite prints passed count)
            total_passed += 1
        except Exception as e:
            print(f"✗ {suite_name} FAILED: {e}")
            total_failed += 1
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    print(f"Test Suites: {len(test_suites)}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print("=" * 70)
    
    return total_failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
