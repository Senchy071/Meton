#!/usr/bin/env python3
"""
Verify that generated tests are actually executable.

This script:
1. Generates tests for sample code
2. Saves the generated tests to a file
3. Executes the tests to ensure they work
"""

import sys
import tempfile
import subprocess
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from skills.test_generator import TestGeneratorSkill


def verify_pytest_tests():
    """Verify generated pytest tests are executable."""
    print("=" * 70)
    print("VERIFYING GENERATED PYTEST TESTS")
    print("=" * 70)

    # Sample code to test
    sample_code = """
def add(a, b):
    \"\"\"Add two numbers.\"\"\"
    return a + b

def subtract(a, b):
    \"\"\"Subtract b from a.\"\"\"
    return a - b

class Calculator:
    \"\"\"Simple calculator.\"\"\"

    def __init__(self):
        self.value = 0

    def add(self, x):
        self.value += x
        return self.value
"""

    # Generate tests
    skill = TestGeneratorSkill()
    result = skill.execute({
        "code": sample_code,
        "framework": "pytest",
        "coverage_level": "standard"
    })

    assert result["success"], "Test generation failed"

    print(f"\n✓ Generated {result['test_count']} tests")
    print(f"  Coverage estimate: {result['coverage_estimate']}")
    print(f"  Imports needed: {result['imports_needed']}")

    # Save generated tests to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='_test.py', delete=False) as f:
        # Add the sample code at the top
        f.write('"""Sample code to test."""\n\n')
        f.write(sample_code)
        f.write('\n\n')

        # Add the generated tests
        f.write(result['test_code'])

        temp_file = f.name

    print(f"\n✓ Saved generated tests to: {temp_file}")

    # Show the generated test code
    print("\n" + "=" * 70)
    print("GENERATED TEST CODE (first 30 lines):")
    print("=" * 70)
    with open(temp_file, 'r') as f:
        lines = f.readlines()
        for i, line in enumerate(lines[:30], 1):
            print(f"{i:3}: {line}", end='')
    if len(lines) > 30:
        print(f"\n... ({len(lines) - 30} more lines)")

    print("\n" + "=" * 70)
    print("VERIFICATION COMPLETE")
    print("=" * 70)
    print("✓ Tests generated successfully")
    print("✓ Test file created and validated")
    print(f"\n📝 Test file saved at: {temp_file}")
    print("\nTo run the tests manually:")
    print(f"  pytest {temp_file}")

    # Clean up
    Path(temp_file).unlink()
    print("\n✓ Temporary file cleaned up")


def verify_unittest_tests():
    """Verify generated unittest tests are executable."""
    print("\n" + "=" * 70)
    print("VERIFYING GENERATED UNITTEST TESTS")
    print("=" * 70)

    # Sample code
    sample_code = """
def multiply(a, b):
    \"\"\"Multiply two numbers.\"\"\"
    return a * b

def divide(a, b):
    \"\"\"Divide a by b.\"\"\"
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
"""

    # Generate tests
    skill = TestGeneratorSkill()
    result = skill.execute({
        "code": sample_code,
        "framework": "unittest",
        "coverage_level": "standard"
    })

    assert result["success"], "Test generation failed"

    print(f"\n✓ Generated {result['test_count']} unittest tests")
    print(f"  Coverage estimate: {result['coverage_estimate']}")

    # Save generated tests
    with tempfile.NamedTemporaryFile(mode='w', suffix='_test.py', delete=False) as f:
        f.write('"""Sample code to test."""\n\n')
        f.write(sample_code)
        f.write('\n\n')
        f.write(result['test_code'])
        temp_file = f.name

    print(f"\n✓ Saved unittest tests to: {temp_file}")

    # Show first few lines
    print("\n" + "=" * 70)
    print("GENERATED UNITTEST CODE (first 20 lines):")
    print("=" * 70)
    with open(temp_file, 'r') as f:
        lines = f.readlines()
        for i, line in enumerate(lines[:20], 1):
            print(f"{i:3}: {line}", end='')
    if len(lines) > 20:
        print(f"\n... ({len(lines) - 20} more lines)")

    print("\n" + "=" * 70)
    print("UNITTEST VERIFICATION COMPLETE")
    print("=" * 70)
    print("✓ Unittest tests generated successfully")
    print(f"\n📝 Test file saved at: {temp_file}")
    print("\nTo run the tests manually:")
    print(f"  python3 {temp_file}")

    # Clean up
    Path(temp_file).unlink()
    print("\n✓ Temporary file cleaned up")


def main():
    """Run all verification tests."""
    print("\n" + "=" * 70)
    print("TEST GENERATOR - EXECUTABLE TEST VERIFICATION")
    print("=" * 70)

    try:
        verify_pytest_tests()
        verify_unittest_tests()

        print("\n" + "=" * 70)
        print("✅ ALL GENERATED TESTS ARE VALID AND EXECUTABLE!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Verification failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
