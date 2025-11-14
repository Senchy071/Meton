#!/usr/bin/env python3
"""
Chain-of-Thought Reasoning for Meton.

Implements explicit reasoning steps before action selection through:
- Query decomposition into sub-questions
- Requirement analysis for tool selection
- Step-by-step reasoning chain generation
- Reasoning quality evaluation
- Proactive tool recommendation

Example:
    cot = ChainOfThoughtReasoning(model_manager, config)

    # Reason about a complex query
    reasoning = cot.reason_about_query(
        "Find authentication bugs in the codebase and suggest fixes",
        context={}
    )

    # Use recommended tools
    tools_to_use = reasoning["recommended_tools"]
    # ["codebase_search", "code_reviewer", "web_search"]
"""

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict


@dataclass
class ReasoningRecord:
    """Record of a single reasoning event."""
    query: str
    reasoning: str
    steps: List[str]
    recommended_tools: List[str]
    confidence: float
    complexity: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ChainOfThoughtReasoning:
    """Implements explicit reasoning steps before action selection.

    Features:
    - Query decomposition into atomic sub-questions
    - Requirement analysis for tool and information needs
    - Step-by-step reasoning chain generation
    - Reasoning quality evaluation (0.0-1.0)
    - Complexity detection (simple, medium, high)
    - Proactive tool recommendation
    - Statistics tracking

    The system uses LLM-based reasoning to plan tool usage before execution,
    reducing trial-and-error and improving task completion quality.
    """

    # Complexity indicators
    SIMPLE_INDICATORS = {
        "what is", "show me", "display", "get", "find file",
        "read", "list", "view"
    }

    MEDIUM_INDICATORS = {
        "explain", "how does", "why", "describe", "summarize",
        "find", "search for", "look for"
    }

    HIGH_INDICATORS = {
        "compare", "analyze", "evaluate", "review", "assess",
        "suggest", "recommend", "improve", "optimize", "debug",
        "find and fix", "research and"
    }

    # Tool categories
    TOOL_CAPABILITIES = {
        "codebase_search": ["find code", "search codebase", "locate implementation"],
        "web_search": ["research", "find information", "look up", "learn about"],
        "file_operations": ["read file", "write file", "modify file", "create file"],
        "code_executor": ["run code", "execute", "test code", "verify"],
        "code_reviewer": ["review code", "check quality", "find bugs", "security"],
        "debugger": ["debug", "troubleshoot", "find errors", "diagnose"],
        "refactoring_engine": ["refactor", "improve code", "optimize", "restructure"],
    }

    # Reasoning prompt template
    COT_PROMPT = """Think step-by-step about this query:

Query: {query}
Context: {context}

Break down your reasoning:
1. What is being asked?
2. What information is needed?
3. What tools should be used and why?
4. What is the logical sequence of steps?

Output format (MUST follow exactly):
REASONING: [Your step-by-step thinking process]
STEPS:
- [Step 1]
- [Step 2]
- [Step 3]
TOOLS: [Comma-separated list of tools to use]
CONFIDENCE: [Score from 0.0 to 1.0]

Available tools: codebase_search, web_search, file_operations, code_executor, code_reviewer, debugger, refactoring_engine
"""

    def __init__(self, model_manager, config: Dict):
        """Initialize chain-of-thought reasoning.

        Args:
            model_manager: Model manager for LLM access
            config: Configuration dictionary
        """
        self.model_manager = model_manager
        self.config = config

        # Get CoT config
        cot_config = config.get("chain_of_thought", {})
        self.min_complexity = cot_config.get("min_complexity_threshold", "medium")
        self.include_in_response = cot_config.get("include_in_response", False)
        self.max_steps = cot_config.get("max_reasoning_steps", 10)

        # Statistics tracking
        self.reasoning_history: List[ReasoningRecord] = []

    def reason_about_query(self, query: str, context: Dict = None) -> Dict:
        """Generate reasoning steps before tool selection.

        Args:
            query: User query to reason about
            context: Optional context (tools used, previous results, etc.)

        Returns:
            Dictionary with:
            - reasoning: Step-by-step thinking process
            - steps: List of action steps
            - recommended_tools: Tools to use
            - confidence: Confidence score (0.0-1.0)
            - complexity: Query complexity (simple, medium, high)
        """
        if context is None:
            context = {}

        # Detect complexity
        complexity = self.detect_complexity(query)

        # Generate reasoning using LLM
        llm = self.model_manager.get_model("primary")

        # Format prompt
        context_str = self._format_context(context)
        prompt = self.COT_PROMPT.format(query=query, context=context_str)

        # Get LLM response
        try:
            response = llm.invoke(prompt)
            reasoning_output = response.content
        except Exception as e:
            # Fallback to basic analysis
            return self._fallback_reasoning(query, complexity)

        # Parse reasoning output
        parsed = self._parse_reasoning_output(reasoning_output)

        # Ensure we have valid data
        reasoning_text = parsed.get("reasoning", "Unable to generate reasoning")
        steps = parsed.get("steps", [])
        tools = parsed.get("tools", [])
        confidence = parsed.get("confidence", 0.5)

        # Validate and clamp confidence
        confidence = max(0.0, min(1.0, confidence))

        # Store in history
        record = ReasoningRecord(
            query=query,
            reasoning=reasoning_text,
            steps=steps,
            recommended_tools=tools,
            confidence=confidence,
            complexity=complexity
        )
        self.reasoning_history.append(record)

        return {
            "reasoning": reasoning_text,
            "steps": steps,
            "recommended_tools": tools,
            "confidence": confidence,
            "complexity": complexity
        }

    def decompose_query(self, query: str) -> List[str]:
        """Break complex query into sub-questions.

        Args:
            query: Query to decompose

        Returns:
            List of atomic sub-questions
        """
        # Check for explicit multi-part queries
        parts = []

        # Check for comparison queries (do this FIRST before generic "and" split)
        if "compare" in query.lower():
            # "Compare X and Y" → ["What is X?", "What is Y?", "How do they differ?"]
            match = re.search(r'compare\s+(\w+)\s+and\s+(\w+)', query, re.IGNORECASE)
            if match:
                item1, item2 = match.groups()
                parts = [
                    f"What is {item1}?",
                    f"What is {item2}?",
                    f"How do {item1} and {item2} differ?"
                ]

        # Check for "find and" patterns
        elif re.search(r'find\s+\w+\s+and\s+\w+', query, re.IGNORECASE):
            # "Find bugs and suggest fixes" → ["Find bugs", "Suggest fixes"]
            parts = [p.strip() for p in re.split(r'\s+and\s+', query, flags=re.IGNORECASE)]

        # Split on common conjunctions (generic case)
        elif " and " in query.lower():
            parts = [p.strip() for p in re.split(r'\s+and\s+', query, flags=re.IGNORECASE)]

        # If no decomposition needed, return original
        if not parts or len(parts) == 1:
            return [query]

        return parts

    def analyze_requirements(self, query: str) -> Dict:
        """Determine what's needed to answer the query.

        Args:
            query: Query to analyze

        Returns:
            Dictionary with:
            - information_needed: List of information requirements
            - tools_required: List of tools needed
            - complexity: Complexity level (simple, medium, high)
        """
        complexity = self.detect_complexity(query)

        # Determine information needs
        information_needed = []
        tools_required = []

        query_lower = query.lower()

        # Code-related needs
        if any(word in query_lower for word in ["code", "implementation", "function", "class"]):
            information_needed.append("source code")
            tools_required.append("codebase_search")

        # Bug/error needs
        if any(word in query_lower for word in ["bug", "error", "issue", "problem", "debug"]):
            information_needed.append("error information")
            tools_required.append("debugger")

        # Research needs
        if any(word in query_lower for word in ["research", "find information", "look up", "learn"]):
            information_needed.append("external information")
            tools_required.append("web_search")

        # Review/quality needs
        if any(word in query_lower for word in ["review", "check", "quality", "security"]):
            information_needed.append("code quality metrics")
            tools_required.append("code_reviewer")

        # Refactoring needs
        if any(word in query_lower for word in ["refactor", "improve", "optimize", "restructure"]):
            information_needed.append("refactoring suggestions")
            tools_required.append("refactoring_engine")

        # File operation needs
        if any(word in query_lower for word in ["read file", "write file", "create file", "modify"]):
            information_needed.append("file access")
            tools_required.append("file_operations")

        # Code execution needs
        if any(word in query_lower for word in ["run", "execute", "test"]):
            information_needed.append("code execution")
            tools_required.append("code_executor")

        # Default if nothing detected
        if not information_needed:
            information_needed.append("general information")

        if not tools_required:
            # Make a guess based on query type
            if "?" in query:
                tools_required.append("web_search")
            else:
                tools_required.append("codebase_search")

        return {
            "information_needed": information_needed,
            "tools_required": list(set(tools_required)),  # Remove duplicates
            "complexity": complexity
        }

    def generate_reasoning_chain(
        self,
        query: str,
        context: Dict = None
    ) -> List[Dict]:
        """Create explicit reasoning steps.

        Args:
            query: Query to reason about
            context: Optional context

        Returns:
            List of reasoning steps, each with:
            - step: Step number
            - thought: What to think about
            - action: What action to take
            - justification: Why this step is needed
        """
        if context is None:
            context = {}

        # Decompose query
        sub_questions = self.decompose_query(query)

        # Analyze requirements
        requirements = self.analyze_requirements(query)

        # Build reasoning chain
        chain = []
        step_num = 1

        # Initial understanding step
        chain.append({
            "step": step_num,
            "thought": f"Understanding the query: {query}",
            "action": "Analyze query requirements",
            "justification": "Need to understand what information is required"
        })
        step_num += 1

        # Sub-question steps
        for sub_q in sub_questions[:self.max_steps - 2]:  # Reserve space for final steps
            chain.append({
                "step": step_num,
                "thought": f"Addressing sub-question: {sub_q}",
                "action": f"Gather information for: {sub_q}",
                "justification": "Breaking down complex query into manageable parts"
            })
            step_num += 1

        # Tool selection steps
        for tool in requirements["tools_required"][:3]:  # Limit to 3 tools
            chain.append({
                "step": step_num,
                "thought": f"Using {tool} to gather required information",
                "action": f"Execute {tool}",
                "justification": f"Tool needed for: {', '.join(requirements['information_needed'])}"
            })
            step_num += 1

        # Synthesis step
        chain.append({
            "step": step_num,
            "thought": "Synthesizing gathered information into coherent response",
            "action": "Generate final answer",
            "justification": "Combine all gathered information to answer the original query"
        })

        return chain[:self.max_steps]  # Enforce max steps limit

    def evaluate_reasoning_quality(self, reasoning: Dict) -> float:
        """Score reasoning quality 0.0-1.0.

        Args:
            reasoning: Reasoning dictionary from reason_about_query

        Returns:
            Quality score (0.0-1.0)
        """
        score = 0.0

        # Check reasoning text quality (30%)
        reasoning_text = reasoning.get("reasoning", "")
        if len(reasoning_text) > 50:
            score += 0.3
        elif len(reasoning_text) > 20:
            score += 0.15

        # Check steps quality (30%)
        steps = reasoning.get("steps", [])
        if len(steps) >= 3:
            score += 0.3
        elif len(steps) >= 1:
            score += 0.15

        # Check tool appropriateness (20%)
        tools = reasoning.get("recommended_tools", [])
        if len(tools) > 0 and len(tools) <= 5:
            score += 0.2
        elif len(tools) > 0:
            score += 0.1

        # Check confidence calibration (20%)
        confidence = reasoning.get("confidence", 0.0)
        if 0.6 <= confidence <= 0.9:  # Well-calibrated confidence
            score += 0.2
        elif confidence > 0:
            score += 0.1

        return min(1.0, score)

    def detect_complexity(self, query: str) -> str:
        """Detect query complexity.

        Args:
            query: Query to analyze

        Returns:
            Complexity level: "simple", "medium", or "high"
        """
        query_lower = query.lower()

        # Check for high complexity indicators
        for indicator in self.HIGH_INDICATORS:
            if indicator in query_lower:
                return "high"

        # Check for medium complexity indicators
        for indicator in self.MEDIUM_INDICATORS:
            if indicator in query_lower:
                return "medium"

        # Check for simple indicators
        for indicator in self.SIMPLE_INDICATORS:
            if indicator in query_lower:
                return "simple"

        # Default to medium if unclear
        return "medium"

    def should_use_cot(self, query: str) -> bool:
        """Determine if chain-of-thought is beneficial.

        Args:
            query: Query to evaluate

        Returns:
            True if CoT should be used, False otherwise
        """
        complexity = self.detect_complexity(query)

        # Map threshold to complexity
        threshold_map = {
            "simple": ["high"],  # Only use CoT for high complexity
            "medium": ["medium", "high"],  # Use CoT for medium and high
            "high": ["simple", "medium", "high"],  # Always use CoT
            "all": ["simple", "medium", "high"]  # Always use CoT
        }

        allowed_complexities = threshold_map.get(self.min_complexity, ["medium", "high"])
        return complexity in allowed_complexities

    def get_reasoning_stats(self) -> Dict:
        """Get reasoning statistics.

        Returns:
            Dictionary with statistics:
            - total_reasonings: Total reasoning operations
            - avg_steps_per_reasoning: Average number of steps
            - avg_confidence: Average confidence score
            - complexity_distribution: Count by complexity level
            - tool_recommendations: Most recommended tools
        """
        if not self.reasoning_history:
            return {
                "total_reasonings": 0,
                "avg_steps_per_reasoning": 0.0,
                "avg_confidence": 0.0,
                "complexity_distribution": {},
                "tool_recommendations": {}
            }

        # Calculate averages
        total = len(self.reasoning_history)
        total_steps = sum(len(r.steps) for r in self.reasoning_history)
        avg_steps = total_steps / total if total > 0 else 0.0

        total_confidence = sum(r.confidence for r in self.reasoning_history)
        avg_confidence = total_confidence / total if total > 0 else 0.0

        # Complexity distribution
        complexity_dist = defaultdict(int)
        for record in self.reasoning_history:
            complexity_dist[record.complexity] += 1

        # Tool recommendations
        tool_counts = defaultdict(int)
        for record in self.reasoning_history:
            for tool in record.recommended_tools:
                tool_counts[tool] += 1

        # Sort tools by frequency
        sorted_tools = dict(sorted(tool_counts.items(), key=lambda x: x[1], reverse=True))

        return {
            "total_reasonings": total,
            "avg_steps_per_reasoning": avg_steps,
            "avg_confidence": avg_confidence,
            "complexity_distribution": dict(complexity_dist),
            "tool_recommendations": sorted_tools
        }

    def _format_context(self, context: Dict) -> str:
        """Format context for prompt.

        Args:
            context: Context dictionary

        Returns:
            Formatted context string
        """
        if not context:
            return "No additional context"

        parts = []

        if "tools_used" in context:
            parts.append(f"Tools used: {', '.join(context['tools_used'])}")

        if "previous_results" in context:
            parts.append(f"Previous results available: Yes")

        if "reflection_score" in context:
            parts.append(f"Reflection score: {context['reflection_score']}")

        return "; ".join(parts) if parts else "No additional context"

    def _parse_reasoning_output(self, output: str) -> Dict:
        """Parse reasoning output from LLM.

        Args:
            output: Raw LLM output

        Returns:
            Dictionary with parsed reasoning components
        """
        # Extract sections
        reasoning = ""
        steps = []
        tools = []
        confidence = 0.5

        # Extract REASONING section
        reasoning_match = re.search(r'REASONING:\s*(.+?)(?=STEPS:|TOOLS:|CONFIDENCE:|$)', output, re.DOTALL)
        if reasoning_match:
            reasoning = reasoning_match.group(1).strip()

        # Extract STEPS section
        steps_match = re.search(r'STEPS:\s*(.+?)(?=TOOLS:|CONFIDENCE:|$)', output, re.DOTALL)
        if steps_match:
            steps_text = steps_match.group(1).strip()
            # Parse bullet points or numbered list
            steps = [
                line.strip().lstrip('-•*0123456789. ')
                for line in steps_text.split('\n')
                if line.strip() and line.strip()[0] in '-•*0123456789'
            ]

        # Extract TOOLS section
        tools_match = re.search(r'TOOLS:\s*(.+?)(?=CONFIDENCE:|$)', output, re.DOTALL)
        if tools_match:
            tools_text = tools_match.group(1).strip()
            # Parse comma-separated tools
            tools = [
                tool.strip()
                for tool in tools_text.split(',')
                if tool.strip()
            ]

        # Extract CONFIDENCE section
        confidence_match = re.search(r'CONFIDENCE:\s*([\d.]+)', output)
        if confidence_match:
            try:
                confidence = float(confidence_match.group(1))
            except ValueError:
                confidence = 0.5

        return {
            "reasoning": reasoning,
            "steps": steps,
            "tools": tools,
            "confidence": confidence
        }

    def _fallback_reasoning(self, query: str, complexity: str) -> Dict:
        """Provide fallback reasoning when LLM fails.

        Args:
            query: Query to reason about
            complexity: Detected complexity

        Returns:
            Basic reasoning dictionary
        """
        # Analyze requirements as fallback
        requirements = self.analyze_requirements(query)

        reasoning = f"Query requires: {', '.join(requirements['information_needed'])}"
        steps = [f"Use {tool}" for tool in requirements['tools_required']]
        tools = requirements['tools_required']

        return {
            "reasoning": reasoning,
            "steps": steps,
            "recommended_tools": tools,
            "confidence": 0.5,
            "complexity": complexity
        }

    def reset_history(self) -> None:
        """Reset reasoning history."""
        self.reasoning_history = []
