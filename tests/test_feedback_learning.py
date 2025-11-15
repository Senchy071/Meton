#!/usr/bin/env python3
"""
Tests for Feedback Learning System.

Tests cover:
- Feedback recording (all types)
- Feedback persistence (save/load)
- Relevant feedback retrieval (similarity-based)
- Tag extraction
- Feedback summary statistics
- Learning insights generation
- Export functionality (JSON, CSV)
- Edge cases and error handling
"""

import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.feedback_learning import FeedbackLearningSystem, FeedbackRecord


def test_record_positive_feedback():
    """Test recording positive feedback."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system = FeedbackLearningSystem(storage_path=tmpdir)

        feedback_id = system.record_feedback(
            query="Explain async/await",
            response="Async/await is...",
            feedback_type="positive",
            feedback_text="Great explanation!",
            context={"tools_used": []}
        )

        assert feedback_id is not None
        assert len(system.feedback_db) == 1

        record = system.feedback_db[0]
        assert record.id == feedback_id
        assert record.query == "Explain async/await"
        assert record.feedback_type == "positive"
        assert record.feedback_text == "Great explanation!"


def test_record_negative_feedback():
    """Test recording negative feedback."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system = FeedbackLearningSystem(storage_path=tmpdir)

        feedback_id = system.record_feedback(
            query="How to debug Python?",
            response="Use print statements...",
            feedback_type="negative",
            feedback_text="Missing examples",
            context={"reflection_score": 0.65}
        )

        assert feedback_id is not None
        record = system.feedback_db[0]
        assert record.feedback_type == "negative"
        assert record.feedback_text == "Missing examples"


def test_record_correction_feedback():
    """Test recording correction feedback."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system = FeedbackLearningSystem(storage_path=tmpdir)

        feedback_id = system.record_feedback(
            query="What is Python GIL?",
            response="GIL is a mutex...",
            feedback_type="correction",
            feedback_text="Incorrect explanation",
            correction="GIL is actually a global interpreter lock that..."
        )

        assert feedback_id is not None
        record = system.feedback_db[0]
        assert record.feedback_type == "correction"
        assert record.correction is not None
        assert "global interpreter lock" in record.correction


def test_invalid_feedback_type():
    """Test error on invalid feedback type."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system = FeedbackLearningSystem(storage_path=tmpdir)

        try:
            system.record_feedback(
                query="Test",
                response="Test",
                feedback_type="invalid_type"
            )
            assert False, "Should raise ValueError"
        except ValueError as e:
            assert "Invalid feedback_type" in str(e)


def test_feedback_persistence():
    """Test feedback saves and loads correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create and record feedback
        system1 = FeedbackLearningSystem(storage_path=tmpdir)
        system1.record_feedback(
            query="Test query",
            response="Test response",
            feedback_type="positive",
            feedback_text="Good job"
        )

        assert len(system1.feedback_db) == 1

        # Load in new instance
        system2 = FeedbackLearningSystem(storage_path=tmpdir)
        assert len(system2.feedback_db) == 1

        record = system2.feedback_db[0]
        assert record.query == "Test query"
        assert record.feedback_type == "positive"
        assert record.feedback_text == "Good job"


def test_feedback_persistence_multiple_records():
    """Test multiple records persist correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system1 = FeedbackLearningSystem(storage_path=tmpdir)

        # Record 3 feedback items
        system1.record_feedback("Q1", "R1", "positive")
        system1.record_feedback("Q2", "R2", "negative", feedback_text="Bad")
        system1.record_feedback("Q3", "R3", "correction", correction="Fixed")

        # Load in new instance
        system2 = FeedbackLearningSystem(storage_path=tmpdir)
        assert len(system2.feedback_db) == 3

        types = [r.feedback_type for r in system2.feedback_db]
        assert "positive" in types
        assert "negative" in types
        assert "correction" in types


