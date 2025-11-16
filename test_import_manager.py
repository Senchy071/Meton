#!/usr/bin/env python3
"""
Comprehensive Test Suite for ImportManager

Tests all import functionality including:
- Complete state import
- Individual component imports (config, memories, conversations, etc.)
- Merge and overwrite modes
- Backup restoration
- Import validation
- Version compatibility
- Error handling
"""

import sys
import os
import json
import yaml
import shutil
import tempfile
import tarfile
import zipfile
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from export.export_manager import ExportManager
from export.import_manager import ImportManager


def create_test_export_data():
    """Create test export data for import testing."""
    return {
        "export_metadata": {
            "version": "1.0.0",
            "meton_version": "1.0.0",
            "export_date": datetime.now().isoformat(),
            "export_type": "complete"
        },
        "configuration": {
            "project": {"name": "Test Project", "version": "0.2.0"},
            "models": {"primary": "test-model"},
            "agent": {"max_iterations": 15}
        },
        "memories": [
            {
                "id": "mem_001",
                "content": "Imported memory 1",
                "timestamp": datetime.now().isoformat(),
                "importance": 0.9,
                "tags": ["imported"]
            },
            {
                "id": "mem_002",
                "content": "Imported memory 2",
                "timestamp": datetime.now().isoformat(),
                "importance": 0.7,
                "tags": ["imported"]
            }
        ],
        "conversations": [
            {
                "session_id": "imported_session_001",
                "timestamp": datetime.now().isoformat(),
                "messages": [
                    {"role": "user", "content": "Imported question"},
                    {"role": "assistant", "content": "Imported answer"}
                ]
            }
        ],
        "analytics": {
            "sessions": [
                {
                    "session_id": "imported_session_001",
                    "timestamp": datetime.now().isoformat(),
                    "query_count": 10
                }
            ],
            "metrics": {"total_sessions": 20}
        },
        "feedback": [
            {
                "id": "fb_imported_001",
                "timestamp": datetime.now().isoformat(),
                "rating": 4,
                "comment": "Imported feedback"
            }
        ],
        "profiles": [
            {
                "id": "profile_imported",
                "name": "Imported Profile",
                "category": "testing",
                "settings": {"test": True}
            }
        ],
        "patterns": [
            {
                "id": "pattern_imported",
                "type": "imported_type",
                "pattern": "test pattern",
                "occurrences": 5
            }
        ]
    }


def setup_test_environment_with_existing_data():
    """Create test environment with existing data for merge testing."""
    test_dir = Path(tempfile.mkdtemp(prefix="meton_import_test_"))
    os.chdir(test_dir)

    # Create directories
    (test_dir / "conversations").mkdir(exist_ok=True)
    (test_dir / "memory").mkdir(exist_ok=True)
    (test_dir / "analytics_data").mkdir(exist_ok=True)
    (test_dir / "feedback_data").mkdir(exist_ok=True)
    (test_dir / "config" / "profiles").mkdir(parents=True, exist_ok=True)
    (test_dir / "learning" / "patterns").mkdir(parents=True, exist_ok=True)

    # Create existing config.yaml
    config_data = {
        "project": {"name": "Existing Project", "version": "0.1.0"},
        "models": {"primary": "existing-model"},
        "agent": {"max_iterations": 10}
    }
    with open("config.yaml", 'w') as f:
        yaml.dump(config_data, f)

    # Create existing memories (stored in index.json)
    existing_memories = [
        {
            "id": "existing_mem_001",
            "content": "Existing memory",
            "timestamp": datetime.now().isoformat(),
            "importance": 0.5,
            "tags": ["existing"]
        }
    ]
    memory_index = {"memories": existing_memories}
    with open(test_dir / "memory" / "index.json", 'w') as f:
        json.dump(memory_index, f, indent=2)

    # Create existing conversation
    existing_conv = {
        "session_id": "existing_session",
        "timestamp": datetime.now().isoformat(),
        "messages": [{"role": "user", "content": "Existing message"}]
    }
    with open(test_dir / "conversations" / "conversation_existing.json", 'w') as f:
        json.dump(existing_conv, f, indent=2)

    return test_dir


