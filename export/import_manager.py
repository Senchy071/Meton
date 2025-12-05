#!/usr/bin/env python3
"""
Import Manager for Meton

Handles importing all types of Meton data with validation and merge capabilities.
Supports restoring from backups and validating import files.
"""

import os
import json
import yaml
import tarfile
import zipfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging


class ImportManager:
    """Imports Meton data and configurations."""

    METON_VERSION = "1.0.0"
    COMPATIBLE_VERSIONS = ["1.0.0"]  # List of compatible format versions

    def __init__(self):
        """Initialize import manager."""
        self.logger = logging.getLogger(__name__)

    def import_all(self, import_file: str, merge: bool = False) -> Dict:
        """Import complete Meton state.

        Args:
            import_file: Path to import file
            merge: If True, merge with existing data; else replace

        Returns:
            Summary of imported data

        Raises:
            ValueError: If import file is invalid
        """
        import_path = Path(import_file)
        if not import_path.exists():
            raise ValueError(f"Import file not found: {import_file}")

        # Load and validate import data
        with open(import_path, 'r') as f:
            import_data = json.load(f)

        # Validate
        validation = self.validate_import_file(import_file)
        if not validation["valid"]:
            raise ValueError(f"Invalid import file: {validation['errors']}")

        summary = {
            "imported_date": datetime.now().isoformat(),
            "source_file": str(import_file),
            "merge_mode": merge,
            "counts": {}
        }

        # Import configuration
        if "configuration" in import_data:
            try:
                self._import_configuration_data(import_data["configuration"])
                summary["counts"]["configuration"] = 1
            except Exception as e:
                self.logger.error(f"Failed to import configuration: {e}")
                summary["counts"]["configuration"] = 0

        # Import memories
        if "memories" in import_data:
            try:
                count = self._import_memories_data(import_data["memories"], merge)
                summary["counts"]["memories"] = count
            except Exception as e:
                self.logger.error(f"Failed to import memories: {e}")
                summary["counts"]["memories"] = 0

        # Import conversations
        if "conversations" in import_data:
            try:
                count = self._import_conversations_data(import_data["conversations"], merge)
                summary["counts"]["conversations"] = count
            except Exception as e:
                self.logger.error(f"Failed to import conversations: {e}")
                summary["counts"]["conversations"] = 0

        # Import analytics
        if "analytics" in import_data:
            try:
                count = self._import_analytics_data(import_data["analytics"], merge)
                summary["counts"]["analytics"] = count
            except Exception as e:
                self.logger.error(f"Failed to import analytics: {e}")
                summary["counts"]["analytics"] = 0

        # Import feedback
        if "feedback" in import_data:
            try:
                count = self._import_feedback_data(import_data["feedback"], merge)
                summary["counts"]["feedback"] = count
            except Exception as e:
                self.logger.error(f"Failed to import feedback: {e}")
                summary["counts"]["feedback"] = 0

        # Import profiles
        if "profiles" in import_data:
            try:
                count = self._import_profiles_data(import_data["profiles"], overwrite=merge)
                summary["counts"]["profiles"] = count
            except Exception as e:
                self.logger.error(f"Failed to import profiles: {e}")
                summary["counts"]["profiles"] = 0

        # Import patterns
        if "patterns" in import_data:
            try:
                count = self._import_patterns_data(import_data["patterns"], merge)
                summary["counts"]["patterns"] = count
            except Exception as e:
                self.logger.error(f"Failed to import patterns: {e}")
                summary["counts"]["patterns"] = 0

        self.logger.info(f"Import complete: {summary}")
        return summary

    def import_configuration(self, import_file: str, apply: bool = True) -> Dict:
        """Import configuration.

        Args:
            import_file: Path to import file
            apply: If True, activate immediately

        Returns:
            Imported configuration

        Raises:
            ValueError: If import file is invalid
        """
        import_path = Path(import_file)
        if not import_path.exists():
            raise ValueError(f"Import file not found: {import_file}")

        # Load configuration
        with open(import_path, 'r') as f:
            if import_path.suffix == '.yaml':
                config = yaml.safe_load(f)
            else:
                config = json.load(f)

        if apply:
            self._import_configuration_data(config)

        self.logger.info(f"Configuration imported from {import_file}")
        return config

    def import_memories(self, import_file: str, merge: bool = True) -> int:
        """Import memories.

        Args:
            import_file: Path to import file
            merge: Merge or replace existing

        Returns:
            Count of imported memories

        Raises:
            ValueError: If import file is invalid
        """
        import_path = Path(import_file)
        if not import_path.exists():
            raise ValueError(f"Import file not found: {import_file}")

        with open(import_path, 'r') as f:
            import_data = json.load(f)

        memories = import_data.get("memories", [])
        count = self._import_memories_data(memories, merge)

        self.logger.info(f"Imported {count} memories from {import_file}")
        return count

    def import_conversations(self, import_file: str, merge: bool = True) -> int:
        """Import conversation history.

        Args:
            import_file: Path to import file
            merge: Merge or replace existing

        Returns:
            Count of imported conversations

        Raises:
            ValueError: If import file is invalid
        """
        import_path = Path(import_file)
        if not import_path.exists():
            raise ValueError(f"Import file not found: {import_file}")

        with open(import_path, 'r') as f:
            import_data = json.load(f)

        conversations = import_data.get("conversations", [])
        count = self._import_conversations_data(conversations, merge)

        self.logger.info(f"Imported {count} conversations from {import_file}")
        return count

    def import_analytics(self, import_file: str, merge: bool = True) -> int:
        """Import analytics data.

        Args:
            import_file: Path to import file
            merge: Merge or replace existing

        Returns:
            Count of imported analytics records

        Raises:
            ValueError: If import file is invalid
        """
        import_path = Path(import_file)
        if not import_path.exists():
            raise ValueError(f"Import file not found: {import_file}")

        with open(import_path, 'r') as f:
            import_data = json.load(f)

        analytics = import_data.get("analytics", {})
        count = self._import_analytics_data(analytics, merge)

        self.logger.info(f"Imported analytics from {import_file}")
        return count

    def import_feedback(self, import_file: str, merge: bool = True) -> int:
        """Import feedback data.

        Args:
            import_file: Path to import file
            merge: Merge or replace existing

        Returns:
            Count of imported feedback records

        Raises:
            ValueError: If import file is invalid
        """
        import_path = Path(import_file)
        if not import_path.exists():
            raise ValueError(f"Import file not found: {import_file}")

        with open(import_path, 'r') as f:
            import_data = json.load(f)

        feedback = import_data.get("feedback", [])
        count = self._import_feedback_data(feedback, merge)

        self.logger.info(f"Imported {count} feedback records from {import_file}")
        return count

    def import_profiles(self, import_file: str, overwrite: bool = False) -> int:
        """Import profiles.

        Args:
            import_file: Path to import file
            overwrite: Overwrite existing with same ID

        Returns:
            Count of imported profiles

        Raises:
            ValueError: If import file is invalid
        """
        import_path = Path(import_file)
        if not import_path.exists():
            raise ValueError(f"Import file not found: {import_file}")

        with open(import_path, 'r') as f:
            import_data = json.load(f)

        profiles = import_data.get("profiles", [])
        count = self._import_profiles_data(profiles, overwrite)

        self.logger.info(f"Imported {count} profiles from {import_file}")
        return count

    def import_patterns(self, import_file: str, merge: bool = True) -> int:
        """Import patterns and insights.

        Args:
            import_file: Path to import file
            merge: Merge or replace existing

        Returns:
            Count of imported patterns

        Raises:
            ValueError: If import file is invalid
        """
        import_path = Path(import_file)
        if not import_path.exists():
            raise ValueError(f"Import file not found: {import_file}")

        with open(import_path, 'r') as f:
            import_data = json.load(f)

        patterns = import_data.get("patterns", [])
        count = self._import_patterns_data(patterns, merge)

        self.logger.info(f"Imported {count} patterns from {import_file}")
        return count

    def restore_backup(self, backup_file: str) -> Dict:
        """Restore from backup archive.

        Args:
            backup_file: Path to backup file

        Returns:
            Restoration summary

        Raises:
            ValueError: If backup file is invalid
        """
        backup_path = Path(backup_file)
        if not backup_path.exists():
            raise ValueError(f"Backup file not found: {backup_file}")

        # Create temporary directory for extraction
        import tempfile
        temp_dir = Path(tempfile.mkdtemp())

        try:
            # Extract archive
            if backup_path.suffix == '.gz' or backup_path.name.endswith('.tar.gz'):
                with tarfile.open(backup_path, "r:gz") as tar:
                    tar.extractall(temp_dir)
            elif backup_path.suffix == '.zip':
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(temp_dir)
            else:
                # Assume uncompressed directory
                shutil.copytree(backup_path, temp_dir / backup_path.name)

            # Find backup directory (may be nested)
            backup_dirs = list(temp_dir.iterdir())
            if len(backup_dirs) == 1 and backup_dirs[0].is_dir():
                backup_dir = backup_dirs[0]
            else:
                backup_dir = temp_dir

            # Validate metadata
            metadata_file = backup_dir / "metadata.json"
            if not metadata_file.exists():
                raise ValueError("Invalid backup: missing metadata.json")

            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            # Check version compatibility
            format_version = metadata.get("format_version", "0.0.0")
            if not self._check_version_compatibility(format_version):
                raise ValueError(f"Incompatible backup version: {format_version}")

            summary = {
                "restored_date": datetime.now().isoformat(),
                "backup_file": str(backup_file),
                "backup_metadata": metadata,
                "counts": {}
            }

            # Restore configuration
            config_file = backup_dir / "config.yaml"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                self._import_configuration_data(config)
                summary["counts"]["configuration"] = 1

            # Restore memories
            memories_file = backup_dir / "memories.json"
            if memories_file.exists():
                with open(memories_file, 'r') as f:
                    memories = json.load(f)
                count = self._import_memories_data(memories, merge=False)
                summary["counts"]["memories"] = count

            # Restore conversations
            conv_dir = backup_dir / "conversations"
            if conv_dir.exists():
                conversations = []
                for conv_file in conv_dir.glob("*.json"):
                    with open(conv_file, 'r') as f:
                        conversations.append(json.load(f))
                count = self._import_conversations_data(conversations, merge=False)
                summary["counts"]["conversations"] = count

            # Restore analytics
            analytics_file = backup_dir / "analytics.json"
            if analytics_file.exists():
                with open(analytics_file, 'r') as f:
                    analytics = json.load(f)
                count = self._import_analytics_data(analytics, merge=False)
                summary["counts"]["analytics"] = count

            # Restore feedback
            feedback_file = backup_dir / "feedback.json"
            if feedback_file.exists():
                with open(feedback_file, 'r') as f:
                    feedback = json.load(f)
                count = self._import_feedback_data(feedback, merge=False)
                summary["counts"]["feedback"] = count

            # Restore profiles
            profiles_dir = backup_dir / "profiles"
            if profiles_dir.exists():
                profiles = []
                for profile_file in profiles_dir.glob("*.yaml"):
                    with open(profile_file, 'r') as f:
                        profiles.append(yaml.safe_load(f))
                count = self._import_profiles_data(profiles, overwrite=True)
                summary["counts"]["profiles"] = count

            # Restore patterns
            patterns_file = backup_dir / "patterns.json"
            if patterns_file.exists():
                with open(patterns_file, 'r') as f:
                    patterns = json.load(f)
                count = self._import_patterns_data(patterns, merge=False)
                summary["counts"]["patterns"] = count

            self.logger.info(f"Backup restored: {summary}")
            return summary

        finally:
            # Clean up temp directory
            shutil.rmtree(temp_dir)

    def validate_import_file(self, import_file: str) -> Dict:
        """Validate import file before importing.

        Args:
            import_file: Path to import file

        Returns:
            Validation result dict with 'valid', 'errors', 'warnings'
        """
        result = {
            "valid": False,
            "errors": [],
            "warnings": []
        }

        import_path = Path(import_file)

        # Check file exists
        if not import_path.exists():
            result["errors"].append(f"File not found: {import_file}")
            return result

        # Check file size (prevent DoS)
        max_size = 100 * 1024 * 1024  # 100MB
        if import_path.stat().st_size > max_size:
            result["errors"].append(f"File too large (max {max_size} bytes)")
            return result

        try:
            # Load and parse file
            with open(import_path, 'r') as f:
                if import_path.suffix == '.yaml':
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)

            # Check for metadata
            if "export_metadata" not in data:
                result["warnings"].append("Missing export_metadata")
            else:
                metadata = data["export_metadata"]

                # Check version
                version = metadata.get("version", "0.0.0")
                if not self._check_version_compatibility(version):
                    result["errors"].append(f"Incompatible version: {version}")

                # Check export type
                export_type = metadata.get("export_type")
                if not export_type:
                    result["warnings"].append("Missing export_type")

            # Validate structure based on export type
            export_type = data.get("export_metadata", {}).get("export_type", "unknown")

            if export_type == "complete":
                # Check for expected keys
                expected_keys = ["configuration", "memories", "conversations",
                               "analytics", "feedback", "profiles", "patterns"]
                for key in expected_keys:
                    if key not in data:
                        result["warnings"].append(f"Missing {key} data")

            # If no errors, mark as valid
            if not result["errors"]:
                result["valid"] = True

        except json.JSONDecodeError as e:
            result["errors"].append(f"Invalid JSON: {str(e)}")
        except yaml.YAMLError as e:
            result["errors"].append(f"Invalid YAML: {str(e)}")
        except Exception as e:
            result["errors"].append(f"Validation error: {str(e)}")

        return result

    # ========== Private Helper Methods ==========

    def _check_version_compatibility(self, version: str) -> bool:
        """Check if version is compatible."""
        try:
            # Major version must match
            import_major = int(version.split(".")[0])
            for compat_version in self.COMPATIBLE_VERSIONS:
                compat_major = int(compat_version.split(".")[0])
                if import_major == compat_major:
                    return True
            return False
        except (ValueError, IndexError, AttributeError):
            # Version parsing failed
            return False

    def _import_configuration_data(self, config: Dict):
        """Import configuration data."""
        # Write to config.yaml
        config_path = Path("config.yaml")
        with open(config_path, 'w') as f:
            yaml.safe_dump(config, f, default_flow_style=False)

    def _import_memories_data(self, memories: List[Dict], merge: bool) -> int:
        """Import memories data."""
        memory_dir = Path("memory")
        memory_dir.mkdir(parents=True, exist_ok=True)

        index_file = memory_dir / "index.json"

        # Load existing memories if merging
        existing_memories = []
        if merge and index_file.exists():
            with open(index_file, 'r') as f:
                memory_index = json.load(f)
                existing_memories = memory_index.get("memories", [])

        # Merge or replace
        if merge:
            # Create ID set for deduplication
            existing_ids = {m.get("id") for m in existing_memories if m.get("id")}
            new_memories = [m for m in memories if m.get("id") not in existing_ids]
            all_memories = existing_memories + new_memories
        else:
            all_memories = memories

        # Write updated index
        memory_index = {
            "memories": all_memories,
            "last_updated": datetime.now().isoformat()
        }
        with open(index_file, 'w') as f:
            json.dump(memory_index, f, indent=2, default=str)

        return len(memories)

    def _import_conversations_data(self, conversations: List[Dict], merge: bool) -> int:
        """Import conversations data."""
        conv_dir = Path("conversations")
        conv_dir.mkdir(parents=True, exist_ok=True)

        if not merge:
            # Clear existing conversations
            for conv_file in conv_dir.glob("*.json"):
                conv_file.unlink()

        # Write conversations
        for i, conv in enumerate(conversations):
            session_id = conv.get("session_id", f"imported_{i}")
            conv_file = conv_dir / f"{session_id}.json"
            with open(conv_file, 'w') as f:
                json.dump(conv, f, indent=2, default=str)

        return len(conversations)

    def _import_analytics_data(self, analytics: Dict, merge: bool) -> int:
        """Import analytics data."""
        analytics_dir = Path("analytics_data")
        analytics_dir.mkdir(parents=True, exist_ok=True)

        metrics_file = analytics_dir / "metrics.json"

        if merge and metrics_file.exists():
            # Load existing and merge
            with open(metrics_file, 'r') as f:
                existing = json.load(f)
            # Simple merge - append new data
            merged = {**existing, **analytics}
        else:
            merged = analytics

        with open(metrics_file, 'w') as f:
            json.dump(merged, f, indent=2, default=str)

        return len(analytics)

    def _import_feedback_data(self, feedback: List[Dict], merge: bool) -> int:
        """Import feedback data."""
        feedback_dir = Path("feedback_data")
        feedback_dir.mkdir(parents=True, exist_ok=True)

        feedback_file = feedback_dir / "feedback.json"

        if merge and feedback_file.exists():
            # Load existing and merge
            with open(feedback_file, 'r') as f:
                existing = json.load(f)
            # Deduplicate by ID
            existing_ids = {f.get("id") for f in existing if f.get("id")}
            new_feedback = [f for f in feedback if f.get("id") not in existing_ids]
            all_feedback = existing + new_feedback
        else:
            all_feedback = feedback

        with open(feedback_file, 'w') as f:
            json.dump(all_feedback, f, indent=2, default=str)

        return len(feedback)

    def _import_profiles_data(self, profiles: List[Dict], overwrite: bool) -> int:
        """Import profiles data."""
        profiles_dir = Path("config/profiles")
        profiles_dir.mkdir(parents=True, exist_ok=True)

        imported_count = 0

        for profile in profiles:
            profile_id = profile.get("id")
            if not profile_id:
                continue

            # Skip built-in profiles unless overwriting
            is_builtin = profile.get("is_builtin", False)
            if is_builtin and not overwrite:
                continue

            profile_file = profiles_dir / f"{profile_id}.yaml"

            # Check if exists
            if profile_file.exists() and not overwrite:
                continue

            # Write profile
            with open(profile_file, 'w') as f:
                yaml.safe_dump(profile, f, default_flow_style=False)

            imported_count += 1

        return imported_count

    def _import_patterns_data(self, patterns: List[Dict], merge: bool) -> int:
        """Import patterns data."""
        patterns_file = Path("feedback_data/patterns.json")
        patterns_file.parent.mkdir(parents=True, exist_ok=True)

        if merge and patterns_file.exists():
            # Load existing and merge
            with open(patterns_file, 'r') as f:
                existing_data = json.load(f)
                existing = existing_data.get("patterns", [])

            # Deduplicate by ID
            existing_ids = {p.get("id") for p in existing if p.get("id")}
            new_patterns = [p for p in patterns if p.get("id") not in existing_ids]
            all_patterns = existing + new_patterns
        else:
            all_patterns = patterns

        # Write patterns
        patterns_data = {
            "patterns": all_patterns,
            "last_updated": datetime.now().isoformat()
        }
        with open(patterns_file, 'w') as f:
            json.dump(patterns_data, f, indent=2, default=str)

        return len(patterns)
