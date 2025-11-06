import asyncio
import inspect
import sys
from typing import Protocol, Dict, Any, List, Optional
import time, uuid


# --- Protocols (interfaces) ---

class Storage(Protocol):
    def save(self, key: str, value: Any) -> None: ...
    def get(self, key: str) -> Any: ...
    def delete(self, key: str) -> bool: ...
    def __call__(self, key: str, value: Any) -> None: ...


class Observability(Protocol):
    def __call__(self, action: str, key: str, value: Any) -> None: ...


# --- Pause/Resume Exception ---

class PauseExecution(Exception):
    """Exception raised when pipeline execution is paused"""
    pass


# --- Global storage for persistence tracking across all runs ---
# All runs stored under "runs" key to keep namespace clean for user data
_GLOBAL_PERSISTENCE_STORE: Dict[str, Any] = {"runs": {}}


# --- Persistence class (per-run instance) ---

class Persistence:
    def __init__(
        self,
        run_id: str,
        storage: Optional[Storage] = None,
        observability: Optional[Observability] = None,
    ):
        self.run_id = run_id
        self._storage = storage
        self._observability = observability
        self.kv: Dict[str, Any] = {}
        self.history: List[Dict[str, Any]] = []

        # Store this run's persistence in global store for tracking/resumption
        _GLOBAL_PERSISTENCE_STORE["runs"][run_id] = {
            "kv": self.kv,
            "history": self.history,
            "created_at": time.time(),
            "status": "running"
        }

    def _record_node_execution(
        self,
        node_name: str,
        input_data: Any,
        output_data: Any,
        duration: float
    ) -> None:
        """Internal method to record node execution in history"""
        entry = {
            "run_id": self.run_id,
            "node_name": node_name,
            "timestamp": time.time(),
            "duration": duration,
            "input": input_data,
            "output": output_data,
        }

        # Store in KV with timestamp-based key for consistency
        timestamp = entry["timestamp"]
        self.save(f"history:{self.run_id}:{timestamp}", entry)

        # Also maintain in-memory list for quick access
        self.history.append(entry)

        if self._observability:
            self._observability("node_execution", node_name, entry)

        # Save to storage if provided (keep for backward compatibility)
        if self._storage:
            self._storage.save(f"history:{self.run_id}", self.history)

    def save(self, key: str, val: Any) -> None:
        """Save a key-value pair in this run's persistence"""
        self.kv[key] = val

        if self._observability:
            self._observability("save", key, val)

        if self._storage:
            self._storage.save(f"{self.run_id}:{key}", val)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from this run's persistence"""
        # First check run-specific kv store
        if key in self.kv:
            return self.kv[key]

        # Then check storage if provided
        if self._storage:
            try:
                return self._storage.get(f"{self.run_id}:{key}")
            except:
                pass

        return default

    def delete(self, key: str) -> bool:
        """Delete a key from this run's persistence"""
        deleted = False
        if key in self.kv:
            del self.kv[key]
            deleted = True

        if self._observability:
            self._observability("delete", key, None)

        if self._storage:
            self._storage.delete(f"{self.run_id}:{key}")

        return deleted

    def get_history(self) -> List[Dict[str, Any]]:
        """Get the execution history for this run"""
        return self.history

    def set_status(self, status: str, error: Optional[str] = None) -> None:
        """Set run status - consolidates mark_complete, mark_failed, and pause"""
        if self.run_id in _GLOBAL_PERSISTENCE_STORE["runs"]:
            _GLOBAL_PERSISTENCE_STORE["runs"][self.run_id]["status"] = status
            if status == "complete":
                _GLOBAL_PERSISTENCE_STORE["runs"][self.run_id]["completed_at"] = time.time()
            elif status == "failed":
                _GLOBAL_PERSISTENCE_STORE["runs"][self.run_id]["error"] = error
                _GLOBAL_PERSISTENCE_STORE["runs"][self.run_id]["failed_at"] = time.time()
            elif status == "paused":
                _GLOBAL_PERSISTENCE_STORE["runs"][self.run_id]["paused_at"] = time.time()

    def pause(self) -> None:
        """Pause execution - marks run as paused and raises PauseExecution"""
        if self.run_id in _GLOBAL_PERSISTENCE_STORE["runs"]:
            _GLOBAL_PERSISTENCE_STORE["runs"][self.run_id]["status"] = "paused"
            _GLOBAL_PERSISTENCE_STORE["runs"][self.run_id]["paused_at"] = time.time()
        raise PauseExecution(f"Run {self.run_id} paused")

    @staticmethod
    def get_run(run_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve persistence data for a specific run (for resumption/inspection)"""
        return _GLOBAL_PERSISTENCE_STORE["runs"].get(run_id)

    @staticmethod
    def list_runs() -> Dict[str, Dict[str, Any]]:
        """List all tracked runs"""
        return _GLOBAL_PERSISTENCE_STORE["runs"]


class Node:
    def __init__(self, func):
        self.func = func
        self.name = getattr(func, '__name__', 'piped')
        self.is_async = inspect.iscoroutinefunction(func)
        sig = inspect.signature(func)
        self.accepts_shared = 'shared' in sig.parameters
        self.accepts_persistence = 'persistence' in sig.parameters
        self.accepts_node = 'node' in sig.parameters
        self.next_node = None  # Reference to the next node in the pipeline

    async def __call__(self, *args, shared=None, persistence=None, storage=None, observability=None, **kwargs):
        # Create persistence instance on first node call if not provided
        if persistence is None:
            run_id = str(uuid.uuid4())
            persistence = Persistence(
                run_id=run_id,
                storage=storage,
                observability=observability
            )

        # Prepare kwargs for function call
        call_kwargs = {**kwargs}
        if self.accepts_shared:
            call_kwargs['shared'] = shared
        if self.accepts_persistence:
            call_kwargs['persistence'] = persistence
        if self.accepts_node:
            call_kwargs['node'] = self

        # Track execution time
        start_time = time.time()

        # Execute function
        try:
            if self.is_async:
                result = await self.func(*args, **call_kwargs)
            else:
                result = await asyncio.to_thread(self.func, *args, **call_kwargs)

            # Record successful execution in history
            duration = time.time() - start_time
            persistence._record_node_execution(
                node_name=self.name,
                input_data=args[0] if args else None,
                output_data=result,
                duration=duration
            )

            return result
        except PauseExecution:
            # Re-raise pause without marking as failed
            raise
        except Exception as e:
            # Record failed execution
            duration = time.time() - start_time
            persistence.set_status("failed", str(e))
            raise

    def __or__(self, other):
        async def piped(*args, shared=None, persistence=None, storage=None, observability=None, **kwargs):
            # Only pass kwargs to the first node, not to subsequent nodes
            result = await self(*args, shared=shared, persistence=persistence, storage=storage, observability=observability, **kwargs)
            return await other(result, shared=shared, persistence=persistence)
        piped_node = Node(piped)
        piped_node.next_node = other  # Set the next node for pause/resume
        return piped_node

    def __sub__(self, condition_map):
        """Overload - for conditional branching syntax"""
        return Conditional(self, condition_map)

    def pause(self, persistence=None):
        """Pause execution"""
        if persistence:
            persistence.pause()


class Parallel(Node):
    def __init__(self, *branches):
        self.branches = branches
        self.name = 'Parallel'
        self.is_async = True
        self.accepts_shared = False
        self.accepts_persistence = False

    async def __call__(self, *args, shared=None, persistence=None, storage=None, observability=None, **kwargs):
        # Create persistence instance if not provided
        if persistence is None:
            run_id = str(uuid.uuid4())
            persistence = Persistence(
                run_id=run_id,
                storage=storage,
                observability=observability
            )
        
        # Track execution time for parallel node
        start_time = time.time()
        
        # Run all branches with same persistence instance (no kwargs for branches)
        tasks = [
            branch(*args, shared=shared, persistence=persistence)
            for branch in self.branches
        ]
        result = await asyncio.gather(*tasks)
        
        # Record parallel execution in history
        duration = time.time() - start_time
        persistence._record_node_execution(
            node_name=self.name,
            input_data=args[0] if args else None,
            output_data=result,
            duration=duration
        )
        
        return result


class Conditional(Node):
    def __init__(self, previous_node, condition_map):
        self.previous_node = previous_node
        self.condition_map = condition_map
        self.name = 'Conditional'
        self.is_async = True
        self.accepts_shared = False
        self.accepts_persistence = False

    async def __call__(self, *args, shared=None, persistence=None, storage=None, observability=None, **kwargs):
        # Create persistence instance if not provided
        if persistence is None:
            run_id = str(uuid.uuid4())
            persistence = Persistence(
                run_id=run_id,
                storage=storage,
                observability=observability
            )
        
        # Track execution time for conditional node
        start_time = time.time()
        
        # Execute previous node to get condition value
        condition_value = await self.previous_node(*args, shared=shared, persistence=persistence, **kwargs)
        
        # Find matching branch (exact match first, then default "")
        branch = self.condition_map.get(condition_value, self.condition_map.get(""))
        
        if branch is None:
            raise ValueError(f"No branch found for condition '{condition_value}' and no default branch provided")
        
        # Execute the selected branch with the condition value as input (no kwargs for branches)
        result = await branch(condition_value, shared=shared, persistence=persistence)
        
        # Record conditional execution in history
        duration = time.time() - start_time
        persistence._record_node_execution(
            node_name=f"{self.name}[{condition_value}]",
            input_data=args[0] if args else None,
            output_data=result,
            duration=duration
        )
        
        return result


### quick test
async def quick_test():
    @Node
    def f1(input, persistence=None):
      print("f1", input)
      if persistence:
          persistence.save("f1_executed", True)
          persistence.save("f1_input", input)
      return f"f1({input})"

    @Node
    def f2(input, persistence=None, node=None):
      print("f2", input)
      if persistence:
          # Can access what f1 saved
          f1_executed = persistence.get("f1_executed", False)
          print(f"  f2 knows f1_executed={f1_executed}")
          # Demonstrate pause - pause after first execution
          if not persistence.get("f2_paused", False):
              persistence.save("f2_paused", True)
              if node:
                  node.pause(persistence)  # Pause using the node instance
      return f"f2({input})"

    @Node
    def f3(input):
      print("f3", input)
      return f"f3({input})"

    @Node
    def concat(input: list):
      return " + ".join(input)

    # Sequential: f1 → f2
    seq1 = f1 | f2

    # Parallel: [f1 → f2, f3]
    parallel = Parallel(seq1, f3)

    # Final: concat → f2
    pipeline = parallel | concat | f2

    result = await pipeline("start")

    return result

async def main():
    print("=== Running Pipeline with Pause Demo ===")

    # First run - should pause at f2
    print("First run (will pause at f2):")
    result = await quick_test()
    print(f"Result: {result}")

    # Check if paused
    all_runs = Persistence.list_runs()
    run_id = list(all_runs.keys())[0] if all_runs else None
    if run_id:
        run_data = all_runs[run_id]
        if run_data.get("status") == "paused":
            print(f"\nPipeline paused at run {run_id}")
            print("Resuming pipeline...")

            # Resume the pipeline
            result = await quick_test()
            print(f"Final result after resume: {result}")

    # Demonstrate persistence tracking
    print("\n=== Persistence Tracking ===")
    all_runs = Persistence.list_runs()
    print(f"Total runs tracked: {len(all_runs)}")

    for run_id, run_data in all_runs.items():
        print(f"\nRun ID: {run_id}")
        print(f"Status: {run_data['status']}")
        print(f"History entries: {len(run_data['history'])}")
        print("Execution flow:")
        for entry in run_data['history']:
            print(f"  - {entry['node_name']}: {entry['duration']:.4f}s")
    

if __name__ == "__main__":
    asyncio.run(main())
