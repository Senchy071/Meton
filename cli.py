#!/usr/bin/env python3
"""Interactive CLI for Meton coding assistant.

This module provides a beautiful, interactive command-line interface using Rich.
It integrates the Model Manager, Conversation Manager, Agent, and Tools.
"""

import sys
import signal
import os
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn

from core.config import Config
from core.models import ModelManager
from core.conversation import ConversationManager
from core.agent import MetonAgent
from tools.file_ops import FileOperationsTool
from tools.code_executor import CodeExecutorTool
from tools.web_search import WebSearchTool
from tools.codebase_search import CodebaseSearchTool
from utils.logger import setup_logger


class MetonCLI:
    """Interactive CLI for Meton coding assistant."""

    def __init__(self):
        """Initialize CLI."""
        self.console = Console()
        self.config = Config()
        self.logger = setup_logger(name="meton_cli", console_output=False)
        
        # Components (initialized later)
        self.model_manager: Optional[ModelManager] = None
        self.conversation: Optional[ConversationManager] = None
        self.agent: Optional[MetonAgent] = None

        # Tools (for control)
        self.file_tool: Optional[FileOperationsTool] = None
        self.code_tool: Optional[CodeExecutorTool] = None
        self.web_tool: Optional[WebSearchTool] = None
        self.codebase_search_tool: Optional[CodebaseSearchTool] = None

        # CLI state
        self.running = True
        self.verbose = False

        # RAG state (for index management)
        self.last_indexed_path: Optional[str] = None
        self.last_indexed_time: Optional[datetime] = None
        self.indexed_files_count: int = 0
        self.indexed_chunks_count: int = 0

        # Setup signal handler
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully."""
        self.console.print("\n\n[yellow]Interrupted by user[/yellow]")
        self.shutdown()
        sys.exit(0)

    def initialize(self) -> bool:
        """Initialize all components."""
        try:
            self.console.print("[cyan]🔧 Initializing Meton...[/cyan]")
            
            # Initialize Model Manager
            self.console.print("  [dim]Loading model manager...[/dim]")
            self.model_manager = ModelManager(self.config, logger=self.logger)
            
            # Initialize Conversation Manager
            self.console.print("  [dim]Loading conversation manager...[/dim]")
            self.conversation = ConversationManager(self.config, logger=self.logger)
            
            # Initialize Tools
            self.console.print("  [dim]Loading tools...[/dim]")
            self.file_tool = FileOperationsTool(self.config)
            self.code_tool = CodeExecutorTool(self.config)
            self.web_tool = WebSearchTool(self.config)
            self.codebase_search_tool = CodebaseSearchTool(self.config)

            # Initialize Agent
            self.console.print("  [dim]Loading agent...[/dim]")
            self.agent = MetonAgent(
                config=self.config,
                model_manager=self.model_manager,
                conversation=self.conversation,
                tools=[self.file_tool, self.code_tool, self.web_tool, self.codebase_search_tool],
                verbose=self.verbose
            )
            
            self.console.print("[green]✓ Initialization complete![/green]\n")
            return True
            
        except Exception as e:
            self.console.print(f"[red]❌ Initialization failed: {str(e)}[/red]")
            if self.logger:
                self.logger.error(f"Initialization error: {e}")
            return False

    def display_welcome(self):
        """Display welcome banner."""
        banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║    METON - Local Coding Assistant                                            ║
║             by Senad Arifhodzic & Claude                                     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        self.console.print(banner, style="bold magenta")
        
        model_name = self.model_manager.current_model if self.model_manager else "Unknown"
        tools = self.agent.get_tool_names() if self.agent else []
        tools_str = ", ".join(tools) if tools else "None"
        
        info = f"""
[cyan]Model:[/cyan]    {model_name}
[cyan]Tools:[/cyan]    {tools_str}
[cyan]Verbose:[/cyan]  {'ON' if self.verbose else 'OFF'}

