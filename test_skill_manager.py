#!/usr/bin/env python3
"""
Test suite for Skill Manager

Tests the dynamic skill loading and management capabilities including:
- Skill discovery
- Loading and unloading skills
- Reloading skills
- Listing operations
- Error handling
- Bulk operations (load all, unload all)
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from skills.skill_manager import SkillManager, SkillManagerError
from skills.base import BaseSkill


def test_initialization():
    """Test SkillManager initialization."""
    print("\n" + "=" * 70)
    print("TEST: Skill Manager Initialization")
    print("=" * 70)

    manager = SkillManager()

    assert manager.skills_dir is not None
    assert isinstance(manager.loaded_skills, dict)
    assert isinstance(manager.available_skills, dict)

    print("✓ SkillManager initialized successfully")
    print(f"  Skills directory: {manager.skills_dir}")
    print(f"  Available skills: {len(manager.available_skills)}")


def test_skill_discovery():
    """Test that skills are discovered."""
    print("\n" + "=" * 70)
    print("TEST: Skill Discovery")
    print("=" * 70)

    manager = SkillManager()

    available = manager.list_available_skills()

    # Should find at least the skills we've created
    expected_skills = [
        "code_explainer",
        "debugger",
        "refactoring_engine",
        "test_generator",
        "documentation_generator",
        "code_reviewer"
    ]

    for skill in expected_skills:
        assert skill in available, f"Expected skill '{skill}' not found"

    print(f"✓ Discovered {len(available)} skills")
    print(f"  Skills found: {', '.join(available[:5])}...")


def test_load_single_skill():
    """Test loading a single skill."""
    print("\n" + "=" * 70)
    print("TEST: Load Single Skill")
    print("=" * 70)

    manager = SkillManager()

    # Load code_explainer skill
    success = manager.load_skill("code_explainer")

    assert success is True
    assert "code_explainer" in manager.loaded_skills
    assert manager.is_loaded("code_explainer")

    # Get the skill instance
    skill = manager.get_skill("code_explainer")
    assert skill is not None
    assert isinstance(skill, BaseSkill)
    assert skill.name == "code_explainer"

    print("✓ Successfully loaded code_explainer skill")
    print(f"  Skill instance: {skill}")


def test_unload_skill():
    """Test unloading a skill."""
    print("\n" + "=" * 70)
    print("TEST: Unload Skill")
    print("=" * 70)

    manager = SkillManager()

    # Load then unload
    manager.load_skill("code_explainer")
    assert manager.is_loaded("code_explainer")

    success = manager.unload_skill("code_explainer")

    assert success is True
    assert "code_explainer" not in manager.loaded_skills
    assert not manager.is_loaded("code_explainer")

    print("✓ Successfully unloaded code_explainer skill")


def test_unload_not_loaded():
    """Test unloading a skill that isn't loaded."""
    print("\n" + "=" * 70)
    print("TEST: Unload Not Loaded Skill")
    print("=" * 70)

    manager = SkillManager()

    # Try to unload skill that isn't loaded
    success = manager.unload_skill("code_explainer")

    assert success is False

    print("✓ Correctly handled unloading non-loaded skill")


def test_reload_skill():
    """Test reloading a skill."""
    print("\n" + "=" * 70)
    print("TEST: Reload Skill")
    print("=" * 70)

    manager = SkillManager()

    # Load skill
    manager.load_skill("code_explainer")
    skill1 = manager.get_skill("code_explainer")

    # Reload skill
    success = manager.reload_skill("code_explainer")
    skill2 = manager.get_skill("code_explainer")

    assert success is True
    assert skill2 is not None
    assert skill2 is not skill1  # Different instance

    print("✓ Successfully reloaded skill")
    print(f"  Old instance: {id(skill1)}")
    print(f"  New instance: {id(skill2)}")


def test_load_invalid_skill():
    """Test loading a non-existent skill."""
    print("\n" + "=" * 70)
    print("TEST: Load Invalid Skill")
    print("=" * 70)

    manager = SkillManager()

    success = manager.load_skill("nonexistent_skill")

    assert success is False
    assert "nonexistent_skill" not in manager.loaded_skills

    print("✓ Correctly handled loading invalid skill")


def test_load_already_loaded():
    """Test loading a skill that's already loaded."""
    print("\n" + "=" * 70)
    print("TEST: Load Already Loaded Skill")
    print("=" * 70)

    manager = SkillManager()

    # Load skill twice
    success1 = manager.load_skill("code_explainer")
    success2 = manager.load_skill("code_explainer")

    assert success1 is True
    assert success2 is True
    assert manager.get_loaded_count() == 1

    print("✓ Correctly handled loading already-loaded skill")


def test_list_loaded_skills():
    """Test listing loaded skills."""
    print("\n" + "=" * 70)
    print("TEST: List Loaded Skills")
    print("=" * 70)

    manager = SkillManager()

    # Initially empty
    loaded = manager.list_loaded_skills()
    assert len(loaded) == 0

    # Load some skills
    manager.load_skill("code_explainer")
    manager.load_skill("debugger")

    loaded = manager.list_loaded_skills()
    assert len(loaded) == 2
    assert "code_explainer" in loaded
    assert "debugger" in loaded

    print(f"✓ Correctly listed {len(loaded)} loaded skills")
    print(f"  Loaded: {', '.join(loaded)}")