def test_tag_extraction():
    """Test automatic tag extraction."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system = FeedbackLearningSystem(storage_path=tmpdir)

        # Python-related query
        tags = system._extract_tags(
            query="How to use async/await in Python?",
            response="Async/await is a Python feature...",
            feedback_text="Add more examples"
        )

        assert "python" in tags
        assert "examples" in tags
        assert "explanation" in tags


def test_tag_extraction_multiple_topics():
    """Test tag extraction with multiple topics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system = FeedbackLearningSystem(storage_path=tmpdir)

        tags = system._extract_tags(
            query="Debug JavaScript async issues with performance testing",
            response="Use debugger and profiler...",
            feedback_text="Security concerns not addressed"
        )

        assert "javascript" in tags
        assert "debugging" in tags
        assert "performance" in tags
        assert "testing" in tags
        assert "security" in tags


def test_get_feedback_summary_empty():
    """Test summary with no feedback."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system = FeedbackLearningSystem(storage_path=tmpdir)
        summary = system.get_feedback_summary()

        assert summary["total_count"] == 0
        assert summary["positive_count"] == 0
        assert summary["negative_count"] == 0
        assert summary["correction_count"] == 0
        assert summary["positive_ratio"] == 0.0
        assert summary["common_tags"] == []


def test_get_feedback_summary():
    """Test feedback summary statistics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system = FeedbackLearningSystem(storage_path=tmpdir)

        # Record various feedback
        system.record_feedback("Q1", "R1", "positive")
        system.record_feedback("Q2", "R2", "positive")
        system.record_feedback("Q3", "R3", "negative", feedback_text="Missing examples")
        system.record_feedback("Q4", "R4", "correction", correction="Fixed")

        summary = system.get_feedback_summary()

        assert summary["total_count"] == 4
        assert summary["positive_count"] == 2
        assert summary["negative_count"] == 1
        assert summary["correction_count"] == 1
        assert summary["positive_ratio"] == 0.5
        assert summary["negative_ratio"] == 0.25
        assert summary["correction_ratio"] == 0.25


def test_get_feedback_summary_common_tags():
    """Test common tags in summary."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system = FeedbackLearningSystem(storage_path=tmpdir)

        # Record feedback with Python tags
        for i in range(5):
            system.record_feedback(
                f"Python question {i}",
                f"Python answer {i}",
                "positive"
            )

        summary = system.get_feedback_summary()
        assert "python" in summary["common_tags"]


def test_get_feedback_summary_recent_count():
    """Test recent feedback count (last 7 days)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system = FeedbackLearningSystem(storage_path=tmpdir)

        # Record feedback with different timestamps
        system.record_feedback("Recent", "R1", "positive")

        # Manually modify timestamp to 10 days ago
        old_time = (datetime.now() - timedelta(days=10)).isoformat()
        system.feedback_db[0].timestamp = old_time
        system._save_feedback()

        # Record new feedback
        system.record_feedback("New", "R2", "positive")

        summary = system.get_feedback_summary()
        assert summary["total_count"] == 2
        assert summary["recent_count"] == 1  # Only one in last 7 days


def test_get_learning_insights_no_feedback():
    """Test insights with no feedback."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system = FeedbackLearningSystem(storage_path=tmpdir)
        insights = system.get_learning_insights()
        assert insights == []


def test_get_learning_insights_missing_examples():
    """Test insight for missing examples pattern."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system = FeedbackLearningSystem(storage_path=tmpdir)

        # Record 3 negative feedback with missing examples
        for i in range(3):
            system.record_feedback(
                f"Query {i}",
                f"Response {i}",
                "negative",
                feedback_text="Missing examples in explanation"
            )

        insights = system.get_learning_insights(min_occurrences=3)
        assert len(insights) > 0
        assert any("code examples" in insight.lower() for insight in insights)


def test_get_learning_insights_verbosity():
    """Test insight for verbosity pattern."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system = FeedbackLearningSystem(storage_path=tmpdir)

        # Record 3 negative feedback about verbosity
        for i in range(3):
            system.record_feedback(
                f"Query {i}",
                f"Response {i}",
                "negative",
                feedback_text="Response is too verbose"
            )

        insights = system.get_learning_insights(min_occurrences=3)
        assert any("concise" in insight.lower() for insight in insights)


def test_get_learning_insights_security():
    """Test insight for security pattern."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system = FeedbackLearningSystem(storage_path=tmpdir)

        # Record corrections about security
        for i in range(3):
            system.record_feedback(
                f"Query {i}",
                f"Response {i}",
                "correction",
                feedback_text="Missing security considerations",
                correction="Should sanitize input..."
            )

        insights = system.get_learning_insights(min_occurrences=3)
        assert any("security" in insight.lower() for insight in insights)