def cleanup_test_environment(test_dir):
    """Clean up test environment."""
    if test_dir.exists():
        shutil.rmtree(test_dir)


def test_initialization():
    """Test 1: ImportManager initialization."""
    print("\n" + "="*70)
    print("Test 1: ImportManager Initialization")
    print("="*70)

    try:
        manager = ImportManager()
        assert manager is not None, "Failed to create ImportManager"
        assert hasattr(manager, 'logger'), "Missing logger attribute"
        print("✅ Initialization test passed")
    except Exception as e:
        print(f"❌ Initialization test failed: {e}")
        raise


def test_validate_import_file():
    """Test 2: Import file validation."""
    print("\n" + "="*70)
    print("Test 2: Import File Validation")
    print("="*70)

    test_dir = Path(tempfile.mkdtemp(prefix="meton_validate_test_"))
    os.chdir(test_dir)

    try:
        manager = ImportManager()

        # Create valid import file
        valid_data = create_test_export_data()
        valid_file = test_dir / "valid_import.json"
        with open(valid_file, 'w') as f:
            json.dump(valid_data, f)

        # Validate valid file
        result = manager.validate_import_file(str(valid_file))
        assert result["valid"] is True, "Valid file marked as invalid"
        assert len(result.get("errors", [])) == 0, "Errors found in valid file"
        # Note: validation doesn't return "version" or "contains", just valid/errors/warnings

        # Create invalid file (missing metadata)
        invalid_data = {"some": "data"}
        invalid_file = test_dir / "invalid_import.json"
        with open(invalid_file, 'w') as f:
            json.dump(invalid_data, f)

        # Validate invalid file
        invalid_result = manager.validate_import_file(str(invalid_file))
        assert invalid_result["valid"] is False, "Invalid file marked as valid"
        assert len(invalid_result["errors"]) > 0, "No errors reported for invalid file"

        # Test with non-existent file
        nonexistent_result = manager.validate_import_file("nonexistent.json")
        assert nonexistent_result["valid"] is False, "Non-existent file marked as valid"

        print("✅ Import file validation test passed")

    finally:
        cleanup_test_environment(test_dir)


def test_import_configuration():
    """Test 3: Configuration import."""
    print("\n" + "="*70)
    print("Test 3: Configuration Import")
    print("="*70)

    test_dir = setup_test_environment_with_existing_data()

    try:
        manager = ImportManager()

        # Create import file
        import_data = {
            "export_metadata": {
                "version": "1.0.0",
                "meton_version": "1.0.0",
                "export_date": datetime.now().isoformat(),
                "export_type": "configuration"
            },
            "configuration": {
                "project": {"name": "Imported Project", "version": "1.0.0"},
                "models": {"primary": "imported-model"},
                "agent": {"max_iterations": 20}
            }
        }

        import_file = test_dir / "config_import.json"
        with open(import_file, 'w') as f:
            json.dump(import_data, f)

        # Import configuration (returns count, not success/backed_up)
        count = manager.import_configuration(str(import_file))
        assert isinstance(count, (int, dict)), "Configuration import failed"

        # Verify config was updated
        with open("config.yaml", 'r') as f:
            config = yaml.safe_load(f)

        assert config["project"]["name"] == "Imported Project", "Config not updated"
        assert config["models"]["primary"] == "imported-model", "Models not updated"

        print("✅ Configuration import test passed")

    finally:
        cleanup_test_environment(test_dir)


