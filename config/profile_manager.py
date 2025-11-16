#!/usr/bin/env python3
"""
Configuration Profile Manager for Meton

Manages configuration profiles for different use cases (development, research, writing, etc.)
Supports creating, activating, comparing, and managing profiles.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
import shutil
import copy


@dataclass
class Profile:
    """Represents a configuration profile."""
    id: str
    name: str
    description: str
    category: str  # development, research, writing, general, custom
    config: Dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_used: str = field(default_factory=lambda: datetime.now().isoformat())
    usage_count: int = 0
    is_builtin: bool = False  # Built-in profiles cannot be deleted


class ProfileManager:
    """Manages configuration profiles for different use cases."""

    VALID_CATEGORIES = ["development", "research", "writing", "general", "custom"]
    REQUIRED_CONFIG_KEYS = ["models", "tools", "agent"]

    def __init__(self, profiles_dir: str = "config/profiles", config_manager=None):
        """Initialize profile manager.

        Args:
            profiles_dir: Directory containing profile YAML files
            config_manager: Reference to ConfigManager instance for applying profiles
        """
        # Handle both absolute and relative paths
        if not os.path.isabs(profiles_dir):
            # Get project root (parent of this file's parent)
            project_root = Path(__file__).parent.parent
            self.profiles_dir = project_root / profiles_dir
        else:
            self.profiles_dir = Path(profiles_dir)

        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.available_profiles: Dict[str, Profile] = {}
        self.active_profile: Optional[str] = None
        self.config_manager = config_manager

        # Load all profiles
        self._load_profiles()

    def _load_profiles(self):
        """Load all profile YAML files from profiles directory."""
        self.available_profiles.clear()

        if not self.profiles_dir.exists():
            return

        # Load all .yaml files
        for yaml_file in self.profiles_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r') as f:
                    data = yaml.safe_load(f)

                if not data:
                    continue

                # Create Profile object
                profile = Profile(
                    id=data.get("id", yaml_file.stem),
                    name=data.get("name", "Unnamed Profile"),
                    description=data.get("description", ""),
                    category=data.get("category", "custom"),
                    config=data.get("config", {}),
                    created_at=data.get("created_at", datetime.now().isoformat()),
                    last_used=data.get("last_used", datetime.now().isoformat()),
                    usage_count=data.get("usage_count", 0),
                    is_builtin=data.get("is_builtin", False)
                )

                self.available_profiles[profile.id] = profile

            except Exception as e:
                print(f"Warning: Failed to load profile {yaml_file}: {e}")

    def list_profiles(self, category: Optional[str] = None) -> List[Profile]:
        """List available profiles.

        Args:
            category: Filter by category (optional)

        Returns:
            List of Profile objects, sorted by usage_count descending
        """
        profiles = list(self.available_profiles.values())

        # Filter by category if specified
        if category:
            profiles = [p for p in profiles if p.category == category]

        # Sort by usage count (most used first), then by name
        profiles.sort(key=lambda p: (-p.usage_count, p.name))

        return profiles

    def get_profile(self, profile_id: str) -> Profile:
        """Get specific profile by ID.

        Args:
            profile_id: Profile identifier

        Returns:
            Profile object

        Raises:
            ValueError: If profile not found
        """
        if profile_id not in self.available_profiles:
            raise ValueError(f"Profile '{profile_id}' not found")

        return self.available_profiles[profile_id]

    def activate_profile(self, profile_id: str) -> None:
        """Set profile as active and apply configuration.

        Args:
            profile_id: Profile identifier

        Raises:
            ValueError: If profile not found
        """
        profile = self.get_profile(profile_id)

        # Update usage statistics
        profile.last_used = datetime.now().isoformat()
        profile.usage_count += 1

        # Set as active
        self.active_profile = profile_id

        # Save updated profile
        self._save_profile(profile)

        # Apply configuration if config_manager is available
        if self.config_manager:
            self._apply_profile_config(profile)

    def _apply_profile_config(self, profile: Profile):
        """Apply profile configuration to config_manager.

        Args:
            profile: Profile to apply
        """
        if not self.config_manager:
            return

        # Deep merge profile config into current config
        self._deep_merge(self.config_manager.config.__dict__, profile.config)

    def _deep_merge(self, target: Dict, source: Dict):
        """Deep merge source dictionary into target dictionary.

        Args:
            target: Target dictionary (modified in place)
            source: Source dictionary
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = copy.deepcopy(value)

    def create_profile(
        self,
        name: str,
        description: str,
        category: str,
        config: Dict,
        profile_id: Optional[str] = None
    ) -> str:
        """Create new profile.

        Args:
            name: Profile name
            description: Profile description
            category: Profile category
            config: Configuration dictionary
            profile_id: Custom profile ID (optional, auto-generated if not provided)

        Returns:
            Profile ID

        Raises:
            ValueError: If profile is invalid
        """
        # Generate ID if not provided
        if not profile_id:
            profile_id = name.lower().replace(" ", "-")

        # Create profile
        profile = Profile(
            id=profile_id,
            name=name,
            description=description,
            category=category,
            config=config,
            created_at=datetime.now().isoformat(),
            last_used=datetime.now().isoformat(),
            usage_count=0,
            is_builtin=False
        )

        # Validate profile
        issues = self.validate_profile(profile)
        if issues:
            raise ValueError(f"Invalid profile: {'; '.join(issues)}")

        # Save profile
        self.available_profiles[profile.id] = profile
        self._save_profile(profile)

        return profile.id

    def update_profile(self, profile_id: str, **kwargs) -> None:
        """Update profile fields.

        Args:
            profile_id: Profile identifier
            **kwargs: Fields to update (name, description, category, config)

        Raises:
            ValueError: If profile not found or is built-in
        """
        profile = self.get_profile(profile_id)

        if profile.is_builtin:
            raise ValueError(f"Cannot modify built-in profile '{profile_id}'")

        # Update allowed fields
        if "name" in kwargs:
            profile.name = kwargs["name"]
        if "description" in kwargs:
            profile.description = kwargs["description"]
        if "category" in kwargs:
            profile.category = kwargs["category"]
        if "config" in kwargs:
            profile.config = kwargs["config"]

        # Validate updated profile
        issues = self.validate_profile(profile)
        if issues:
            raise ValueError(f"Invalid profile update: {'; '.join(issues)}")

        # Save updated profile
        self._save_profile(profile)

    def delete_profile(self, profile_id: str) -> bool:
        """Delete profile.

        Args:
            profile_id: Profile identifier

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If trying to delete built-in profile
        """
        if profile_id not in self.available_profiles:
            return False

        profile = self.available_profiles[profile_id]

        if profile.is_builtin:
            raise ValueError(f"Cannot delete built-in profile '{profile_id}'")

        # Remove from memory
        del self.available_profiles[profile_id]

        # Delete file
        profile_file = self.profiles_dir / f"{profile_id}.yaml"
        if profile_file.exists():
            profile_file.unlink()

        # Clear active if this was active
        if self.active_profile == profile_id:
            self.active_profile = None

        return True

    def get_active_profile(self) -> Optional[Profile]:
        """Get currently active profile.

        Returns:
            Active Profile object or None if using default config
        """
        if self.active_profile and self.active_profile in self.available_profiles:
            return self.available_profiles[self.active_profile]
        return None

    def save_current_as_profile(
        self,
        name: str,
        description: str,
        category: str,
        current_config: Dict
    ) -> str:
        """Save current configuration as new profile.

        Args:
            name: Profile name
            description: Profile description
            category: Profile category
            current_config: Current configuration dictionary

        Returns:
            Profile ID
        """
        return self.create_profile(
            name=name,
            description=description,
            category=category,
            config=current_config
        )

    def compare_profiles(self, profile_id1: str, profile_id2: str) -> Dict[str, Any]:
        """Show differences between two profiles.

        Args:
            profile_id1: First profile ID
            profile_id2: Second profile ID

        Returns:
            Dictionary of changed settings

        Raises:
            ValueError: If either profile not found
        """
        profile1 = self.get_profile(profile_id1)
        profile2 = self.get_profile(profile_id2)

        differences = {
            "profile1": {"id": profile1.id, "name": profile1.name},
            "profile2": {"id": profile2.id, "name": profile2.name},
            "changes": {}
        }

        # Compare configurations
        self._compare_dicts(
            profile1.config,
            profile2.config,
            differences["changes"],
            path=""
        )

        return differences

    def _compare_dicts(self, dict1: Dict, dict2: Dict, result: Dict, path: str):
        """Recursively compare two dictionaries.

        Args:
            dict1: First dictionary
            dict2: Second dictionary
            result: Result dictionary to store differences
            path: Current path in nested structure
        """
        all_keys = set(dict1.keys()) | set(dict2.keys())

        for key in sorted(all_keys):
            current_path = f"{path}.{key}" if path else key

            if key not in dict1:
                result[current_path] = {"profile1": None, "profile2": dict2[key]}
            elif key not in dict2:
                result[current_path] = {"profile1": dict1[key], "profile2": None}
            elif isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                # Recursively compare nested dicts
                self._compare_dicts(dict1[key], dict2[key], result, current_path)
            elif dict1[key] != dict2[key]:
                result[current_path] = {"profile1": dict1[key], "profile2": dict2[key]}

    def validate_profile(self, profile: Profile) -> List[str]:
        """Check profile validity.

        Args:
            profile: Profile to validate

        Returns:
            List of validation issues (empty if valid)
        """
        issues = []

        # Check required fields
        if not profile.id:
            issues.append("Profile ID is required")

        if not profile.name:
            issues.append("Profile name is required")

        if not profile.category:
            issues.append("Profile category is required")
        elif profile.category not in self.VALID_CATEGORIES:
            issues.append(
                f"Invalid category '{profile.category}'. "
                f"Must be one of: {', '.join(self.VALID_CATEGORIES)}"
            )

        # Check configuration
        if profile.config is None:
            issues.append("Profile must have a configuration")
        else:
            # Check required top-level keys
            for key in self.REQUIRED_CONFIG_KEYS:
                if key not in profile.config:
                    issues.append(f"Configuration missing required key: {key}")

        return issues

    def _save_profile(self, profile: Profile):
        """Save profile to YAML file.

        Args:
            profile: Profile to save
        """
        profile_file = self.profiles_dir / f"{profile.id}.yaml"

        # Convert to dictionary
        data = {
            "id": profile.id,
            "name": profile.name,
            "description": profile.description,
            "category": profile.category,
            "config": profile.config,
            "created_at": profile.created_at,
            "last_used": profile.last_used,
            "usage_count": profile.usage_count,
            "is_builtin": profile.is_builtin
        }

        # Write to file
        with open(profile_file, 'w') as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

    def get_categories(self) -> List[str]:
        """Get list of profile categories.

        Returns:
            List of category names
        """
        return self.VALID_CATEGORIES.copy()

    def reload_profiles(self):
        """Reload all profiles from disk."""
        self._load_profiles()

    def suggest_profile(self, query: str) -> Optional[str]:
        """Suggest profile based on query content.

        Args:
            query: User query

        Returns:
            Suggested profile ID or None
        """
        query_lower = query.lower()

        # Code-related keywords → development profile
        code_keywords = ["code", "debug", "function", "class", "implement", "refactor",
                        "test", "bug", "error", "git", "commit"]
        if any(kw in query_lower for kw in code_keywords):
            if "development" in self.available_profiles:
                return "development"

        # Research keywords → research profile
        research_keywords = ["research", "compare", "analyze", "find", "search",
                            "investigate", "study", "explore"]
        if any(kw in query_lower for kw in research_keywords):
            if "research" in self.available_profiles:
                return "research"

        # Writing keywords → writing profile
        writing_keywords = ["write", "document", "blog", "article", "essay",
                           "content", "draft", "compose"]
        if any(kw in query_lower for kw in writing_keywords):
            if "writing" in self.available_profiles:
                return "writing"

        # Review keywords → code-review profile
        review_keywords = ["review", "audit", "check", "validate", "inspect"]
        if any(kw in query_lower for kw in review_keywords):
            if "code-review" in self.available_profiles:
                return "code-review"

        return None

    def export_profile(self, profile_id: str, output_path: str) -> None:
        """Export profile to file.

        Args:
            profile_id: Profile identifier
            output_path: Output file path

        Raises:
            ValueError: If profile not found
        """
        profile = self.get_profile(profile_id)

        # Copy profile file to output path
        source_file = self.profiles_dir / f"{profile_id}.yaml"
        if source_file.exists():
            shutil.copy2(source_file, output_path)
        else:
            # Generate from in-memory profile
            self._save_profile(profile)
            shutil.copy2(source_file, output_path)

    def import_profile(self, input_path: str) -> str:
        """Import profile from file.

        Args:
            input_path: Input file path

        Returns:
            Profile ID

        Raises:
            ValueError: If file is invalid
        """
        # Load profile from file
        with open(input_path, 'r') as f:
            data = yaml.safe_load(f)

        if not data:
            raise ValueError("Invalid profile file: empty or invalid YAML")

        # Create profile
        profile_id = data.get("id", Path(input_path).stem)

        profile = Profile(
            id=profile_id,
            name=data.get("name", "Imported Profile"),
            description=data.get("description", ""),
            category=data.get("category", "custom"),
            config=data.get("config", {}),
            created_at=data.get("created_at", datetime.now().isoformat()),
            last_used=datetime.now().isoformat(),
            usage_count=0,
            is_builtin=False  # Imported profiles are never built-in
        )

        # Validate
        issues = self.validate_profile(profile)
        if issues:
            raise ValueError(f"Invalid profile: {'; '.join(issues)}")

        # Save
        self.available_profiles[profile.id] = profile
        self._save_profile(profile)

        return profile.id

    def get_profile_preview(self, profile_id: str) -> str:
        """Get formatted preview of profile.

        Args:
            profile_id: Profile identifier

        Returns:
            Formatted preview string

        Raises:
            ValueError: If profile not found
        """
        profile = self.get_profile(profile_id)

        preview = f"""Profile: {profile.name}
ID: {profile.id}
Category: {profile.category}
Description: {profile.description}

Usage Statistics:
  - Used {profile.usage_count} times
  - Last used: {profile.last_used}
  - Created: {profile.created_at}
  - Built-in: {'Yes' if profile.is_builtin else 'No'}

Configuration Highlights:
  - Primary model: {profile.config.get('models', {}).get('primary', 'N/A')}
  - Temperature: {profile.config.get('models', {}).get('temperature', 'N/A')}
  - Enabled tools: {len([k for k, v in profile.config.get('tools', {}).items() if isinstance(v, dict) and v.get('enabled')])}
  - Skills enabled: {profile.config.get('skills', {}).get('enabled', False)}
  - Reflection enabled: {profile.config.get('reflection', {}).get('enabled', False)}
"""

        return preview
