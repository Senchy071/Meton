#!/usr/bin/env python3
"""
Comprehensive tests for Configuration Profile Manager

Tests all aspects of profile management including:
- Profile loading and listing
- Profile activation
- Profile creation and updates
- Profile validation
- Profile comparison
- Custom profile management
- Auto-suggestions
- Edge cases and error handling
"""

import pytest
import tempfile
import shutil
import yaml
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)  # Ensure we're in the right directory

from config.profile_manager import ProfileManager, Profile


@pytest.fixture
def temp_profiles_dir():
    """Create temporary profiles directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def profile_manager(temp_profiles_dir):
    """Create profile manager with temporary directory."""
    return ProfileManager(profiles_dir=temp_profiles_dir)


@pytest.fixture
def sample_profile():
    """Create sample profile for testing."""
    return Profile(
        id="test-profile",
        name="Test Profile",
        description="A test profile",
        category="general",
        config={
            "models": {
                "primary": "test-model",
                "temperature": 0.5
            },
            "tools": {
                "web_search": {"enabled": True}
            },
            "agent": {
                "max_iterations": 10
            }
        }
    )


# ========== Profile Loading Tests ==========

def test_profile_manager_initialization(profile_manager):
    """Test profile manager initializes correctly."""
    assert profile_manager is not None
    assert isinstance(profile_manager.available_profiles, dict)
    assert profile_manager.profiles_dir.exists()


def test_list_all_profiles(profile_manager, sample_profile):
    """Test listing all profiles."""
    profile_manager.available_profiles[sample_profile.id] = sample_profile
    profile_manager._save_profile(sample_profile)

    profiles = profile_manager.list_profiles()
    assert len(profiles) >= 1
    assert any(p.id == sample_profile.id for p in profiles)


def test_list_profiles_by_category():
    """Test filtering profiles by category."""
    # Use built-in profiles
    manager = ProfileManager()
    dev_profiles = manager.list_profiles(category="development")
    research_profiles = manager.list_profiles(category="research")

    # Built-in profiles should include at least one development and one research profile
    assert len(dev_profiles) >= 1
    assert len(research_profiles) >= 1
    assert all(p.category == "development" for p in dev_profiles)
    assert all(p.category == "research" for p in research_profiles)


def test_get_existing_profile():
    """Test retrieving existing profile."""
    manager = ProfileManager()
    profiles = manager.list_profiles()

    if profiles:
        profile = manager.get_profile(profiles[0].id)
        assert profile is not None
        assert profile.id == profiles[0].id


def test_get_nonexistent_profile(profile_manager):
    """Test getting non-existent profile raises error."""
    with pytest.raises(ValueError, match="not found"):
        profile_manager.get_profile("nonexistent-profile")


# ========== Profile Activation Tests ==========

def test_activate_profile(profile_manager, sample_profile):
    """Test activating a profile."""
    profile_manager.available_profiles[sample_profile.id] = sample_profile
    profile_manager._save_profile(sample_profile)

    initial_usage = sample_profile.usage_count
    profile_manager.activate_profile(sample_profile.id)

    assert profile_manager.active_profile == sample_profile.id
    # Usage count should be incremented
    profile = profile_manager.get_profile(sample_profile.id)
    assert profile.usage_count == initial_usage + 1


def test_activate_nonexistent_profile(profile_manager):
    """Test activating non-existent profile fails."""
    with pytest.raises(ValueError, match="not found"):
        profile_manager.activate_profile("nonexistent")


def test_get_active_profile(profile_manager, sample_profile):
    """Test getting active profile."""
    profile_manager.available_profiles[sample_profile.id] = sample_profile
    profile_manager._save_profile(sample_profile)
    profile_manager.activate_profile(sample_profile.id)

    active = profile_manager.get_active_profile()
    assert active is not None
    assert active.id == sample_profile.id


def test_get_active_profile_none(profile_manager):
    """Test getting active profile when none is active."""
    active = profile_manager.get_active_profile()
    assert active is None


# ========== Profile Creation Tests ==========

def test_create_profile(profile_manager):
    """Test creating a new profile."""
    config = {
        "models": {"primary": "test"},
        "tools": {"web_search": {"enabled": True}},
        "agent": {"max_iterations": 10}
    }

    profile_id = profile_manager.create_profile(
        name="New Profile",
        description="Test profile",
        category="custom",
        config=config
    )

    assert profile_id in profile_manager.available_profiles
    profile = profile_manager.get_profile(profile_id)
    assert profile.name == "New Profile"
    assert profile.category == "custom"


def test_create_profile_with_custom_id(profile_manager):
    """Test creating profile with custom ID."""
    config = {
        "models": {"primary": "test"},
        "tools": {"web_search": {"enabled": True}},
        "agent": {"max_iterations": 10}
    }

    profile_id = profile_manager.create_profile(
        name="Custom ID Profile",
        description="Test",
        category="custom",
        config=config,
        profile_id="my-custom-id"
    )

    assert profile_id == "my-custom-id"
    assert "my-custom-id" in profile_manager.available_profiles


def test_create_invalid_profile(profile_manager):
    """Test creating invalid profile fails."""
    with pytest.raises(ValueError, match="Invalid profile"):
        profile_manager.create_profile(
            name="",  # Invalid: empty name
            description="Test",
            category="custom",
            config={}  # Invalid: empty config
        )


# ========== Profile Update Tests ==========

def test_update_profile(profile_manager, sample_profile):
    """Test updating profile."""
    sample_profile.is_builtin = False  # Make it updatable
    profile_manager.available_profiles[sample_profile.id] = sample_profile
    profile_manager._save_profile(sample_profile)

    profile_manager.update_profile(
        sample_profile.id,
        name="Updated Name",
        description="Updated description"
    )

    updated = profile_manager.get_profile(sample_profile.id)
    assert updated.name == "Updated Name"
    assert updated.description == "Updated description"


def test_update_builtin_profile_fails(profile_manager, sample_profile):
    """Test updating built-in profile fails."""
    sample_profile.is_builtin = True
    profile_manager.available_profiles[sample_profile.id] = sample_profile

    with pytest.raises(ValueError, match="Cannot modify built-in"):
        profile_manager.update_profile(sample_profile.id, name="New Name")


def test_update_nonexistent_profile(profile_manager):
    """Test updating non-existent profile fails."""
    with pytest.raises(ValueError, match="not found"):
        profile_manager.update_profile("nonexistent", name="New Name")


# ========== Profile Deletion Tests ==========

def test_delete_profile(profile_manager, sample_profile):
    """Test deleting profile."""
    sample_profile.is_builtin = False
    profile_manager.available_profiles[sample_profile.id] = sample_profile
    profile_manager._save_profile(sample_profile)

    result = profile_manager.delete_profile(sample_profile.id)
    assert result is True
    assert sample_profile.id not in profile_manager.available_profiles


def test_delete_builtin_profile_fails(profile_manager, sample_profile):
    """Test deleting built-in profile fails."""
    sample_profile.is_builtin = True
    profile_manager.available_profiles[sample_profile.id] = sample_profile

    with pytest.raises(ValueError, match="Cannot delete built-in"):
        profile_manager.delete_profile(sample_profile.id)


def test_delete_nonexistent_profile(profile_manager):
    """Test deleting non-existent profile."""
    result = profile_manager.delete_profile("nonexistent")
    assert result is False


# ========== Profile Validation Tests ==========

def test_validate_valid_profile(profile_manager, sample_profile):
    """Test validation of valid profile."""
    issues = profile_manager.validate_profile(sample_profile)
    assert len(issues) == 0


def test_validate_missing_id(profile_manager):
    """Test validation fails without ID."""
    profile = Profile(
        id="",
        name="Test",
        description="Test",
        category="general",
        config={"models": {}, "tools": {}, "agent": {}}
    )
    issues = profile_manager.validate_profile(profile)
    assert any("ID is required" in issue for issue in issues)


def test_validate_missing_name(profile_manager):
    """Test validation fails without name."""
    profile = Profile(
        id="test",
        name="",
        description="Test",
        category="general",
        config={"models": {}, "tools": {}, "agent": {}}
    )
    issues = profile_manager.validate_profile(profile)
    assert any("name is required" in issue for issue in issues)


def test_validate_invalid_category(profile_manager):
    """Test validation fails with invalid category."""
    profile = Profile(
        id="test",
        name="Test",
        description="Test",
        category="invalid_category",
        config={"models": {}, "tools": {}, "agent": {}}
    )
    issues = profile_manager.validate_profile(profile)
    assert any("Invalid category" in issue for issue in issues)


def test_validate_missing_config_keys(profile_manager):
    """Test validation fails with missing required config keys."""
    profile = Profile(
        id="test",
        name="Test",
        description="Test",
        category="general",
        config={}  # Missing required keys
    )
    issues = profile_manager.validate_profile(profile)
    assert len(issues) >= 3  # Should have issues for missing models, tools, agent


# ========== Profile Comparison Tests ==========

def test_compare_profiles():
    """Test comparing two profiles."""
    manager = ProfileManager()
    profiles = manager.list_profiles()

    if len(profiles) >= 2:
        differences = manager.compare_profiles(profiles[0].id, profiles[1].id)
        assert "profile1" in differences
        assert "profile2" in differences
        assert "changes" in differences


def test_compare_nonexistent_profiles(profile_manager):
    """Test comparing non-existent profiles fails."""
    with pytest.raises(ValueError, match="not found"):
        profile_manager.compare_profiles("nonexistent1", "nonexistent2")


# ========== Save Current As Profile Tests ==========

def test_save_current_as_profile(profile_manager):
    """Test saving current config as profile."""
    current_config = {
        "models": {"primary": "test"},
        "tools": {"web_search": {"enabled": True}},
        "agent": {"max_iterations": 10}
    }

    profile_id = profile_manager.save_current_as_profile(
        name="My Config",
        description="Saved config",
        category="custom",
        current_config=current_config
    )

    assert profile_id in profile_manager.available_profiles
    profile = profile_manager.get_profile(profile_id)
    assert profile.name == "My Config"


# ========== Profile Preview Tests ==========

def test_get_profile_preview(profile_manager, sample_profile):
    """Test generating profile preview."""
    profile_manager.available_profiles[sample_profile.id] = sample_profile
    preview = profile_manager.get_profile_preview(sample_profile.id)

    assert sample_profile.name in preview
    assert sample_profile.description in preview
    assert sample_profile.id in preview


def test_get_preview_nonexistent(profile_manager):
    """Test preview of non-existent profile fails."""
    with pytest.raises(ValueError, match="not found"):
        profile_manager.get_profile_preview("nonexistent")


# ========== Utility Tests ==========

def test_get_categories():
    """Test getting list of categories."""
    manager = ProfileManager()
    categories = manager.get_categories()
    assert isinstance(categories, list)
    assert len(categories) > 0
    assert "development" in categories
    assert "research" in categories


def test_reload_profiles(profile_manager):
    """Test reloading profiles."""
    initial_count = len(profile_manager.available_profiles)
    profile_manager.reload_profiles()
    # Count should be the same after reload
    assert len(profile_manager.available_profiles) == initial_count


# ========== Built-in Profiles Tests ==========

def test_development_profile_exists():
    """Test development profile is available."""
    manager = ProfileManager()
    profiles = manager.list_profiles()
    dev = [p for p in profiles if p.id == "development"]
    assert len(dev) == 1
    assert dev[0].category == "development"
    assert dev[0].is_builtin is True


def test_research_profile_exists():
    """Test research profile is available."""
    manager = ProfileManager()
    profiles = manager.list_profiles()
    research = [p for p in profiles if p.id == "research"]
    assert len(research) == 1
    assert research[0].category == "research"
    assert research[0].is_builtin is True


def test_writing_profile_exists():
    """Test writing profile is available."""
    manager = ProfileManager()
    profiles = manager.list_profiles()
    writing = [p for p in profiles if p.id == "writing"]
    assert len(writing) == 1
    assert writing[0].category == "writing"
    assert writing[0].is_builtin is True


def test_quick_profile_exists():
    """Test quick profile is available."""
    manager = ProfileManager()
    profiles = manager.list_profiles()
    quick = [p for p in profiles if p.id == "quick"]
    assert len(quick) == 1
    assert quick[0].category == "general"
    assert quick[0].is_builtin is True


def test_code_review_profile_exists():
    """Test code-review profile is available."""
    manager = ProfileManager()
    profiles = manager.list_profiles()
    review = [p for p in profiles if p.id == "code-review"]
    assert len(review) == 1
    assert review[0].category == "development"
    assert review[0].is_builtin is True


# ========== Auto-Suggestion Tests ==========

def test_suggest_profile_development():
    """Test auto-suggesting development profile."""
    manager = ProfileManager()
    suggestion = manager.suggest_profile("debug this code")
    assert suggestion == "development"


def test_suggest_profile_research():
    """Test auto-suggesting research profile."""
    manager = ProfileManager()
    suggestion = manager.suggest_profile("research about quantum computing")
    assert suggestion == "research"


def test_suggest_profile_writing():
    """Test auto-suggesting writing profile."""
    manager = ProfileManager()
    suggestion = manager.suggest_profile("write a blog post")
    assert suggestion == "writing"


def test_suggest_profile_code_review():
    """Test auto-suggesting code-review profile."""
    manager = ProfileManager()
    suggestion = manager.suggest_profile("review this pull request")
    assert suggestion == "code-review"


def test_suggest_profile_none():
    """Test no suggestion for generic query."""
    manager = ProfileManager()
    suggestion = manager.suggest_profile("what is the weather?")
    assert suggestion is None


# ========== Import/Export Tests ==========

def test_export_profile(profile_manager, sample_profile, temp_profiles_dir):
    """Test exporting profile."""
    profile_manager.available_profiles[sample_profile.id] = sample_profile
    profile_manager._save_profile(sample_profile)

    output_path = Path(temp_profiles_dir) / "exported.yaml"
    profile_manager.export_profile(sample_profile.id, str(output_path))

    assert output_path.exists()
    with open(output_path, 'r') as f:
        data = yaml.safe_load(f)
        assert data["id"] == sample_profile.id


def test_import_profile(profile_manager, temp_profiles_dir):
    """Test importing profile."""
    # Create a profile YAML file
    import_file = Path(temp_profiles_dir) / "import_test.yaml"
    profile_data = {
        "id": "imported-profile",
        "name": "Imported Profile",
        "description": "Test import",
        "category": "custom",
        "config": {
            "models": {"primary": "test"},
            "tools": {"web_search": {"enabled": True}},
            "agent": {"max_iterations": 10}
        }
    }

    with open(import_file, 'w') as f:
        yaml.safe_dump(profile_data, f)

    profile_id = profile_manager.import_profile(str(import_file))
    assert profile_id == "imported-profile"
    assert profile_id in profile_manager.available_profiles


def test_import_invalid_profile(profile_manager, temp_profiles_dir):
    """Test importing invalid profile fails."""
    # Create invalid YAML file
    import_file = Path(temp_profiles_dir) / "invalid.yaml"
    with open(import_file, 'w') as f:
        f.write("")  # Empty file

    with pytest.raises(ValueError, match="Invalid profile"):
        profile_manager.import_profile(str(import_file))


# ========== Integration Tests ==========

def test_full_workflow(temp_profiles_dir):
    """Test complete workflow: load, create, activate, compare."""
    manager = ProfileManager(profiles_dir=temp_profiles_dir)

    # Create profile
    config = {
        "models": {"primary": "test-model"},
        "tools": {"web_search": {"enabled": True}},
        "agent": {"max_iterations": 10}
    }

    profile_id = manager.create_profile(
        name="Test Profile",
        description="Integration test",
        category="custom",
        config=config
    )

    # Activate profile
    manager.activate_profile(profile_id)
    active = manager.get_active_profile()
    assert active.id == profile_id

    # List profiles
    profiles = manager.list_profiles()
    assert len(profiles) >= 1

    # Get preview
    preview = manager.get_profile_preview(profile_id)
    assert "Test Profile" in preview


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