def test_list_available_skills():
    """Test listing available skills."""
    print("\n" + "=" * 70)
    print("TEST: List Available Skills")
    print("=" * 70)

    manager = SkillManager()

    available = manager.list_available_skills()

    assert len(available) > 0
    assert "code_explainer" in available

    print(f"✓ Found {len(available)} available skills")


def test_get_skill_not_loaded():
    """Test getting a skill that isn't loaded."""
    print("\n" + "=" * 70)
    print("TEST: Get Not Loaded Skill")
    print("=" * 70)

    manager = SkillManager()

    skill = manager.get_skill("code_explainer")

    assert skill is None

    print("✓ Correctly returned None for non-loaded skill")


def test_load_all_skills():
    """Test loading all available skills."""
    print("\n" + "=" * 70)
    print("TEST: Load All Skills")
    print("=" * 70)

    manager = SkillManager()

    available_count = len(manager.list_available_skills())
    loaded_count = manager.load_all_skills()

    assert loaded_count > 0
    assert loaded_count == available_count
    assert manager.get_loaded_count() == available_count

    print(f"✓ Successfully loaded all {loaded_count} skills")


def test_unload_all_skills():
    """Test unloading all skills."""
    print("\n" + "=" * 70)
    print("TEST: Unload All Skills")
    print("=" * 70)

    manager = SkillManager()

    # Load all skills first
    manager.load_all_skills()
    initial_count = manager.get_loaded_count()

    # Unload all
    unloaded_count = manager.unload_all_skills()

    assert unloaded_count == initial_count
    assert manager.get_loaded_count() == 0
    assert len(manager.list_loaded_skills()) == 0

    print(f"✓ Successfully unloaded all {unloaded_count} skills")


def test_get_skill_info():
    """Test getting skill information."""
    print("\n" + "=" * 70)
    print("TEST: Get Skill Info")
    print("=" * 70)

    manager = SkillManager()

    manager.load_skill("code_explainer")
    info = manager.get_skill_info("code_explainer")

    assert info is not None
    assert "name" in info
    assert "description" in info
    assert "version" in info
    assert info["name"] == "code_explainer"

    print("✓ Successfully retrieved skill info")
    print(f"  Name: {info['name']}")
    print(f"  Description: {info['description'][:50]}...")


def test_get_skill_info_not_loaded():
    """Test getting info for non-loaded skill."""
    print("\n" + "=" * 70)
    print("TEST: Get Info - Not Loaded Skill")
    print("=" * 70)

    manager = SkillManager()

    info = manager.get_skill_info("code_explainer")

    assert info is None

    print("✓ Correctly returned None for non-loaded skill info")


def test_is_loaded():
    """Test is_loaded check."""
    print("\n" + "=" * 70)
    print("TEST: Is Loaded Check")
    print("=" * 70)

    manager = SkillManager()

    # Not loaded initially
    assert not manager.is_loaded("code_explainer")

    # Load it
    manager.load_skill("code_explainer")
    assert manager.is_loaded("code_explainer")

    # Unload it
    manager.unload_skill("code_explainer")
    assert not manager.is_loaded("code_explainer")

    print("✓ is_loaded() works correctly")


def test_is_available():
    """Test is_available check."""
    print("\n" + "=" * 70)
    print("TEST: Is Available Check")
    print("=" * 70)

    manager = SkillManager()

    # Should be available
    assert manager.is_available("code_explainer")

    # Should not be available
    assert not manager.is_available("nonexistent_skill")

    print("✓ is_available() works correctly")


def test_rediscover_skills():
    """Test rediscovering skills."""
    print("\n" + "=" * 70)
    print("TEST: Rediscover Skills")
    print("=" * 70)

    manager = SkillManager()

    initial_count = len(manager.list_available_skills())

    # Rediscover (should find same skills)
    new_count = manager.rediscover_skills()

    # No new skills should be found
    assert new_count == 0
    assert len(manager.list_available_skills()) == initial_count

    print(f"✓ Rediscovery works (found {new_count} new skills)")


def test_get_loaded_count():
    """Test getting loaded skill count."""
    print("\n" + "=" * 70)
    print("TEST: Get Loaded Count")
    print("=" * 70)

    manager = SkillManager()

    assert manager.get_loaded_count() == 0

    manager.load_skill("code_explainer")
    assert manager.get_loaded_count() == 1

    manager.load_skill("debugger")
    assert manager.get_loaded_count() == 2

    manager.unload_skill("code_explainer")
    assert manager.get_loaded_count() == 1

    print("✓ get_loaded_count() works correctly")


def test_get_available_count():
    """Test getting available skill count."""
    print("\n" + "=" * 70)
    print("TEST: Get Available Count")
    print("=" * 70)

    manager = SkillManager()

    count = manager.get_available_count()

    assert count > 0
    assert count == len(manager.list_available_skills())

    print(f"✓ get_available_count() returns {count}")


