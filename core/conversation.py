"""Conversation memory management for Meton.

This module provides comprehensive conversation history management with
thread-safe operations, context window management, and persistence.

Example:
    >>> from core.config import Config
    >>> from core.conversation import ConversationManager
    >>>
    >>> config = Config()
    >>> manager = ConversationManager(config)
    >>>
    >>> # Add messages
    >>> manager.add_message("user", "Hello!")
    >>> manager.add_message("assistant", "Hi! How can I help?")
    >>>
    >>> # Get context for LLM
    >>> context = manager.get_context_window()
    >>>
    >>> # Save conversation
    >>> path = manager.save()
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from threading import Lock
from pydantic import BaseModel, Field


# Custom Exceptions
class ConversationError(Exception):
    """Base exception for conversation-related errors."""
    pass


class ConversationLoadError(ConversationError):
    """Failed to load conversation from disk."""
    pass


class ConversationSaveError(ConversationError):
    """Failed to save conversation to disk."""
    pass


class Message(BaseModel):
    """A single message in the conversation.

    Attributes:
        role: Message role ('user', 'assistant', 'system', 'tool')
        content: Message content text
        timestamp: ISO 8601 timestamp
        metadata: Optional metadata dictionary
    """
    role: str
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationManager:
    """Manages conversation history and persistence.

    This class handles all conversation operations including:
    - Thread-safe message storage
    - Context window management
    - Conversation persistence to disk
    - Auto-save functionality
    - Integration with LangChain message format

    Attributes:
        config: Configuration loader instance
        session_id: Unique session identifier (UUID)
        messages: List of conversation messages
        logger: Optional logger instance
    """

    def __init__(self, config, session_id: Optional[str] = None, logger=None):
        """Initialize conversation manager.

        Args:
            config: Configuration loader instance
            session_id: Optional session ID (generates UUID if None)
            logger: Optional logger for operation tracking

        Example:
            >>> config = Config()
            >>> manager = ConversationManager(config)
            >>> print(manager.get_session_id())
        """
        self.config = config
        self.logger = logger
        self._lock = Lock()

        # Generate or use provided session ID
        if session_id is None:
            self.session_id = str(uuid.uuid4())
        else:
            self.session_id = session_id

        # Initialize message list
        self.messages: List[Message] = []

        # Track start time
        self.start_time = datetime.now().isoformat()

        # Get conversation settings from config
        self.max_history = config.get('conversation.max_history', 20)
        self.save_path = Path(config.get('conversation.save_path', './conversations/'))
        self.auto_save = config.get('conversation.auto_save', True)

        # Ensure save directory exists
        self.save_path.mkdir(parents=True, exist_ok=True)

        if self.logger:
            self.logger.info(f"ConversationManager initialized with session: {self.session_id}")

    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a message to conversation history.

        Thread-safe operation that adds a message and optionally auto-saves.

        Args:
            role: Message role ('user', 'assistant', 'system', 'tool')
            content: Message content
            metadata: Optional metadata (tool name, model, timestamps, etc.)

        Example:
            >>> manager.add_message("user", "Read main.py")
            >>> manager.add_message("tool", "File contents...",
            ...                     metadata={"tool_name": "file_ops"})
            >>> manager.add_message("assistant", "The file contains...")
        """
        with self._lock:
            message = Message(
                role=role,
                content=content,
                timestamp=datetime.now().isoformat(),
                metadata=metadata or {}
            )

            self.messages.append(message)

            if self.logger:
                self.logger.debug(f"Added {role} message (total: {len(self.messages)})")

            # Auto-save if enabled - use internal method to avoid deadlock
            if self.auto_save:
                try:
                    self._save_internal()
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"Auto-save failed: {e}")

    def add_user_message(self, content: str) -> None:
        """Add a user message.

        Args:
            content: User message content

        Example:
            >>> manager.add_user_message("Hello, how are you?")
        """
        self.add_message("user", content)

    def add_assistant_message(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add an assistant message.

        Args:
            content: Assistant response content
            metadata: Optional metadata (model, tokens, etc.)

        Example:
            >>> manager.add_assistant_message(
            ...     "I'm doing well!",
            ...     metadata={"model": "codellama:34b", "tokens": 120}
            ... )
        """
        self.add_message("assistant", content, metadata)

    def add_system_message(self, content: str) -> None:
        """Add a system message.

        Args:
            content: System message content

        Example:
            >>> manager.add_system_message("You are a helpful coding assistant")
        """
        self.add_message("system", content)

    def add_tool_message(
        self,
        content: str,
        tool_name: str,
        action: Optional[str] = None
    ) -> None:
        """Add a tool execution message.

        Args:
            content: Tool output content
            tool_name: Name of the tool that was executed
            action: Optional action performed by the tool

        Example:
            >>> manager.add_tool_message(
            ...     "File read successfully",
            ...     tool_name="file_ops",
            ...     action="read"
            ... )
        """
        metadata = {"tool_name": tool_name}
        if action:
            metadata["action"] = action

        self.add_message("tool", content, metadata)

    def get_messages(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get conversation messages.

        Args:
            limit: Maximum number of recent messages (None = all)

        Returns:
            List of message dictionaries

        Example:
            >>> messages = manager.get_messages(limit=5)
            >>> for msg in messages:
            ...     print(f"{msg['role']}: {msg['content']}")
        """
        with self._lock:
            if limit is None:
                messages = self.messages
            else:
                messages = self.messages[-limit:]

            return [msg.model_dump() for msg in messages]

    def get_context_window(self) -> List[Dict[str, str]]:
        """Get messages within context window for LLM.

        Returns messages that fit within the configured max_history limit.
        Preserves system messages and maintains user-assistant pairs.

        Returns:
            List of message dicts in LangChain format (role, content)

        Example:
            >>> context = manager.get_context_window()
            >>> # Use with Model Manager
            >>> response = model_manager.chat(context)
        """
        with self._lock:
            # If no max_history limit, return all messages
            if self.max_history <= 0:
                return [
                    {"role": msg.role, "content": msg.content}
                    for msg in self.messages
                ]

            # Separate system messages from conversation
            system_messages = [msg for msg in self.messages if msg.role == "system"]
            other_messages = [msg for msg in self.messages if msg.role != "system"]

            # Calculate how many non-system messages we can include
            available_slots = self.max_history - len(system_messages)

            if available_slots <= 0:
                # Only system messages fit
                selected_messages = system_messages
            elif len(other_messages) <= available_slots:
                # All messages fit
                selected_messages = self.messages
            else:
                # Need to trim - take most recent messages
                selected_messages = system_messages + other_messages[-available_slots:]

            # Convert to LangChain format
            return [
                {"role": msg.role, "content": msg.content}
                for msg in selected_messages
            ]

    def clear(self) -> None:
        """Clear all messages from current conversation.

        Thread-safe operation that removes all messages.

        Example:
            >>> manager.clear()
            >>> print(manager.get_message_count())  # 0
        """
        with self._lock:
            self.messages = []

            if self.logger:
                self.logger.info("Conversation cleared")

    def _save_internal(self, filepath: Optional[Path] = None) -> Path:
        """Internal save method without lock acquisition.

        Used by auto-save when lock is already held.
        IMPORTANT: This method assumes the lock is already acquired!

        Args:
            filepath: Optional custom save path

        Returns:
            Path where conversation was saved

        Raises:
            ConversationSaveError: If save operation fails
        """
        try:
            if filepath is None:
                # Generate filename with session ID and timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"session_{timestamp}_{self.session_id[:8]}.json"
                filepath = self.save_path / filename

            # Prepare conversation data
            conversation_data = {
                "session_id": self.session_id,
                "start_time": self.start_time,
                "end_time": datetime.now().isoformat(),
                "message_count": len(self.messages),
                "max_history": self.max_history,
                "messages": [msg.model_dump() for msg in self.messages]
            }

            # Save to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, indent=2, ensure_ascii=False)

            if self.logger:
                self.logger.debug(f"Conversation saved to {filepath}")

            return filepath

        except Exception as e:
            raise ConversationSaveError(
                f"Failed to save conversation: {e}"
            ) from e

    def save(self, filepath: Optional[Path] = None) -> Path:
        """Save conversation to disk.

        Saves conversation as JSON file with session metadata.

        Args:
            filepath: Optional custom save path

        Returns:
            Path where conversation was saved

        Raises:
            ConversationSaveError: If save operation fails

        Example:
            >>> path = manager.save()
            >>> print(f"Saved to {path}")
        """
        with self._lock:
            return self._save_internal(filepath)

    def load(self, filepath: Path) -> bool:
        """Load conversation from disk.

        Loads a saved conversation and restores all messages.

        Args:
            filepath: Path to conversation file

        Returns:
            True if successful

        Raises:
            ConversationLoadError: If load operation fails

        Example:
            >>> path = Path("conversations/session_20251028_123456.json")
            >>> manager.load(path)
            >>> print(manager.get_message_count())
        """
        with self._lock:
            try:
                if not filepath.exists():
                    raise ConversationLoadError(
                        f"Conversation file not found: {filepath}"
                    )

                # Load conversation data
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Restore session data
                self.session_id = data.get("session_id", self.session_id)
                self.start_time = data.get("start_time", datetime.now().isoformat())

                # Restore messages
                self.messages = [
                    Message(**msg) for msg in data.get("messages", [])
                ]

                if self.logger:
                    self.logger.info(
                        f"Loaded conversation: {len(self.messages)} messages "
                        f"from {filepath}"
                    )

                return True

            except Exception as e:
                raise ConversationLoadError(
                    f"Failed to load conversation: {e}"
                ) from e

    def get_session_id(self) -> str:
        """Get current session ID.

        Returns:
            Session UUID string

        Example:
            >>> session = manager.get_session_id()
            >>> print(session)  # '550e8400-e29b-41d4-a716-446655440000'
        """
        return self.session_id

    def get_message_count(self) -> int:
        """Get total message count.

        Returns:
            Number of messages in conversation

        Example:
            >>> count = manager.get_message_count()
            >>> print(f"Messages: {count}")
        """
        with self._lock:
            return len(self.messages)

    def get_summary(self) -> Dict[str, Any]:
        """Get conversation summary.

        Returns dictionary with session metadata and statistics.

        Returns:
            Dict with session_id, message_count, start_time, etc.

        Example:
            >>> summary = manager.get_summary()
            >>> print(f"Session: {summary['session_id']}")
            >>> print(f"Messages: {summary['message_count']}")
        """
        with self._lock:
            # Count messages by role
            role_counts = {}
            for msg in self.messages:
                role_counts[msg.role] = role_counts.get(msg.role, 0) + 1

            return {
                "session_id": self.session_id,
                "message_count": len(self.messages),
                "start_time": self.start_time,
                "current_time": datetime.now().isoformat(),
                "role_distribution": role_counts,
                "max_history": self.max_history,
                "auto_save": self.auto_save
            }

    def format_for_display(self) -> str:
        """Format conversation for display in CLI.

        Creates a human-readable representation of the conversation
        with color-coded roles.

        Returns:
            Formatted string with conversation history

        Example:
            >>> formatted = manager.format_for_display()
            >>> print(formatted)
        """
        with self._lock:
            if not self.messages:
                return "[dim]No messages in conversation[/dim]"

            lines = []
            lines.append(f"[bold cyan]Session: {self.session_id[:8]}...[/bold cyan]")
            lines.append(f"[dim]Messages: {len(self.messages)} | Started: {self.start_time[:19]}[/dim]")
            lines.append("")

            for i, msg in enumerate(self.messages, 1):
                # Color by role
                if msg.role == "user":
                    role_display = "[cyan]👤 User[/cyan]"
                elif msg.role == "assistant":
                    role_display = "[green]🧠 Assistant[/green]"
                elif msg.role == "system":
                    role_display = "[blue]⚙️  System[/blue]"
                elif msg.role == "tool":
                    tool_name = msg.metadata.get("tool_name", "unknown")
                    role_display = f"[yellow]🔧 Tool ({tool_name})[/yellow]"
                else:
                    role_display = f"[white]{msg.role}[/white]"

                # Format timestamp
                timestamp = msg.timestamp[:19].replace('T', ' ')

                # Truncate long messages
                content = msg.content
                if len(content) > 200:
                    content = content[:200] + "..."

                lines.append(f"{i}. {role_display} [dim]{timestamp}[/dim]")
                lines.append(f"   {content}")
                lines.append("")

            return "\n".join(lines)

    def list_saved_conversations(self) -> List[Path]:
        """List all saved conversation files.

        Returns:
            List of conversation file paths sorted by modification time

        Example:
            >>> conversations = manager.list_saved_conversations()
            >>> for path in conversations:
            ...     print(path.name)
        """
        return sorted(
            self.save_path.glob("session_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

    def get_langchain_format(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """Get messages in LangChain chat format.

        Args:
            limit: Maximum number of recent messages (None = all)

        Returns:
            List of message dicts with 'role' and 'content' keys

        Example:
            >>> messages = manager.get_langchain_format(limit=5)
            >>> response = model_manager.chat(messages)
        """
        with self._lock:
            if limit is None:
                messages = self.messages
            else:
                messages = self.messages[-limit:]

            return [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]


# Alias for backwards compatibility
ConversationMemory = ConversationManager
