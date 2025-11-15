#!/usr/bin/env python3
"""
Tests for Session Manager.

Tests cover:
- Session creation
- Session retrieval
- Session updates
- Session deletion
- Session listing
- Persistence (save/load)
- Cleanup of expired sessions
- Concurrent access
- Edge cases
"""

import sys
import tempfile
import shutil
import time
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from web.session_manager import SessionManager, Session


def create_test_manager():
    """Create test session manager with temp storage."""
    temp_dir = tempfile.mkdtemp()
    manager = SessionManager(storage_path=temp_dir)
    return manager, temp_dir


def cleanup_test_manager(manager, temp_dir):
    """Clean up test session manager."""
    manager.clear_all_sessions()
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_create_session():
    """Test creating new session."""
    manager, temp_dir = create_test_manager()

    session_id = manager.create_session()

    assert session_id is not None
    assert len(session_id) == 36  # UUID length
    assert session_id in manager.sessions

    cleanup_test_manager(manager, temp_dir)


def test_create_session_with_settings():
    """Test creating session with initial settings."""
    manager, temp_dir = create_test_manager()

    settings = {"model": "test-model", "temperature": 0.7}
    session_id = manager.create_session(initial_settings=settings)

    session = manager.get_session(session_id)
    assert session.settings == settings

    cleanup_test_manager(manager, temp_dir)


def test_get_session():
    """Test retrieving session."""
    manager, temp_dir = create_test_manager()

    session_id = manager.create_session()
    session = manager.get_session(session_id)

    assert session.id == session_id
    assert isinstance(session, Session)

    cleanup_test_manager(manager, temp_dir)


def test_get_nonexistent_session():
    """Test retrieving non-existent session raises error."""
    manager, temp_dir = create_test_manager()

    try:
        manager.get_session("nonexistent-id")
        assert False, "Should have raised KeyError"
    except KeyError:
        pass

    cleanup_test_manager(manager, temp_dir)


def test_update_session():
    """Test updating session fields."""
    manager, temp_dir = create_test_manager()

    session_id = manager.create_session()

    # Update conversation history
    new_history = [{"role": "user", "content": "Hello"}]
    manager.update_session(session_id, conversation_history=new_history)

    session = manager.get_session(session_id)
    assert session.conversation_history == new_history

    cleanup_test_manager(manager, temp_dir)


def test_update_multiple_fields():
    """Test updating multiple session fields."""
    manager, temp_dir = create_test_manager()

    session_id = manager.create_session()

    manager.update_session(
        session_id,
        conversation_history=[{"role": "user", "content": "Test"}],
        uploaded_files=["/tmp/file.py"],
        settings={"model": "new-model"}
    )

    session = manager.get_session(session_id)
    assert len(session.conversation_history) == 1
    assert len(session.uploaded_files) == 1
    assert session.settings["model"] == "new-model"

    cleanup_test_manager(manager, temp_dir)


def test_delete_session():
    """Test deleting session."""
    manager, temp_dir = create_test_manager()

    session_id = manager.create_session()
    assert session_id in manager.sessions

    success = manager.delete_session(session_id)

    assert success is True
    assert session_id not in manager.sessions

    cleanup_test_manager(manager, temp_dir)


def test_delete_nonexistent_session():
    """Test deleting non-existent session."""
    manager, temp_dir = create_test_manager()

    success = manager.delete_session("nonexistent-id")

    # Should return False (not found)
    assert success is False

    cleanup_test_manager(manager, temp_dir)


def test_list_sessions():
    """Test listing all sessions."""
    manager, temp_dir = create_test_manager()

    # Create multiple sessions
    id1 = manager.create_session()
    id2 = manager.create_session()
    id3 = manager.create_session()

    sessions = manager.list_sessions()

    assert len(sessions) == 3
    assert all('id' in s for s in sessions)
    assert all('created_at' in s for s in sessions)
    assert all('message_count' in s for s in sessions)

    cleanup_test_manager(manager, temp_dir)


def test_list_sessions_empty():
    """Test listing sessions when empty."""
    manager, temp_dir = create_test_manager()

    sessions = manager.list_sessions()

    assert sessions == []

    cleanup_test_manager(manager, temp_dir)


def test_save_and_load_session():
    """Test session persistence."""
    temp_dir = tempfile.mkdtemp()

    # Create manager and session
    manager1 = SessionManager(storage_path=temp_dir)
    session_id = manager1.create_session()

    # Add data
    manager1.update_session(
        session_id,
        conversation_history=[{"role": "user", "content": "Test"}]
    )

    # Create new manager (should load from disk)
    manager2 = SessionManager(storage_path=temp_dir)

    session = manager2.get_session(session_id)
    assert len(session.conversation_history) == 1
    assert session.conversation_history[0]["content"] == "Test"

    cleanup_test_manager(manager2, temp_dir)