def test_multiple_load_unload():
    """Test multiple load/unload cycles."""
    print("\n" + "=" * 70)
    print("TEST: Multiple Load/Unload Cycles")
    print("=" * 70)

    manager = SkillManager()

    # Cycle 1
    manager.load_skill("code_explainer")
    assert manager.is_loaded("code_explainer")
    manager.unload_skill("code_explainer")
    assert not manager.is_loaded("code_explainer")

    # Cycle 2
    manager.load_skill("code_explainer")
    assert manager.is_loaded("code_explainer")
    manager.unload_skill("code_explainer")
    assert not manager.is_loaded("code_explainer")

    # Cycle 3
    manager.load_skill("code_explainer")
    assert manager.is_loaded("code_explainer")

    print("✓ Multiple load/unload cycles work correctly")


def test_skill_execution():
    """Test executing a loaded skill."""
    print("\n" + "=" * 70)
    print("TEST: Skill Execution")
    print("=" * 70)

    manager = SkillManager()

    manager.load_skill("code_explainer")
    skill = manager.get_skill("code_explainer")

    # Execute the skill
    result = skill.execute({
        "code": "def add(a, b):\n    return a + b"
    })

    assert result is not None
    assert result["success"] is True
    assert "summary" in result

    print("✓ Successfully executed loaded skill")
    print(f"  Result success: {result['success']}")


def test_repr():
    """Test string representation."""
    print("\n" + "=" * 70)
    print("TEST: String Representation")
    print("=" * 70)

    manager = SkillManager()

    repr_str = repr(manager)

    assert "SkillManager" in repr_str
    assert "loaded=" in repr_str
    assert "available=" in repr_str

    print(f"✓ String representation: {repr_str}")


def test_load_multiple_skills():
    """Test loading multiple different skills."""
    print("\n" + "=" * 70)
    print("TEST: Load Multiple Skills")
    print("=" * 70)

    manager = SkillManager()

    skills_to_load = ["code_explainer", "debugger", "refactoring_engine"]

    for skill_name in skills_to_load:
        success = manager.load_skill(skill_name)
        assert success is True

    loaded = manager.list_loaded_skills()
    assert len(loaded) == len(skills_to_load)

    for skill_name in skills_to_load:
        assert skill_name in loaded

    print(f"✓ Successfully loaded {len(skills_to_load)} different skills")


def test_skill_independence():
    """Test that skills are independent instances."""
    print("\n" + "=" * 70)
    print("TEST: Skill Independence")
    print("=" * 70)

    manager = SkillManager()

    manager.load_skill("code_explainer")
    manager.load_skill("debugger")

    skill1 = manager.get_skill("code_explainer")
    skill2 = manager.get_skill("debugger")

    assert skill1 is not skill2
    assert skill1.name != skill2.name

    print("✓ Skills are independent instances")
    print(f"  Skill 1: {skill1.name}")
    print(f"  Skill 2: {skill2.name}")


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "=" * 80)
    print(" " * 25 + "SKILL MANAGER TEST SUITE")
    print("=" * 80)

    tests = [
        ("Initialization", test_initialization),
        ("Skill Discovery", test_skill_discovery),
        ("Load Single Skill", test_load_single_skill),
        ("Unload Skill", test_unload_skill),
        ("Unload Not Loaded", test_unload_not_loaded),
        ("Reload Skill", test_reload_skill),
        ("Load Invalid Skill", test_load_invalid_skill),
        ("Load Already Loaded", test_load_already_loaded),
        ("List Loaded Skills", test_list_loaded_skills),
        ("List Available Skills", test_list_available_skills),
        ("Get Not Loaded Skill", test_get_skill_not_loaded),
        ("Load All Skills", test_load_all_skills),
        ("Unload All Skills", test_unload_all_skills),
        ("Get Skill Info", test_get_skill_info),
        ("Get Info Not Loaded", test_get_skill_info_not_loaded),
        ("Is Loaded Check", test_is_loaded),
        ("Is Available Check", test_is_available),
        ("Rediscover Skills", test_rediscover_skills),
        ("Get Loaded Count", test_get_loaded_count),
        ("Get Available Count", test_get_available_count),
        ("Multiple Load/Unload", test_multiple_load_unload),
        ("Skill Execution", test_skill_execution),
        ("String Representation", test_repr),
        ("Load Multiple Skills", test_load_multiple_skills),
        ("Skill Independence", test_skill_independence),
    ]

    passed = 0
    failed = 0
    errors = []

    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            failed += 1
            errors.append((test_name, str(e)))
            print(f"\n✗ FAILED: {test_name}")
            print(f"  {str(e)}")
        except Exception as e:
            failed += 1
            errors.append((test_name, str(e)))
            print(f"\n✗ ERROR: {test_name}")
            print(f"  {str(e)}")

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if errors:
        print("\nFailed tests:")
        for test_name, error in errors:
            print(f"  - {test_name}: {error}")
    else:
        print("\n✅ All Skill Manager tests passed!")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