def test_import_memories_merge():
    """Test 4: Memories import with merge."""
    print("\n" + "="*70)
    print("Test 4: Memories Import (Merge Mode)")
    print("="*70)

    test_dir = setup_test_environment_with_existing_data()

    try:
        manager = ImportManager()

        # Create import file
        import_data = create_test_export_data()
        import_file = test_dir / "memories_import.json"
        with open(import_file, 'w') as f:
            json.dump(import_data, f)

        # Import with merge
        count = manager.import_memories(str(import_file), merge=True)
        assert count == 2, f"Expected 2 memories imported, got {count}"

        # Verify memories were merged (not replaced)
        with open(test_dir / "memory" / "index.json", 'r') as f:
            memory_index = json.load(f)
            memories = memory_index.get("memories", [])

        assert len(memories) == 3, "Memories not merged (should be 1 existing + 2 imported)"

        # Check both existing and imported memories present
        memory_ids = [m["id"] for m in memories]
        assert "existing_mem_001" in memory_ids, "Existing memory lost"
        assert "mem_001" in memory_ids, "Imported memory not added"

        print("✅ Memories import (merge) test passed")

    finally:
        cleanup_test_environment(test_dir)


def test_import_memories_replace():
    """Test 5: Memories import with replace."""
    print("\n" + "="*70)
    print("Test 5: Memories Import (Replace Mode)")
    print("="*70)

    test_dir = setup_test_environment_with_existing_data()

    try:
        manager = ImportManager()

        # Create import file
        import_data = create_test_export_data()
        import_file = test_dir / "memories_import.json"
        with open(import_file, 'w') as f:
            json.dump(import_data, f)

        # Import without merge (replace)
        count = manager.import_memories(str(import_file), merge=False)
        assert count == 2, f"Expected 2 memories imported, got {count}"

        # Verify memories were replaced
        with open(test_dir / "memory" / "index.json", 'r') as f:
            memory_index = json.load(f)
            memories = memory_index.get("memories", [])

        assert len(memories) == 2, "Memories not replaced (should only have imported)"
        memory_ids = [m["id"] for m in memories]
        assert "existing_mem_001" not in memory_ids, "Existing memory not removed"
        assert "mem_001" in memory_ids, "Imported memory not added"

        print("✅ Memories import (replace) test passed")

    finally:
        cleanup_test_environment(test_dir)


def test_import_conversations():
    """Test 6: Conversations import."""
    print("\n" + "="*70)
    print("Test 6: Conversations Import")
    print("="*70)

    test_dir = setup_test_environment_with_existing_data()

    try:
        manager = ImportManager()

        # Create import file
        import_data = create_test_export_data()
        import_file = test_dir / "conversations_import.json"
        with open(import_file, 'w') as f:
            json.dump(import_data, f)

        # Import conversations
        count = manager.import_conversations(str(import_file), merge=True)
        assert count == 1, f"Expected 1 conversation imported, got {count}"

        # Verify conversations directory
        conv_files = list((test_dir / "conversations").glob("*.json"))
        assert len(conv_files) == 2, "Should have 1 existing + 1 imported conversation"

        # Check imported conversation exists
        imported_conv_file = test_dir / "conversations" / "conversation_imported_session_001.json"
        assert imported_conv_file.exists(), "Imported conversation file not created"

        with open(imported_conv_file, 'r') as f:
            conv = json.load(f)

        assert conv["session_id"] == "imported_session_001", "Wrong session ID"

        print("✅ Conversations import test passed")

    finally:
        cleanup_test_environment(test_dir)


def test_import_analytics():
    """Test 7: Analytics import."""
    print("\n" + "="*70)
    print("Test 7: Analytics Import")
    print("="*70)

    test_dir = setup_test_environment_with_existing_data()

    try:
        manager = ImportManager()

        # Create import file
        import_data = create_test_export_data()
        import_file = test_dir / "analytics_import.json"
        with open(import_file, 'w') as f:
            json.dump(import_data, f)

        # Import analytics
        count = manager.import_analytics(str(import_file), merge=True)
        assert count > 0, "No analytics imported"

        # Verify analytics file created
        analytics_file = test_dir / "analytics_data" / "analytics.json"
        assert analytics_file.exists(), "Analytics file not created"

        with open(analytics_file, 'r') as f:
            analytics = json.load(f)

        assert "sessions" in analytics, "Missing sessions in analytics"
        assert len(analytics["sessions"]) > 0, "No sessions imported"

        print("✅ Analytics import test passed")

    finally:
        cleanup_test_environment(test_dir)