def test_cleanup_expired_sessions():
    """Test cleaning up old sessions."""
    manager, temp_dir = create_test_manager()

    # Create session
    session_id = manager.create_session()

    # Manually set last_activity to old time
    session = manager.sessions[session_id]
    old_time = datetime.now() - timedelta(hours=25)
    session.last_activity = old_time.isoformat()

    # Cleanup sessions older than 24 hours
    deleted = manager.cleanup_expired(max_age_hours=24)

    assert deleted == 1
    assert session_id not in manager.sessions

    cleanup_test_manager(manager, temp_dir)


def test_cleanup_no_expired_sessions():
    """Test cleanup when no sessions are expired."""
    manager, temp_dir = create_test_manager()

    # Create fresh session
    session_id = manager.create_session()

    # Cleanup should not delete it
    deleted = manager.cleanup_expired(max_age_hours=24)

    assert deleted == 0
    assert session_id in manager.sessions

    cleanup_test_manager(manager, temp_dir)


def test_session_activity_update():
    """Test that session activity is updated on access."""
    manager, temp_dir = create_test_manager()

    session_id = manager.create_session()

    # Get original activity time
    session1 = manager.sessions[session_id]
    original_activity = session1.last_activity

    # Wait a bit and access again
    time.sleep(0.1)
    session2 = manager.get_session(session_id)

    # Activity should be updated
    assert session2.last_activity > original_activity

    cleanup_test_manager(manager, temp_dir)


def test_get_session_count():
    """Test getting session count."""
    manager, temp_dir = create_test_manager()

    assert manager.get_session_count() == 0

    manager.create_session()
    assert manager.get_session_count() == 1

    manager.create_session()
    assert manager.get_session_count() == 2

    cleanup_test_manager(manager, temp_dir)


def test_clear_all_sessions():
    """Test clearing all sessions."""
    manager, temp_dir = create_test_manager()

    # Create multiple sessions
    manager.create_session()
    manager.create_session()
    manager.create_session()

    count = manager.clear_all_sessions()

    assert count == 3
    assert manager.get_session_count() == 0

    cleanup_test_manager(manager, temp_dir)


def test_get_session_stats():
    """Test getting session statistics."""
    manager, temp_dir = create_test_manager()

    # Empty stats
    stats = manager.get_session_stats()
    assert stats['total_sessions'] == 0

    # Create sessions with data
    session_id = manager.create_session()
    manager.update_session(
        session_id,
        conversation_history=[
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello"}
        ]
    )

    stats = manager.get_session_stats()
    assert stats['total_sessions'] == 1
    assert stats['total_messages'] == 2
    assert stats['avg_messages_per_session'] == 2.0

    cleanup_test_manager(manager, temp_dir)


def test_concurrent_session_creation():
    """Test creating multiple sessions concurrently."""
    manager, temp_dir = create_test_manager()

    session_ids = []
    for i in range(10):
        session_id = manager.create_session()
        session_ids.append(session_id)

    # All IDs should be unique
    assert len(set(session_ids)) == 10
    assert manager.get_session_count() == 10

    cleanup_test_manager(manager, temp_dir)


def test_session_dataclass():
    """Test Session dataclass."""
    session = Session(
        id="test-id",
        created_at="2025-01-01T00:00:00",
        last_activity="2025-01-01T00:00:00"
    )

    assert session.id == "test-id"
    assert session.conversation_history == []
    assert session.uploaded_files == []
    assert session.settings == {}


def test_session_update_activity():
    """Test Session update_activity method."""
    session = Session(
        id="test-id",
        created_at="2025-01-01T00:00:00",
        last_activity="2025-01-01T00:00:00"
    )

    old_activity = session.last_activity
    time.sleep(0.1)
    session.update_activity()

    assert session.last_activity > old_activity


def test_list_sessions_sorted():
    """Test that sessions are sorted by last activity."""
    manager, temp_dir = create_test_manager()

    # Create sessions
    id1 = manager.create_session()
    time.sleep(0.1)
    id2 = manager.create_session()
    time.sleep(0.1)
    id3 = manager.create_session()

    sessions = manager.list_sessions()

    # Should be sorted by last activity (most recent first)
    assert sessions[0]['id'] == id3
    assert sessions[1]['id'] == id2
    assert sessions[2]['id'] == id1

    cleanup_test_manager(manager, temp_dir)


def run_all_tests():
    """Run all tests and report results."""
    tests = [
        test_create_session,
        test_create_session_with_settings,
        test_get_session,
        test_get_nonexistent_session,
        test_update_session,
        test_update_multiple_fields,
        test_delete_session,
        test_delete_nonexistent_session,
        test_list_sessions,
        test_list_sessions_empty,
        test_save_and_load_session,
        test_cleanup_expired_sessions,
        test_cleanup_no_expired_sessions,
        test_session_activity_update,
        test_get_session_count,
        test_clear_all_sessions,
        test_get_session_stats,
        test_concurrent_session_creation,
        test_session_dataclass,
        test_session_update_activity,
        test_list_sessions_sorted,
    ]

    print(f"Running {len(tests)} tests...\n")

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            print(f"✅ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {type(e).__name__}: {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print(f"Success rate: {passed/len(tests)*100:.1f}%")

    if failed == 0:
        print("✅ All tests passed!")
        return 0
    else:
        print(f"❌ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(run_all_tests())
