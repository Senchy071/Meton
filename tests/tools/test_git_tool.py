#!/usr/bin/env python3
"""
Tests for Git Tool.

Tests cover:
- Repository detection
- Status retrieval
- Diff generation
- Commit analysis
- Commit message generation
- File history
- Branch operations
- Search functionality
- Error handling
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from tools.git_tool import GitTool
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    print("Warning: GitPython not installed, skipping tests")


def test_git_tool_initialization():
    """Test GitTool initialization."""
    if not GIT_AVAILABLE:
        print("⏭️  test_git_tool_initialization (GitPython not available)")
        return

    git_tool = GitTool(".")
    assert git_tool is not None
    assert git_tool.repo_path is not None


def test_is_git_repo():
    """Test repository detection."""
    if not GIT_AVAILABLE:
        print("⏭️  test_is_git_repo (GitPython not available)")
        return

    git_tool = GitTool(".")
    # Should be in a git repo (the meton project itself)
    assert git_tool.is_git_repo() is True


def test_get_repo_status():
    """Test getting repository status."""
    if not GIT_AVAILABLE:
        print("⏭️  test_get_repo_status (GitPython not available)")
        return

    git_tool = GitTool(".")
    if not git_tool.is_git_repo():
        print("⏭️  test_get_repo_status (not in git repo)")
        return

    status = git_tool.get_repo_status()

    assert "branch" in status
    assert "is_dirty" in status
    assert isinstance(status["is_dirty"], bool)


def test_get_branch_info():
    """Test getting branch information."""
    if not GIT_AVAILABLE:
        print("⏭️  test_get_branch_info (GitPython not available)")
        return

    git_tool = GitTool(".")
    if not git_tool.is_git_repo():
        print("⏭️  test_get_branch_info (not in git repo)")
        return

    info = git_tool.get_branch_info()

    assert "current" in info
    assert "all_branches" in info
    assert isinstance(info["all_branches"], list)


def test_analyze_commit_head():
    """Test analyzing HEAD commit."""
    if not GIT_AVAILABLE:
        print("⏭️  test_analyze_commit_head (GitPython not available)")
        return

    git_tool = GitTool(".")
    if not git_tool.is_git_repo():
        print("⏭️  test_analyze_commit_head (not in git repo)")
        return

    commit = git_tool.analyze_commit("HEAD")

    assert "sha" in commit
    assert "author" in commit
    assert "message" in commit


def test_suggest_branch_name_feature():
    """Test branch name suggestion for feature."""
    if not GIT_AVAILABLE:
        print("⏭️  test_suggest_branch_name_feature (GitPython not available)")
        return

    git_tool = GitTool(".")

    name = git_tool.suggest_branch_name("add user authentication")

    assert name.startswith("feature/")
    assert "authentication" in name


def test_suggest_branch_name_bugfix():
    """Test branch name suggestion for bugfix."""
    if not GIT_AVAILABLE:
        print("⏭️  test_suggest_branch_name_bugfix (GitPython not available)")
        return

    git_tool = GitTool(".")

    name = git_tool.suggest_branch_name("fix login bug")

    assert name.startswith("bugfix/")
    assert "login" in name


def test_suggest_branch_name_hotfix():
    """Test branch name suggestion for hotfix."""
    if not GIT_AVAILABLE:
        print("⏭️  test_suggest_branch_name_hotfix (GitPython not available)")
        return

    git_tool = GitTool(".")

    name = git_tool.suggest_branch_name("urgent security hotfix")

    assert name.startswith("hotfix/")


def test_get_file_history():
    """Test getting file history."""
    if not GIT_AVAILABLE:
        print("⏭️  test_get_file_history (GitPython not available)")
        return

    git_tool = GitTool(".")
    if not git_tool.is_git_repo():
        print("⏭️  test_get_file_history (not in git repo)")
        return

    # Test with README or meton.py which should exist
    history = git_tool.get_file_history("meton.py", max_commits=5)

    assert isinstance(history, list)
    if history and "error" not in history[0]:
        assert "sha" in history[0]
        assert "author" in history[0]


def test_find_related_commits():
    """Test searching commits."""
    if not GIT_AVAILABLE:
        print("⏭️  test_find_related_commits (GitPython not available)")
        return

    git_tool = GitTool(".")
    if not git_tool.is_git_repo():
        print("⏭️  test_find_related_commits (not in git repo)")
        return

    # Search for recent commits
    commits = git_tool.find_related_commits("Task", max_results=5)

    assert isinstance(commits, list)


def test_execute_status():
    """Test execute with status action."""
    if not GIT_AVAILABLE:
        print("⏭️  test_execute_status (GitPython not available)")
        return

    git_tool = GitTool(".")
    if not git_tool.is_git_repo():
        print("⏭️  test_execute_status (not in git repo)")
        return

    result = git_tool.execute("status")

    assert isinstance(result, str)
    assert "Branch:" in result


def test_execute_branch_info():
    """Test execute with branch_info action."""
    if not GIT_AVAILABLE:
        print("⏭️  test_execute_branch_info (GitPython not available)")
        return

    git_tool = GitTool(".")
    if not git_tool.is_git_repo():
        print("⏭️  test_execute_branch_info (not in git repo)")
        return

    result = git_tool.execute("branch_info")

    assert isinstance(result, str)
    assert "Current branch:" in result


def test_execute_suggest_branch():
    """Test execute with suggest_branch action."""
    if not GIT_AVAILABLE:
        print("⏭️  test_execute_suggest_branch (GitPython not available)")
        return

    git_tool = GitTool(".")

    result = git_tool.execute("suggest_branch", description="add new feature")

    assert isinstance(result, str)
    assert "/" in result  # Should have prefix/name format


def test_execute_unknown_action():
    """Test execute with unknown action."""
    if not GIT_AVAILABLE:
        print("⏭️  test_execute_unknown_action (GitPython not available)")
        return

    git_tool = GitTool(".")

    result = git_tool.execute("unknown_action")

    assert "Error" in result
    assert "Unknown action" in result


def test_suggest_commit_message_no_changes():
    """Test commit message generation with no changes."""
    if not GIT_AVAILABLE:
        print("⏭️  test_suggest_commit_message_no_changes (GitPython not available)")
        return

    git_tool = GitTool(".")
    if not git_tool.is_git_repo():
        print("⏭️  test_suggest_commit_message_no_changes (not in git repo)")
        return

    message = git_tool.suggest_commit_message()

    assert isinstance(message, str)


def test_review_changes():
    """Test reviewing changes."""
    if not GIT_AVAILABLE:
        print("⏭️  test_review_changes (GitPython not available)")
        return

    git_tool = GitTool(".")
    if not git_tool.is_git_repo():
        print("⏭️  test_review_changes (not in git repo)")
        return

    review = git_tool.review_changes()

    assert "files" in review or "error" in review


def test_get_diff():
    """Test getting diff."""
    if not GIT_AVAILABLE:
        print("⏭️  test_get_diff (GitPython not available)")
        return

    git_tool = GitTool(".")
    if not git_tool.is_git_repo():
        print("⏭️  test_get_diff (not in git repo)")
        return

    diff = git_tool.get_diff()

    assert isinstance(diff, str)


def test_format_status():
    """Test status formatting."""
    if not GIT_AVAILABLE:
        print("⏭️  test_format_status (GitPython not available)")
        return

    git_tool = GitTool(".")

    status = {"branch": "main", "is_dirty": False, "ahead": 0, "behind": 0, "untracked_files": [], "modified_files": [], "staged_files": []}
    result = git_tool._format_status(status)

    assert "Branch: main" in result
    assert "clean" in result


def test_format_history():
    """Test history formatting."""
    if not GIT_AVAILABLE:
        print("⏭️  test_format_history (GitPython not available)")
        return

    git_tool = GitTool(".")

    history = [
        {"sha": "abc123", "author": "Test", "date": "2025-01-01", "message": "Test commit"}
    ]
    result = git_tool._format_history(history)

    assert "Commit History:" in result
    assert "abc123" in result


def test_determine_commit_type():
    """Test commit type determination."""
    if not GIT_AVAILABLE:
        print("⏭️  test_determine_commit_type (GitPython not available)")
        return

    git_tool = GitTool(".")

    # Test with bug fix
    commit_type = git_tool._determine_commit_type(["file.py"], "fix the bug in authentication")
    assert commit_type == "fix"

    # Test with test files
    commit_type = git_tool._determine_commit_type(["test_file.py"], "add tests")
    assert commit_type == "test"

    # Test with docs
    commit_type = git_tool._determine_commit_type(["README.md"], "update docs")
    assert commit_type == "docs"


def run_all_tests():
    """Run all tests and report results."""
    tests = [
        test_git_tool_initialization,
        test_is_git_repo,
        test_get_repo_status,
        test_get_branch_info,
        test_analyze_commit_head,
        test_suggest_branch_name_feature,
        test_suggest_branch_name_bugfix,
        test_suggest_branch_name_hotfix,
        test_get_file_history,
        test_find_related_commits,
        test_execute_status,
        test_execute_branch_info,
        test_execute_suggest_branch,
        test_execute_unknown_action,
        test_suggest_commit_message_no_changes,
        test_review_changes,
        test_get_diff,
        test_format_status,
        test_format_history,
        test_determine_commit_type,
    ]

    print(f"Running {len(tests)} tests...\n")

    passed = 0
    failed = 0
    skipped = 0

    for test in tests:
        try:
            test()
            print(f"✅ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            if "not available" in str(e) or "GitPython" in str(e):
                skipped += 1
            else:
                print(f"❌ {test.__name__}: {type(e).__name__}: {e}")
                failed += 1

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped out of {len(tests)} tests")
    if passed > 0:
        print(f"Success rate: {passed/(passed+failed)*100:.1f}% (of non-skipped)")

    if failed == 0:
        print("✅ All tests passed!")
        return 0
    else:
        print(f"❌ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    if not GIT_AVAILABLE:
        print("⚠️  GitPython not installed. Install with: pip install GitPython")
        print("Tests will be skipped.")
        exit(0)

    exit(run_all_tests())