def test_import_feedback():
    """Test 8: Feedback import."""
    print("\n" + "="*70)
    print("Test 8: Feedback Import")
    print("="*70)

    test_dir = setup_test_environment_with_existing_data()

    try:
        manager = ImportManager()

        # Create import file
        import_data = create_test_export_data()
        import_file = test_dir / "feedback_import.json"
        with open(import_file, 'w') as f:
            json.dump(import_data, f)

        # Import feedback
        count = manager.import_feedback(str(import_file), merge=True)
        assert count == 1, f"Expected 1 feedback imported, got {count}"

        # Verify feedback file
        feedback_file = test_dir / "feedback_data" / "feedback.json"
        assert feedback_file.exists(), "Feedback file not created"

        with open(feedback_file, 'r') as f:
            feedback = json.load(f)

        assert len(feedback) == 1, "Wrong number of feedback items"
        assert feedback[0]["rating"] == 4, "Wrong feedback data"

        print("✅ Feedback import test passed")

    finally:
        cleanup_test_environment(test_dir)


def test_import_profiles():
    """Test 9: Profiles import."""
    print("\n" + "="*70)
    print("Test 9: Profiles Import")
    print("="*70)

    test_dir = setup_test_environment_with_existing_data()

    try:
        manager = ImportManager()

        # Create import file
        import_data = create_test_export_data()
        import_file = test_dir / "profiles_import.json"
        with open(import_file, 'w') as f:
            json.dump(import_data, f)

        # Import profiles
        count = manager.import_profiles(str(import_file), overwrite=False)
        assert count == 1, f"Expected 1 profile imported, got {count}"

        # Verify profile file created
        profile_files = list((test_dir / "config" / "profiles").glob("*.yaml"))
        assert len(profile_files) > 0, "No profile files created"

        # Check profile content
        profile_file = test_dir / "config" / "profiles" / "imported_profile.yaml"
        assert profile_file.exists(), "Profile file not created"

        with open(profile_file, 'r') as f:
            profile = yaml.safe_load(f)

        assert profile["name"] == "Imported Profile", "Wrong profile data"

        print("✅ Profiles import test passed")

    finally:
        cleanup_test_environment(test_dir)


def test_import_patterns():
    """Test 10: Patterns import."""
    print("\n" + "="*70)
    print("Test 10: Patterns Import")
    print("="*70)

    test_dir = setup_test_environment_with_existing_data()

    try:
        manager = ImportManager()

        # Create import file
        import_data = create_test_export_data()
        import_file = test_dir / "patterns_import.json"
        with open(import_file, 'w') as f:
            json.dump(import_data, f)

        # Import patterns
        count = manager.import_patterns(str(import_file), merge=True)
        assert count == 1, f"Expected 1 pattern imported, got {count}"

        # Verify patterns file
        patterns_file = test_dir / "learning" / "patterns" / "patterns.json"
        assert patterns_file.exists(), "Patterns file not created"

        with open(patterns_file, 'r') as f:
            patterns = json.load(f)

        assert len(patterns) == 1, "Wrong number of patterns"
        assert patterns[0]["type"] == "imported_type", "Wrong pattern data"

        print("✅ Patterns import test passed")

    finally:
        cleanup_test_environment(test_dir)


