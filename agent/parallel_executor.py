#!/usr/bin/env python3
"""
Parallel Tool Executor for Meton.

Executes independent tools concurrently for faster responses through:
- Automatic dependency detection between tool calls
- Parallel execution of independent tools using ThreadPoolExecutor
- Sequential execution of dependent tools in correct order
- Timeout handling and error recovery
- Performance statistics tracking

Example:
    executor = ParallelToolExecutor(tools, config)

    # Execute multiple tools
    tool_calls = [
        {"tool": "web_search", "args": {"query": "Python async"}},
        {"tool": "codebase_search", "args": {"query": "authentication"}},
        {"tool": "web_search", "args": {"query": "FastAPI tutorial"}}
    ]

    results = executor.execute_parallel(tool_calls)
    # All 3 execute concurrently (~3x speedup)
"""

import time
from concurrent.futures import ThreadPoolExecutor, Future, TimeoutError as FutureTimeoutError
from typing import Dict, List, Any, Callable, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict
import threading


@dataclass
class ExecutionRecord:
    """Record of a single execution."""
    tool_calls: List[Dict]
    sequential_time: float
    parallel_time: float
    speedup: float
    independent_count: int
    dependent_count: int
    timeout_count: int = 0
    error_count: int = 0


class ParallelToolExecutor:
    """Executes independent tools concurrently for faster responses.

    Features:
    - Automatic dependency detection between tool calls
    - Parallel execution using ThreadPoolExecutor
    - Sequential execution for dependent tools
    - Timeout handling per tool
    - Error recovery (partial results)
    - Performance statistics and speedup tracking
    - Thread-safe execution

    The executor analyzes tool calls to determine which can run concurrently
    and which must run sequentially due to dependencies.
    """

    # Dependency rules
    # Tools that can always run in parallel with each other
    # Pairs must be in sorted order for tuple(sorted([name1, name2])) comparison
    ALWAYS_INDEPENDENT = {
        ("codebase_search", "codebase_search"),
        ("codebase_search", "web_search"),  # Sorted: codebase_search < web_search
        ("web_search", "web_search"),
    }

    # Tools that write data (may create dependencies)
    WRITERS = {"file_operations"}

    # Tools that execute code (depend on file writes)
    EXECUTORS = {"code_executor"}

    def __init__(self, tools: Dict[str, Callable], config: Dict):
        """Initialize parallel tool executor.

        Args:
            tools: Dictionary mapping tool names to callable tools
            config: Configuration dictionary with parallel_execution settings
        """
        self.tools = tools
        self.config = config

        # Get parallel execution config
        parallel_config = config.get("parallel_execution", {})
        max_workers = parallel_config.get("max_parallel_tools", 3)
        self.timeout = parallel_config.get("timeout_per_tool", 30)
        self.fallback_to_sequential = parallel_config.get("fallback_to_sequential", True)

        # Thread pool for parallel execution
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # Statistics tracking
        self._lock = threading.Lock()
        self.execution_history: List[ExecutionRecord] = []
        self.tool_execution_times: Dict[str, List[float]] = defaultdict(list)
        self.timeout_count = 0
        self.error_count = 0

    def execute_parallel(self, tool_calls: List[Dict]) -> Dict[str, Any]:
        """Execute tools in parallel where possible.

        Args:
            tool_calls: List of tool call dicts with "tool" and "args" keys
                Example: [{"tool": "web_search", "args": {"query": "..."}}]

        Returns:
            Dictionary mapping tool names to results or errors
            Example: {"web_search": {...}, "codebase_search": {...}}
        """
        if not tool_calls:
            return {}

        # Single tool - no parallelization needed
        if len(tool_calls) == 1:
            call = tool_calls[0]
            tool_name = call["tool"]
            args = call.get("args", {})

            start_time = time.time()
            result = self._execute_single_tool(tool_name, args, self.timeout)
            execution_time = time.time() - start_time

            self._record_tool_time(tool_name, execution_time)

            return {tool_name: result}

        # Multiple tools - analyze dependencies
        try:
            start_time = time.time()

            dependency_info = self._analyze_dependencies(tool_calls)
            independent_calls = dependency_info["independent"]
            dependent_groups = dependency_info["dependent"]

            results = {}

            # Execute independent tools in parallel
            if independent_calls:
                parallel_results = self._execute_independent_batch(independent_calls)
                results.update(parallel_results)

            # Execute dependent tools sequentially
            if dependent_groups:
                sequential_results = self._execute_sequential(dependent_groups, results)
                results.update(sequential_results)

            # Calculate statistics
            parallel_time = time.time() - start_time
            sequential_time = sum(
                sum(self.tool_execution_times.get(call["tool"], [0])[-1:])
                for call in tool_calls
            )

            # Record execution
            self._record_execution(
                tool_calls=tool_calls,
                sequential_time=sequential_time,
                parallel_time=parallel_time,
                independent_count=len(independent_calls),
                dependent_count=len(dependent_groups)
            )

            return results

        except Exception as e:
            # Fallback to sequential execution
            if self.fallback_to_sequential:
                return self._fallback_sequential(tool_calls)
            else:
                raise RuntimeError(f"Parallel execution failed: {e}")

    def _analyze_dependencies(self, tool_calls: List[Dict]) -> Dict:
        """Analyze dependencies between tool calls.

        Args:
            tool_calls: List of tool call dicts

        Returns:
            Dictionary with:
            - "independent": List of independent tool calls
            - "dependent": List of dependent tool call groups
        """
        independent = []
        dependent = []

        # Track file operations
        file_writes = []  # [(index, path), ...]
        file_reads = []   # [(index, path), ...]

        # First pass: categorize all calls
        for i, call in enumerate(tool_calls):
            tool_name = call["tool"]
            args = call.get("args", {})

            # Track file operations
            if tool_name == "file_operations":
                action = args.get("action", "")
                path = args.get("path", "")

                if action in ["write", "create_dir"]:
                    file_writes.append((i, path))
                elif action in ["read", "list", "get_info"]:
                    file_reads.append((i, path))

        # Second pass: determine independence
        for i, call in enumerate(tool_calls):
            tool_name = call["tool"]
            args = call.get("args", {})

            # Check if this call depends on previous calls
            has_dependency = False

            # Check for file dependencies
            if tool_name == "code_executor":
                # Code executor depends on file writes
                code = args.get("code", "")
                for write_idx, write_path in file_writes:
                    if write_idx < i and write_path in code:
                        has_dependency = True
                        dependent.append(call)
                        break

            elif tool_name == "file_operations":
                action = args.get("action", "")
                path = args.get("path", "")

                if action in ["read", "get_info"]:
                    # Read depends on writes to same file
                    for write_idx, write_path in file_writes:
                        if write_idx < i and write_path == path:
                            has_dependency = True
                            dependent.append(call)
                            break

            # If no dependency found, check if independent with all others
            if not has_dependency:
                can_parallelize = True

                for j, other_call in enumerate(tool_calls):
                    if i != j:
                        if not self._is_independent(call, other_call):
                            can_parallelize = False
                            break

                if can_parallelize:
                    independent.append(call)
                else:
                    # Conservative: if unsure, make it dependent
                    dependent.append(call)

        return {
            "independent": independent,
            "dependent": dependent
        }

    def _is_independent(self, tool1: Dict, tool2: Dict) -> bool:
        """Check if two tools can run concurrently.

        Args:
            tool1: First tool call dict
            tool2: Second tool call dict

        Returns:
            True if tools are independent, False otherwise
        """
        name1 = tool1["tool"]
        name2 = tool2["tool"]

        # Check always-independent pairs
        pair = tuple(sorted([name1, name2]))
        if pair in self.ALWAYS_INDEPENDENT:
            return True

        # Same tool type that's in always-independent set
        if name1 == name2:
            if (name1, name1) in self.ALWAYS_INDEPENDENT:
                return True

        # File operations analysis
        if name1 == "file_operations" or name2 == "file_operations":
            args1 = tool1.get("args", {})
            args2 = tool2.get("args", {})

            # Get actions and paths
            action1 = args1.get("action", "") if name1 == "file_operations" else ""
            action2 = args2.get("action", "") if name2 == "file_operations" else ""
            path1 = args1.get("path", "") if name1 == "file_operations" else ""
            path2 = args2.get("path", "") if name2 == "file_operations" else ""

            # Write operations create dependencies
            if action1 in ["write", "create_dir"] or action2 in ["write", "create_dir"]:
                # If paths are different, they're independent
                if path1 and path2 and path1 != path2:
                    # Unless one is code_executor using the written file
                    if name1 == "code_executor":
                        code = args1.get("code", "")
                        if path2 in code:
                            return False
                    if name2 == "code_executor":
                        code = args2.get("code", "")
                        if path1 in code:
                            return False
                    return True
                return False  # Same path or unknown - dependent

            # Both reads are independent
            if action1 == "read" and action2 == "read":
                return True

            # Read + search tools are independent
            if action1 == "read" and name2 in ["web_search", "codebase_search"]:
                return True
            if action2 == "read" and name1 in ["web_search", "codebase_search"]:
                return True

        # Code executor is dependent on most other tools
        if name1 in self.EXECUTORS or name2 in self.EXECUTORS:
            return False

        # Default: assume dependent (conservative)
        return False

    def _execute_independent_batch(self, tool_calls: List[Dict]) -> Dict[str, Any]:
        """Execute independent tools in parallel.

        Args:
            tool_calls: List of independent tool calls

        Returns:
            Dictionary mapping tool names to results
        """
        if not tool_calls:
            return {}

        # Submit all tasks
        futures: Dict[str, Tuple[Future, Dict, float]] = {}

        for call in tool_calls:
            tool_name = call["tool"]
            args = call.get("args", {})

            # Generate unique key for this call
            call_key = f"{tool_name}_{id(call)}"

            start_time = time.time()
            future = self.executor.submit(
                self._execute_single_tool,
                tool_name,
                args,
                self.timeout
            )

            futures[call_key] = (future, call, start_time)

        # Collect results
        results = {}

        for call_key, (future, call, start_time) in futures.items():
            tool_name = call["tool"]

            try:
                result = future.result(timeout=self.timeout + 5)
                execution_time = time.time() - start_time

                self._record_tool_time(tool_name, execution_time)

                # Use tool name as key (may overwrite if same tool called multiple times)
                results[tool_name] = result

            except FutureTimeoutError:
                with self._lock:
                    self.timeout_count += 1

                results[tool_name] = {
                    "error": f"Timeout after {self.timeout}s",
                    "tool": tool_name
                }
            except Exception as e:
                with self._lock:
                    self.error_count += 1

                results[tool_name] = {
                    "error": str(e),
                    "tool": tool_name
                }

        return results

    def _execute_sequential(
        self,
        tool_calls: List[Dict],
        previous_results: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute dependent tools sequentially.

        Args:
            tool_calls: List of dependent tool calls
            previous_results: Results from previous executions (for dependencies)

        Returns:
            Dictionary mapping tool names to results
        """
        if previous_results is None:
            previous_results = {}

        results = {}

        for call in tool_calls:
            tool_name = call["tool"]
            args = call.get("args", {})

            start_time = time.time()
            result = self._execute_single_tool(tool_name, args, self.timeout)
            execution_time = time.time() - start_time

            self._record_tool_time(tool_name, execution_time)
            results[tool_name] = result

        return results

    def _execute_single_tool(
        self,
        tool_name: str,
        args: Dict,
        timeout: int = 30
    ) -> Any:
        """Execute a single tool with timeout.

        Args:
            tool_name: Name of tool to execute
            args: Arguments for the tool
            timeout: Timeout in seconds

        Returns:
            Tool result or error dict
        """
        if tool_name not in self.tools:
            return {
                "error": f"Tool '{tool_name}' not found",
                "tool": tool_name
            }

        tool = self.tools[tool_name]

        try:
            # Execute tool (tools should handle their own timeouts)
            result = tool.run(args) if hasattr(tool, "run") else tool(args)
            return result

        except Exception as e:
            with self._lock:
                self.error_count += 1

            return {
                "error": str(e),
                "tool": tool_name
            }

    def _fallback_sequential(self, tool_calls: List[Dict]) -> Dict[str, Any]:
        """Fallback to sequential execution if parallel fails.

        Args:
            tool_calls: List of tool calls

        Returns:
            Dictionary mapping tool names to results
        """
        results = {}

        for call in tool_calls:
            tool_name = call["tool"]
            args = call.get("args", {})

            start_time = time.time()
            result = self._execute_single_tool(tool_name, args, self.timeout)
            execution_time = time.time() - start_time

            self._record_tool_time(tool_name, execution_time)
            results[tool_name] = result

        return results

    def _record_tool_time(self, tool_name: str, execution_time: float) -> None:
        """Record execution time for a tool.

        Args:
            tool_name: Name of tool
            execution_time: Execution time in seconds
        """
        with self._lock:
            self.tool_execution_times[tool_name].append(execution_time)

    def _record_execution(
        self,
        tool_calls: List[Dict],
        sequential_time: float,
        parallel_time: float,
        independent_count: int,
        dependent_count: int
    ) -> None:
        """Record execution statistics.

        Args:
            tool_calls: List of tool calls executed
            sequential_time: Estimated sequential execution time
            parallel_time: Actual parallel execution time
            independent_count: Number of independent tools
            dependent_count: Number of dependent tools
        """
        speedup = sequential_time / parallel_time if parallel_time > 0 else 1.0

        record = ExecutionRecord(
            tool_calls=tool_calls,
            sequential_time=sequential_time,
            parallel_time=parallel_time,
            speedup=speedup,
            independent_count=independent_count,
            dependent_count=dependent_count
        )

        with self._lock:
            self.execution_history.append(record)

    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics.

        Returns:
            Dictionary with statistics:
            - total_executions: Total parallel executions
            - average_speedup: Average speedup (parallel vs sequential)
            - tool_execution_times: Average time per tool
            - timeout_count: Total timeouts
            - error_count: Total errors
            - total_independent: Total independent tool executions
            - total_dependent: Total dependent tool executions
        """
        with self._lock:
            if not self.execution_history:
                return {
                    "total_executions": 0,
                    "average_speedup": 0.0,
                    "tool_execution_times": {},
                    "timeout_count": 0,
                    "error_count": 0,
                    "total_independent": 0,
                    "total_dependent": 0
                }

            # Calculate averages
            total_speedup = sum(r.speedup for r in self.execution_history)
            avg_speedup = total_speedup / len(self.execution_history)

            # Average tool execution times
            avg_tool_times = {}
            for tool_name, times in self.tool_execution_times.items():
                avg_tool_times[tool_name] = sum(times) / len(times) if times else 0.0

            # Count independent and dependent
            total_independent = sum(r.independent_count for r in self.execution_history)
            total_dependent = sum(r.dependent_count for r in self.execution_history)

            return {
                "total_executions": len(self.execution_history),
                "average_speedup": avg_speedup,
                "tool_execution_times": avg_tool_times,
                "timeout_count": self.timeout_count,
                "error_count": self.error_count,
                "total_independent": total_independent,
                "total_dependent": total_dependent
            }

    def reset_stats(self) -> None:
        """Reset all statistics."""
        with self._lock:
            self.execution_history = []
            self.tool_execution_times = defaultdict(list)
            self.timeout_count = 0
            self.error_count = 0

    def shutdown(self) -> None:
        """Shutdown the thread pool executor."""
        self.executor.shutdown(wait=True)
