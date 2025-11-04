"""LangGraph agent implementation for Meton.

This module implements a ReAct (Reasoning + Acting) agent using LangGraph's StateGraph.
The agent follows a Think → Act → Observe loop for multi-step reasoning and tool usage.

Example:
    >>> from core.agent import MetonAgent
    >>> from core.config import Config
    >>> from core.models import ModelManager
    >>> from core.conversation import ConversationManager
    >>>
    >>> config = Config()
    >>> model_manager = ModelManager(config)
    >>> conversation = ConversationManager(config)
    >>> tools = [FileOperationsTool(config)]
    >>>
    >>> agent = MetonAgent(config, model_manager, conversation, tools)
    >>> result = agent.run("Read the README.md file")
"""

from typing import TypedDict, Annotated, List, Dict, Any, Optional
import re
from langchain.tools import BaseTool
from langgraph.graph import StateGraph, END

from core.models import ModelManager
from core.conversation import ConversationManager
from core.config import ConfigLoader
from utils.logger import setup_logger


# Custom Exceptions
class AgentError(Exception):
    """Base exception for agent errors."""
    pass


class AgentExecutionError(AgentError):
    """Agent execution failed."""
    pass


class AgentParsingError(AgentError):
    """Failed to parse agent output."""
    pass


class AgentState(TypedDict):
    """State for the agent graph.

    This state is passed between nodes in the LangGraph StateGraph.
    Each node can read from and write to this state.

    Attributes:
        messages: Full conversation history including user query and agent responses
        thoughts: Agent's reasoning steps (list of thought strings)
        tool_calls: Tools called and their results [(tool_name, input, output), ...]
        iteration: Current iteration number (to prevent infinite loops)
        finished: Whether agent has completed reasoning
        final_answer: The final answer to return to user (if finished)
    """
    messages: List[str]  # Conversation history
    thoughts: List[str]  # Agent's reasoning steps
    tool_calls: List[Dict[str, Any]]  # Tool executions
    iteration: int  # Current iteration
    finished: bool  # Whether reasoning is complete
    final_answer: Optional[str]  # Final response


