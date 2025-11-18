#!/usr/bin/env python3
"""
Comprehensive Test Runner

Runs all test suites and generates reports.
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime


class TestRunner:
    """Comprehensive test runner."""

    def __init__(self):
        """Initialize test runner."""
        self.results = {}
        self.total_passed = 0
        self.total_failed = 0

    def run_test_file(self, test_file: Path, suite_name: str) -> bool:
        """
        Run a single test file.

        Args:
            test_file: Path to test file
            suite_name: Name of test suite

        Returns:
            True if tests passed
        """
        print(f"\n{'='*80}")
        print(f"Running: {suite_name}")
        print(f"File: {test_file}")
        print('='*80)

        try:
            result = subprocess.run(
                ["python3", str(test_file)],
                capture_output=True,
                text=True,
                timeout=120
            )

            # Print output
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)

            success = result.returncode == 0
            self.results[suite_name] = {
                "success": success,
                "returncode": result.returncode
            }

            return success

        except subprocess.TimeoutExpired:
            print(f"   ⏱️  TIMEOUT: Test exceeded 120 seconds")
            self.results[suite_name] = {
                "success": False,
                "returncode": -1,
                "error": "Timeout"
            }
            return False

        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            self.results[suite_name] = {
                "success": False,
                "returncode": -1,
                "error": str(e)
            }
            return False

    def run_all_tests(self) -> bool:
        """
        Run all test suites.

        Returns:
            True if all tests passed
        """
        print("\n" + "="*80)
        print("METON COMPREHENSIVE TEST SUITE")
        print("="*80)
        print(f"Started: {datetime.now().isoformat()}")
        print("="*80)

        test_suites = [
            # Integration tests
            ("tests/integration/test_end_to_end.py", "End-to-End Integration"),
            ("tests/integration/test_cli_integration.py", "CLI Integration"),

            # Performance tests
            ("tests/performance/test_load.py", "Load & Stress Tests"),
            ("tests/performance/test_benchmarks.py", "Performance Benchmarks"),

            # System tests
            ("tests/system/test_user_scenarios.py", "User Scenarios"),

            # Optimization tests
            ("tests/optimization/test_optimizations.py", "Optimization Tests"),
        ]

        passed = 0
        failed = 0

        for test_file, suite_name in test_suites:
            test_path = Path(test_file)

            if not test_path.exists():
                print(f"\n⚠️  SKIPPED: {suite_name} (file not found: {test_file})")
                continue

            if self.run_test_file(test_path, suite_name):
                passed += 1
            else:
                failed += 1

        # Summary
        self.print_summary(passed, failed)

        return failed == 0

    def print_summary(self, passed: int, failed: int):
        """
        Print test summary.

        Args:
            passed: Number of passed test suites
            failed: Number of failed test suites
        """
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Completed: {datetime.now().isoformat()}")
        print("-"*80)

        for suite_name, result in self.results.items():
            status = "✅ PASSED" if result["success"] else "❌ FAILED"
            print(f"{suite_name:40s} {status}")

            if not result["success"] and "error" in result:
                print(f"  Error: {result['error']}")

        print("-"*80)
        total = passed + failed
        pass_rate = (passed / total * 100) if total > 0 else 0

        print(f"\nTotal Suites: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Pass Rate: {pass_rate:.1f}%")

        print("\n" + "="*80)

        if failed == 0:
            print("✅ ALL TEST SUITES PASSED!")
        else:
            print(f"❌ {failed} TEST SUITE(S) FAILED")

        print("="*80 + "\n")


def main():
    """Main entry point."""
    runner = TestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