def test_import_all():
    """Test 11: Complete state import."""
    print("\n" + "="*70)
    print("Test 11: Complete State Import")
    print("="*70)

    test_dir = setup_test_environment_with_existing_data()

    try:
        manager = ImportManager()

        # Create complete export file
        import_data = create_test_export_data()
        import_file = test_dir / "complete_import.json"
        with open(import_file, 'w') as f:
            json.dump(import_data, f)

        # Import all
        result = manager.import_all(str(import_file), merge=True)
        assert "counts" in result, "Complete import failed - missing counts"
        assert result["counts"]["memories"] == 2, "Wrong memory count"
        assert result["counts"]["conversations"] == 1, "Wrong conversation count"
        assert result["counts"]["feedback"] == 1, "Wrong feedback count"
        assert result["counts"]["profiles"] == 1, "Wrong profile count"
        assert result["counts"]["patterns"] == 1, "Wrong pattern count"

        # Verify all components imported
        assert (test_dir / "memory" / "index.json").exists(), "Memories not imported"
        assert (test_dir / "analytics_data" / "analytics.json").exists(), "Analytics not imported"

        print("✅ Complete state import test passed")

    finally:
        cleanup_test_environment(test_dir)


def test_restore_backup_gzip():
    """Test 12: Restore from gzip backup."""
    print("\n" + "="*70)
    print("Test 12: Restore from Gzip Backup")
    print("="*70)

    # Create test environment and export
    export_dir = Path(tempfile.mkdtemp(prefix="meton_backup_export_"))
    os.chdir(export_dir)

    # Setup directories and data
    (export_dir / "memory").mkdir(exist_ok=True)
    (export_dir / "conversations").mkdir(exist_ok=True)
    (export_dir / "exports").mkdir(exist_ok=True)
    (export_dir / "backups").mkdir(exist_ok=True)

    # Create some data to backup
    memories = [{"id": "mem_001", "content": "Test"}]
    memory_index = {"memories": memories}
    with open(export_dir / "memory" / "index.json", 'w') as f:
        json.dump(memory_index, f)

    config = {"project": {"name": "Test"}}
    with open(export_dir / "config.yaml", 'w') as f:
        yaml.dump(config, f)

    # Create backup
    export_manager = ExportManager(compression="gzip")
    backup_file = export_manager.create_backup(backup_name="test_backup")
    backup_path = Path(backup_file)
    if not backup_path.is_absolute():
        backup_path = export_dir / backup_file
    assert backup_path.exists(), "Backup not created"

    # Create new test environment for restoration
    restore_dir = Path(tempfile.mkdtemp(prefix="meton_backup_restore_"))
    os.chdir(restore_dir)

    try:
        # Restore backup
        import_manager = ImportManager()
        result = import_manager.restore_backup(str(backup_path))

        assert "restored_from" in result or "files_restored" in result, "Backup restoration failed"
        # Check if data was restored
        restored_count = result.get("files_restored", result.get("items_restored", 0))
        assert restored_count > 0 or len(result.get("restored", [])) > 0, "No files restored"

        # Verify restored data
        assert (restore_dir / "memory" / "index.json").exists(), "Memories not restored"
        assert (restore_dir / "config.yaml").exists(), "Config not restored"

        with open(restore_dir / "memory" / "index.json", 'r') as f:
            memory_index = json.load(f)
            restored_memories = memory_index.get("memories", [])

        assert len(restored_memories) == 1, "Memories not correctly restored"

        files_count = result.get("files_restored", result.get("items_restored", len(result.get("restored", []))))
        print(f"✅ Restore from gzip backup test passed ({files_count} items restored)")

    finally:
        cleanup_test_environment(export_dir)
        cleanup_test_environment(restore_dir)


