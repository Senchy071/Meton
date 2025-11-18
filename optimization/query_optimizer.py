#!/usr/bin/env python3
"""
Query Optimizer - Optimize query processing.

Features:
- Query classification
- Optimal tool selection
- Parallel execution detection
- RAG search optimization
- Query batching
"""

from typing import List, Dict, Any, Optional, Set
import re
from collections import defaultdict


class QueryOptimizer:
    """Optimize query processing."""

    def __init__(self):
        """Initialize query optimizer."""
        self.query_patterns: Dict[str, Dict[str, Any]] = {}
        self.tool_dependencies: Dict[str, Set[str]] = {
            "file_operations": set(),
            "code_executor": {"file_operations"},  # May need to read files first
            "web_search": set(),
            "codebase_search": set(),
            "git_operations": {"file_operations"},
        }

        # Query classification patterns
        self.classification_patterns = {
            "code_search": [
                r"\b(find|search|where is|locate|show me)\b.*\b(function|class|method|code)\b",
                r"\b(how does|what does)\b.*\b(work|implement)\b",
                r"\bexplain\b.*\b(code|implementation)\b"
            ],
            "code_review": [
                r"\b(review|check|analyze|inspect)\b.*\b(code|file|function)\b",
                r"\b(find|look for)\b.*\b(bugs|issues|problems|errors)\b",
                r"\bcode quality\b"
            ],
            "research": [
                r"\b(compare|what is|explain|tell me about)\b",
                r"\b(how to|best practices|tutorial)\b",
                r"\b(differences between|pros and cons)\b"
            ],
            "generation": [
                r"\b(generate|create|write|implement)\b",
                r"\b(add|build|make)\b.*\b(function|class|feature)\b"
            ],
            "file_operations": [
                r"\b(read|write|create|delete|modify)\b.*\b(file|directory)\b",
                r"\blist files\b"
            ],
            "debugging": [
                r"\b(debug|fix|solve)\b.*\b(error|bug|issue|problem)\b",
                r"\bwhy.*\b(not working|failing|broken)\b"
            ]
        }

    def optimize_tool_selection(self, query: str, context: Optional[Dict] = None) -> List[str]:
        """
        Select optimal tools based on query pattern.

        Args:
            query: Query string
            context: Optional context information

        Returns:
            List of recommended tool names
        """
        query_type = self.classify_query(query)
        tools = []

        # Map query types to tools
        tool_mapping = {
            "code_search": ["codebase_search"],
            "code_review": ["codebase_search", "file_operations"],
            "research": ["web_search", "codebase_search"],
            "generation": ["codebase_search", "file_operations"],
            "file_operations": ["file_operations"],
            "debugging": ["codebase_search", "code_executor", "file_operations"]
        }

        # Get tools for query type
        if query_type in tool_mapping:
            tools = tool_mapping[query_type]
        else:
            # Default tools
            tools = ["codebase_search"]

        # Check context for additional hints
        if context:
            if context.get("has_code"):
                if "code_executor" not in tools:
                    tools.append("code_executor")

            if context.get("needs_web_search"):
                if "web_search" not in tools:
                    tools.append("web_search")

        return tools

    def classify_query(self, query: str) -> str:
        """
        Classify query type.

        Args:
            query: Query string

        Returns:
            Query type
        """
        query_lower = query.lower()

        # Check patterns
        for query_type, patterns in self.classification_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return query_type

        return "general"

    def should_use_parallel(self, tools: List[str]) -> bool:
        """
        Determine if tools can execute in parallel.

        Args:
            tools: List of tool names

        Returns:
            True if parallel execution is safe
        """
        # Check for dependencies between tools
        for i, tool1 in enumerate(tools):
            for tool2 in tools[i+1:]:
                # Check if tool2 depends on tool1
                if tool1 in self.tool_dependencies.get(tool2, set()):
                    return False
                # Check if tool1 depends on tool2
                if tool2 in self.tool_dependencies.get(tool1, set()):
                    return False

        # No dependencies found
        return True

    def optimize_rag_search(self, query: str) -> Dict[str, Any]:
        """
        Optimize RAG search parameters.

        Args:
            query: Query string

        Returns:
            Optimized search parameters
        """
        params = {
            "top_k": 5,
            "similarity_threshold": 0.7,
            "use_reranking": False
        }

        query_lower = query.lower()

        # Adjust top_k based on query complexity
        if len(query.split()) > 10:
            # Complex query, get more results
            params["top_k"] = 10
        elif len(query.split()) < 5:
            # Simple query, fewer results needed
            params["top_k"] = 3

        # Adjust similarity threshold
        if any(word in query_lower for word in ["explain", "how does", "what is"]):
            # More exploratory, lower threshold
            params["similarity_threshold"] = 0.6
        elif any(word in query_lower for word in ["exact", "specific", "find"]):
            # More specific, higher threshold
            params["similarity_threshold"] = 0.8

        # Use reranking for complex queries
        if len(query.split()) > 15 or "compare" in query_lower:
            params["use_reranking"] = True

        return params

    def batch_similar_queries(self, queries: List[str]) -> List[List[str]]:
        """
        Batch similar queries for efficient processing.

        Args:
            queries: List of query strings

        Returns:
            List of query batches
        """
        if not queries:
            return []

        # Classify all queries
        classified = defaultdict(list)
        for query in queries:
            query_type = self.classify_query(query)
            classified[query_type].append(query)

        # Create batches by type
        batches = [queries for queries in classified.values() if queries]

        return batches

    def suggest_improvements(self, query: str, execution_time: float) -> List[str]:
        """
        Suggest query improvements based on performance.

        Args:
            query: Query string
            execution_time: Query execution time in seconds

        Returns:
            List of improvement suggestions
        """
        suggestions = []

        # Slow query suggestions
        if execution_time > 10.0:
            suggestions.append(
                "Query took >10s. Consider breaking into smaller, more specific queries."
            )

            if len(query.split()) > 20:
                suggestions.append(
                    "Query is very long. Try shorter, more focused questions."
                )

        # Vague query suggestions
        vague_words = ["something", "anything", "everything", "stuff", "things"]
        if any(word in query.lower() for word in vague_words):
            suggestions.append(
                "Query is vague. Be more specific about what you're looking for."
            )

        # Multiple question suggestion
        if query.count("?") > 1:
            suggestions.append(
                "Multiple questions detected. Ask them separately for better results."
            )

        return suggestions

    def estimate_execution_time(self, query: str, tools: List[str]) -> float:
        """
        Estimate query execution time.

        Args:
            query: Query string
            tools: Tools to be used

        Returns:
            Estimated time in seconds
        """
        # Base time for query processing
        base_time = 1.0

        # Tool execution times (estimates)
        tool_times = {
            "file_operations": 0.5,
            "code_executor": 2.0,
            "web_search": 3.0,
            "codebase_search": 1.5,
            "git_operations": 1.0
        }

        # Sum tool times
        total_time = base_time
        for tool in tools:
            total_time += tool_times.get(tool, 1.0)

        # Adjust for query complexity
        word_count = len(query.split())
        if word_count > 20:
            total_time *= 1.5
        elif word_count > 10:
            total_time *= 1.2

        return total_time

    def get_optimization_report(self, query: str) -> str:
        """
        Generate optimization report for query.

        Args:
            query: Query string

        Returns:
            Formatted report
        """
        query_type = self.classify_query(query)
        tools = self.optimize_tool_selection(query)
        can_parallel = self.should_use_parallel(tools)
        rag_params = self.optimize_rag_search(query)
        estimated_time = self.estimate_execution_time(query, tools)

        report = []
        report.append("=" * 60)
        report.append("QUERY OPTIMIZATION REPORT")
        report.append("=" * 60)
        report.append(f"\nQuery: {query[:100]}...")
        report.append(f"\nClassification: {query_type}")
        report.append(f"\nRecommended Tools: {', '.join(tools)}")
        report.append(f"Parallel Execution: {'Yes' if can_parallel else 'No'}")
        report.append(f"Estimated Time: {estimated_time:.1f}s")
        report.append(f"\nRAG Parameters:")
        for key, value in rag_params.items():
            report.append(f"  {key}: {value}")

        suggestions = self.suggest_improvements(query, estimated_time)
        if suggestions:
            report.append(f"\nSuggestions:")
            for suggestion in suggestions:
                report.append(f"  • {suggestion}")

        report.append("\n" + "=" * 60)

        return "\n".join(report)


