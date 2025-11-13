#!/usr/bin/env python3
"""
Feedback Learning System for Meton.

Learns from user feedback to improve future responses through:
- Recording and categorizing user feedback (positive, negative, corrections)
- Finding relevant past feedback using semantic similarity
- Extracting actionable learning insights from feedback patterns
- Providing context to the agent for improved responses

Example:
    feedback_system = FeedbackLearningSystem()

    # Record feedback
    feedback_id = feedback_system.record_feedback(
        query="Explain async/await",
        response="...",
        feedback_type="negative",
        feedback_text="Missing practical examples"
    )

    # Get relevant feedback for similar queries
    relevant = feedback_system.get_relevant_feedback("How does Python handle concurrency?")

    # Get learning insights
    insights = feedback_system.get_learning_insights("python")
"""

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np
from collections import Counter, defaultdict

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False


@dataclass
class FeedbackRecord:
    """Record of a single feedback event.

    Attributes:
        id: Unique identifier (UUID)
        timestamp: When feedback was recorded (ISO 8601 format)
        query: Original user query
        response: Agent's response that received feedback
        feedback_type: Type of feedback (positive, negative, correction)
        feedback_text: Optional user feedback text
        correction: Optional corrected version from user
        context: Additional context (tools used, reflection scores, etc.)
        tags: Auto-extracted tags for categorization
    """
    id: str
    timestamp: str
    query: str
    response: str
    feedback_type: str  # positive, negative, correction
    feedback_text: Optional[str] = None
    correction: Optional[str] = None
    context: Dict = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "FeedbackRecord":
        """Create FeedbackRecord from dictionary."""
        return cls(**data)