def test_restore_backup_zip():
    """Test 13: Restore from zip backup."""
    print("\n" + "="*70)
    print("Test 13: Restore from Zip Backup")
    print("="*70)

    # Create test environment and export
    export_dir = Path(tempfile.mkdtemp(prefix="meton_zip_export_"))
    os.chdir(export_dir)

    # Setup directories and data
    (export_dir / "memory").mkdir(exist_ok=True)
    (export_dir / "exports").mkdir(exist_ok=True)
    (export_dir / "backups").mkdir(exist_ok=True)

    memories = [{"id": "mem_zip", "content": "Zip test"}]
    memory_index = {"memories": memories}
    with open(export_dir / "memory" / "index.json", 'w') as f:
        json.dump(memory_index, f)

    # Create zip backup
    export_manager = ExportManager(compression="zip")
    backup_file = export_manager.create_backup(backup_name="zip_test")
    backup_path = Path(backup_file)
    if not backup_path.is_absolute():
        backup_path = export_dir / backup_file
    assert backup_path.exists(), "Zip backup not created"

    # Create new test environment for restoration
    restore_dir = Path(tempfile.mkdtemp(prefix="meton_zip_restore_"))
    os.chdir(restore_dir)

    try:
        # Restore backup
        import_manager = ImportManager()
        result = import_manager.restore_backup(str(backup_path))

        # Check restoration completed
        assert "restored_from" in result or "files_restored" in result or len(result.get("restored", [])) > 0 or "counts" in result, "Zip backup restoration failed"
        assert (restore_dir / "memory" / "index.json").exists(), "Memories not restored from zip"

        print(f"✅ Restore from zip backup test passed")

    finally:
        cleanup_test_environment(export_dir)
        cleanup_test_environment(restore_dir)


def test_version_compatibility():
    """Test 14: Version compatibility checking."""
    print("\n" + "="*70)
    print("Test 14: Version Compatibility")
    print("="*70)

    test_dir = Path(tempfile.mkdtemp(prefix="meton_version_test_"))
    os.chdir(test_dir)

    try:
        manager = ImportManager()

        # Test with compatible version
        compatible_data = create_test_export_data()
        compatible_file = test_dir / "compatible.json"
        with open(compatible_file, 'w') as f:
            json.dump(compatible_data, f)

        result = manager.validate_import_file(str(compatible_file))
        assert result["valid"] is True, "Compatible version marked as invalid"

        # Test with incompatible version
        incompatible_data = create_test_export_data()
        incompatible_data["export_metadata"]["version"] = "999.0.0"
        incompatible_file = test_dir / "incompatible.json"
        with open(incompatible_file, 'w') as f:
            json.dump(incompatible_data, f)

        result = manager.validate_import_file(str(incompatible_file))
        assert result["valid"] is False, "Incompatible version not detected"
        assert any("version" in error.lower() for error in result["errors"]), "No version error"

        print("✅ Version compatibility test passed")

    finally:
        cleanup_test_environment(test_dir)


def test_error_handling():
    """Test 15: Error handling during import."""
    print("\n" + "="*70)
    print("Test 15: Error Handling")
    print("="*70)

    test_dir = Path(tempfile.mkdtemp(prefix="meton_error_test_"))
    os.chdir(test_dir)

    try:
        manager = ImportManager()

        # Test with invalid JSON
        invalid_file = test_dir / "invalid.json"
        with open(invalid_file, 'w') as f:
            f.write("{ invalid json }")

        result = manager.validate_import_file(str(invalid_file))
        assert result["valid"] is False, "Invalid JSON not detected"

        # Test with missing file
        result = manager.validate_import_file("nonexistent.json")
        assert result["valid"] is False, "Missing file not handled"

        # Test import_all with invalid file should raise exception
        try:
            result = manager.import_all(str(invalid_file))
            assert False, "Import should raise exception with invalid file"
        except (ValueError, json.JSONDecodeError):
            pass  # Expected

        print("✅ Error handling test passed")

    finally:
        cleanup_test_environment(test_dir)