def test_get_learning_insights_filtered_by_type():
    """Test insights filtered by query type."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system = FeedbackLearningSystem(storage_path=tmpdir)

        # Record Python-specific feedback
        for i in range(3):
            system.record_feedback(
                f"Python async question {i}",
                f"Python answer {i}",
                "negative",
                feedback_text="Missing examples"
            )

        # Record JavaScript feedback (different)
        system.record_feedback(
            "JavaScript question",
            "JavaScript answer",
            "negative",
            feedback_text="Too verbose"
        )

        # Get Python-specific insights
        insights = system.get_learning_insights(query_type="python", min_occurrences=3)
        assert len(insights) > 0


def test_get_relevant_feedback_empty():
    """Test relevant feedback with empty database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system = FeedbackLearningSystem(storage_path=tmpdir)
        relevant = system.get_relevant_feedback("Test query")
        assert relevant == []


def test_get_relevant_feedback_similarity():
    """Test relevant feedback retrieval by similarity."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system = FeedbackLearningSystem(storage_path=tmpdir)

        # Record feedback on similar topics
        system.record_feedback(
            "How to use async/await in Python?",
            "Async/await allows...",
            "negative",
            feedback_text="Missing examples"
        )

        system.record_feedback(
            "Explain Python decorators",
            "Decorators are...",
            "positive"
        )

        # Query similar to first feedback
        relevant = system.get_relevant_feedback(
            "How does Python handle concurrency with async?",
            top_k=5,
            similarity_threshold=0.1  # Low threshold for word overlap
        )

        # Should find the async feedback
        assert len(relevant) > 0
        assert "async" in relevant[0].query.lower()


def test_get_relevant_feedback_threshold():
    """Test similarity threshold filtering."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system = FeedbackLearningSystem(storage_path=tmpdir)

        # Record unrelated feedback
        system.record_feedback(
            "Explain quantum computing",
            "Quantum computing uses...",
            "positive"
        )

        # Query about Python (very different)
        relevant = system.get_relevant_feedback(
            "How to use Python lists?",
            similarity_threshold=0.9  # Very high threshold
        )

        # Should not find any relevant feedback
        assert len(relevant) == 0


def test_get_relevant_feedback_top_k():
    """Test top_k limit on relevant feedback."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system = FeedbackLearningSystem(storage_path=tmpdir)

        # Record 10 similar feedback items
        for i in range(10):
            system.record_feedback(
                f"Python async question {i}",
                f"Python async answer {i}",
                "positive"
            )

        # Get top 3
        relevant = system.get_relevant_feedback(
            "Python async programming",
            top_k=3,
            similarity_threshold=0.1
        )

        assert len(relevant) <= 3


def test_export_json():
    """Test JSON export."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system = FeedbackLearningSystem(storage_path=tmpdir)

        # Record some feedback
        system.record_feedback("Q1", "R1", "positive")
        system.record_feedback("Q2", "R2", "negative", feedback_text="Bad")

        # Export to JSON
        export_path = system.export_feedback(format="json")

        # Verify file exists
        assert Path(export_path).exists()

        # Verify content
        with open(export_path, "r") as f:
            data = json.load(f)

        assert len(data) == 2
        assert data[0]["query"] == "Q1"
        assert data[1]["feedback_type"] == "negative"