class FeedbackLearningSystem:
    """Learns from user feedback to improve future responses.

    Features:
    - Records feedback (positive, negative, corrections)
    - Uses semantic similarity to find relevant past feedback
    - Extracts actionable insights from feedback patterns
    - Persists feedback to local storage
    - Exports feedback data for analysis

    The system uses sentence embeddings to find similar queries and
    provides context to the agent for improved future responses.
    """

    # Feedback type constants
    POSITIVE = "positive"
    NEGATIVE = "negative"
    CORRECTION = "correction"

    # Tag extraction keywords
    TAG_KEYWORDS = {
        "python": ["python", "py", "async", "await", "decorator", "class", "function"],
        "javascript": ["javascript", "js", "node", "react", "async", "promise"],
        "debugging": ["debug", "error", "bug", "fix", "issue", "problem"],
        "refactoring": ["refactor", "improve", "optimize", "clean", "restructure"],
        "explanation": ["explain", "how", "what", "why", "understand"],
        "examples": ["example", "sample", "demo", "show", "illustrate"],
        "documentation": ["document", "comment", "docstring", "readme"],
        "security": ["security", "vulnerability", "safe", "sanitize", "validate"],
        "performance": ["performance", "slow", "fast", "optimize", "efficient"],
        "testing": ["test", "unittest", "pytest", "coverage", "assert"],
    }

    # Insight patterns (feedback_text keywords → insight)
    INSIGHT_PATTERNS = {
        "missing examples": "Include code examples when explaining concepts",
        "no examples": "Include code examples when explaining concepts",
        "add examples": "Include code examples when explaining concepts",
        "too verbose": "Users prefer concise responses over verbose explanations",
        "too long": "Users prefer concise responses over verbose explanations",
        "be concise": "Users prefer concise responses over verbose explanations",
        "security": "Emphasize security implications in code reviews",
        "vulnerable": "Emphasize security implications in code reviews",
        "sanitize": "Emphasize security implications in code reviews",
        "incomplete": "Ensure responses fully address all parts of the query",
        "missing": "Ensure responses fully address all parts of the query",
        "unclear": "Improve clarity and structure of explanations",
        "confusing": "Improve clarity and structure of explanations",
    }

    def __init__(self, storage_path: str = "./feedback_data"):
        """Initialize feedback learning system.

        Args:
            storage_path: Directory to store feedback data
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True, parents=True)
        self.feedback_db: List[FeedbackRecord] = []
        self.embedding_model = None
        self._embedding_cache: Dict[str, np.ndarray] = {}

        # Initialize embedding model if available
        if EMBEDDINGS_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer(
                    "sentence-transformers/all-mpnet-base-v2"
                )
            except Exception:
                self.embedding_model = None

        self._load_feedback()

    def record_feedback(
        self,
        query: str,
        response: str,
        feedback_type: str,
        feedback_text: Optional[str] = None,
        correction: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> str:
        """Record user feedback.

        Args:
            query: Original user query
            response: Agent's response
            feedback_type: Type of feedback (positive, negative, correction)
            feedback_text: Optional feedback text
            correction: Optional corrected version
            context: Optional context (tools used, scores, etc.)

        Returns:
            Feedback ID (UUID)

        Raises:
            ValueError: If feedback_type is invalid
        """
        # Validate feedback type
        valid_types = [self.POSITIVE, self.NEGATIVE, self.CORRECTION]
        if feedback_type not in valid_types:
            raise ValueError(
                f"Invalid feedback_type: {feedback_type}. "
                f"Must be one of: {valid_types}"
            )

        # Generate UUID
        feedback_id = str(uuid.uuid4())

        # Extract tags
        tags = self._extract_tags(query, response, feedback_text or "")

        # Create feedback record
        record = FeedbackRecord(
            id=feedback_id,
            timestamp=datetime.now().isoformat(),
            query=query,
            response=response,
            feedback_type=feedback_type,
            feedback_text=feedback_text,
            correction=correction,
            context=context or {},
            tags=tags
        )

        # Add to database
        self.feedback_db.append(record)

        # Persist immediately
        self._save_feedback()

        return feedback_id

    def get_relevant_feedback(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[FeedbackRecord]:
        """Find relevant past feedback using semantic similarity.

        Args:
            query: Query to find similar feedback for
            top_k: Maximum number of results
            similarity_threshold: Minimum similarity score (0.0-1.0)

        Returns:
            List of relevant feedback records, sorted by similarity
        """
        if not self.feedback_db:
            return []

        # Calculate similarities
        similarities: List[Tuple[FeedbackRecord, float]] = []

        for record in self.feedback_db:
            similarity = self._calculate_similarity(query, record.query)

            # Filter by threshold
            if similarity >= similarity_threshold:
                similarities.append((record, similarity))

        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Return top-k records
        return [record for record, _ in similarities[:top_k]]

    def get_feedback_summary(self) -> Dict:
        """Get aggregate feedback statistics.

        Returns:
            Dictionary with statistics:
            - total_count: Total feedback records
            - positive_count: Number of positive feedback
            - negative_count: Number of negative feedback
            - correction_count: Number of corrections
            - positive_ratio: Ratio of positive feedback
            - negative_ratio: Ratio of negative feedback
            - correction_ratio: Ratio of corrections
            - common_tags: Most common tags (top 10)
            - recent_count: Feedback in last 7 days
        """
        if not self.feedback_db:
            return {
                "total_count": 0,
                "positive_count": 0,
                "negative_count": 0,
                "correction_count": 0,
                "positive_ratio": 0.0,
                "negative_ratio": 0.0,
                "correction_ratio": 0.0,
                "common_tags": [],
                "recent_count": 0
            }

        # Count by type
        type_counts = Counter(r.feedback_type for r in self.feedback_db)
        total = len(self.feedback_db)

        positive_count = type_counts.get(self.POSITIVE, 0)
        negative_count = type_counts.get(self.NEGATIVE, 0)
        correction_count = type_counts.get(self.CORRECTION, 0)

        # Calculate ratios
        positive_ratio = positive_count / total if total > 0 else 0.0
        negative_ratio = negative_count / total if total > 0 else 0.0
        correction_ratio = correction_count / total if total > 0 else 0.0

        # Get common tags
        all_tags = []
        for record in self.feedback_db:
            all_tags.extend(record.tags)

        tag_counts = Counter(all_tags)
        common_tags = [tag for tag, _ in tag_counts.most_common(10)]

        # Count recent feedback (last 7 days)
        now = datetime.now()
        recent_count = 0
        for record in self.feedback_db:
            try:
                record_time = datetime.fromisoformat(record.timestamp)
                days_ago = (now - record_time).days
                if days_ago <= 7:
                    recent_count += 1
            except (ValueError, AttributeError):
                pass

        return {
            "total_count": total,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "correction_count": correction_count,
            "positive_ratio": positive_ratio,
            "negative_ratio": negative_ratio,
            "correction_ratio": correction_ratio,
            "common_tags": common_tags,
            "recent_count": recent_count
        }

    def get_learning_insights(
        self,
        query_type: Optional[str] = None,
        min_occurrences: int = 3
    ) -> List[str]:
        """Extract actionable insights from feedback patterns.

        Analyzes feedback text and tags to identify common patterns
        and generate actionable insights for improving responses.

        Args:
            query_type: Optional filter by tag (e.g., "python", "debugging")
            min_occurrences: Minimum pattern occurrences to generate insight

        Returns:
            List of insight strings
        """
        # Filter feedback
        feedback_to_analyze = self.feedback_db

        if query_type:
            feedback_to_analyze = [
                r for r in self.feedback_db
                if query_type.lower() in [t.lower() for t in r.tags]
            ]

        if not feedback_to_analyze:
            return []

        # Count pattern occurrences
        pattern_counts: Dict[str, int] = defaultdict(int)

        for record in feedback_to_analyze:
            # Only analyze negative and correction feedback
            if record.feedback_type in [self.NEGATIVE, self.CORRECTION]:
                text = (record.feedback_text or "").lower()

                # Check each pattern
                for pattern, insight in self.INSIGHT_PATTERNS.items():
                    if pattern in text:
                        pattern_counts[insight] += 1

        # Filter by minimum occurrences
        insights = [
            insight for insight, count in pattern_counts.items()
            if count >= min_occurrences
        ]

        # Sort by frequency (most common first)
        insights.sort(
            key=lambda x: pattern_counts[x],
            reverse=True
        )

        return insights

    def _extract_tags(
        self,
        query: str,
        response: str,
        feedback_text: str
    ) -> List[str]:
        """Auto-extract tags for categorization.

        Args:
            query: User query
            response: Agent response
            feedback_text: Feedback text

        Returns:
            List of extracted tags
        """
        tags = set()

        # Combine all text for analysis
        combined_text = f"{query} {response} {feedback_text}".lower()

        # Special handling for language tags - require explicit language name
        if any(word in combined_text for word in ["python", "py"]):
            tags.add("python")
        if any(word in combined_text for word in ["javascript", " js ", "node"]):
            tags.add("javascript")

        # Check for other tag keywords (non-language tags)
        non_language_tags = {
            k: v for k, v in self.TAG_KEYWORDS.items()
            if k not in ["python", "javascript"]
        }

        for tag, keywords in non_language_tags.items():
            for keyword in keywords:
                if keyword in combined_text:
                    tags.add(tag)
                    break  # Tag found, move to next tag

        return sorted(list(tags))

    def _calculate_similarity(self, query1: str, query2: str) -> float:
        """Calculate semantic similarity between queries.

        Uses sentence embeddings if available, otherwise falls back
        to simple word overlap.

        Args:
            query1: First query
            query2: Second query

        Returns:
            Similarity score (0.0-1.0)
        """
        # Use embeddings if available
        if self.embedding_model is not None:
            return self._calculate_embedding_similarity(query1, query2)

        # Fallback to word overlap
        return self._calculate_word_overlap(query1, query2)

    def _calculate_embedding_similarity(
        self,
        query1: str,
        query2: str
    ) -> float:
        """Calculate cosine similarity using embeddings.

        Args:
            query1: First query
            query2: Second query

        Returns:
            Cosine similarity (0.0-1.0)
        """
        # Get or compute embeddings
        emb1 = self._get_embedding(query1)
        emb2 = self._get_embedding(query2)

        # Calculate cosine similarity
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)

        # Clamp to [0.0, 1.0]
        return max(0.0, min(1.0, float(similarity)))

    def _get_embedding(self, text: str) -> np.ndarray:
        """Get or compute embedding for text.

        Uses cache to avoid recomputing embeddings.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        # Check cache
        if text in self._embedding_cache:
            return self._embedding_cache[text]

        # Compute embedding
        embedding = self.embedding_model.encode(text)

        # Cache it
        self._embedding_cache[text] = embedding

        return embedding

    def _calculate_word_overlap(self, query1: str, query2: str) -> float:
        """Calculate similarity using word overlap (fallback).

        Args:
            query1: First query
            query2: Second query

        Returns:
            Jaccard similarity (0.0-1.0)
        """
        # Tokenize and lowercase
        words1 = set(query1.lower().split())
        words2 = set(query2.lower().split())

        if not words1 or not words2:
            return 0.0

        # Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)

        if union == 0:
            return 0.0

        return intersection / union

    def _load_feedback(self) -> None:
        """Load feedback from storage.

        Loads from feedback_db.json in storage_path.
        Creates empty database if file doesn't exist.
        """
        db_path = self.storage_path / "feedback_db.json"

        if not db_path.exists():
            self.feedback_db = []
            return

        try:
            with open(db_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Convert dicts to FeedbackRecord objects
            self.feedback_db = [
                FeedbackRecord.from_dict(record)
                for record in data
            ]
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            # Corrupt file, start fresh
            print(f"Warning: Failed to load feedback database: {e}")
            self.feedback_db = []

    def _save_feedback(self) -> None:
        """Persist feedback to storage.

        Uses atomic write (temp file + rename) to prevent corruption.
        Saves to feedback_db.json in storage_path.
        """
        db_path = self.storage_path / "feedback_db.json"
        temp_path = self.storage_path / "feedback_db.json.tmp"

        try:
            # Convert records to dicts
            data = [record.to_dict() for record in self.feedback_db]

            # Write to temp file
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Atomic rename
            temp_path.replace(db_path)
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise RuntimeError(f"Failed to save feedback database: {e}")

    def export_feedback(
        self,
        format: str = "json",
        output_path: Optional[str] = None
    ) -> str:
        """Export all feedback data.

        Args:
            format: Export format ("json" or "csv")
            output_path: Optional custom output path

        Returns:
            Path to exported file

        Raises:
            ValueError: If format is invalid
        """
        if format not in ["json", "csv"]:
            raise ValueError(f"Invalid format: {format}. Must be 'json' or 'csv'")

        # Determine output path
        if output_path:
            export_path = Path(output_path)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"feedback_export_{timestamp}.{format}"
            export_path = self.storage_path / filename

        if format == "json":
            self._export_json(export_path)
        else:  # csv
            self._export_csv(export_path)

        return str(export_path)

    def _export_json(self, path: Path) -> None:
        """Export to JSON format.

        Args:
            path: Output file path
        """
        data = [record.to_dict() for record in self.feedback_db]

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _export_csv(self, path: Path) -> None:
        """Export to CSV format.

        Args:
            path: Output file path
        """
        import csv

        if not self.feedback_db:
            # Create empty file with headers
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "id", "timestamp", "query", "response",
                    "feedback_type", "feedback_text", "correction",
                    "context", "tags"
                ])
            return

        # Write data
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                "id", "timestamp", "query", "response",
                "feedback_type", "feedback_text", "correction",
                "context", "tags"
            ])

            # Rows
            for record in self.feedback_db:
                writer.writerow([
                    record.id,
                    record.timestamp,
                    record.query,
                    record.response,
                    record.feedback_type,
                    record.feedback_text or "",
                    record.correction or "",
                    json.dumps(record.context),
                    ", ".join(record.tags)
                ])

    def clear_feedback(self) -> int:
        """Clear all feedback data.

        Returns:
            Number of records cleared
        """
        count = len(self.feedback_db)
        self.feedback_db = []
        self._embedding_cache.clear()
        self._save_feedback()
        return count

    def get_feedback_by_id(self, feedback_id: str) -> Optional[FeedbackRecord]:
        """Get feedback record by ID.

        Args:
            feedback_id: Feedback UUID

        Returns:
            FeedbackRecord if found, None otherwise
        """
        for record in self.feedback_db:
            if record.id == feedback_id:
                return record
        return None

    def get_feedback_by_type(self, feedback_type: str) -> List[FeedbackRecord]:
        """Get all feedback of a specific type.

        Args:
            feedback_type: Type to filter by (positive, negative, correction)

        Returns:
            List of matching feedback records
        """
        return [
            record for record in self.feedback_db
            if record.feedback_type == feedback_type
        ]

    def get_feedback_by_tag(self, tag: str) -> List[FeedbackRecord]:
        """Get all feedback with a specific tag.

        Args:
            tag: Tag to filter by

        Returns:
            List of matching feedback records
        """
        tag_lower = tag.lower()
        return [
            record for record in self.feedback_db
            if tag_lower in [t.lower() for t in record.tags]
        ]
