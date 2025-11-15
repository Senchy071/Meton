#!/usr/bin/env python3
"""
Tests for Meton Web UI.

Tests cover:
- UI initialization
- Message processing
- Conversation history management
- File upload handling
- Tool toggling
- Settings updates
- Export functionality
- Error handling
- Edge cases
"""

import sys
import tempfile
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from web.app import MetonWebUI, ConversationMessage


def create_test_ui():
    """Create test UI instance."""
    # Create temporary config
    temp_dir = tempfile.mkdtemp()
    config_path = Path(temp_dir) / "config.yaml"

    config_content = """
web_ui:
  enabled: true
  host: 127.0.0.1
  port: 7860
  share: false
  theme: soft
  max_file_size_mb: 10
models:
  primary: test-model
"""

    config_path.write_text(config_content)

    ui = MetonWebUI(config_path=str(config_path))

    return ui, temp_dir


def cleanup_test_ui(ui, temp_dir):
    """Clean up test UI."""
    ui.cleanup()
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_ui_initialization():
    """Test UI initialization."""
    ui, temp_dir = create_test_ui()

    assert ui is not None
    assert ui.conversation_history == []
    assert ui.uploaded_files == []
    assert ui.agent_status == "Not initialized"

    cleanup_test_ui(ui, temp_dir)


def test_config_loading():
    """Test configuration loading."""
    ui, temp_dir = create_test_ui()

    assert "web_ui" in ui.config
    assert ui.config["web_ui"]["port"] == 7860
    assert ui.config["web_ui"]["theme"] == "soft"

    cleanup_test_ui(ui, temp_dir)


def test_initialize_agent():
    """Test agent initialization."""
    ui, temp_dir = create_test_ui()

    result = ui.initialize_agent()

    assert "initialized successfully" in result.lower()
    assert ui.agent_status == "Ready"

    cleanup_test_ui(ui, temp_dir)


def test_process_message_simple():
    """Test processing simple message."""
    ui, temp_dir = create_test_ui()

    history = []
    new_history, empty = ui.process_message("Hello", history)

    assert len(new_history) == 1
    assert new_history[0][0] == "Hello"
    assert empty == ""
    assert len(ui.conversation_history) == 2  # user + assistant

    cleanup_test_ui(ui, temp_dir)


def test_process_empty_message():
    """Test processing empty message."""
    ui, temp_dir = create_test_ui()

    history = []
    new_history, empty = ui.process_message("", history)

    assert new_history == history
    assert len(ui.conversation_history) == 0

    cleanup_test_ui(ui, temp_dir)


def test_process_multiple_messages():
    """Test processing multiple messages."""
    ui, temp_dir = create_test_ui()

    history = []

    # First message
    history, empty = ui.process_message("First message", history)
    assert len(history) == 1

    # Second message
    history, empty = ui.process_message("Second message", history)
    assert len(history) == 2

    # Third message
    history, empty = ui.process_message("Third message", history)
    assert len(history) == 3

    assert len(ui.conversation_history) == 6  # 3 user + 3 assistant

    cleanup_test_ui(ui, temp_dir)


def test_clear_conversation():
    """Test clearing conversation."""
    ui, temp_dir = create_test_ui()

    # Add some messages
    history = []
    history, _ = ui.process_message("Test message", history)

    assert len(ui.conversation_history) > 0

    # Clear conversation
    empty_history = ui.clear_conversation()

    assert empty_history == []
    assert len(ui.conversation_history) == 0

    cleanup_test_ui(ui, temp_dir)


def test_file_upload_single():
    """Test uploading single file."""
    ui, temp_dir = create_test_ui()

    # Create test file
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text("print('hello')")

    # Mock file object
    class MockFile:
        def __init__(self, path):
            self.name = path

    files = [MockFile(str(test_file))]

    file_list, status = ui.upload_file(files)

    assert "test.py" in file_list
    assert "✅" in status
    assert "test.py" in ui.uploaded_files

    cleanup_test_ui(ui, temp_dir)


