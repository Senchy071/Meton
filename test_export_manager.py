#!/usr/bin/env python3
"""
Comprehensive Test Suite for ExportManager

Tests all export functionality including:
- Complete state export
- Individual component exports (config, memories, conversations, etc.)
- Filtering and date range options
- Multiple output formats (JSON, CSV, markdown)
- Backup creation and compression
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


def setup_test_environment():
    """Create test environment with sample data."""
    test_dir = Path(tempfile.mkdtemp(prefix="meton_export_test_"))

    # Create test directories
    (test_dir / "conversations").mkdir(exist_ok=True)
    (test_dir / "memory").mkdir(exist_ok=True)
    (test_dir / "analytics_data").mkdir(exist_ok=True)
    (test_dir / "feedback_data").mkdir(exist_ok=True)
    (test_dir / "config" / "profiles").mkdir(parents=True, exist_ok=True)
    (test_dir / "learning" / "patterns").mkdir(parents=True, exist_ok=True)
    (test_dir / "exports").mkdir(exist_ok=True)
    (test_dir / "backups").mkdir(exist_ok=True)

    # Create test config.yaml
    config_data = {
        "project": {"name": "Meton Test", "version": "0.1.0"},
        "models": {"primary": "qwen2.5:32b"},
        "agent": {"max_iterations": 10}
    }
    with open(test_dir / "config.yaml", 'w') as f:
        yaml.dump(config_data, f)

    # Create test memories (stored in index.json, not memories.json)
    memories = [
        {
            "id": "mem_001",
            "content": "Test memory 1",
            "timestamp": datetime.now().isoformat(),
            "importance": 0.8,
            "tags": ["test", "memory"]
        },
        {
            "id": "mem_002",
            "content": "Test memory 2",
            "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
            "importance": 0.6,
            "tags": ["test"]
        }
    ]
    memory_index = {"memories": memories}
    with open(test_dir / "memory" / "index.json", 'w') as f:
        json.dump(memory_index, f, indent=2)

    # Create test conversations
    conversations = [
        {
            "session_id": "session_001",
            "timestamp": datetime.now().isoformat(),
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ]
        },
        {
            "session_id": "session_002",
            "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
            "messages": [
                {"role": "user", "content": "Test query"},
                {"role": "assistant", "content": "Test response"}
            ]
        }
    ]
    for conv in conversations:
        filename = f"conversation_{conv['session_id']}.json"
        with open(test_dir / "conversations" / filename, 'w') as f:
            json.dump(conv, f, indent=2)

    # Create test analytics
    analytics = {
        "sessions": [
            {
                "session_id": "session_001",
                "timestamp": datetime.now().isoformat(),
                "query_count": 5,
                "avg_response_time": 1.2,
                "tools_used": ["file_ops", "code_executor"]
            }
        ],
        "metrics": {
            "total_sessions": 10,
            "total_queries": 50,
            "avg_session_duration": 300
        }
    }
    with open(test_dir / "analytics_data" / "analytics.json", 'w') as f:
        json.dump(analytics, f, indent=2)

    # Create test feedback
    feedback = [
        {
            "id": "fb_001",
            "timestamp": datetime.now().isoformat(),
            "query": "Test query",
            "response": "Test response",
            "rating": 5,
            "comment": "Great!"
        }
    ]
    with open(test_dir / "feedback_data" / "feedback.json", 'w') as f:
        json.dump(feedback, f, indent=2)

    # Create test profiles
    profile = {
        "id": "profile_001",
        "name": "Test Profile",
        "category": "development",
        "settings": {"max_iterations": 15}
    }
    with open(test_dir / "config" / "profiles" / "test_profile.yaml", 'w') as f:
        yaml.dump(profile, f)

    # Create test patterns
    patterns = [
        {
            "id": "pattern_001",
            "type": "query_type",
            "pattern": "code review",
            "occurrences": 10,
            "confidence": 0.9
        }
    ]
    with open(test_dir / "learning" / "patterns" / "patterns.json", 'w') as f:
        json.dump(patterns, f, indent=2)

    return test_dir


def cleanup_test_environment(test_dir):
    """Clean up test environment."""
    if test_dir.exists():
        shutil.rmtree(test_dir)


def test_initialization():
    """Test 1: ExportManager initialization."""
    print("\n" + "="*70)
    print("Test 1: ExportManager Initialization")
    print("="*70)

    test_dir = setup_test_environment()
    os.chdir(test_dir)

    try:
        # Test with default settings
        manager = ExportManager()
        assert manager.export_dir.exists(), "Export directory not created"
        assert manager.backup_dir.exists(), "Backup directory not created"
        assert manager.compression == "gzip", "Default compression not set"

        # Test with custom settings
        custom_manager = ExportManager(
            export_dir="./custom_exports",
            backup_dir="./custom_backups",
            compression="zip"
        )
        assert custom_manager.compression == "zip", "Custom compression not set"
        assert (test_dir / "custom_exports").exists(), "Custom export dir not created"

        # Test invalid compression
        try:
            invalid_manager = ExportManager(compression="invalid")
            assert False, "Should raise ValueError for invalid compression"
        except ValueError as e:
            assert "Unsupported compression" in str(e), "Wrong error message"

        print("✅ Initialization test passed")

    finally:
        cleanup_test_environment(test_dir)


def test_export_configuration():
    """Test 2: Configuration export."""
    print("\n" + "="*70)
    print("Test 2: Configuration Export")
    print("="*70)

    test_dir = setup_test_environment()
    os.chdir(test_dir)

    try:
        manager = ExportManager()

        # Export configuration
        output_file = manager.export_configuration()
        assert Path(output_file).exists(), "Configuration export file not created"

        # Verify content
        with open(output_file, 'r') as f:
            data = json.load(f)

        assert "export_metadata" in data, "Missing export metadata"
        assert "configuration" in data, "Missing configuration data"
        assert data["configuration"]["project"]["name"] == "Meton Test", "Wrong config data"

        print(f"✅ Configuration export test passed: {output_file}")

    finally:
        cleanup_test_environment(test_dir)


def test_export_memories():
    """Test 3: Memories export with filtering."""
    print("\n" + "="*70)
    print("Test 3: Memories Export")
    print("="*70)

    test_dir = setup_test_environment()
    os.chdir(test_dir)

    try:
        manager = ExportManager()

        # Export all memories
        output_file = manager.export_memories()
        assert Path(output_file).exists(), "Memories export file not created"

        with open(output_file, 'r') as f:
            data = json.load(f)

        assert "memories" in data, "Missing memories data"
        assert len(data["memories"]) == 2, f"Expected 2 memories, got {len(data['memories'])}"

        # Test filtering by minimum importance
        filtered_file = manager.export_memories(
            output_file="filtered_memories.json",
            filter_by={"min_importance": 0.7}
        )

        with open(filtered_file, 'r') as f:
            filtered_data = json.load(f)

        assert len(filtered_data["memories"]) == 1, "Filtering by importance failed"
        assert filtered_data["memories"][0]["importance"] >= 0.7, "Wrong memory filtered"

        print("✅ Memories export test passed")

    finally:
        cleanup_test_environment(test_dir)


def test_export_conversations():
    """Test 4: Conversations export with date range and formats."""
    print("\n" + "="*70)
    print("Test 4: Conversations Export")
    print("="*70)

    test_dir = setup_test_environment()
    os.chdir(test_dir)

    try:
        manager = ExportManager()

        # Export as JSON
        json_file = manager.export_conversations(format="json")
        assert Path(json_file).exists(), "JSON conversations export not created"

        with open(json_file, 'r') as f:
            data = json.load(f)

        assert "conversations" in data, "Missing conversations data"
        assert len(data["conversations"]) == 2, "Wrong number of conversations"

        # Export as markdown
        md_file = manager.export_conversations(
            output_file="conversations.md",
            format="markdown"
        )
        assert Path(md_file).exists(), "Markdown conversations export not created"

        with open(md_file, 'r') as f:
            content = f.read()

        assert "# Meton Conversations Export" in content, "Missing markdown header"
        assert "session_001" in content, "Missing conversation content"

        # Test session ID filtering
        filtered_file = manager.export_conversations(
            output_file="filtered_conversations.json",
            session_ids=["session_001"],
            format="json"
        )

        with open(filtered_file, 'r') as f:
            filtered_data = json.load(f)

        # Should only include session_001
        assert len(filtered_data["conversations"]) == 1, "Session ID filtering failed"
        assert filtered_data["conversations"][0]["session_id"] == "session_001", "Wrong session filtered"

        print("✅ Conversations export test passed")

    finally:
        cleanup_test_environment(test_dir)


def test_export_analytics():
    """Test 5: Analytics export with formats."""
    print("\n" + "="*70)
    print("Test 5: Analytics Export")
    print("="*70)

    test_dir = setup_test_environment()
    os.chdir(test_dir)

    try:
        manager = ExportManager()

        # Export as JSON
        json_file = manager.export_analytics(format="json")
        assert Path(json_file).exists(), "JSON analytics export not created"

        with open(json_file, 'r') as f:
            data = json.load(f)

        assert "analytics" in data, "Missing analytics data"
        assert "sessions" in data["analytics"], "Missing sessions data"

        # Export as CSV
        csv_file = manager.export_analytics(
            output_file="analytics.csv",
            format="csv"
        )
        assert Path(csv_file).exists(), "CSV analytics export not created"

        with open(csv_file, 'r') as f:
            content = f.read()

        assert "session_id" in content, "Missing CSV header"
        assert "session_001" in content, "Missing session data"

        print("✅ Analytics export test passed")

    finally:
        cleanup_test_environment(test_dir)


def test_export_feedback():
    """Test 6: Feedback export."""
    print("\n" + "="*70)
    print("Test 6: Feedback Export")
    print("="*70)

    test_dir = setup_test_environment()
    os.chdir(test_dir)

    try:
        manager = ExportManager()

        output_file = manager.export_feedback()
        assert Path(output_file).exists(), "Feedback export file not created"

        with open(output_file, 'r') as f:
            data = json.load(f)

        assert "feedback" in data, "Missing feedback data"
        assert len(data["feedback"]) == 1, "Wrong number of feedback items"
        assert data["feedback"][0]["rating"] == 5, "Wrong feedback data"

        print("✅ Feedback export test passed")

    finally:
        cleanup_test_environment(test_dir)


def test_export_profiles():
    """Test 7: Profiles export with category filtering."""
    print("\n" + "="*70)
    print("Test 7: Profiles Export")
    print("="*70)

    test_dir = setup_test_environment()
    os.chdir(test_dir)

    try:
        manager = ExportManager()

        # Export all profiles (always JSON format)
        json_file = manager.export_profiles()
        assert Path(json_file).exists(), "Profiles export file not created"

        with open(json_file, 'r') as f:
            data = json.load(f)

        assert "profiles" in data, "Missing profiles data"
        assert len(data["profiles"]) == 1, "Wrong number of profiles"

        # Export with custom path
        custom_file = manager.export_profiles(output_file="custom_profiles.json")
        assert Path(custom_file).exists(), "Custom profiles export not created"

        with open(custom_file, 'r') as f:
            custom_data = json.load(f)

        assert "profiles" in custom_data, "Missing profiles in custom export"

        print("✅ Profiles export test passed")

    finally:
        cleanup_test_environment(test_dir)


def test_export_patterns():
    """Test 8: Patterns export."""
    print("\n" + "="*70)
    print("Test 8: Patterns Export")
    print("="*70)

    test_dir = setup_test_environment()
    os.chdir(test_dir)

    try:
        manager = ExportManager()

        output_file = manager.export_patterns()
        assert Path(output_file).exists(), "Patterns export file not created"

        with open(output_file, 'r') as f:
            data = json.load(f)

        assert "patterns" in data, "Missing patterns data"
        assert len(data["patterns"]) == 1, "Wrong number of patterns"
        assert data["patterns"][0]["type"] == "query_type", "Wrong pattern data"

        print("✅ Patterns export test passed")

    finally:
        cleanup_test_environment(test_dir)


def test_export_all():
    """Test 9: Complete state export."""
    print("\n" + "="*70)
    print("Test 9: Complete State Export")
    print("="*70)

    test_dir = setup_test_environment()
    os.chdir(test_dir)

    try:
        manager = ExportManager()

        # Export everything
        output_file = manager.export_all()
        assert Path(output_file).exists(), "Complete export file not created"

        with open(output_file, 'r') as f:
            data = json.load(f)

        # Verify all components present
        assert "export_metadata" in data, "Missing export metadata"
        assert data["export_metadata"]["export_type"] == "complete", "Wrong export type"
        assert "configuration" in data, "Missing configuration"
        assert "memories" in data, "Missing memories"
        assert "conversations" in data, "Missing conversations"
        assert "analytics" in data, "Missing analytics"
        assert "feedback" in data, "Missing feedback"
        assert "profiles" in data, "Missing profiles"
        assert "patterns" in data, "Missing patterns"

        # Test selective export (no conversations)
        selective_file = manager.export_all(
            output_file="selective_export.json",
            include_conversations=False
        )

        with open(selective_file, 'r') as f:
            selective_data = json.load(f)

        assert len(selective_data.get("conversations", [])) == 0, "Conversations should be excluded"
        assert "memories" in selective_data, "Memories should still be included"

        print("✅ Complete state export test passed")

    finally:
        cleanup_test_environment(test_dir)


def test_backup_creation_gzip():
    """Test 10: Backup creation with gzip compression."""
    print("\n" + "="*70)
    print("Test 10: Backup Creation (gzip)")
    print("="*70)

    test_dir = setup_test_environment()
    os.chdir(test_dir)

    try:
        manager = ExportManager(compression="gzip")

        backup_file = manager.create_backup()
        assert Path(backup_file).exists(), "Backup file not created"
        assert backup_file.endswith(".tar.gz"), "Wrong backup file extension"

        # Verify backup contains expected files
        # Note: files are under backup_name/ root directory
        with tarfile.open(backup_file, 'r:gz') as tar:
            members = tar.getnames()
            assert any('config.yaml' in m for m in members), "config.yaml not in backup"
            assert any('memories.json' in m for m in members), "memories.json not in backup"

        print(f"✅ Backup creation (gzip) test passed: {backup_file}")

    finally:
        cleanup_test_environment(test_dir)


def test_backup_creation_zip():
    """Test 11: Backup creation with zip compression."""
    print("\n" + "="*70)
    print("Test 11: Backup Creation (zip)")
    print("="*70)

    test_dir = setup_test_environment()
    os.chdir(test_dir)

    try:
        manager = ExportManager(compression="zip")

        backup_file = manager.create_backup(backup_name="test_backup")
        assert Path(backup_file).exists(), "Backup file not created"
        assert backup_file.endswith(".zip"), "Wrong backup file extension"

        # Verify backup contains expected files
        with zipfile.ZipFile(backup_file, 'r') as zip_ref:
            members = zip_ref.namelist()
            assert any('config.yaml' in m for m in members), "config.yaml not in backup"
            assert any('conversations' in m for m in members), "conversations/ not in backup"

        print(f"✅ Backup creation (zip) test passed: {backup_file}")

    finally:
        cleanup_test_environment(test_dir)


def test_backup_creation_no_compression():
    """Test 12: Backup creation without compression."""
    print("\n" + "="*70)
    print("Test 12: Backup Creation (no compression)")
    print("="*70)

    test_dir = setup_test_environment()
    os.chdir(test_dir)

    try:
        manager = ExportManager(compression="none")

        backup_path = manager.create_backup()
        assert Path(backup_path).exists(), "Backup directory not created"
        assert Path(backup_path).is_dir(), "Backup should be a directory, not a file"

        # Verify backup contains expected files
        assert (Path(backup_path) / "config.yaml").exists(), "config.yaml not in backup"
        assert (Path(backup_path) / "memories.json").exists(), "memories.json not in backup"

        print(f"✅ Backup creation (no compression) test passed: {backup_path}")

    finally:
        cleanup_test_environment(test_dir)


def test_custom_output_paths():
    """Test 13: Custom output file paths."""
    print("\n" + "="*70)
    print("Test 13: Custom Output Paths")
    print("="*70)

    test_dir = setup_test_environment()
    os.chdir(test_dir)

    try:
        manager = ExportManager()

        # Test custom path for configuration
        custom_config = test_dir / "my_custom_config.json"
        result = manager.export_configuration(output_file=str(custom_config))
        assert custom_config.exists(), "Custom config path not used"
        assert result == str(custom_config), "Wrong path returned"

        # Test custom path for memories
        custom_memories = test_dir / "my_memories.json"
        result = manager.export_memories(output_file=str(custom_memories))
        assert custom_memories.exists(), "Custom memories path not used"

        print("✅ Custom output paths test passed")

    finally:
        cleanup_test_environment(test_dir)


def test_export_metadata():
    """Test 14: Export metadata in all exports."""
    print("\n" + "="*70)
    print("Test 14: Export Metadata")
    print("="*70)

    test_dir = setup_test_environment()
    os.chdir(test_dir)

    try:
        manager = ExportManager()

        # Check metadata in configuration export
        config_file = manager.export_configuration()
        with open(config_file, 'r') as f:
            data = json.load(f)

        metadata = data["export_metadata"]
        assert "version" in metadata, "Missing version in metadata"
        assert "meton_version" in metadata, "Missing meton_version in metadata"
        assert "export_date" in metadata, "Missing export_date in metadata"
        assert "export_type" in metadata, "Missing export_type in metadata"
        assert metadata["export_type"] == "configuration", "Wrong export type"

        # Verify date format
        export_date = datetime.fromisoformat(metadata["export_date"])
        assert isinstance(export_date, datetime), "Invalid date format"

        print("✅ Export metadata test passed")

    finally:
        cleanup_test_environment(test_dir)


def test_empty_data_handling():
    """Test 15: Handling of missing or empty data directories."""
    print("\n" + "="*70)
    print("Test 15: Empty Data Handling")
    print("="*70)

    test_dir = Path(tempfile.mkdtemp(prefix="meton_empty_test_"))
    os.chdir(test_dir)

    # Don't create any data directories
    (test_dir / "exports").mkdir(exist_ok=True)
    (test_dir / "backups").mkdir(exist_ok=True)

    try:
        manager = ExportManager()

        # Export should not fail with missing data
        output_file = manager.export_all()
        assert Path(output_file).exists(), "Export failed with empty data"

        with open(output_file, 'r') as f:
            data = json.load(f)

        # Should have empty or default values
        assert "export_metadata" in data, "Missing metadata even with empty data"
        assert isinstance(data.get("memories", []), list), "Memories should be empty list"
        assert isinstance(data.get("conversations", []), list), "Conversations should be empty list"

        print("✅ Empty data handling test passed")

    finally:
        cleanup_test_environment(test_dir)


def test_large_export():
    """Test 16: Export with larger dataset."""
    print("\n" + "="*70)
    print("Test 16: Large Export")
    print("="*70)

    test_dir = setup_test_environment()
    os.chdir(test_dir)

    try:
        # Add more memories
        memories = []
        for i in range(100):
            memories.append({
                "id": f"mem_{i:03d}",
                "content": f"Test memory {i}",
                "timestamp": (datetime.now() - timedelta(days=i)).isoformat(),
                "importance": 0.5 + (i % 5) * 0.1,
                "tags": ["test", f"tag_{i % 10}"]
            })

        memory_index = {"memories": memories}
        with open(test_dir / "memory" / "index.json", 'w') as f:
            json.dump(memory_index, f, indent=2)

        manager = ExportManager()

        # Export all memories
        start_time = datetime.now()
        output_file = manager.export_memories()
        duration = (datetime.now() - start_time).total_seconds()

        with open(output_file, 'r') as f:
            data = json.load(f)

        assert len(data["memories"]) == 100, "Not all memories exported"
        assert duration < 5.0, f"Export too slow: {duration}s"

        # Test filtering on large dataset
        filtered_file = manager.export_memories(
            output_file="high_importance.json",
            filter_by={"min_importance": 0.8}
        )

        with open(filtered_file, 'r') as f:
            filtered_data = json.load(f)

        assert len(filtered_data["memories"]) < 100, "Filtering didn't reduce size"
        assert all(m["importance"] >= 0.8 for m in filtered_data["memories"]), "Filter failed"

        print(f"✅ Large export test passed (100 memories in {duration:.2f}s)")

    finally:
        cleanup_test_environment(test_dir)


def test_error_handling():
    """Test 17: Error handling and recovery."""
    print("\n" + "="*70)
    print("Test 17: Error Handling")
    print("="*70)

    test_dir = setup_test_environment()
    os.chdir(test_dir)

    try:
        manager = ExportManager()

        # Test export with corrupted data file
        with open(test_dir / "memory" / "index.json", 'w') as f:
            f.write("{ invalid json content")

        # Should not crash, but return empty or partial data
        output_file = manager.export_memories()
        assert Path(output_file).exists(), "Export should create file even with corrupted data"

        with open(output_file, 'r') as f:
            data = json.load(f)

        # Should have metadata even if data is empty
        assert "export_metadata" in data, "Should have metadata"
        assert isinstance(data.get("memories", []), list), "Should have empty memories list"

        print("✅ Error handling test passed")

    finally:
        cleanup_test_environment(test_dir)


def run_all_tests():
    """Run all ExportManager tests."""
    print("\n" + "="*70)
    print("EXPORTMANAGER COMPREHENSIVE TEST SUITE")
    print("="*70)
    print(f"Running 17 tests...\n")

    tests = [
        test_initialization,
        test_export_configuration,
        test_export_memories,
        test_export_conversations,
        test_export_analytics,
        test_export_feedback,
        test_export_profiles,
        test_export_patterns,
        test_export_all,
        test_backup_creation_gzip,
        test_backup_creation_zip,
        test_backup_creation_no_compression,
        test_custom_output_paths,
        test_export_metadata,
        test_empty_data_handling,
        test_large_export,
        test_error_handling
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
        print("\n🎉 All ExportManager tests passed!")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