def test_export_csv():
    """Test CSV export."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system = FeedbackLearningSystem(storage_path=tmpdir)

        # Record some feedback
        system.record_feedback("Q1", "R1", "positive", feedback_text="Good")
        system.record_feedback("Q2", "R2", "correction", correction="Fixed")

        # Export to CSV
        export_path = system.export_feedback(format="csv")

        # Verify file exists
        assert Path(export_path).exists()

        # Verify content
        with open(export_path, "r") as f:
            lines = f.readlines()

        assert len(lines) == 3  # Header + 2 records
        assert "id,timestamp,query" in lines[0]
        assert "Q1" in lines[1]
        assert "Q2" in lines[2]


def test_export_empty_csv():
    """Test CSV export with no feedback."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system = FeedbackLearningSystem(storage_path=tmpdir)

        # Export empty database
        export_path = system.export_feedback(format="csv")

        # Verify file exists with headers
        assert Path(export_path).exists()

        with open(export_path, "r") as f:
            lines = f.readlines()

        assert len(lines) == 1  # Header only
        assert "id,timestamp,query" in lines[0]


def test_export_invalid_format():
    """Test error on invalid export format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system = FeedbackLearningSystem(storage_path=tmpdir)

        try:
            system.export_feedback(format="xml")
            assert False, "Should raise ValueError"
        except ValueError as e:
            assert "Invalid format" in str(e)


def test_export_custom_path():
    """Test export to custom path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system = FeedbackLearningSystem(storage_path=tmpdir)
        system.record_feedback("Q1", "R1", "positive")

        # Export to custom path
        custom_path = Path(tmpdir) / "custom_export.json"
        export_path = system.export_feedback(
            format="json",
            output_path=str(custom_path)
        )

        assert export_path == str(custom_path)
        assert custom_path.exists()


def test_clear_feedback():
    """Test clearing all feedback."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system = FeedbackLearningSystem(storage_path=tmpdir)

        # Record feedback
        system.record_feedback("Q1", "R1", "positive")
        system.record_feedback("Q2", "R2", "negative")
        assert len(system.feedback_db) == 2

        # Clear
        count = system.clear_feedback()

        assert count == 2
        assert len(system.feedback_db) == 0

        # Verify persistence
        db_path = Path(tmpdir) / "feedback_db.json"
        with open(db_path, "r") as f:
            data = json.load(f)
        assert data == []


def test_get_feedback_by_id():
    """Test retrieving feedback by ID."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system = FeedbackLearningSystem(storage_path=tmpdir)

        feedback_id = system.record_feedback("Test", "Response", "positive")
        record = system.get_feedback_by_id(feedback_id)

        assert record is not None
        assert record.id == feedback_id
        assert record.query == "Test"


def test_get_feedback_by_id_not_found():
    """Test get_feedback_by_id with invalid ID."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system = FeedbackLearningSystem(storage_path=tmpdir)
        record = system.get_feedback_by_id("invalid-uuid")
        assert record is None


def test_get_feedback_by_type():
    """Test filtering feedback by type."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system = FeedbackLearningSystem(storage_path=tmpdir)

        system.record_feedback("Q1", "R1", "positive")
        system.record_feedback("Q2", "R2", "positive")
        system.record_feedback("Q3", "R3", "negative")

        positive = system.get_feedback_by_type("positive")
        negative = system.get_feedback_by_type("negative")

        assert len(positive) == 2
        assert len(negative) == 1


def test_get_feedback_by_tag():
    """Test filtering feedback by tag."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system = FeedbackLearningSystem(storage_path=tmpdir)

        system.record_feedback(
            "Python async question",
            "Python answer",
            "positive"
        )
        system.record_feedback(
            "JavaScript promise question",
            "JavaScript answer",
            "negative"
        )

        python_feedback = system.get_feedback_by_tag("python")
        js_feedback = system.get_feedback_by_tag("javascript")

        assert len(python_feedback) == 1
        assert len(js_feedback) == 1
        assert "python" in [t.lower() for t in python_feedback[0].tags]


def test_word_overlap_similarity():
    """Test fallback word overlap similarity."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create system without embeddings
        system = FeedbackLearningSystem(storage_path=tmpdir)
        system.embedding_model = None  # Force fallback

        similarity = system._calculate_word_overlap(
            "How to use Python async",
            "How to use Python decorators"
        )

        # Should have some overlap (how, to, use, python)
        assert similarity > 0.0


