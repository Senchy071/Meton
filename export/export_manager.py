#!/usr/bin/env python3
"""
Export Manager for Meton

Handles exporting all types of Meton data including configurations,
memories, conversations, analytics, feedback, profiles, and patterns.
Supports multiple formats and compression options.
"""

import os
import json
import yaml
import tarfile
import zipfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging


class ExportManager:
    """Exports Meton data and configurations."""

    METON_VERSION = "1.0.0"
    EXPORT_FORMAT_VERSION = "1.0.0"

    SUPPORTED_COMPRESSIONS = ["gzip", "zip", "none"]

    def __init__(
        self,
        export_dir: str = "./exports",
        backup_dir: str = "./backups",
        compression: str = "gzip"
    ):
        """Initialize export manager.

        Args:
            export_dir: Directory for exports
            backup_dir: Directory for backups
            compression: Compression format (gzip, zip, none)
        """
        self.export_dir = Path(export_dir)
        self.backup_dir = Path(backup_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        if compression not in self.SUPPORTED_COMPRESSIONS:
            raise ValueError(f"Unsupported compression: {compression}")
        self.compression = compression

        self.logger = logging.getLogger(__name__)

    def export_all(
        self,
        output_file: Optional[str] = None,
        include_conversations: bool = True,
        include_analytics: bool = True
    ) -> str:
        """Export complete Meton state.

        Args:
            output_file: Output file path (auto-generated if None)
            include_conversations: Include conversation history
            include_analytics: Include analytics data

        Returns:
            Path to export file
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.export_dir / f"meton_complete_{timestamp}.json"
        else:
            output_file = Path(output_file)

        # Gather all data
        export_data = {
            "export_metadata": {
                "version": self.EXPORT_FORMAT_VERSION,
                "meton_version": self.METON_VERSION,
                "export_date": datetime.now().isoformat(),
                "export_type": "complete"
            }
        }

        # Export configuration
        try:
            config_path = Path("config.yaml")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    export_data["configuration"] = yaml.safe_load(f)
        except Exception as e:
            self.logger.warning(f"Could not export configuration: {e}")
            export_data["configuration"] = {}

        # Export memories
        try:
            export_data["memories"] = self._export_memories_data()
        except Exception as e:
            self.logger.warning(f"Could not export memories: {e}")
            export_data["memories"] = []

        # Export conversations
        if include_conversations:
            try:
                export_data["conversations"] = self._export_conversations_data()
            except Exception as e:
                self.logger.warning(f"Could not export conversations: {e}")
                export_data["conversations"] = []

        # Export analytics
        if include_analytics:
            try:
                export_data["analytics"] = self._export_analytics_data()
            except Exception as e:
                self.logger.warning(f"Could not export analytics: {e}")
                export_data["analytics"] = {}

        # Export feedback
        try:
            export_data["feedback"] = self._export_feedback_data()
        except Exception as e:
            self.logger.warning(f"Could not export feedback: {e}")
            export_data["feedback"] = []

        # Export profiles
        try:
            export_data["profiles"] = self._export_profiles_data()
        except Exception as e:
            self.logger.warning(f"Could not export profiles: {e}")
            export_data["profiles"] = []

        # Export patterns
        try:
            export_data["patterns"] = self._export_patterns_data()
        except Exception as e:
            self.logger.warning(f"Could not export patterns: {e}")
            export_data["patterns"] = []

        # Write to file
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)

        self.logger.info(f"Complete export saved to {output_file}")
        return str(output_file)

    def export_configuration(self, output_file: Optional[str] = None) -> str:
        """Export current configuration.

        Args:
            output_file: Output file path (auto-generated if None)

        Returns:
            Path to export file
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.export_dir / f"config_{timestamp}.yaml"
        else:
            output_file = Path(output_file)

        config_path = Path("config.yaml")
        if config_path.exists():
            shutil.copy2(config_path, output_file)
        else:
            # Create minimal config
            minimal_config = {"project": {"name": "Meton", "version": self.METON_VERSION}}
            with open(output_file, 'w') as f:
                yaml.safe_dump(minimal_config, f)

        self.logger.info(f"Configuration exported to {output_file}")
        return str(output_file)

    def export_memories(
        self,
        output_file: Optional[str] = None,
        filter_by: Optional[Dict] = None
    ) -> str:
        """Export long-term memories.

        Args:
            output_file: Output file path (auto-generated if None)
            filter_by: Optional filters (type, importance, date_range)

        Returns:
            Path to export file
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.export_dir / f"memories_{timestamp}.json"
        else:
            output_file = Path(output_file)

        memories_data = self._export_memories_data(filter_by)

        export_data = {
            "export_metadata": {
                "version": self.EXPORT_FORMAT_VERSION,
                "export_date": datetime.now().isoformat(),
                "export_type": "memories",
                "filter_applied": filter_by or {}
            },
            "memories": memories_data
        }

        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)

        self.logger.info(f"Exported {len(memories_data)} memories to {output_file}")
        return str(output_file)

    def export_conversations(
        self,
        output_file: Optional[str] = None,
        session_ids: Optional[List[str]] = None,
        format: str = "json"
    ) -> str:
        """Export conversation history.

        Args:
            output_file: Output file path (auto-generated if None)
            session_ids: Optional list of session IDs to export
            format: Output format (json or markdown)

        Returns:
            Path to export file
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ext = "md" if format == "markdown" else "json"
            output_file = self.export_dir / f"conversations_{timestamp}.{ext}"
        else:
            output_file = Path(output_file)

        conversations_data = self._export_conversations_data(session_ids)

        if format == "markdown":
            self._write_conversations_markdown(conversations_data, output_file)
        else:
            export_data = {
                "export_metadata": {
                    "version": self.EXPORT_FORMAT_VERSION,
                    "export_date": datetime.now().isoformat(),
                    "export_type": "conversations"
                },
                "conversations": conversations_data
            }
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)

        self.logger.info(f"Exported {len(conversations_data)} conversations to {output_file}")
        return str(output_file)

    def export_analytics(
        self,
        output_file: Optional[str] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        format: str = "json"
    ) -> str:
        """Export performance analytics.

        Args:
            output_file: Output file path (auto-generated if None)
            date_range: Optional (start_date, end_date) tuple
            format: Output format (json or csv)

        Returns:
            Path to export file
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ext = "csv" if format == "csv" else "json"
            output_file = self.export_dir / f"analytics_{timestamp}.{ext}"
        else:
            output_file = Path(output_file)

        analytics_data = self._export_analytics_data(date_range)

        if format == "csv":
            self._write_analytics_csv(analytics_data, output_file)
        else:
            export_data = {
                "export_metadata": {
                    "version": self.EXPORT_FORMAT_VERSION,
                    "export_date": datetime.now().isoformat(),
                    "export_type": "analytics",
                    "date_range": [str(d) for d in date_range] if date_range else None
                },
                "analytics": analytics_data
            }
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)

        self.logger.info(f"Analytics exported to {output_file}")
        return str(output_file)

    def export_feedback(self, output_file: Optional[str] = None) -> str:
        """Export feedback data.

        Args:
            output_file: Output file path (auto-generated if None)

        Returns:
            Path to export file
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.export_dir / f"feedback_{timestamp}.json"
        else:
            output_file = Path(output_file)

        feedback_data = self._export_feedback_data()

        export_data = {
            "export_metadata": {
                "version": self.EXPORT_FORMAT_VERSION,
                "export_date": datetime.now().isoformat(),
                "export_type": "feedback"
            },
            "feedback": feedback_data
        }

        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)

        self.logger.info(f"Exported {len(feedback_data)} feedback records to {output_file}")
        return str(output_file)

    def export_profiles(
        self,
        output_file: Optional[str] = None,
        profile_ids: Optional[List[str]] = None
    ) -> str:
        """Export configuration profiles.

        Args:
            output_file: Output file path (auto-generated if None)
            profile_ids: Optional list of profile IDs to export

        Returns:
            Path to export file
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.export_dir / f"profiles_{timestamp}.json"
        else:
            output_file = Path(output_file)

        profiles_data = self._export_profiles_data(profile_ids)

        export_data = {
            "export_metadata": {
                "version": self.EXPORT_FORMAT_VERSION,
                "export_date": datetime.now().isoformat(),
                "export_type": "profiles"
            },
            "profiles": profiles_data
        }

        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)

        self.logger.info(f"Exported {len(profiles_data)} profiles to {output_file}")
        return str(output_file)

    def export_patterns(self, output_file: Optional[str] = None) -> str:
        """Export learned patterns and insights.

        Args:
            output_file: Output file path (auto-generated if None)

        Returns:
            Path to export file
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.export_dir / f"patterns_{timestamp}.json"
        else:
            output_file = Path(output_file)

        patterns_data = self._export_patterns_data()

        export_data = {
            "export_metadata": {
                "version": self.EXPORT_FORMAT_VERSION,
                "export_date": datetime.now().isoformat(),
                "export_type": "patterns"
            },
            "patterns": patterns_data
        }

        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)

        self.logger.info(f"Exported {len(patterns_data)} patterns to {output_file}")
        return str(output_file)

    def create_backup(
        self,
        backup_name: Optional[str] = None,
        include_conversations: bool = True,
        include_analytics: bool = True
    ) -> str:
        """Create complete backup archive.

        Args:
            backup_name: Backup name (auto-generated if None)
            include_conversations: Include conversation history
            include_analytics: Include analytics data

        Returns:
            Path to backup file
        """
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"meton_backup_{timestamp}"

        # Create temporary directory for backup contents
        import tempfile
        temp_dir = Path(tempfile.mkdtemp())

        try:
            # Export metadata
            metadata = {
                "backup_name": backup_name,
                "backup_date": datetime.now().isoformat(),
                "meton_version": self.METON_VERSION,
                "format_version": self.EXPORT_FORMAT_VERSION
            }
            with open(temp_dir / "metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)

            # Export configuration
            config_path = Path("config.yaml")
            if config_path.exists():
                shutil.copy2(config_path, temp_dir / "config.yaml")

            # Export memories
            memories_data = self._export_memories_data()
            with open(temp_dir / "memories.json", 'w') as f:
                json.dump(memories_data, f, indent=2, default=str)

            # Export conversations
            if include_conversations:
                conv_dir = temp_dir / "conversations"
                conv_dir.mkdir()
                conversations_data = self._export_conversations_data()
                for i, conv in enumerate(conversations_data):
                    with open(conv_dir / f"session_{i+1}.json", 'w') as f:
                        json.dump(conv, f, indent=2, default=str)

            # Export analytics
            if include_analytics:
                analytics_data = self._export_analytics_data()
                with open(temp_dir / "analytics.json", 'w') as f:
                    json.dump(analytics_data, f, indent=2, default=str)

            # Export feedback
            feedback_data = self._export_feedback_data()
            with open(temp_dir / "feedback.json", 'w') as f:
                json.dump(feedback_data, f, indent=2, default=str)

            # Export profiles
            profiles_dir = temp_dir / "profiles"
            profiles_dir.mkdir()
            profiles_data = self._export_profiles_data()
            for profile in profiles_data:
                profile_file = profiles_dir / f"{profile.get('id', 'unknown')}.yaml"
                with open(profile_file, 'w') as f:
                    yaml.safe_dump(profile, f)

            # Export patterns
            patterns_data = self._export_patterns_data()
            with open(temp_dir / "patterns.json", 'w') as f:
                json.dump(patterns_data, f, indent=2, default=str)

            # Create archive
            if self.compression == "gzip":
                backup_file = self.backup_dir / f"{backup_name}.tar.gz"
                with tarfile.open(backup_file, "w:gz") as tar:
                    tar.add(temp_dir, arcname=backup_name)
            elif self.compression == "zip":
                backup_file = self.backup_dir / f"{backup_name}.zip"
                with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = Path(root) / file
                            arcname = Path(backup_name) / file_path.relative_to(temp_dir)
                            zipf.write(file_path, arcname)
            else:  # none
                backup_file = self.backup_dir / backup_name
                shutil.copytree(temp_dir, backup_file)

            self.logger.info(f"Backup created: {backup_file}")
            return str(backup_file)

        finally:
            # Clean up temp directory
            shutil.rmtree(temp_dir)

    # ========== Private Helper Methods ==========

    def _export_memories_data(self, filter_by: Optional[Dict] = None) -> List[Dict]:
        """Export memories from long-term memory system."""
        memories = []

        try:
            memory_dir = Path("memory")
            if memory_dir.exists():
                # Load memory index
                index_file = memory_dir / "index.json"
                if index_file.exists():
                    with open(index_file, 'r') as f:
                        memory_index = json.load(f)
                        memories = memory_index.get("memories", [])

                    # Apply filters if provided
                    if filter_by:
                        memories = self._filter_memories(memories, filter_by)
        except Exception as e:
            self.logger.warning(f"Error exporting memories: {e}")

        return memories

    def _filter_memories(self, memories: List[Dict], filter_by: Dict) -> List[Dict]:
        """Apply filters to memory list."""
        filtered = memories

        # Filter by type
        if "type" in filter_by:
            filtered = [m for m in filtered if m.get("type") == filter_by["type"]]

        # Filter by importance
        if "min_importance" in filter_by:
            min_imp = filter_by["min_importance"]
            filtered = [m for m in filtered if m.get("importance", 0) >= min_imp]

        # Filter by date range
        if "date_range" in filter_by:
            start, end = filter_by["date_range"]
            filtered = [
                m for m in filtered
                if start <= datetime.fromisoformat(m.get("created_at", "1970-01-01")) <= end
            ]

        return filtered

    def _export_conversations_data(
        self,
        session_ids: Optional[List[str]] = None
    ) -> List[Dict]:
        """Export conversation history."""
        conversations = []

        try:
            conv_dir = Path("conversations")
            if conv_dir.exists():
                conv_files = list(conv_dir.glob("*.json"))

                for conv_file in conv_files:
                    # Check session ID filter
                    if session_ids and conv_file.stem not in session_ids:
                        continue

                    with open(conv_file, 'r') as f:
                        conversations.append(json.load(f))
        except Exception as e:
            self.logger.warning(f"Error exporting conversations: {e}")

        return conversations

    def _export_analytics_data(
        self,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict:
        """Export analytics data."""
        analytics = {}

        try:
            analytics_dir = Path("analytics_data")
            if analytics_dir.exists():
                # Load metrics
                metrics_file = analytics_dir / "metrics.json"
                if metrics_file.exists():
                    with open(metrics_file, 'r') as f:
                        analytics = json.load(f)

                    # Apply date range filter if provided
                    if date_range:
                        analytics = self._filter_analytics(analytics, date_range)
        except Exception as e:
            self.logger.warning(f"Error exporting analytics: {e}")

        return analytics

    def _filter_analytics(self, analytics: Dict, date_range: Tuple) -> Dict:
        """Filter analytics by date range."""
        # Implement date range filtering for analytics
        # This is a simplified version - actual implementation depends on analytics structure
        return analytics

    def _export_feedback_data(self) -> List[Dict]:
        """Export feedback data."""
        feedback = []

        try:
            feedback_dir = Path("feedback_data")
            if feedback_dir.exists():
                feedback_file = feedback_dir / "feedback.json"
                if feedback_file.exists():
                    with open(feedback_file, 'r') as f:
                        feedback = json.load(f)
        except Exception as e:
            self.logger.warning(f"Error exporting feedback: {e}")

        return feedback

    def _export_profiles_data(
        self,
        profile_ids: Optional[List[str]] = None
    ) -> List[Dict]:
        """Export configuration profiles."""
        profiles = []

        try:
            profiles_dir = Path("config/profiles")
            if profiles_dir.exists():
                profile_files = list(profiles_dir.glob("*.yaml"))

                for profile_file in profile_files:
                    # Check profile ID filter
                    if profile_ids and profile_file.stem not in profile_ids:
                        continue

                    with open(profile_file, 'r') as f:
                        profiles.append(yaml.safe_load(f))
        except Exception as e:
            self.logger.warning(f"Error exporting profiles: {e}")

        return profiles

    def _export_patterns_data(self) -> List[Dict]:
        """Export learned patterns and insights."""
        patterns = []

        try:
            patterns_file = Path("feedback_data/patterns.json")
            if patterns_file.exists():
                with open(patterns_file, 'r') as f:
                    data = json.load(f)
                    patterns = data.get("patterns", [])
        except Exception as e:
            self.logger.warning(f"Error exporting patterns: {e}")

        return patterns

    def _write_conversations_markdown(
        self,
        conversations: List[Dict],
        output_file: Path
    ):
        """Write conversations to markdown format."""
        with open(output_file, 'w') as f:
            f.write("# Meton Conversations Export\n\n")
            f.write(f"**Exported:** {datetime.now().isoformat()}\n\n")
            f.write("---\n\n")

            for i, conv in enumerate(conversations, 1):
                f.write(f"## Conversation {i}\n\n")
                f.write(f"**Session ID:** {conv.get('session_id', 'Unknown')}\n")
                f.write(f"**Date:** {conv.get('created_at', 'Unknown')}\n\n")

                messages = conv.get('messages', [])
                for msg in messages:
                    role = msg.get('role', 'unknown').capitalize()
                    content = msg.get('content', '')
                    f.write(f"### {role}\n\n")
                    f.write(f"{content}\n\n")

                f.write("---\n\n")

    def _write_analytics_csv(self, analytics: Dict, output_file: Path):
        """Write analytics to CSV format."""
        import csv

        with open(output_file, 'w', newline='') as f:
            # This is a simplified version - actual implementation depends on analytics structure
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])

            for key, value in analytics.items():
                if isinstance(value, (str, int, float)):
                    writer.writerow([key, value])