def test_file_upload_multiple():
    """Test uploading multiple files."""
    ui, temp_dir = create_test_ui()

    # Create test files
    test_file1 = Path(temp_dir) / "file1.py"
    test_file2 = Path(temp_dir) / "file2.js"

    test_file1.write_text("# Python")
    test_file2.write_text("// JavaScript")

    class MockFile:
        def __init__(self, path):
            self.name = path

    files = [MockFile(str(test_file1)), MockFile(str(test_file2))]

    file_list, status = ui.upload_file(files)

    assert "file1.py" in file_list
    assert "file2.js" in file_list
    assert len(ui.uploaded_files) == 2

    cleanup_test_ui(ui, temp_dir)


def test_file_upload_empty():
    """Test uploading no files."""
    ui, temp_dir = create_test_ui()

    file_list, status = ui.upload_file([])

    assert "No files selected" in status

    cleanup_test_ui(ui, temp_dir)


def test_file_upload_duplicate():
    """Test uploading duplicate file."""
    ui, temp_dir = create_test_ui()

    # Create test file
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text("print('hello')")

    class MockFile:
        def __init__(self, path):
            self.name = path

    # Upload twice
    ui.upload_file([MockFile(str(test_file))])
    file_list, status = ui.upload_file([MockFile(str(test_file))])

    # Should only appear once
    assert ui.uploaded_files.count("test.py") == 1

    cleanup_test_ui(ui, temp_dir)


def test_delete_file():
    """Test deleting uploaded file."""
    ui, temp_dir = create_test_ui()

    # Upload file
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text("print('hello')")

    class MockFile:
        def __init__(self, path):
            self.name = path

    ui.upload_file([MockFile(str(test_file))])

    assert "test.py" in ui.uploaded_files

    # Delete file
    file_list, status = ui.delete_file("test.py")

    assert "test.py" not in ui.uploaded_files
    assert "✅" in status

    cleanup_test_ui(ui, temp_dir)


def test_toggle_tool():
    """Test toggling tools."""
    ui, temp_dir = create_test_ui()

    # Enable web search
    status = ui.toggle_tool("web_search", True)

    assert "✅" in status
    assert ui.tools_enabled["web_search"] is True

    # Disable web search
    status = ui.toggle_tool("web_search", False)

    assert ui.tools_enabled["web_search"] is False

    cleanup_test_ui(ui, temp_dir)


def test_toggle_multiple_tools():
    """Test toggling multiple tools."""
    ui, temp_dir = create_test_ui()

    ui.toggle_tool("web_search", True)
    ui.toggle_tool("reflection", True)
    ui.toggle_tool("chain_of_thought", True)

    assert ui.tools_enabled["web_search"] is True
    assert ui.tools_enabled["reflection"] is True
    assert ui.tools_enabled["chain_of_thought"] is True

    cleanup_test_ui(ui, temp_dir)


def test_update_model():
    """Test updating model."""
    ui, temp_dir = create_test_ui()

    initial_model = ui.current_model

    status = ui.update_model("llama3.1:8b")

    assert ui.current_model == "llama3.1:8b"
    assert "✅" in status

    cleanup_test_ui(ui, temp_dir)


def test_export_markdown():
    """Test exporting conversation to markdown."""
    ui, temp_dir = create_test_ui()

    # Add some messages
    history = []
    ui.process_message("Hello", history)
    ui.process_message("How are you?", history)

    # Export
    filepath = ui.export_conversation("markdown")

    assert not filepath.startswith("❌")
    assert Path(filepath).exists()
    assert Path(filepath).suffix == ".md"

    cleanup_test_ui(ui, temp_dir)


def test_export_json():
    """Test exporting conversation to JSON."""
    ui, temp_dir = create_test_ui()

    # Add some messages
    history = []
    ui.process_message("Test message", history)

    # Export
    filepath = ui.export_conversation("json")

    assert not filepath.startswith("❌")
    assert Path(filepath).exists()
    assert Path(filepath).suffix == ".json"

    cleanup_test_ui(ui, temp_dir)


