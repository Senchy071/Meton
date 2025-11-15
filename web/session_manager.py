"""
Session Management for Meton Web UI.

Handles multiple concurrent user sessions with:
- Session creation and lifecycle management
- Conversation history persistence
- File uploads per session
- Settings and agent state per session
- Automatic cleanup of expired sessions
"""

import json
import uuid
import shutil
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
import threading


@dataclass
class Session:
    """Single user session."""
    id: str
    created_at: str  # ISO 8601
    last_activity: str  # ISO 8601
    conversation_history: List[Dict] = field(default_factory=list)
    uploaded_files: List[str] = field(default_factory=list)
    settings: Dict = field(default_factory=dict)
    agent_state: Dict = field(default_factory=dict)

    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.now().isoformat()


class SessionManager:
    """Manages multiple concurrent user sessions."""

    def __init__(self, storage_path: str = "./web_sessions"):
        """
        Initialize session manager.

        Args:
            storage_path: Directory for session storage
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # In-memory session cache
        self.sessions: Dict[str, Session] = {}

        # Thread lock for concurrent access
        self.lock = threading.Lock()

        # Load existing sessions
        self._load_all_sessions()

    def create_session(self, initial_settings: Optional[Dict] = None) -> str:
        """
        Create new session.

        Args:
            initial_settings: Optional initial settings

        Returns:
            Session ID
        """
        with self.lock:
            session_id = str(uuid.uuid4())
            now = datetime.now().isoformat()

            session = Session(
                id=session_id,
                created_at=now,
                last_activity=now,
                conversation_history=[],
                uploaded_files=[],
                settings=initial_settings or {},
                agent_state={}
            )

            self.sessions[session_id] = session
            self.save_session(session_id)

            return session_id

    def get_session(self, session_id: str) -> Session:
        """
        Get session by ID.

        Args:
            session_id: Session ID

        Returns:
            Session object

        Raises:
            KeyError: If session not found
        """
        with self.lock:
            if session_id not in self.sessions:
                # Try loading from disk
                try:
                    self._load_session_from_disk(session_id)
                except FileNotFoundError:
                    raise KeyError(f"Session {session_id} not found")

            session = self.sessions[session_id]
            session.update_activity()
            self.save_session(session_id)

            return session

    def update_session(
        self,
        session_id: str,
        **kwargs
    ) -> None:
        """
        Update session fields.

        Args:
            session_id: Session ID
            **kwargs: Fields to update

        Raises:
            KeyError: If session not found
        """
        with self.lock:
            session = self.get_session(session_id)

            # Update allowed fields
            allowed_fields = {
                'conversation_history',
                'uploaded_files',
                'settings',
                'agent_state'
            }

            for key, value in kwargs.items():
                if key in allowed_fields:
                    setattr(session, key, value)

            session.update_activity()
            self.save_session(session_id)

    def delete_session(self, session_id: str) -> bool:
        """
        Delete session.

        Args:
            session_id: Session ID

        Returns:
            True if deleted, False if not found
        """
        with self.lock:
            try:
                # Remove from memory
                if session_id in self.sessions:
                    session = self.sessions[session_id]

                    # Clean up uploaded files
                    for file_path in session.uploaded_files:
                        try:
                            Path(file_path).unlink(missing_ok=True)
                        except Exception:
                            pass

                    del self.sessions[session_id]

                # Remove from disk
                session_file = self.storage_path / f"session_{session_id}.json"
                if session_file.exists():
                    session_file.unlink()

                return True

            except Exception:
                return False

    def list_sessions(self) -> List[Dict]:
        """
        List all sessions.

        Returns:
            List of session summaries
        """
        with self.lock:
            summaries = []

            for session_id, session in self.sessions.items():
                summaries.append({
                    'id': session_id,
                    'created_at': session.created_at,
                    'last_activity': session.last_activity,
                    'message_count': len(session.conversation_history),
                    'file_count': len(session.uploaded_files)
                })

            # Sort by last activity (most recent first)
            summaries.sort(key=lambda x: x['last_activity'], reverse=True)

            return summaries

    def cleanup_expired(self, max_age_hours: int = 24) -> int:
        """
        Remove old inactive sessions.

        Args:
            max_age_hours: Maximum session age in hours

        Returns:
            Number of sessions deleted
        """
        with self.lock:
            cutoff = datetime.now() - timedelta(hours=max_age_hours)
            deleted_count = 0

            # Find expired sessions
            expired_ids = []
            for session_id, session in self.sessions.items():
                last_activity = datetime.fromisoformat(session.last_activity)
                if last_activity < cutoff:
                    expired_ids.append(session_id)

            # Delete expired sessions
            for session_id in expired_ids:
                if self.delete_session(session_id):
                    deleted_count += 1

            return deleted_count

    def save_session(self, session_id: str) -> None:
        """
        Persist session to disk.

        Args:
            session_id: Session ID

        Raises:
            KeyError: If session not found
        """
        if session_id not in self.sessions:
            raise KeyError(f"Session {session_id} not found")

        session = self.sessions[session_id]
        session_file = self.storage_path / f"session_{session_id}.json"

        # Atomic write using temp file
        with tempfile.NamedTemporaryFile(
            mode='w',
            dir=self.storage_path,
            delete=False
        ) as tmp_file:
            json.dump(asdict(session), tmp_file, indent=2)
            tmp_path = tmp_file.name

        # Atomic rename
        shutil.move(tmp_path, session_file)

    def load_session(self, session_id: str) -> Session:
        """
        Load session from disk.

        Args:
            session_id: Session ID

        Returns:
            Session object

        Raises:
            FileNotFoundError: If session file not found
        """
        self._load_session_from_disk(session_id)
        return self.sessions[session_id]

    def _load_session_from_disk(self, session_id: str) -> None:
        """
        Load single session from disk into memory.

        Args:
            session_id: Session ID

        Raises:
            FileNotFoundError: If session file not found
        """
        session_file = self.storage_path / f"session_{session_id}.json"

        if not session_file.exists():
            raise FileNotFoundError(f"Session file not found: {session_file}")

        with open(session_file, 'r') as f:
            data = json.load(f)

        session = Session(**data)
        self.sessions[session_id] = session

    def _load_all_sessions(self) -> None:
        """Load all existing sessions from disk."""
        if not self.storage_path.exists():
            return

        for session_file in self.storage_path.glob("session_*.json"):
            try:
                # Extract session ID from filename
                session_id = session_file.stem.replace("session_", "")
                self._load_session_from_disk(session_id)
            except Exception as e:
                print(f"Warning: Failed to load session {session_file}: {e}")

    def get_session_count(self) -> int:
        """
        Get total number of active sessions.

        Returns:
            Session count
        """
        with self.lock:
            return len(self.sessions)

    def clear_all_sessions(self) -> int:
        """
        Delete all sessions (use with caution).

        Returns:
            Number of sessions deleted
        """
        with self.lock:
            count = len(self.sessions)
            session_ids = list(self.sessions.keys())

            for session_id in session_ids:
                self.delete_session(session_id)

            return count

    def get_session_stats(self) -> Dict[str, Any]:
        """
        Get session statistics.

        Returns:
            Statistics dictionary
        """
        with self.lock:
            if not self.sessions:
                return {
                    'total_sessions': 0,
                    'total_messages': 0,
                    'total_files': 0,
                    'avg_messages_per_session': 0.0,
                    'oldest_session': None,
                    'newest_session': None
                }

            total_messages = sum(
                len(s.conversation_history) for s in self.sessions.values()
            )
            total_files = sum(
                len(s.uploaded_files) for s in self.sessions.values()
            )

            sessions_by_date = sorted(
                self.sessions.values(),
                key=lambda s: s.created_at
            )

            return {
                'total_sessions': len(self.sessions),
                'total_messages': total_messages,
                'total_files': total_files,
                'avg_messages_per_session': total_messages / len(self.sessions),
                'oldest_session': sessions_by_date[0].created_at if sessions_by_date else None,
                'newest_session': sessions_by_date[-1].created_at if sessions_by_date else None
            }