[dim]Type /help for commands or just start chatting![/dim]
"""
        self.console.print(info)

    def display_help(self):
        """Display help information."""
        table = Table(title="Available Commands", show_header=True, header_style="bold cyan")
        table.add_column("Command", style="yellow", width=25)
        table.add_column("Description", style="white")

        table.add_row("/help, /h", "Show this help message")
        table.add_row("/clear, /c", "Clear conversation history")
        table.add_row("/model <name>", "Switch model (primary/fallback/quick)")
        table.add_row("/models", "List available models")
        table.add_row("/status", "Show current status")
        table.add_row("/verbose on/off", "Toggle verbose mode")
        table.add_row("/save", "Save conversation")
        table.add_row("/history", "Show conversation history")
        table.add_row("/search <keyword>", "Search conversation history")
        table.add_row("/reload", "Reload configuration")
        table.add_row("/tools", "List available tools with status")
        table.add_row("/web [on|off|status]", "Control web search tool")

        # Add RAG commands section
        table.add_section()
        table.add_row("[bold cyan]RAG & Code Search:[/]", "")
        table.add_row("/index [path]", "Index a codebase for semantic search")
        table.add_row("/index status", "Show indexing status and statistics")
        table.add_row("/index clear", "Clear the current index")
        table.add_row("/index refresh", "Re-index the last indexed path")
        table.add_row("/csearch <query>", "Test semantic code search")

        # Add memory commands section
        table.add_section()
        table.add_row("[bold cyan]Long-Term Memory:[/]", "")
        table.add_row("/memory stats", "Show memory statistics")
        table.add_row("/memory search <query>", "Search memories")
        table.add_row("/memory add <content>", "Manually add memory")
        table.add_row("/memory export [format]", "Export memories (json/csv)")
        table.add_row("/memory consolidate", "Merge similar memories")
        table.add_row("/memory decay", "Apply decay to old memories")

        table.add_section()
        table.add_row("/exit, /quit, /q", "Exit Meton")

        self.console.print()
        self.console.print(table)
        self.console.print()

    def display_status(self):
        """Display current status."""
        if not self.agent:
            self.console.print("[red]❌ Agent not initialized[/red]")
            return

        info = self.agent.get_info()
        session_id = self.conversation.get_session_id()[:16] + "..." if self.conversation else "Unknown"

        # Base status
        status_text = f"""[cyan]Model:[/cyan]        {info['model']}