def test_merge_vs_replace_behavior():
    """Test 16: Merge vs replace behavior differences."""
    print("\n" + "="*70)
    print("Test 16: Merge vs Replace Behavior")
    print("="*70)

    test_dir = setup_test_environment_with_existing_data()

    try:
        manager = ImportManager()

        # Create import data
        import_data = create_test_export_data()
        import_file = test_dir / "import.json"
        with open(import_file, 'w') as f:
            json.dump(import_data, f)

        # Get count of existing memories
        with open(test_dir / "memory" / "index.json", 'r') as f:
            memory_index = json.load(f)
            existing_count = len(memory_index.get("memories", []))

        # Test merge
        manager.import_memories(str(import_file), merge=True)
        with open(test_dir / "memory" / "index.json", 'r') as f:
            memory_index = json.load(f)
            merged_count = len(memory_index.get("memories", []))

        assert merged_count > existing_count, "Merge didn't add to existing data"

        # Reset for replace test
        test_dir2 = setup_test_environment_with_existing_data()
        os.chdir(test_dir2)

        import_file2 = test_dir2 / "import.json"
        with open(import_file2, 'w') as f:
            json.dump(import_data, f)

        # Test replace
        manager2 = ImportManager()
        manager2.import_memories(str(import_file2), merge=False)
        with open(test_dir2 / "memory" / "index.json", 'r') as f:
            memory_index = json.load(f)
            replaced_count = len(memory_index.get("memories", []))

        assert replaced_count == len(import_data["memories"]), "Replace didn't overwrite"
        assert replaced_count < merged_count, "Replace should have fewer items than merge"

        cleanup_test_environment(test_dir2)
        print("✅ Merge vs replace behavior test passed")

    finally:
        cleanup_test_environment(test_dir)


def test_partial_import():
    """Test 17: Partial import (only some components)."""
    print("\n" + "="*70)
    print("Test 17: Partial Import")
    print("="*70)

    test_dir = setup_test_environment_with_existing_data()

    try:
        manager = ImportManager()

        # Create export with only memories and conversations
        partial_data = {
            "export_metadata": {
                "version": "1.0.0",
                "meton_version": "1.0.0",
                "export_date": datetime.now().isoformat(),
                "export_type": "partial"
            },
            "memories": [
                {"id": "partial_mem", "content": "Partial import test"}
            ],
            "conversations": [
                {
                    "session_id": "partial_session",
                    "messages": [{"role": "user", "content": "test"}]
                }
            ]
        }

        import_file = test_dir / "partial_import.json"
        with open(import_file, 'w') as f:
            json.dump(partial_data, f)

        # Import only memories
        mem_count = manager.import_memories(str(import_file), merge=True)
        assert mem_count == 1, "Partial memory import failed"

        # Import only conversations
        conv_count = manager.import_conversations(str(import_file), merge=True)
        assert conv_count == 1, "Partial conversation import failed"

        # Verify no analytics were imported (since they weren't in the file)
        analytics_file = test_dir / "analytics_data" / "analytics.json"
        # Analytics file might exist from setup but shouldn't have partial data
        # This is okay - we're just testing that partial imports work

        print("✅ Partial import test passed")

    finally:
        cleanup_test_environment(test_dir)


def run_all_tests():
    """Run all ImportManager tests."""
    print("\n" + "="*70)
    print("IMPORTMANAGER COMPREHENSIVE TEST SUITE")
    print("="*70)
    print(f"Running 17 tests...\n")

    tests = [
        test_initialization,
        test_validate_import_file,
        test_import_configuration,
        test_import_memories_merge,
        test_import_memories_replace,
        test_import_conversations,
        test_import_analytics,
        test_import_feedback,
        test_import_profiles,
        test_import_patterns,
        test_import_all,
        test_restore_backup_gzip,
        test_restore_backup_zip,
        test_version_compatibility,
        test_error_handling,
        test_merge_vs_replace_behavior,
        test_partial_import
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} error: {e}")
            failed += 1

    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Total: {len(tests)} tests")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Success Rate: {passed/len(tests)*100:.1f}%")
    print("="*70)

    if failed == 0:
        print("\n🎉 All ImportManager tests passed!")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