class MetonAgent:
    """ReAct agent using LangGraph for multi-step reasoning.

    Implements a Think → Act → Observe loop using LangGraph's StateGraph:
    1. Reasoning Node: Agent thinks about what to do
    2. Tool Execution Node: Executes selected tool
    3. Observation Node: Processes tool results
    4. Decision: Continue reasoning or return final answer

    Example:
        >>> agent = MetonAgent(config, model_manager, conversation, tools, verbose=True)
        >>> result = agent.run("What files are in the current directory?")
        >>> print(result['output'])
    """

    def __init__(
        self,
        config: ConfigLoader,
        model_manager: ModelManager,
        conversation: ConversationManager,
        tools: List[BaseTool],
        verbose: bool = False
    ):
        """Initialize Meton agent.

        Args:
            config: Configuration loader
            model_manager: Model manager instance
            conversation: Conversation manager instance
            tools: List of available tools
            verbose: Whether to show agent's thought process
        """
        self.config = config
        self.model_manager = model_manager
        self.conversation = conversation
        self.tools = tools

        # Agent configuration
        agent_config = config.config.agent
        self.max_iterations = agent_config.max_iterations
        self.verbose = verbose or agent_config.verbose

        # Create tool name → tool mapping
        self.tool_map = {tool.name: tool for tool in tools}

        # Setup logger
        self.logger = setup_logger(name="meton_agent", console_output=False)

        # Build the LangGraph StateGraph
        # Set recursion limit higher than default (25) to allow multi-step reasoning
        self.recursion_limit = self.max_iterations * 3  # 3 nodes per iteration
        self.graph = self._build_graph()

        if self.logger:
            self.logger.info(f"MetonAgent initialized with {len(tools)} tools")
            self.logger.debug(f"Tools: {list(self.tool_map.keys())}")
            self.logger.debug(f"Max iterations: {self.max_iterations}")
            self.logger.debug(f"Recursion limit: {self.recursion_limit}")

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph StateGraph for ReAct pattern.

        Creates a graph with three nodes:
        - reasoning: Agent thinks about what to do
        - tool_execution: Executes selected tool
        - observation: Processes tool results

        Returns:
            Compiled StateGraph ready for execution
        """
        # Create StateGraph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("reasoning", self._reasoning_node)
        workflow.add_node("tool_execution", self._tool_execution_node)
        workflow.add_node("observation", self._observation_node)

        # Set entry point
        workflow.set_entry_point("reasoning")

        # Add conditional edges from reasoning
        workflow.add_conditional_edges(
            "reasoning",
            self._should_execute_tool,
            {
                "tool_execution": "tool_execution",
                "end": END
            }
        )

        # Add edge from tool_execution to observation
        workflow.add_edge("tool_execution", "observation")

        # Add conditional edge from observation
        workflow.add_conditional_edges(
            "observation",
            self._should_continue,
            {
                "reasoning": "reasoning",
                "end": END
            }
        )

        return workflow.compile()

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the agent.

        Returns:
            System prompt string with ReAct instructions
        """
        from pathlib import Path

        tool_descriptions = "\n".join([
            f"- {tool.name}: {tool.description}"
            for tool in self.tools
        ])

        # Get current working directory
        cwd = str(Path.cwd())

        # Get allowed paths from config
        allowed_paths = "\n".join([
            f"  • {path}"
            for path in self.config.config.tools.file_ops.allowed_paths
        ])

        return f"""You are Meton, a local AI coding assistant with wisdom and action.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL FILE ACCESS INFORMATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Current Working Directory: {cwd}

Allowed Directories (you can only access these):
{allowed_paths}

IMPORTANT:
- When user asks "what files can you see" or about files, list: {cwd}
- Always use REAL paths from above, NEVER use placeholders like "/path/to/directory"
- Start all file operations from: {cwd}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AVAILABLE TOOLS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{tool_descriptions}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR RESPONSE FORMAT (ReAct Pattern):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

THOUGHT: [Think about what you need to do next]
ACTION: [tool_name or NONE if no tool needed]
ACTION_INPUT: [JSON input for the tool with REAL paths, or empty if ACTION is NONE]
ANSWER: [Your final answer to the user, or empty if you need more steps]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXAMPLES WITH REAL PATHS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Example 1 - Simple query (complete flow):
User: "What files can you see?"

Step 1 (First call):
THOUGHT: I need to list the current working directory to show available files
ACTION: file_operations
ACTION_INPUT: {{"action": "list", "path": "{cwd}"}}
ANSWER:

[Tool executes and returns file list]

Step 2 (After receiving tool result):
THOUGHT: I received the directory listing, now I can answer the user's question
ACTION: NONE
ACTION_INPUT:
ANSWER: I can see the following files in {cwd}: [list the files from the tool result]

Example 2 - Direct file read:
User: "Read config.yaml"

Step 1 (First call):
THOUGHT: I should read the config.yaml file from the current directory
ACTION: file_operations
ACTION_INPUT: {{"action": "read", "path": "{cwd}/config.yaml"}}
ANSWER:

[Tool executes and returns file contents]

Step 2 (After receiving tool result):
THOUGHT: I have the file contents, now I can present them to the user
ACTION: NONE
ACTION_INPUT:
ANSWER: Here are the contents of config.yaml: [show the contents from tool result]

Example 3 - Write a file:
User: "Create a file called test.py that prints hello"

Step 1 (First call):
THOUGHT: I need to create a new file with Python code
ACTION: file_operations
ACTION_INPUT: {{"action": "write", "path": "{cwd}/test.py", "content": "print('hello')"}}
ANSWER:

[Tool executes and returns: "✓ Wrote 1 lines (14 characters) to /path/test.py"]

Step 2 (After receiving tool result):
THOUGHT: The tool confirmed the file was written successfully
ACTION: NONE
ACTION_INPUT:
ANSWER: I've created test.py with the code to print 'hello'. The file is ready to use.

Example 4 - Multi-step with THEN (CRITICAL - agent must complete ALL steps):
User: "List files in core/ THEN read agent.py and explain the loop detection"

Step 1 (First call):
THOUGHT: User wants TWO things: 1) list core/ directory, 2) read agent.py and explain. I'll start with listing.
ACTION: file_operations
ACTION_INPUT: {{"action": "list", "path": "{cwd}/core"}}
ANSWER:

[Tool returns: "Files: agent.py, models.py, config.py..."]

Step 2 (After first tool result - DO NOT STOP HERE):
THOUGHT: I completed step 1 (listing). Now I need step 2: read agent.py to explain loop detection. I MUST continue.
ACTION: file_operations
ACTION_INPUT: {{"action": "read", "path": "{cwd}/core/agent.py"}}
ANSWER:

[Tool returns file contents with loop detection code at lines 431-455]

Step 3 (After second tool result - NOW answer):
THOUGHT: I have both the list AND the file contents. Now I can provide the complete answer.
ACTION: NONE
ACTION_INPUT:
ANSWER: In core/ there are 4 Python files: agent.py, models.py, config.py, conversation.py. Regarding loop detection in agent.py: The code at lines 431-455 detects when the agent tries to call the same tool twice with identical input, and forces completion to prevent infinite loops.

Example 5 - Answer extraction (NOT full file dump):
User: "Read config.yaml and tell me what the primary model is"

Step 1 (First call):
THOUGHT: I need to read config.yaml to find the primary model setting
ACTION: file_operations
ACTION_INPUT: {{"action": "read", "path": "{cwd}/config.yaml"}}
ANSWER:

[Tool returns 45 lines of config file including: "primary_model: codellama:34b"]

Step 2 (After receiving tool result):
THOUGHT: I have the full config. User asked for primary model specifically, so I extract that ONE detail.
ACTION: NONE
ACTION_INPUT:
ANSWER: The primary model is codellama:34b

Example 6 - Code analysis (MUST read file before claiming details):
User: "What safety measures are in file_ops.py?"

Step 1 (First call):
THOUGHT: I need to read the actual file to see what safety measures exist. I cannot guess or make up code.
ACTION: file_operations
ACTION_INPUT: {{"action": "read", "path": "{cwd}/tools/file_ops.py"}}
ANSWER:

[Tool returns file contents showing _validate_path(), blocked_paths check, file size limits]

Step 2 (After receiving tool result):
THOUGHT: Now I can see the ACTUAL code. I'll describe only what I see in the tool result.
ACTION: NONE
ACTION_INPUT:
ANSWER: Based on the actual code, file_ops.py implements these safety measures: 1) _validate_path() resolves paths and checks against blocked_paths list, 2) blocked_paths includes /etc/, /sys/, /proc/, 3) File size limits via max_file_size check, 4) Path must be in allowed_paths list. I see these in the tool result.

Example 7 - Code execution:
User: "Can you test this code: print(2+2)"

Step 1 (First call):
THOUGHT: I need to execute the Python code using the code_executor tool
ACTION: code_executor
ACTION_INPUT: {{"code": "print(2+2)"}}
ANSWER:

[Tool returns: {{"success": true, "output": "4", "error": "", "execution_time": 0.006}}]

Step 2 (After receiving tool result):
THOUGHT: The code executed successfully and output 4
ACTION: NONE
ACTION_INPUT:
ANSWER: The code executes successfully and outputs 4

Example 8 - Web search when DISABLED (default state):
User: "Search for Python async best practices"

Step 1 (First call):
THOUGHT: User wants to search the web. I should try the web_search tool.
ACTION: web_search
ACTION_INPUT: {{"query": "Python async best practices"}}
ANSWER:

[Tool returns: {{"success": false, "error": "Web search is disabled. Enable with /web on command or set tools.web_search.enabled=true in config.yaml", "count": 0}}]

Step 2 (After receiving tool result):
THOUGHT: The tool says web search is disabled. I need to inform the user how to enable it.
ACTION: NONE
ACTION_INPUT:
ANSWER: Web search is currently disabled. You can enable it with the /web on command.

Example 9 - Web search when ENABLED:
User: "Search for FastAPI tutorials"

Step 1 (First call):
THOUGHT: User wants to search for FastAPI tutorials online
ACTION: web_search
ACTION_INPUT: {{"query": "FastAPI tutorials"}}
ANSWER:

[Tool returns: {{"success": true, "results": [{{"title": "FastAPI Tutorial", "url": "https://fastapi.tiangolo.com", "snippet": "FastAPI framework..."}}, ...], "count": 5}}]

Step 2 (After receiving tool result):
THOUGHT: I received 5 search results. I'll present them to the user.
ACTION: NONE
ACTION_INPUT:
ANSWER: Here are the top FastAPI tutorial results:
1. FastAPI Tutorial - https://fastapi.tiangolo.com - FastAPI framework...
[list remaining results]

Example 10 - Counting files (TRUST TOOL COUNTS, DON'T LIST ALL FILES):
User: "List all directories and the number of Python files they contain."

Step 1 (Find files in core/):
THOUGHT: User wants directory names with counts. I'll search each subdirectory for Python files. Starting with core/
ACTION: file_operations
ACTION_INPUT: {{"action": "find", "path": "{cwd}/core", "pattern": "*.py", "recursive": true}}
ANSWER:

[Tool returns: "✓ Found 5 file(s) matching '*.py' (recursive search from /path/core)\n\n/path/core/__init__.py\n/path/core/agent.py\n..."]

Step 2 (Find files in tools/):
THOUGHT: Tool output said "✓ Found 5 file(s)" - that's the count for core/. Now checking tools/.
ACTION: file_operations
ACTION_INPUT: {{"action": "find", "path": "{cwd}/tools", "pattern": "*.py", "recursive": true}}
ANSWER:

[Tool returns: "✓ Found 5 file(s) matching '*.py' (recursive search from /path/tools)\n\n/path/tools/__init__.py\n/path/tools/base.py\n/path/tools/code_executor.py\n/path/tools/file_ops.py\n/path/tools/web_search.py"]

Step 3 (Provide answer with COUNTS ONLY):
THOUGHT: Tool said "✓ Found 5 file(s)" for tools/. I now have counts for both directories from the tool headers. User asked for "number", NOT to list files. I'll use the counts from "Found X file(s)" headers, NOT by manually counting the file paths.
ACTION: NONE
ACTION_INPUT:
ANSWER: Here are the directories with Python file counts:
- core/: 5 Python files (from "Found 5 file(s)" in tool output)
- tools/: 5 Python files (from "Found 5 file(s)" in tool output)

CRITICAL: I used the counts from "✓ Found X file(s)" headers, NOT by counting file paths. Never say "based on file paths, I count X" - always use the tool's count.

Example 11 - Searching Codebase for Understanding (RAG enabled):
User: "How does authentication work in this project?"

Step 1 (First call):
THOUGHT: User wants to understand how authentication works in the codebase. I should use codebase_search to find relevant authentication code.
ACTION: codebase_search
ACTION_INPUT: {{"query": "authentication login user verify"}}
ANSWER:

[Tool returns: {{"success": true, "results": [{{"file": "auth/login.py", "type": "function", "name": "authenticate_user", "lines": "45-67", "similarity": 0.89, "code_snippet": "def authenticate_user(username, password):\\n    # Verify credentials\\n    ..."}}], "count": 3}}]

Step 2 (After receiving search results):
THOUGHT: I received code chunks showing authentication implementation. Now I can explain based on the actual code found.
ACTION: NONE
ACTION_INPUT:
ANSWER: Based on the code search, authentication is handled in auth/login.py. The authenticate_user() function (lines 45-67) verifies user credentials. [Explain the authentication flow based on code snippets returned]

Example 12 - Finding Specific Functionality (RAG enabled):
User: "Show me how database connections are handled"

Step 1 (First call):
THOUGHT: User wants to see database connection handling code. I'll search for it.
ACTION: codebase_search
ACTION_INPUT: {{"query": "database connection setup"}}
ANSWER:

[Tool returns: {{"success": true, "results": [{{"file": "db/connection.py", "type": "function", "name": "create_connection", "lines": "12-34", "similarity": 0.92, "code_snippet": "def create_connection():\\n    conn = sqlite3.connect(DB_PATH)\\n    ..."}}], "count": 2}}]

Step 2 (After receiving search results):
THOUGHT: Found the database connection code. I'll explain it to the user.
ACTION: NONE
ACTION_INPUT:
ANSWER: Database connections are handled in db/connection.py. The create_connection() function (lines 12-34) establishes connections: [Show code snippet and explain]

Example 13 - Understanding Code Structure (RAG enabled):
User: "What does the indexer do?"

Step 1 (First call):
THOUGHT: User wants to understand the indexer implementation. I'll search for indexer code.
ACTION: codebase_search
ACTION_INPUT: {{"query": "indexer class functions"}}
ANSWER:

[Tool returns: {{"success": true, "results": [{{"file": "rag/indexer.py", "type": "class", "name": "CodebaseIndexer", "lines": "20-150", "similarity": 0.95, "code_snippet": "class CodebaseIndexer:\\n    def __init__(self, embedder, vector_store, metadata_store):\\n        ..."}}], "count": 1}}]

Step 2 (After receiving search results):
THOUGHT: I have the indexer code. I'll explain what it does based on the actual implementation.
ACTION: NONE
ACTION_INPUT:
ANSWER: The indexer is implemented in rag/indexer.py as the CodebaseIndexer class. Based on the actual code, it: [Explain based on code snippet]

Example 14 - RAG Disabled or No Index:
User: "How does X work in the code?"

Step 1 (First call):
THOUGHT: User is asking about code. I should try codebase_search first.
ACTION: codebase_search
ACTION_INPUT: {{"query": "X functionality implementation"}}
ANSWER:

[Tool returns: {{"success": false, "error": "Codebase search is disabled. Index your codebase first, then enable with tools.codebase_search.enabled=true in config.yaml", "count": 0}}]

Step 2 (After receiving error):
THOUGHT: The tool says codebase search is disabled. I need to inform the user how to enable it.
ACTION: NONE
ACTION_INPUT:
ANSWER: No codebase is currently indexed. To search the codebase, you need to index it first using the indexer, then enable codebase search in config.yaml by setting tools.codebase_search.enabled=true.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOOL SELECTION RULES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Use codebase_search when:
- User asks "how does X work" about code functionality in THIS project
- User asks "where is X implemented" or "find code that does X"
- User asks about project architecture or structure
- User wants to understand existing code in the indexed codebase
- Questions start with: "explain", "show me", "how does", "where is", "what does"
- User wants to find functions, classes, or implementations
- NOTE: This tool is DISABLED by default - if it returns error, tell user to index codebase first
- PRIORITY: If asking about THIS project's code → try codebase_search FIRST before file_operations

Use code_executor when:
- User asks to run/test/execute Python code
- User wants to debug code snippets
- User asks "what does this code output"
- User provides code and asks to try it

Use web_search when:
- User explicitly asks to "search" for something online
- User wants to find information on the web
- User asks about current events or documentation online
- User needs information about external libraries or best practices
- Information is NOT available in the indexed codebase
- NOTE: Web search is DISABLED by default - inform user if tool returns disabled error

Use file_operations when:
- User asks to read a SPECIFIC known file path
- User wants to write/create/modify a file
- User wants to list directory contents
- User asks about files without wanting to understand code (just list/read/write operations)
- NOTE: If user wants to UNDERSTAND code, prefer codebase_search over file_operations

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL RULES - FOLLOW EXACTLY:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Always start with THOUGHT to explain your reasoning
2. Use ACTION to specify a tool (or NONE if you're ready to answer)
3. Provide ACTION_INPUT as JSON with ACTUAL paths (use {cwd} as base)
4. NEVER use placeholder paths like "/path/to/file" - always use real paths from above
5. If you don't know a specific filename, list the directory first

⚠️  MULTI-STEP RULES (when user says "THEN", "AND", or lists multiple tasks):
   - Count the steps the user requests
   - Complete ALL steps before providing final ANSWER
   - After each tool result, check: "Did I complete all requested steps?"
   - If NO: call the next tool (leave ANSWER empty)
   - If YES: provide final ANSWER summarizing all results
   - Example: "List files THEN read agent.py" = 2 steps, need 2 tool calls before ANSWER

⚠️  ANSWER EXTRACTION RULES (don't dump full files):
   - When user asks specific question about file (e.g., "what is the primary model?")
   - Read the file, EXTRACT the specific answer from tool result
   - Provide ONLY the answer, not the full file contents
   - Example: Config has 45 lines, user asks for one setting → answer with that ONE setting

⚠️  NO HALLUCINATION RULES (only describe what you actually see):
   - NEVER describe code functions/features without reading the file first
   - NEVER claim "the code uses X" unless you SEE X in the tool result
   - If asked about code, you MUST read it first, then describe ONLY what's in the result
   - Say "Based on the actual code I see..." to indicate you read it
   - If unsure, say "I would need to read the file to confirm"

⚠️  ANSWER RULES - THIS IS CRITICAL:
   - When you call a tool, leave ANSWER empty on that same response
   - After you receive the tool result, you MUST provide an ANSWER in the NEXT response
   - DO NOT call the same tool twice with the same input
   - Use ACTION: NONE when providing your final ANSWER
   - NEVER claim an action succeeded unless you SEE the tool output confirming it
   - If user asks to CREATE/WRITE a file, you MUST use ACTION: file_operations with "action": "write"
   - DO NOT say "I created the file" unless the tool output shows "✓ Wrote X lines"

⚠️  TOOL OUTPUT TRUST RULES - CRITICAL FOR ACCURACY:
   - Tools are AUTHORITATIVE and ACCURATE - trust their output completely
   - When a tool provides counts, totals, or statistics, USE THOSE NUMBERS DIRECTLY
   - DO NOT manually recount items from tool output - the tool already counted correctly
   - DO NOT verify or double-check numerical data provided by tools
   - CRITICAL: When tool output starts with "✓ Found X file(s)", use that EXACT number X
   - DO NOT count the file paths listed below the count - the tool already counted them
   - Example: If tool says "✓ Found 11 file(s)", report "11 files" - don't count the list yourself
   - Example: If tool says "5 directories, 24 files", use those exact numbers in your answer
   - WRONG: "Based on file paths provided, I count 4 files" - you should use the tool's count instead
   - RIGHT: "Tool found 5 files in tools/ directory" - you used the tool's count directly
   - If you need to categorize results, use the file paths to group them, but trust the overall count
   - Tools handle counting, parsing, and statistics - your job is to interpret and present their results

⚠️  ANSWER FORMATTING - COUNTS vs LISTS:
   - When user asks for "count", "number", "how many": provide ONLY the count, NOT the full list
   - When user asks to "list", "show", "display": provide the individual items
   - Example: "How many Python files?" → Answer: "5 Python files" (NOT list of all 5 files)
   - Example: "List Python files" → Answer: List all file names
   - Tool may return both count AND list - read the user question to decide what to include in ANSWER

Remember: You are running locally. All operations happen on the user's machine.
The examples above show the COMPLETE flow - notice how ANSWER is provided AFTER receiving tool results."""

    def _parse_agent_output(self, output: str) -> Dict[str, str]:
        """Parse agent output into structured format.

        Expected format:
            THOUGHT: ...
            ACTION: tool_name or NONE
            ACTION_INPUT: ...
            ANSWER: ...

        Args:
            output: Raw LLM output

        Returns:
            Dictionary with thought, action, action_input, answer

        Raises:
            AgentParsingError: If output format is invalid
        """
        try:
            parsed = {
                "thought": "",
                "action": "NONE",
                "action_input": "",
                "answer": ""
            }

            # Extract THOUGHT
            thought_match = re.search(r'THOUGHT:\s*(.+?)(?=\nACTION:|$)', output, re.DOTALL)
            if thought_match:
                parsed["thought"] = thought_match.group(1).strip()

            # Extract ACTION
            action_match = re.search(r'ACTION:\s*(\S+)', output)
            if action_match:
                parsed["action"] = action_match.group(1).strip()

            # Extract ACTION_INPUT
            input_match = re.search(r'ACTION_INPUT:\s*(.+?)(?=\nANSWER:|$)', output, re.DOTALL)
            if input_match:
                parsed["action_input"] = input_match.group(1).strip()

            # Extract ANSWER
            answer_match = re.search(r'ANSWER:\s*(.+?)$', output, re.DOTALL)
            if answer_match:
                parsed["answer"] = answer_match.group(1).strip()

            return parsed

        except Exception as e:
            raise AgentParsingError(f"Failed to parse agent output: {e}") from e

    def _reasoning_node(self, state: AgentState) -> AgentState:
        """Reasoning node: Agent thinks about what to do.

        Args:
            state: Current agent state

        Returns:
            Updated state with new thought and action decision
        """
        try:
            # Check iteration limit
            if state["iteration"] >= self.max_iterations:
                if self.verbose:
                    print(f"\n⚠ Reached max iterations ({self.max_iterations})")

                state["finished"] = True
                state["final_answer"] = "I've reached the maximum number of reasoning steps. Please try rephrasing your question or breaking it into smaller parts."
                return state

            # Build prompt with system message, conversation context, and current state
            conversation_context = self._build_conversation_context()
            state_context = self._build_state_context(state)

            # Check if we have recent tool results to show
            recent_tool_result = ""
            if state["tool_calls"] and state["tool_calls"][-1]["output"]:
                tool_output = state["tool_calls"][-1]["output"]
                # Count how many steps the user asked for (look for THEN, AND, comma-separated)
                user_query = state['messages'][-1] if state['messages'] else ''
                step_keywords = user_query.lower().count(' then ') + user_query.lower().count(' and then ')
                total_steps_needed = step_keywords + 1  # +1 for the first step
                steps_completed = len([tc for tc in state["tool_calls"] if tc["output"] is not None])

                if steps_completed < total_steps_needed:
                    instruction = f"User asked for {total_steps_needed} steps. You completed {steps_completed}. Call the NEXT tool now (leave ANSWER empty)."
                else:
                    instruction = "You completed ALL steps. Provide your final ANSWER now with ACTION: NONE."

                recent_tool_result = f"""

⚠️ ⚠️ ⚠️ CRITICAL - READ THIS FIRST ⚠️ ⚠️ ⚠️
{instruction}

Tool Result:
{tool_output}"""

            # Detect if we're potentially looping (same tool called multiple times)
            loop_warning = ""
            if len(state["tool_calls"]) >= 2:
                last_call = state["tool_calls"][-1]
                second_last_call = state["tool_calls"][-2]

                if (last_call["tool_name"] == second_last_call["tool_name"] and
                    last_call["input"] == second_last_call["input"]):
                    loop_warning = f"""
⚠️ WARNING: You just called {last_call['tool_name']} with the SAME input twice!
You already have the result. DO NOT call this tool again.
You MUST provide an ANSWER now based on the tool result you received."""

            prompt = f"""{self._get_system_prompt()}

{conversation_context}

{state_context}{recent_tool_result}

{loop_warning}

User Query: {state['messages'][-1] if state['messages'] else 'No query'}

Now, think step by step and respond with THOUGHT, ACTION, ACTION_INPUT, and ANSWER.

CRITICAL RULES:
1. If you just received a tool result above, you MUST provide an ANSWER based on that result
2. DO NOT call the same tool twice in a row with the same input
3. After getting a file's contents or other tool result, immediately provide your ANSWER
4. Only use ACTION: NONE when you're ready to give the final ANSWER"""

            # Get LLM response
            llm = self.model_manager.get_llm()
            response = llm.invoke(prompt)

            # Parse response
            parsed = self._parse_agent_output(response)

            # Validate parsed output - ensure non-empty fields
            if not parsed["thought"]:
                parsed["thought"] = "Continuing with the task"

            # Add thought to state
            state["thoughts"].append(parsed["thought"])

            if self.verbose:
                print(f"\n💭 THOUGHT: {parsed['thought']}")
                print(f"🎯 ACTION: {parsed['action']}")
                if parsed['action_input']:
                    print(f"📥 INPUT: {parsed['action_input'][:100]}...")

            # LOOP DETECTION: Check if agent is trying to call the same tool again
            if parsed["action"] != "NONE" and len(state["tool_calls"]) >= 1:
                last_successful_call = state["tool_calls"][-1]

                # If trying to repeat the exact same call, force an answer
                if (parsed["action"] == last_successful_call["tool_name"] and
                    parsed["action_input"] == last_successful_call["input"] and
                    last_successful_call["output"] is not None):

                    if self.verbose:
                        print(f"\n🚫 LOOP DETECTED: Agent tried to repeat the same tool call")
                        print(f"   Forcing answer based on existing result...")

                    # Extract the tool result
                    tool_result = last_successful_call["output"]

                    # Check if this looks like a raw file dump (long content with file markers)
                    if (tool_result.startswith("✓ Read") and len(tool_result) > 500):
                        # Large file read - don't dump it, provide a summary instead
                        user_query = state['messages'][-1] if state['messages'] else ''
                        state["final_answer"] = f"I read the file but couldn't extract a proper answer to your question: '{user_query}'. The file is too large to process in my current context. Please ask a more specific question or request a search for specific information."
                    else:
                        # Small result - ok to use directly
                        state["final_answer"] = tool_result

                    state["finished"] = True
                    return state

            # Store action for tool execution
            if parsed["action"] != "NONE" and parsed["action"] in self.tool_map:
                state["tool_calls"].append({
                    "tool_name": parsed["action"],
                    "input": parsed["action_input"],
                    "output": None  # Will be filled by tool execution node
                })

            # Check if agent provided final answer
            # Only mark finished if there's an answer AND no pending tool calls
            if parsed["answer"]:
                # Check if there are pending tool calls
                pending_tools = [tc for tc in state["tool_calls"] if tc["output"] is None]
                if not pending_tools:
                    # No pending tools, so this is the final answer
                    state["finished"] = True
                    state["final_answer"] = parsed["answer"]
                # else: there are pending tools, so don't finish yet - let them execute first

            state["iteration"] += 1

            return state

        except Exception as e:
            if self.logger:
                self.logger.error(f"Reasoning node error: {e}")

            state["finished"] = True
            state["final_answer"] = f"I encountered an error while reasoning: {str(e)}"
            return state

    def _tool_execution_node(self, state: AgentState) -> AgentState:
        """Tool execution node: Execute the selected tool.

        Args:
            state: Current agent state

        Returns:
            Updated state with tool results
        """
        try:
            # Get the most recent tool call that hasn't been executed
            pending_calls = [tc for tc in state["tool_calls"] if tc["output"] is None]

            if not pending_calls:
                return state

            tool_call = pending_calls[-1]
            tool_name = tool_call["tool_name"]
            tool_input = tool_call["input"]

            if self.verbose:
                print(f"\n🔧 Executing: {tool_name}")

            # Get tool
            tool = self.tool_map.get(tool_name)
            if not tool:
                error_msg = f"Tool '{tool_name}' not found"
                tool_call["output"] = f"✗ {error_msg}"
                if self.logger:
                    self.logger.warning(error_msg)
                return state

            # Execute tool
            try:
                result = tool._run(tool_input)
                tool_call["output"] = result

                if self.verbose:
                    print(f"✓ Result: {result[:200]}..." if len(result) > 200 else f"✓ Result: {result}")

                # Log to conversation
                self.conversation.add_tool_message(
                    result,
                    tool_name=tool_name,
                    action=tool_call.get("action", "execute")
                )

            except Exception as e:
                error_msg = f"Tool execution failed: {str(e)}"
                tool_call["output"] = f"✗ {error_msg}"
                if self.logger:
                    self.logger.error(error_msg)

            return state

        except Exception as e:
            if self.logger:
                self.logger.error(f"Tool execution node error: {e}")

            # Mark last tool call as failed
            if state["tool_calls"]:
                state["tool_calls"][-1]["output"] = f"✗ Error: {str(e)}"

            return state

    def _observation_node(self, state: AgentState) -> AgentState:
        """Observation node: Process tool results.

        Args:
            state: Current agent state

        Returns:
            Updated state after observing tool results
        """
        try:
            # Get the most recent tool call
            if not state["tool_calls"]:
                return state

            tool_call = state["tool_calls"][-1]

            if self.verbose:
                print(f"\n👁 Observing results from {tool_call['tool_name']}...")

            # Tool result is already in tool_call["output"]
            # Agent will see it in the next reasoning step

            return state

        except Exception as e:
            if self.logger:
                self.logger.error(f"Observation node error: {e}")
            return state

    def _should_execute_tool(self, state: AgentState) -> str:
        """Decision: Should we execute a tool?

        Args:
            state: Current agent state

        Returns:
            "tool_execution" if there's a pending tool call, "end" otherwise
        """
        # Check if finished
        if state["finished"]:
            return "end"

        # Check if there's a pending tool call
        pending = [tc for tc in state["tool_calls"] if tc["output"] is None]
        if pending:
            return "tool_execution"

        return "end"

    def _should_continue(self, state: AgentState) -> str:
        """Decision: Should we continue reasoning?

        Args:
            state: Current agent state

        Returns:
            "reasoning" to continue, "end" if finished
        """
        if state["finished"] or state["iteration"] >= self.max_iterations:
            return "end"

        return "reasoning"

    def _build_conversation_context(self) -> str:
        """Build conversation context from recent messages.

        Returns:
            Formatted conversation history
        """
        messages = self.conversation.get_messages(limit=5)
        if not messages:
            return ""

        context_parts = ["Recent Conversation:"]
        for msg in messages:
            role = msg['role'].upper()
            content = msg['content'][:200]  # Limit length
            if len(msg['content']) > 200:
                content += "..."
            context_parts.append(f"{role}: {content}")

        return "\n".join(context_parts)

    def _build_state_context(self, state: AgentState) -> str:
        """Build context from current agent state.

        Args:
            state: Current agent state

        Returns:
            Formatted state context
        """
        parts = []

        if state["thoughts"]:
            parts.append("Previous Thoughts:")
            for i, thought in enumerate(state["thoughts"][-3:], 1):  # Last 3 thoughts
                parts.append(f"{i}. {thought}")

        if state["tool_calls"]:
            parts.append("\nPrevious Tool Calls:")
            for tc in state["tool_calls"][-3:]:  # Last 3 calls
                # Don't truncate tool output - agent needs full context to reason correctly
                output = tc['output'] if tc['output'] else 'pending'
                parts.append(f"- {tc['tool_name']}: {output}")

        if parts:
            return "\n".join(parts)

        return ""

    def run(self, user_input: str) -> Dict[str, Any]:
        """Run the agent with user input.

        Args:
            user_input: User's question or command

        Returns:
            Dictionary with output, thoughts, tool_calls, success, and error (if any)

        Example:
            >>> result = agent.run("List files in /path/to/dir")
            >>> print(result['output'])
            >>> print(result['thoughts'])
        """
        try:
            # Add user message to conversation
            self.conversation.add_user_message(user_input)

            # Initialize state
            initial_state: AgentState = {
                "messages": [user_input],
                "thoughts": [],
                "tool_calls": [],
                "iteration": 0,
                "finished": False,
                "final_answer": None
            }

            if self.verbose:
                print(f"\n{'='*60}")
                print(f"🤖 Meton Agent Starting")
                print(f"Query: {user_input}")
                print(f"{'='*60}")

            # Run graph with custom recursion limit
            final_state = self.graph.invoke(
                initial_state,
                config={"recursion_limit": self.recursion_limit}
            )

            # Extract result
            output = final_state.get("final_answer", "No answer provided")

            # Ensure output is not None or empty
            if not output or output.strip() == "":
                # If we have tool results, use the last one
                if final_state["tool_calls"]:
                    last_result = final_state["tool_calls"][-1].get("output", "")
                    if last_result:
                        output = f"Task completed. {last_result}"
                    else:
                        output = "Task completed successfully."
                else:
                    output = "Task completed."

            # Check if output is just a tool result dump (starts with tool result markers)
            # This indicates the LLM failed to extract/summarize the answer
            if output.startswith("✓ Read") or output.startswith("✓ Contents") or output.startswith("✓ Wrote"):
                # The agent dumped the tool output instead of answering the question
                # Check if there's a user query that asks a specific question
                user_query = final_state['messages'][-1] if final_state['messages'] else ''
                if any(keyword in user_query.lower() for keyword in ['what', 'how', 'why', 'explain', 'tell me']):
                    # User asked a question but got a file dump - provide a helpful message
                    output = "I retrieved the file contents but didn't properly analyze them to answer your question. Please try asking the question again, or ask me to search for specific information within the file."

            # Add assistant response to conversation
            metadata = {
                "thoughts": len(final_state["thoughts"]),
                "tool_calls": len(final_state["tool_calls"]),
                "iterations": final_state["iteration"],
                "model": self.model_manager.current_model
            }
            self.conversation.add_assistant_message(output, metadata)

            if self.verbose:
                print(f"\n{'='*60}")
                print(f"✅ Agent Finished")
                print(f"Iterations: {final_state['iteration']}")
                print(f"{'='*60}\n")

            return {
                "output": output,
                "thoughts": final_state["thoughts"],
                "tool_calls": final_state["tool_calls"],
                "iterations": final_state["iteration"],
                "success": True
            }

        except Exception as e:
            error_msg = f"Agent execution failed: {str(e)}"

            if self.logger:
                self.logger.error(error_msg)

            self.conversation.add_assistant_message(
                f"I encountered an error: {error_msg}",
                {"error": True}
            )

            if self.verbose:
                print(f"\n❌ Error: {error_msg}\n")

            return {
                "output": error_msg,
                "thoughts": [],
                "tool_calls": [],
                "iterations": 0,
                "success": False,
                "error": str(e)
            }

    def get_tool_names(self) -> List[str]:
        """Get names of available tools.

        Returns:
            List of tool names

        Example:
            >>> tools = agent.get_tool_names()
            >>> print(tools)
            ['file_operations']
        """
        return list(self.tool_map.keys())

    def add_tool(self, tool: BaseTool) -> None:
        """Add a tool to the agent.

        Args:
            tool: Tool to add

        Example:
            >>> new_tool = MyCustomTool()
            >>> agent.add_tool(new_tool)
        """
        self.tools.append(tool)
        self.tool_map[tool.name] = tool

        if self.logger:
            self.logger.info(f"Added tool: {tool.name}")

    def remove_tool(self, tool_name: str) -> bool:
        """Remove a tool from the agent.

        Args:
            tool_name: Name of tool to remove

        Returns:
            True if tool was removed, False if not found

        Example:
            >>> agent.remove_tool("file_operations")
            True
        """
        if tool_name in self.tool_map:
            del self.tool_map[tool_name]
            self.tools = [t for t in self.tools if t.name != tool_name]

            if self.logger:
                self.logger.info(f"Removed tool: {tool_name}")

            return True

        return False

    def get_info(self) -> Dict[str, Any]:
        """Get agent information.

        Returns:
            Dictionary with agent metadata

        Example:
            >>> info = agent.get_info()
            >>> print(info['model'])
            >>> print(info['tools'])
        """
        return {
            "model": self.model_manager.current_model,
            "tools": self.get_tool_names(),
            "max_iterations": self.max_iterations,
            "verbose": self.verbose,
            "conversation_messages": self.conversation.get_message_count()
        }