[cyan]Session:[/cyan]      {session_id}
[cyan]Messages:[/cyan]     {info['conversation_messages']}
[cyan]Tools:[/cyan]        {', '.join(info['tools'])}
[cyan]Max Iter:[/cyan]     {info['max_iterations']}
[cyan]Verbose:[/cyan]      {'ON' if info['verbose'] else 'OFF'}"""

        # Add RAG status if available
        if self.codebase_search_tool:
            rag_enabled = self.config.config.rag.enabled
            tool_enabled = self.codebase_search_tool.is_enabled()
            status_emoji = "✅" if (rag_enabled and tool_enabled) else "❌"

            rag_status = f"\n\n[bold cyan]RAG:[/bold cyan]\n"
            rag_status += f"[cyan]Status:[/cyan]       {status_emoji} {'Enabled' if rag_enabled else 'Disabled'}\n"
            rag_status += f"[cyan]Tool:[/cyan]         {status_emoji} {'Enabled' if tool_enabled else 'Disabled'}"

            if self.indexed_files_count > 0:
                rag_status += f"\n[cyan]Indexed:[/cyan]      {self.indexed_files_count} files, {self.indexed_chunks_count} chunks"
                if self.last_indexed_time:
                    time_str = self.last_indexed_time.strftime("%Y-%m-%d %H:%M:%S")
                    rag_status += f"\n[cyan]Last indexed:[/cyan] {time_str}"
                if self.last_indexed_path:
                    # Truncate path if too long
                    path_str = self.last_indexed_path
                    if len(path_str) > 40:
                        path_str = "..." + path_str[-37:]
                    rag_status += f"\n[cyan]Path:[/cyan]         {path_str}"

            status_text += rag_status

        panel = Panel(status_text, title="Current Status", border_style="cyan", padding=(1, 2))
        self.console.print()
        self.console.print(panel)
        self.console.print()

    def list_models(self):
        """List available models."""
        if not self.model_manager:
            self.console.print("[red]❌ Model manager not initialized[/red]")
            return
        
        try:
            models = self.model_manager.list_available_models()
            current = self.model_manager.current_model
            
            table = Table(title="Available Models", show_header=True, header_style="bold cyan")
            table.add_column("Model Name", style="white")
            table.add_column("Status", style="green")
            
            for model in models:
                status = "✓ Current" if model == current else ""
                table.add_row(model, status)
            
            table.add_section()
            table.add_row("[dim]Aliases:[/dim]", "")
            table.add_row("  primary", f"→ {self.config.config.models.primary_model}")
            table.add_row("  fallback", f"→ {self.config.config.models.fallback_model}")
            table.add_row("  quick", f"→ {self.config.config.models.quick_model}")
            
            self.console.print()
            self.console.print(table)
            self.console.print()
            
        except Exception as e:
            self.console.print(f"[red]❌ Failed to list models: {str(e)}[/red]")

    def handle_command(self, command: str) -> bool:
        """Handle special commands."""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        if cmd in ['/help', '/h']:
            self.display_help()
        elif cmd in ['/status']:
            self.display_status()
        elif cmd in ['/models']:
            self.list_models()
        elif cmd in ['/tools']:
            self.list_tools()
        elif cmd == '/web':
            if args:
                self.control_web_search(args[0])
            else:
                self.show_web_status()
        elif cmd == '/model':
            if args:
                self.switch_model(args[0])
            else:
                self.console.print("[yellow]Usage: /model <name>[/yellow]")
        elif cmd == '/verbose':
            if args:
                self.toggle_verbose(args[0])
            else:
                self.toggle_verbose()
        elif cmd in ['/clear', '/c']:
            self.clear_conversation()
        elif cmd == '/save':
            self.save_conversation()
        elif cmd == '/history':
            self.show_history()
        elif cmd == '/search':
            if args:
                self.search_conversation(args[0])
            else:
                self.console.print("[yellow]Usage: /search <keyword>[/yellow]")
        elif cmd == '/reload':
            self.reload_config()
        elif cmd == '/index':
            # Handle /index subcommands
            if args:
                arg = args[0]
                if arg == 'status' or arg == 'info':
                    self.index_status()
                elif arg == 'clear' or arg == 'reset':
                    self.index_clear()
                elif arg == 'refresh' or arg == 'reload':
                    self.index_refresh()
                else:
                    # Assume it's a path
                    self.index_codebase(arg)
            else:
                # No args - index current directory
                self.index_codebase(os.getcwd())
        elif cmd == '/csearch':
            # Code search command
            if args:
                self.search_codebase(args[0])
            else:
                self.console.print("[yellow]Usage: /csearch <query>[/yellow]")
        elif cmd == '/memory':
            # Memory management command
            if args:
                self.handle_memory_command(args[0])
            else:
                self.console.print("[yellow]Usage: /memory [stats|search|add|export|consolidate|decay][/yellow]")
        elif cmd in ['/exit', '/quit', '/q']:
            self.exit_cli()
        else:
            self.console.print(f"[red]❌ Unknown command: {cmd}[/red]")
            self.console.print("[dim]Type /help for available commands[/dim]")

        return True

    def list_tools(self):
        """List available tools with status."""
        if not self.agent:
            self.console.print("[red]❌ Agent not initialized[/red]")
            return

        table = Table(title="Available Tools", show_header=True, header_style="bold cyan")
        table.add_column("Tool Name", style="yellow", width=20)
        table.add_column("Status", style="white", width=10)
        table.add_column("Description", style="white")

        for tool in self.agent.tools:
            # Get tool status
            if hasattr(tool, 'is_enabled'):
                enabled = tool.is_enabled()
                status = "✅ enabled" if enabled else "❌ disabled"
            else:
                status = "✅ enabled"

            desc = tool.description.split('\n')[0]
            if len(desc) > 50:
                desc = desc[:47] + "..."
            table.add_row(tool.name, status, desc)

        self.console.print()
        self.console.print(table)
        self.console.print()

    def show_web_status(self):
        """Show web search status."""
        if not self.web_tool:
            self.console.print("[red]❌ Web search tool not initialized[/red]")
            return

        enabled = self.web_tool.is_enabled()
        status_text = "[green]enabled[/green]" if enabled else "[red]disabled[/red]"
        self.console.print(f"Web search: {status_text}")

    def control_web_search(self, action: str):
        """Control web search tool (enable/disable)."""
        if not self.web_tool:
            self.console.print("[red]❌ Web search tool not initialized[/red]")
            return

        action_lower = action.lower()

        if action_lower in ['on', 'enable']:
            # Update tool runtime flag, config object, AND persist to file
            self.web_tool.enable()
            self.config.config.tools.web_search.enabled = True
            self.config.save()  # Persist change to config.yaml
            self.console.print("[green]✅ Web search enabled (persisted to config.yaml)[/green]")
        elif action_lower in ['off', 'disable']:
            # Update tool runtime flag, config object, AND persist to file
            self.web_tool.disable()
            self.config.config.tools.web_search.enabled = False
            self.config.save()  # Persist change to config.yaml
            self.console.print("[green]✅ Web search disabled (persisted to config.yaml)[/green]")
        elif action_lower == 'status':
            self.show_web_status()
        else:
            self.console.print(f"[yellow]Unknown action: {action}[/yellow]")
            self.console.print("[dim]Usage: /web [on|off|enable|disable|status][/dim]")

    def switch_model(self, model_name: str):
        """Switch to a different model."""
        if not self.model_manager:
            self.console.print("[red]❌ Model manager not initialized[/red]")
            return
        
        try:
            full_name = self.model_manager.resolve_alias(model_name)
            available = self.model_manager.list_available_models()
            
            if full_name not in available:
                self.console.print(f"[red]❌ Model '{full_name}' not found[/red]")
                self.console.print("[dim]Use /models to see available models[/dim]")
                return
            
            with self.console.status(f"[cyan]Switching to {full_name}...[/cyan]", spinner="dots"):
                self.model_manager.switch_model(full_name)
            
            self.console.print(f"[green]✓ Switched to model: {full_name}[/green]")
            
        except Exception as e:
            self.console.print(f"[red]❌ Failed to switch model: {str(e)}[/red]")

    def toggle_verbose(self, arg: str = None):
        """Toggle verbose mode."""
        if arg:
            if arg.lower() == "on":
                self.verbose = True
                self.agent.verbose = True
                self.console.print("[green]✓ Verbose mode ON[/green]")
            elif arg.lower() == "off":
                self.verbose = False
                self.agent.verbose = False
                self.console.print("[green]✓ Verbose mode OFF[/green]")
            else:
                self.console.print("[yellow]Usage: /verbose on|off[/yellow]")
        else:
            self.verbose = not self.verbose
            self.agent.verbose = self.verbose
            status = "ON" if self.verbose else "OFF"
            self.console.print(f"[green]✓ Verbose mode {status}[/green]")

    def clear_conversation(self):
        """Clear conversation history."""
        if not self.conversation:
            self.console.print("[red]❌ Conversation manager not initialized[/red]")
            return
        
        confirm = Prompt.ask("\n[yellow]Clear conversation history?[/yellow]", choices=["y", "n"], default="n")
        
        if confirm == "y":
            self.conversation.clear()
            self.console.print("[green]✓ Conversation history cleared[/green]")
        else:
            self.console.print("[dim]Cancelled[/dim]")

    def save_conversation(self):
        """Save conversation to disk."""
        if not self.conversation:
            self.console.print("[red]❌ Conversation manager not initialized[/red]")
            return
        
        try:
            with self.console.status("[cyan]💾 Saving conversation...[/cyan]", spinner="dots"):
                saved_path = self.conversation.save()
            
            self.console.print(f"[green]✓ Conversation saved: {saved_path.name}[/green]")
            
        except Exception as e:
            self.console.print(f"[red]❌ Failed to save: {str(e)}[/red]")

    def show_history(self):
        """Show conversation history."""
        if not self.conversation:
            self.console.print("[red]❌ Conversation manager not initialized[/red]")
            return
        
        messages = self.conversation.get_messages()
        
        if not messages:
            self.console.print("[yellow]No conversation history yet[/yellow]")
            return
        
        self.console.print()
        self.console.print("[bold cyan]Conversation History[/bold cyan]")
        self.console.print()
        
        for i, msg in enumerate(messages, 1):
            role = msg['role'].upper()
            content = msg['content'][:150]
            if len(msg['content']) > 150:
                content += "..."
            
            role_colors = {"USER": "cyan", "ASSISTANT": "green", "SYSTEM": "blue", "TOOL": "yellow"}
            color = role_colors.get(role, "white")
            
            self.console.print(f"[{color}]{i}. {role}:[/{color}] {content}")
        
        self.console.print()
        self.console.print(f"[dim]Total messages: {len(messages)}[/dim]")
        self.console.print()

    def search_conversation(self, keyword: str):
        """Search conversation history for keyword."""
        if not self.conversation:
            self.console.print("[red]❌ Conversation manager not initialized[/red]")
            return

        messages = self.conversation.get_messages()

        if not messages:
            self.console.print("[yellow]No conversation history to search[/yellow]")
            return

        # Case-insensitive search
        keyword_lower = keyword.lower()
        matches = []

        for i, msg in enumerate(messages, 1):
            if keyword_lower in msg['content'].lower():
                matches.append((i, msg))

        if not matches:
            self.console.print(f"[yellow]No matches found for '{keyword}'[/yellow]")
            return

        self.console.print()
        self.console.print(f"[bold cyan]Search Results for '{keyword}' ({len(matches)} matches)[/bold cyan]")
        self.console.print()

        for i, msg in matches:
            role = msg['role'].upper()
            content = msg['content']

            # Highlight the keyword
            highlighted = content.replace(keyword, f"[bold yellow]{keyword}[/bold yellow]")
            highlighted = highlighted.replace(keyword.capitalize(), f"[bold yellow]{keyword.capitalize()}[/bold yellow]")
            highlighted = highlighted.replace(keyword.upper(), f"[bold yellow]{keyword.upper()}[/bold yellow]")

            # Truncate if too long
            if len(content) > 200:
                # Try to show context around keyword
                keyword_pos = content.lower().find(keyword_lower)
                start = max(0, keyword_pos - 80)
                end = min(len(content), keyword_pos + 120)
                highlighted = "..." + content[start:end] + "..."
                highlighted = highlighted.replace(keyword, f"[bold yellow]{keyword}[/bold yellow]")

            role_colors = {"USER": "cyan", "ASSISTANT": "green", "SYSTEM": "blue", "TOOL": "yellow"}
            color = role_colors.get(role, "white")

            self.console.print(f"[{color}]{i}. {role}:[/{color}] {highlighted}")

        self.console.print()
        self.console.print(f"[dim]Total matches: {len(matches)}/{len(messages)} messages[/dim]")
        self.console.print()

    def reload_config(self):
        """Reload configuration from file."""
        try:
            with self.console.status("[cyan]🔄 Reloading configuration...[/cyan]", spinner="dots"):
                # Create new config instance
                new_config = Config()

                # Update config
                self.config = new_config

                # Update model manager with new config
                if self.model_manager:
                    self.model_manager.config = new_config

                # Update conversation manager with new config
                if self.conversation:
                    self.conversation.config = new_config

                # Update agent with new config
                if self.agent:
                    self.agent.config = new_config

            self.console.print("[green]✓ Configuration reloaded successfully[/green]")
            self.console.print("[dim]  Note: Model will switch on next query[/dim]")

        except Exception as e:
            self.console.print(f"[red]❌ Failed to reload config: {str(e)}[/red]")

    def process_query(self, query: str):
        """Process a user query through the agent."""
        if not self.agent:
            self.console.print("[red]❌ Agent not initialized[/red]")
            return
        
        try:
            with self.console.status("[cyan]🤔 Thinking...[/cyan]", spinner="dots"):
                result = self.agent.run(query)
            
            if result['success']:
                self.display_response(result['output'])
                
                if self.verbose and result.get('iterations', 0) > 0:
                    self.console.print(f"\n[dim]Iterations: {result['iterations']} | "
                                     f"Tool calls: {len(result.get('tool_calls', []))}[/dim]")
            else:
                self.console.print(f"[red]❌ Query failed: {result.get('error', 'Unknown error')}[/red]")
        
        except KeyboardInterrupt:
            self.console.print("\n[yellow]⚠ Query interrupted[/yellow]")
        except Exception as e:
            self.console.print(f"[red]❌ Error processing query: {str(e)}[/red]")

    def display_response(self, response: str):
        """Display agent's response with formatting."""
        self.console.print("\n[bold green]💬 Assistant:[/bold green]")
        
        if "```" in response:
            parts = response.split("```")
            for i, part in enumerate(parts):
                if i % 2 == 0:
                    if part.strip():
                        self.console.print(part.strip())
                else:
                    lines = part.split('\n', 1)
                    if len(lines) > 1:
                        lang = lines[0].strip()
                        code = lines[1].rstrip()
                        if lang and code:
                            try:
                                syntax = Syntax(code, lang, theme="monokai", line_numbers=False)
                                self.console.print()
                                self.console.print(syntax)
                                self.console.print()
                            except:
                                self.console.print(f"\n{code}\n")
        else:
            self.console.print(response)
        
        self.console.print()

    # ========== RAG & Index Management Commands ==========

    def index_codebase(self, path: str):
        """Index a codebase for semantic search."""
        if not self.codebase_search_tool:
            self.console.print("[red]❌ Codebase search tool not initialized[/red]")
            return

        # Validate path
        path = os.path.abspath(os.path.expanduser(path))
        if not os.path.exists(path):
            self.console.print(f"[red]❌ Path does not exist: {path}[/red]")
            return

        if not os.path.isdir(path):
            self.console.print(f"[red]❌ Path is not a directory: {path}[/red]")
            return

        # Check for Python files
        py_files = list(Path(path).rglob("*.py"))
        if not py_files:
            self.console.print(f"[yellow]⚠ Warning: No Python files found in {path}[/yellow]")
            response = Prompt.ask("Continue anyway?", choices=["y", "n"], default="n")
            if response.lower() != 'y':
                return

        try:
            start_time = datetime.now()

            self.console.print(f"\n[cyan]🔍 Indexing {path}...[/cyan]")
            self.console.print(f"[dim]Found {len(py_files)} Python files[/dim]\n")

            # Import RAG components
            from rag.embeddings import EmbeddingModel
            from rag.vector_store import VectorStore
            from rag.metadata_store import MetadataStore
            from rag.indexer import CodebaseIndexer

            # Initialize components
            embedder = EmbeddingModel()
            vector_store = VectorStore(dimension=self.config.config.rag.dimensions)
            metadata_store = MetadataStore(self.config.config.rag.metadata_path)

            indexer = CodebaseIndexer(
                embedder=embedder,
                vector_store=vector_store,
                metadata_store=metadata_store,
                verbose=False
            )

            # Index with progress display
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                console=self.console
            ) as progress:
                task = progress.add_task("Processing files...", total=len(py_files))

                # Index the codebase
                stats = indexer.index_directory(
                    dirpath=path,
                    recursive=True
                )

                # Update progress to 100%
                progress.update(task, completed=len(py_files))

            # Save the index
            index_path = os.path.join(self.config.config.rag.index_path, "faiss.index")
            os.makedirs(os.path.dirname(index_path), exist_ok=True)
            indexer.save(index_path)

            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()

            # Update state
            self.last_indexed_path = path
            self.last_indexed_time = datetime.now()
            self.indexed_files_count = stats['files_processed']
            self.indexed_chunks_count = stats['chunks_created']

            # Enable RAG and tool
            self.config.config.rag.enabled = True
            object.__setattr__(self.codebase_search_tool, '_rag_enabled', True)
            self.codebase_search_tool.enable()

            # Update config and persist
            self.config.config.tools.codebase_search.enabled = True
            self.config.save()

            # Display success
            self.console.print(f"\n[green]✅ Complete! Indexed {stats['files_processed']} files, {stats['chunks_created']} chunks in {duration:.1f}s[/green]")
            self.console.print("[dim]RAG enabled ✅[/dim]")
            self.console.print("[dim]Codebase search enabled ✅[/dim]\n")

        except Exception as e:
            self.console.print(f"\n[red]❌ Indexing failed: {str(e)}[/red]")
            if self.logger:
                self.logger.error(f"Indexing error: {e}")

    def index_status(self):
        """Show current indexing status."""
        if not self.codebase_search_tool:
            self.console.print("[red]❌ Codebase search tool not initialized[/red]")
            return

        rag_enabled = self.config.config.rag.enabled
        tool_enabled = self.codebase_search_tool.is_enabled()
        status_emoji = "✅" if (rag_enabled and tool_enabled) else "❌"

        status_text = f"""[cyan]RAG Status:[/cyan]       {status_emoji} {'Enabled' if rag_enabled else 'Disabled'}
[cyan]Tool Status:[/cyan]      {status_emoji} {'Enabled' if tool_enabled else 'Disabled'}"""

        if self.indexed_files_count > 0:
            status_text += f"\n[cyan]Indexed Files:[/cyan]    {self.indexed_files_count} files"
            status_text += f"\n[cyan]Indexed Chunks:[/cyan]   {self.indexed_chunks_count} chunks"

            if self.last_indexed_time:
                time_str = self.last_indexed_time.strftime("%Y-%m-%d %H:%M:%S")
                status_text += f"\n[cyan]Last Indexed:[/cyan]     {time_str}"

            if self.last_indexed_path:
                status_text += f"\n[cyan]Path:[/cyan]             {self.last_indexed_path}"

            # Check index size
            index_path = os.path.join(self.config.config.rag.index_path, "faiss.index")
            if os.path.exists(index_path):
                size_mb = os.path.getsize(index_path) / (1024 * 1024)
                status_text += f"\n[cyan]Index Size:[/cyan]       {size_mb:.2f} MB"
        else:
            status_text += "\n\n[yellow]No codebase has been indexed yet[/yellow]"
            status_text += "\n[dim]Use /index <path> to index a codebase[/dim]"

        panel = Panel(status_text, title="📊 RAG Index Status", border_style="cyan", padding=(1, 2))
        self.console.print()
        self.console.print(panel)
        self.console.print()

    def index_clear(self):
        """Clear the current index."""
        if not self.codebase_search_tool:
            self.console.print("[red]❌ Codebase search tool not initialized[/red]")
            return

        if self.indexed_chunks_count == 0:
            self.console.print("[yellow]No index to clear[/yellow]")
            return

        # Confirm
        self.console.print(f"\n[yellow]⚠ This will delete {self.indexed_chunks_count} chunks from the index[/yellow]")
        response = Prompt.ask("Are you sure?", choices=["y", "n"], default="n")

        if response.lower() != 'y':
            self.console.print("[dim]Cancelled[/dim]")
            return

        try:
            # Clear the index files
            index_path = os.path.join(self.config.config.rag.index_path, "faiss.index")
            metadata_path = self.config.config.rag.metadata_path

            if os.path.exists(index_path):
                os.remove(index_path)

            if os.path.exists(metadata_path):
                os.remove(metadata_path)

            # Reset state
            self.last_indexed_path = None
            self.last_indexed_time = None
            self.indexed_files_count = 0
            self.indexed_chunks_count = 0

            # Disable RAG and tool
            self.config.config.rag.enabled = False
            object.__setattr__(self.codebase_search_tool, '_rag_enabled', False)
            self.codebase_search_tool.disable()

            # Update config and persist
            self.config.config.tools.codebase_search.enabled = False
            self.config.save()

            # Reload the tool's indexer
            self.codebase_search_tool.reload_index()

            self.console.print("\n[green]✅ Index cleared[/green]")
            self.console.print("[dim]RAG disabled ❌[/dim]")
            self.console.print("[dim]Codebase search disabled ❌[/dim]\n")

        except Exception as e:
            self.console.print(f"\n[red]❌ Failed to clear index: {str(e)}[/red]")
            if self.logger:
                self.logger.error(f"Index clear error: {e}")

    def index_refresh(self):
        """Re-index the last indexed path."""
        if not self.last_indexed_path:
            self.console.print("[yellow]No previous index found. Use /index <path> first[/yellow]")
            return

        self.console.print(f"[cyan]Re-indexing {self.last_indexed_path}...[/cyan]\n")
        self.index_codebase(self.last_indexed_path)

    def search_codebase(self, query: str):
        """Test semantic code search."""
        if not self.codebase_search_tool:
            self.console.print("[red]❌ Codebase search tool not initialized[/red]")
            return

        if not self.codebase_search_tool.is_enabled():
            self.console.print("[yellow]⚠ Codebase search is disabled. Use /index first[/yellow]")
            return

        try:
            self.console.print(f"\n[cyan]🔍 Searching for: [bold]{query}[/bold][/cyan]\n")

            # Perform search using the tool
            input_json = json.dumps({"query": query})
            result_json = self.codebase_search_tool._run(input_json)
            result = json.loads(result_json)

            if not result['success']:
                self.console.print(f"[red]❌ Search failed: {result['error']}[/red]\n")
                return

            if result['count'] == 0:
                self.console.print("[yellow]No results found[/yellow]\n")
                return

            # Display results
            for i, res in enumerate(result['results'], 1):
                file_path = res['file']
                chunk_type = res['type']
                name = res['name']
                lines = res['lines']
                similarity = res['similarity']
                snippet = res['code_snippet']

                # Color based on similarity score
                if similarity >= 0.8:
                    score_color = "green"
                elif similarity >= 0.6:
                    score_color = "yellow"
                else:
                    score_color = "white"

                self.console.print(f"[bold cyan]{i}. {file_path}:{name}[/bold cyan] [{chunk_type}] ([{score_color}]{similarity:.2f}[/{score_color}])")
                self.console.print(f"   [dim]Lines {lines}[/dim]")

                # Show code snippet (truncated)
                snippet_lines = snippet.split('\n')
                max_lines = 3
                if len(snippet_lines) > max_lines:
                    snippet_preview = '\n'.join(snippet_lines[:max_lines]) + "\n   ..."
                else:
                    snippet_preview = snippet

                try:
                    syntax = Syntax(snippet_preview, "python", theme="monokai", line_numbers=False)
                    self.console.print(syntax)
                except:
                    self.console.print(f"   {snippet_preview}")

                self.console.print()

            self.console.print(f"[dim]Found {result['count']} results[/dim]\n")

        except Exception as e:
            self.console.print(f"\n[red]❌ Search failed: {str(e)}[/red]\n")
            if self.logger:
                self.logger.error(f"Search error: {e}")

    # ========== End RAG Commands ==========

    # ========== Memory Commands ==========

    def handle_memory_command(self, command_str: str):
        """Handle /memory subcommands."""
        if not self.agent:
            self.console.print("[red]❌ Agent not initialized[/red]")
            return

        if not self.agent.long_term_memory:
            self.console.print("[yellow]⚠️  Long-term memory is not enabled[/yellow]")
            self.console.print("[dim]Enable it in config.yaml: long_term_memory.enabled = true[/dim]")
            return

        parts = command_str.split(maxsplit=1)
        subcmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else None

        try:
            if subcmd == 'stats':
                self.display_memory_stats()
            elif subcmd == 'search':
                if args:
                    self.search_memories(args)
                else:
                    self.console.print("[yellow]Usage: /memory search <query>[/yellow]")
            elif subcmd == 'add':
                if args:
                    self.add_memory(args)
                else:
                    self.console.print("[yellow]Usage: /memory add <content>[/yellow]")
            elif subcmd == 'export':
                format_type = args if args in ['json', 'csv'] else 'json'
                self.export_memories(format_type)
            elif subcmd == 'consolidate':
                self.consolidate_memories()
            elif subcmd == 'decay':
                self.decay_memories()
            else:
                self.console.print(f"[red]❌ Unknown memory command: {subcmd}[/red]")
                self.console.print("[dim]Available: stats, search, add, export, consolidate, decay[/dim]")

        except Exception as e:
            self.console.print(f"[red]❌ Memory operation failed: {str(e)}[/red]")
            if self.logger:
                self.logger.error(f"Memory operation error: {e}")

    def display_memory_stats(self):
        """Display memory system statistics."""
        stats = self.agent.long_term_memory.get_memory_stats()

        self.console.print("\n[bold cyan]═══ Long-Term Memory Statistics ═══[/bold cyan]\n")

        # Basic stats
        self.console.print(f"[yellow]Total Memories:[/yellow] {stats['total_memories']}")
        self.console.print(f"[yellow]Average Importance:[/yellow] {stats['avg_importance']:.2f}")

        # By type
        if stats['by_type']:
            self.console.print("\n[bold]Memories by Type:[/bold]")
            for mem_type, count in stats['by_type'].items():
                self.console.print(f"  • {mem_type}: {count}")

        # Most accessed
        if stats['most_accessed']:
            self.console.print("\n[bold]Most Accessed:[/bold]")
            for mem in stats['most_accessed']:
                self.console.print(f"  • {mem['content']}")
                self.console.print(f"    [dim]Accessed: {mem['access_count']} times, Importance: {mem['importance']:.2f}[/dim]")

        # Recent memories
        if stats['recent_memories']:
            self.console.print("\n[bold]Recent Memories:[/bold]")
            for mem in stats['recent_memories']:
                self.console.print(f"  • [{mem['type']}] {mem['content']}")
                self.console.print(f"    [dim]{mem['timestamp']}[/dim]")

        self.console.print()

    def search_memories(self, query: str):
        """Search memories."""
        self.console.print(f"\n[cyan]🔍 Searching memories for:[/cyan] {query}\n")

        memories = self.agent.long_term_memory.retrieve_relevant(
            query=query,
            top_k=10,
            min_importance=0.0  # Show all results
        )

        if not memories:
            self.console.print("[yellow]No memories found[/yellow]\n")
            return

        for i, mem in enumerate(memories, 1):
            self.console.print(f"[bold]{i}. [{mem.memory_type}][/bold] (importance: {mem.importance:.2f})")
            self.console.print(f"   {mem.content}")
            self.console.print(f"   [dim]Accessed: {mem.access_count} times | {mem.timestamp}[/dim]")
            if mem.tags:
                self.console.print(f"   [dim]Tags: {', '.join(mem.tags)}[/dim]")
            self.console.print()

        self.console.print(f"[dim]Found {len(memories)} memories[/dim]\n")

    def add_memory(self, content: str):
        """Manually add a memory."""
        self.console.print(f"\n[cyan]➕ Adding memory...[/cyan]\n")

        # Determine memory type based on content
        content_lower = content.lower()
        if any(word in content_lower for word in ['prefer', 'like', 'hate', 'favorite']):
            memory_type = 'preference'
        elif any(word in content_lower for word in ['how to', 'pattern', 'technique']):
            memory_type = 'skill'
        else:
            memory_type = 'fact'

        memory_id = self.agent.long_term_memory.store_memory(
            content=content,
            memory_type=memory_type,
            importance=0.7,  # Manual additions are moderately important
            tags=self.agent._extract_tags_from_query(content)
        )

        self.console.print(f"[green]✅ Memory added[/green]")
        self.console.print(f"[dim]ID: {memory_id} | Type: {memory_type}[/dim]\n")

    def export_memories(self, format_type: str):
        """Export memories to file."""
        self.console.print(f"\n[cyan]💾 Exporting memories to {format_type.upper()}...[/cyan]\n")

        export_path = self.agent.long_term_memory.export_memories(format=format_type)

        self.console.print(f"[green]✅ Memories exported[/green]")
        self.console.print(f"[dim]File: {export_path}[/dim]\n")

    def consolidate_memories(self):
        """Consolidate similar memories."""
        self.console.print("\n[cyan]🔄 Consolidating similar memories...[/cyan]\n")

        count = self.agent.long_term_memory.consolidate_memories()

        if count > 0:
            self.console.print(f"[green]✅ Consolidated {count} duplicate memories[/green]\n")
        else:
            self.console.print("[dim]No duplicates found[/dim]\n")

    def decay_memories(self):
        """Apply decay to old memories."""
        self.console.print("\n[cyan]⏰ Applying decay to old memories...[/cyan]\n")

        count = self.agent.long_term_memory.decay_memories()

        if count > 0:
            self.console.print(f"[green]✅ Applied decay to {count} memories[/green]\n")
        else:
            self.console.print("[dim]No memories needed decay[/dim]\n")

    # ========== End Memory Commands ==========

    def exit_cli(self):
        """Exit the CLI."""
        self.running = False
        self.shutdown()

    def shutdown(self):
        """Clean shutdown."""
        self.console.print("\n[cyan]🔄 Shutting down...[/cyan]")
        
        if self.conversation and self.config.config.conversation.auto_save:
            try:
                self.conversation.save()
                self.console.print("[dim]  ✓ Conversation saved[/dim]")
            except Exception as e:
                self.console.print(f"[yellow]  ⚠ Save failed: {str(e)}[/yellow]")
        
        self.console.print("\n[cyan]👋 Goodbye![/cyan]\n")

    def run(self):
        """Main CLI loop."""
        self.display_welcome()
        
        while self.running:
            try:
                user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]").strip()
                
                if not user_input:
                    continue
                
                if user_input.startswith('/'):
                    self.handle_command(user_input)
                else:
                    self.process_query(user_input)
            
            except KeyboardInterrupt:
                self.console.print("\n[yellow]⚠ Use /exit to quit[/yellow]")
                continue
            except EOFError:
                self.shutdown()
                break
            except Exception as e:
                self.console.print(f"[red]❌ Error: {str(e)}[/red]")


def main():
    """Main entry point for CLI."""
    try:
        cli = MetonCLI()
        if cli.initialize():
            cli.run()
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