# Global optimizer instance
_global_optimizer = QueryOptimizer()


def get_optimizer() -> QueryOptimizer:
    """Get global optimizer instance."""
    return _global_optimizer


if __name__ == "__main__":
    # Example usage
    optimizer = QueryOptimizer()

    # Test queries
    test_queries = [
        "Find the main function in the codebase",
        "Review the code in src/main.py for bugs",
        "Compare Python and JavaScript async patterns",
        "Generate a new user authentication function",
        "Why is my code not working?",
        "Read the config file and show me the settings"
    ]

    print("Query Optimization Examples:")
    print("=" * 60)

    for query in test_queries:
        print(f"\nQuery: {query}")
        print(f"Type: {optimizer.classify_query(query)}")
        print(f"Tools: {optimizer.optimize_tool_selection(query)}")

        tools = optimizer.optimize_tool_selection(query)
        print(f"Parallel: {optimizer.should_use_parallel(tools)}")
        print(f"RAG params: {optimizer.optimize_rag_search(query)}")
        print("-" * 60)

    # Test batching
    print("\n\nQuery Batching:")
    print("=" * 60)
    batches = optimizer.batch_similar_queries(test_queries)
    for i, batch in enumerate(batches, 1):
        print(f"\nBatch {i}:")
        for query in batch:
            print(f"  - {query}")