def test_export_txt():
    """Test exporting conversation to TXT."""
    ui, temp_dir = create_test_ui()

    # Add some messages
    history = []
    ui.process_message("Test", history)

    # Export
    filepath = ui.export_conversation("txt")

    assert not filepath.startswith("❌")
    assert Path(filepath).exists()
    assert Path(filepath).suffix == ".txt"

    cleanup_test_ui(ui, temp_dir)


def test_export_unsupported_format():
    """Test exporting with unsupported format."""
    ui, temp_dir = create_test_ui()

    filepath = ui.export_conversation("invalid_format")

    assert "❌" in filepath
    assert "Unsupported format" in filepath

    cleanup_test_ui(ui, temp_dir)


def test_get_status():
    """Test getting UI status."""
    ui, temp_dir = create_test_ui()

    # Add some data
    history = []
    ui.process_message("Test", history)
    ui.toggle_tool("web_search", True)

    status = ui.get_status()

    assert "agent_status" in status
    assert "current_model" in status
    assert "tools_enabled" in status
    assert status["tools_enabled"]["web_search"] is True
    assert status["conversation_messages"] == 2

    cleanup_test_ui(ui, temp_dir)


def test_conversation_message_dataclass():
    """Test ConversationMessage dataclass."""
    msg = ConversationMessage(
        role="user",
        content="Test message",
        timestamp="2025-01-01T00:00:00",
        metadata={"test": "data"}
    )

    assert msg.role == "user"
    assert msg.content == "Test message"
    assert msg.metadata["test"] == "data"


def test_simulate_agent_response_keywords():
    """Test simulated agent responses for various keywords."""
    ui, temp_dir = create_test_ui()

    # Test hello
    response = ui._simulate_agent_response("Hello there")
    assert "Hello" in response

    # Test files
    response = ui._simulate_agent_response("What files do I have?")
    assert "files" in response.lower()

    # Test code
    response = ui._simulate_agent_response("Help me with code")
    assert "code" in response.lower()

    # Test help
    response = ui._simulate_agent_response("I need help")
    assert "Capabilities" in response or "help" in response.lower()

    cleanup_test_ui(ui, temp_dir)


def test_long_message():
    """Test processing very long message."""
    ui, temp_dir = create_test_ui()

    long_message = "Test " * 1000  # 5000 characters

    history = []
    new_history, empty = ui.process_message(long_message, history)

    assert len(new_history) == 1
    assert len(ui.conversation_history) == 2

    cleanup_test_ui(ui, temp_dir)


def test_rapid_messages():
    """Test rapid successive messages."""
    ui, temp_dir = create_test_ui()

    history = []

    for i in range(10):
        history, _ = ui.process_message(f"Message {i}", history)

    assert len(history) == 10
    assert len(ui.conversation_history) == 20

    cleanup_test_ui(ui, temp_dir)


def test_file_list_display_empty():
    """Test file list display when no files."""
    ui, temp_dir = create_test_ui()

    file_list = ui._get_file_list()

    assert "No files uploaded" in file_list

    cleanup_test_ui(ui, temp_dir)


def test_file_list_display_with_files():
    """Test file list display with files."""
    ui, temp_dir = create_test_ui()

    ui.uploaded_files = ["test.py", "main.js"]

    file_list = ui._get_file_list()

    assert "test.py" in file_list
    assert "main.js" in file_list
    assert "📄" in file_list

    cleanup_test_ui(ui, temp_dir)


def run_all_tests():
    """Run all tests and report results."""
    tests = [
        test_ui_initialization,
        test_config_loading,
        test_initialize_agent,
        test_process_message_simple,
        test_process_empty_message,
        test_process_multiple_messages,
        test_clear_conversation,
        test_file_upload_single,
        test_file_upload_multiple,
        test_file_upload_empty,
        test_file_upload_duplicate,
        test_delete_file,
        test_toggle_tool,
        test_toggle_multiple_tools,
        test_update_model,
        test_export_markdown,
        test_export_json,
        test_export_txt,
        test_export_unsupported_format,
        test_get_status,
        test_conversation_message_dataclass,
        test_simulate_agent_response_keywords,
        test_long_message,
        test_rapid_messages,
        test_file_list_display_empty,
        test_file_list_display_with_files,
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