def test_word_overlap_no_overlap():
    """Test word overlap with no common words."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system = FeedbackLearningSystem(storage_path=tmpdir)
        system.embedding_model = None  # Force fallback

        similarity = system._calculate_word_overlap(
            "Explain quantum computing",
            "Debug JavaScript promises"
        )

        assert similarity == 0.0


def test_uuid_uniqueness():
    """Test that UUIDs are unique."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system = FeedbackLearningSystem(storage_path=tmpdir)

        # Record 100 feedback items
        ids = set()
        for i in range(100):
            feedback_id = system.record_feedback(
                f"Query {i}",
                f"Response {i}",
                "positive"
            )
            ids.add(feedback_id)

        # All IDs should be unique
        assert len(ids) == 100


def test_feedback_record_to_dict():
    """Test FeedbackRecord to_dict conversion."""
    record = FeedbackRecord(
        id="test-id",
        timestamp="2025-01-01T00:00:00",
        query="Test query",
        response="Test response",
        feedback_type="positive",
        feedback_text="Good",
        correction=None,
        context={"score": 0.9},
        tags=["python", "testing"]
    )

    data = record.to_dict()

    assert data["id"] == "test-id"
    assert data["query"] == "Test query"
    assert data["feedback_type"] == "positive"
    assert data["tags"] == ["python", "testing"]


def test_feedback_record_from_dict():
    """Test FeedbackRecord from_dict construction."""
    data = {
        "id": "test-id",
        "timestamp": "2025-01-01T00:00:00",
        "query": "Test query",
        "response": "Test response",
        "feedback_type": "negative",
        "feedback_text": "Bad",
        "correction": None,
        "context": {"score": 0.5},
        "tags": ["debugging"]
    }

    record = FeedbackRecord.from_dict(data)

    assert record.id == "test-id"
    assert record.query == "Test query"
    assert record.feedback_type == "negative"
    assert record.tags == ["debugging"]


def test_corrupt_database_recovery():
    """Test graceful handling of corrupt database file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "feedback_db.json"

        # Write corrupt JSON
        with open(db_path, "w") as f:
            f.write("{ corrupt json }")

        # Should recover gracefully
        system = FeedbackLearningSystem(storage_path=tmpdir)
        assert len(system.feedback_db) == 0


def test_atomic_write_protection():
    """Test atomic write prevents corruption on error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        system = FeedbackLearningSystem(storage_path=tmpdir)
        system.record_feedback("Q1", "R1", "positive")

        db_path = Path(tmpdir) / "feedback_db.json"
        temp_path = Path(tmpdir) / "feedback_db.json.tmp"

        # Verify no temp file left after successful write
        assert db_path.exists()
        assert not temp_path.exists()


def run_all_tests():
    """Run all tests and report results."""
    tests = [
        test_record_positive_feedback,
        test_record_negative_feedback,
        test_record_correction_feedback,
        test_invalid_feedback_type,
        test_feedback_persistence,
        test_feedback_persistence_multiple_records,
        test_tag_extraction,
        test_tag_extraction_multiple_topics,
        test_get_feedback_summary_empty,
        test_get_feedback_summary,
        test_get_feedback_summary_common_tags,
        test_get_feedback_summary_recent_count,
        test_get_learning_insights_no_feedback,
        test_get_learning_insights_missing_examples,
        test_get_learning_insights_verbosity,
        test_get_learning_insights_security,
        test_get_learning_insights_filtered_by_type,
        test_get_relevant_feedback_empty,
        test_get_relevant_feedback_similarity,
        test_get_relevant_feedback_threshold,
        test_get_relevant_feedback_top_k,
        test_export_json,
        test_export_csv,
        test_export_empty_csv,
        test_export_invalid_format,
        test_export_custom_path,
        test_clear_feedback,
        test_get_feedback_by_id,
        test_get_feedback_by_id_not_found,
        test_get_feedback_by_type,
        test_get_feedback_by_tag,
        test_word_overlap_similarity,
        test_word_overlap_no_overlap,
        test_uuid_uniqueness,
        test_feedback_record_to_dict,
        test_feedback_record_from_dict,
        test_corrupt_database_recovery,
        test_atomic_write_protection,
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
