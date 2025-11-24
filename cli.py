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
from tools.symbol_lookup import SymbolLookupTool
from tools.import_graph import ImportGraphTool
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
        self.symbol_lookup_tool: Optional[SymbolLookupTool] = None
        self.import_graph_tool: Optional[ImportGraphTool] = None

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
            self.symbol_lookup_tool = SymbolLookupTool(self.config)
            self.import_graph_tool = ImportGraphTool()

            # Initialize Agent
            self.console.print("  [dim]Loading agent...[/dim]")
            self.agent = MetonAgent(
                config=self.config,
                model_manager=self.model_manager,
                conversation=self.conversation,
                tools=[self.file_tool, self.code_tool, self.web_tool, self.codebase_search_tool, self.symbol_lookup_tool, self.import_graph_tool],
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
        table.add_row("/param show", "Show current model parameters")
        table.add_row("/param <name> <value>", "Set parameter value")
        table.add_row("/param reset", "Reset to config defaults")
        table.add_row("/preset <name>", "Apply parameter preset")
        table.add_row("/preset", "List available presets")
        table.add_row("/pprofile", "List parameter profiles")
        table.add_row("/pprofile apply <name>", "Apply parameter profile")
        table.add_row("/pprofile show <name>", "Show profile details")
        table.add_row("/pprofile create <name>", "Create new profile")
        table.add_row("/pprofile delete <name>", "Delete profile")
        table.add_row("/pprofile export <name>", "Export profile to JSON")
        table.add_row("/pprofile import <path>", "Import profile from JSON")
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
        table.add_row("/find <symbol>", "Find symbol definition (function, class, method)")

        # Add memory commands section
        table.add_section()
        table.add_row("[bold cyan]Long-Term Memory:[/]", "")
        table.add_row("/memory stats", "Show memory statistics")
        table.add_row("/memory search <query>", "Search memories")
        table.add_row("/memory add <content>", "Manually add memory")
        table.add_row("/memory export [format]", "Export memories (json/csv)")
        table.add_row("/memory consolidate", "Merge similar memories")
        table.add_row("/memory decay", "Apply decay to old memories")

        # Add learning commands section
        table.add_section()
        table.add_row("[bold cyan]Cross-Session Learning:[/]", "")
        table.add_row("/learn analyze", "Analyze recent sessions for patterns")
        table.add_row("/learn insights", "Show generated insights")
        table.add_row("/learn patterns", "Show detected patterns")
        table.add_row("/learn apply <id>", "Apply specific insight")
        table.add_row("/learn summary", "Learning summary and statistics")

        # Add template commands section
        table.add_section()
        table.add_row("[bold cyan]Project Templates:[/]", "")
        table.add_row("/template list [category]", "List available templates")
        table.add_row("/template create <id> <name>", "Create project from template")
        table.add_row("/template preview <id>", "Show template structure")
        table.add_row("/template categories", "List template categories")

        # Add profile commands section
        table.add_section()
        table.add_row("[bold cyan]Configuration Profiles:[/]", "")
        table.add_row("/profile list [category]", "List available profiles")
        table.add_row("/profile use <id>", "Activate profile")
        table.add_row("/profile current", "Show active profile")
        table.add_row("/profile save <name>", "Save current config as profile")
        table.add_row("/profile compare <id1> <id2>", "Compare two profiles")
        table.add_row("/profile preview <id>", "Show profile details")

        # Add export/import commands section
        table.add_section()
        table.add_row("[bold cyan]Export/Import:[/]", "")
        table.add_row("/export all [file]", "Export complete state")
        table.add_row("/export config [file]", "Export configuration")
        table.add_row("/export memories [file]", "Export memories")
        table.add_row("/export conversations [file]", "Export conversations")
        table.add_row("/export backup [name]", "Create backup archive")
        table.add_row("/import all <file> [--merge]", "Import complete state")
        table.add_row("/import config <file>", "Import configuration")
        table.add_row("/import backup <file>", "Restore from backup")

        # Add optimization commands section
        table.add_section()
        table.add_row("[bold cyan]Optimization:[/]", "")
        table.add_row("/optimize profile", "Show performance profile")
        table.add_row("/optimize cache stats", "Cache statistics")
        table.add_row("/optimize cache clear", "Clear caches")
        table.add_row("/optimize report", "Optimization report")
        table.add_row("/optimize benchmark", "Run benchmarks")
        table.add_row("/optimize resources", "Resource usage")

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
            table.add_row("  primary", f"→ {self.config.config.models.primary}")
            table.add_row("  fallback", f"→ {self.config.config.models.fallback}")
            table.add_row("  quick", f"→ {self.config.config.models.quick}")
            
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
        elif cmd == '/param':
            if args:
                self.handle_param_command(args[0])
            else:
                self.console.print("[yellow]Usage: /param [show|reset|<name> <value>][/yellow]")
        elif cmd == '/preset':
            if args:
                self.handle_preset_command(args[0])
            else:
                self.list_presets()
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
        elif cmd == '/find':
            # Symbol lookup command
            if args:
                self.find_symbol(args[0])
            else:
                self.console.print("[yellow]Usage: /find <symbol> [type:function|class|method][/yellow]")
        elif cmd == '/memory':
            # Memory management command
            if args:
                self.handle_memory_command(args[0])
            else:
                self.console.print("[yellow]Usage: /memory [stats|search|add|export|consolidate|decay][/yellow]")
        elif cmd == '/learn':
            # Cross-session learning command
            if args:
                self.handle_learn_command(args[0])
            else:
                self.console.print("[yellow]Usage: /learn [analyze|insights|patterns|apply|summary][/yellow]")
        elif cmd == '/template':
            # Template management command
            if args:
                self.handle_template_command(args[0])
            else:
                self.console.print("[yellow]Usage: /template [list|create|preview|categories][/yellow]")
        elif cmd == '/profile':
            # Profile management command
            if args:
                self.handle_profile_command(args[0])
            else:
                self.console.print("[yellow]Usage: /profile [list|use|current|save|compare|preview][/yellow]")
        elif cmd == '/pprofile':
            # Parameter profile management command
            if args:
                self.handle_pprofile_command(args[0])
            else:
                self.list_pprofiles()
        elif cmd == '/export':
            # Export data command
            if args:
                self.handle_export_command(args[0])
            else:
                self.console.print("[yellow]Usage: /export [all|config|memories|conversations|backup][/yellow]")
        elif cmd == '/import':
            # Import data command
            if args:
                self.handle_import_command(args[0])
            else:
                self.console.print("[yellow]Usage: /import [all|config|memories|conversations|backup][/yellow]")
        elif cmd == '/optimize':
            # Optimization command
            if args:
                self.handle_optimize_command(' '.join(args))
            else:
                self.console.print("[yellow]Usage: /optimize [profile|cache|report|benchmark|resources][/yellow]")
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

    def handle_param_command(self, args: str):
        """Handle /param command."""
        parts = args.split(maxsplit=1)
        subcommand = parts[0].lower()

        if subcommand == 'show':
            self.show_parameters()
        elif subcommand == 'reset':
            self.reset_parameters()
        else:
            # Assume it's <name> <value>
            if len(parts) < 2:
                self.console.print("[yellow]Usage: /param <name> <value>[/yellow]")
                return
            param_name = parts[0]
            value_str = parts[1]
            self.set_parameter(param_name, value_str)

    def show_parameters(self):
        """Display current model parameters."""
        if not self.model_manager:
            self.console.print("[red]❌ Model manager not initialized[/red]")
            return

        try:
            params = self.model_manager.get_current_parameters()

            table = Table(title="Current Model Parameters", show_header=True, header_style="bold cyan")
            table.add_column("Parameter", style="yellow", width=20)
            table.add_column("Value", style="white", width=15)
            table.add_column("Description", style="dim", width=40)

            # Group parameters by category
            core_params = {
                "temperature": "Randomness control (0.0-2.0)",
                "max_tokens": "Max generation length",
                "top_p": "Nucleus sampling (0.0-1.0)",
                "num_ctx": "Context window size",
            }

            advanced_params = {
                "top_k": "Token diversity (0 = disabled)",
                "min_p": "Adaptive filtering (0.0-1.0)",
            }

            repetition_params = {
                "repeat_penalty": "Repetition penalty (0.0-2.0)",
                "repeat_last_n": "Repetition window",
                "presence_penalty": "Presence penalty (-2.0 to 2.0)",
                "frequency_penalty": "Frequency penalty (-2.0 to 2.0)",
            }

            mirostat_params = {
                "mirostat": "Mirostat mode (0/1/2)",
                "mirostat_tau": "Target entropy",
                "mirostat_eta": "Learning rate (0.0-1.0)",
            }

            other_params = {
                "seed": "Random seed (-1 = random)",
            }

            # Add core parameters
            table.add_row("[bold]Core Parameters[/bold]", "", "", style="cyan")
            for param, desc in core_params.items():
                value = params.get(param, "N/A")
                table.add_row(f"  {param}", str(value), desc)

            # Add advanced parameters
            table.add_row("", "", "")
            table.add_row("[bold]Advanced Sampling[/bold]", "", "", style="cyan")
            for param, desc in advanced_params.items():
                value = params.get(param, "N/A")
                table.add_row(f"  {param}", str(value), desc)

            # Add repetition parameters
            table.add_row("", "", "")
            table.add_row("[bold]Repetition Control[/bold]", "", "", style="cyan")
            for param, desc in repetition_params.items():
                value = params.get(param, "N/A")
                table.add_row(f"  {param}", str(value), desc)

            # Add mirostat parameters
            table.add_row("", "", "")
            table.add_row("[bold]Mirostat[/bold]", "", "", style="cyan")
            for param, desc in mirostat_params.items():
                value = params.get(param, "N/A")
                table.add_row(f"  {param}", str(value), desc)

            # Add other parameters
            table.add_row("", "", "")
            table.add_row("[bold]Other[/bold]", "", "", style="cyan")
            for param, desc in other_params.items():
                value = params.get(param, "N/A")
                table.add_row(f"  {param}", str(value), desc)

            self.console.print()
            self.console.print(table)
            self.console.print()
            self.console.print("[dim]💡 Tip: Use /param <name> <value> to change, /preset <name> for presets[/dim]")

        except Exception as e:
            self.console.print(f"[red]❌ Failed to get parameters: {str(e)}[/red]")

    def set_parameter(self, param_name: str, value_str: str):
        """Set a single parameter value."""
        if not self.model_manager:
            self.console.print("[red]❌ Model manager not initialized[/red]")
            return

        try:
            self.model_manager.update_parameter(param_name, value_str)
            self.console.print(f"[green]✓ Set {param_name} = {value_str}[/green]")
            self.console.print("[dim]  New value will apply to next query[/dim]")

        except ValueError as e:
            self.console.print(f"[red]❌ {str(e)}[/red]")
        except Exception as e:
            self.console.print(f"[red]❌ Failed to set parameter: {str(e)}[/red]")

    def reset_parameters(self):
        """Reset parameters to config defaults."""
        if not self.model_manager:
            self.console.print("[red]❌ Model manager not initialized[/red]")
            return

        try:
            with self.console.status("[cyan]🔄 Resetting parameters...[/cyan]", spinner="dots"):
                self.model_manager.reset_parameters()

            self.console.print("[green]✓ Parameters reset to config defaults[/green]")
            self.console.print("[dim]  Run /param show to see current values[/dim]")

        except Exception as e:
            self.console.print(f"[red]❌ Failed to reset parameters: {str(e)}[/red]")

    def handle_preset_command(self, preset_name: str):
        """Handle /preset <name> command."""
        if not self.model_manager:
            self.console.print("[red]❌ Model manager not initialized[/red]")
            return

        try:
            self.model_manager.apply_preset(preset_name)
            self.console.print(f"[green]✓ Applied preset '{preset_name}'[/green]")
            self.console.print("[dim]  Run /param show to see new values[/dim]")

        except ValueError as e:
            self.console.print(f"[red]❌ {str(e)}[/red]")
        except Exception as e:
            self.console.print(f"[red]❌ Failed to apply preset: {str(e)}[/red]")

    def list_presets(self):
        """List available parameter presets."""
        from core.config import PARAMETER_PRESETS

        table = Table(title="Available Parameter Presets", show_header=True, header_style="bold cyan")
        table.add_column("Preset", style="yellow", width=15)
        table.add_column("Description", style="white", width=50)

        for name, preset in PARAMETER_PRESETS.items():
            table.add_row(name, preset.description)

        self.console.print()
        self.console.print(table)
        self.console.print()
        self.console.print("[dim]💡 Usage: /preset <name> to apply[/dim]")

    # ========== Parameter Profile Commands ==========

    def handle_pprofile_command(self, command_str: str):
        """Handle /pprofile subcommands."""
        parts = command_str.split(maxsplit=3)
        subcmd = parts[0].lower()

        if subcmd == 'list':
            # /pprofile list
            self.list_pprofiles()
        elif subcmd == 'show':
            # /pprofile show <name>
            if len(parts) < 2:
                self.console.print("[yellow]Usage: /pprofile show <name>[/yellow]")
                return
            self.show_pprofile(parts[1])
        elif subcmd == 'apply':
            # /pprofile apply <name>
            if len(parts) < 2:
                self.console.print("[yellow]Usage: /pprofile apply <name>[/yellow]")
                return
            self.apply_pprofile(parts[1])
        elif subcmd == 'create':
            # /pprofile create <name>
            if len(parts) < 2:
                self.console.print("[yellow]Usage: /pprofile create <name>[/yellow]")
                return
            self.create_pprofile(parts[1])
        elif subcmd == 'delete':
            # /pprofile delete <name>
            if len(parts) < 2:
                self.console.print("[yellow]Usage: /pprofile delete <name>[/yellow]")
                return
            self.delete_pprofile(parts[1])
        elif subcmd == 'export':
            # /pprofile export <name> [path]
            if len(parts) < 2:
                self.console.print("[yellow]Usage: /pprofile export <name> [path][/yellow]")
                return
            path = parts[2] if len(parts) > 2 else None
            self.export_pprofile(parts[1], path)
        elif subcmd == 'import':
            # /pprofile import <path>
            if len(parts) < 2:
                self.console.print("[yellow]Usage: /pprofile import <path>[/yellow]")
                return
            self.import_pprofile(parts[1])
        else:
            self.console.print(f"[red]Unknown pprofile command: {subcmd}[/red]")
            self.console.print("[yellow]Usage: /pprofile [list|show|apply|create|delete|export|import][/yellow]")

    def list_pprofiles(self):
        """List all parameter profiles."""
        if not self.model_manager:
            self.console.print("[red]❌ Model manager not initialized[/red]")
            return

        profiles = self.model_manager.list_profiles()

        if not profiles:
            self.console.print()
            self.console.print("[yellow]No parameter profiles defined[/yellow]")
            self.console.print("[dim]💡 Create one with: /pprofile create <name>[/dim]")
            self.console.print()
            return

        table = Table(title="Parameter Profiles", show_header=True, header_style="bold cyan")
        table.add_column("Profile", style="yellow", width=20)
        table.add_column("Description", style="white", width=40)
        table.add_column("Parameters", style="dim", width=30)

        for name, info in profiles.items():
            params = ', '.join(info['settings'].keys())
            if len(params) > 27:
                params = params[:24] + "..."
            table.add_row(name, info['description'], params)

        self.console.print()
        self.console.print(table)
        self.console.print()
        self.console.print("[dim]💡 Use: /pprofile show <name> to see details[/dim]")
        self.console.print("[dim]💡 Use: /pprofile apply <name> to activate[/dim]")

    def show_pprofile(self, name: str):
        """Show details of a specific profile."""
        if not self.model_manager:
            self.console.print("[red]❌ Model manager not initialized[/red]")
            return

        profile = self.model_manager.get_profile(name)

        if not profile:
            self.console.print(f"[red]❌ Profile not found: {name}[/red]")
            return

        self.console.print()
        self.console.print(f"[bold cyan]Profile: {profile['name']}[/bold cyan]")
        self.console.print(f"[dim]{profile['description']}[/dim]")
        self.console.print()

        table = Table(show_header=True, header_style="bold yellow")
        table.add_column("Parameter", style="cyan", width=20)
        table.add_column("Value", style="white", width=20)

        for param, value in profile['settings'].items():
            table.add_row(param, str(value))

        self.console.print(table)
        self.console.print()

    def apply_pprofile(self, name: str):
        """Apply a parameter profile."""
        if not self.model_manager:
            self.console.print("[red]❌ Model manager not initialized[/red]")
            return

        if self.model_manager.apply_profile(name):
            self.console.print(f"[green]✓ Applied profile '{name}'[/green]")
            self.console.print("[dim]  Run /param show to see new values[/dim]")
        else:
            self.console.print(f"[red]❌ Failed to apply profile '{name}'[/red]")

    def create_pprofile(self, name: str):
        """Create a new parameter profile interactively."""
        if not self.model_manager:
            self.console.print("[red]❌ Model manager not initialized[/red]")
            return

        self.console.print()
        self.console.print(f"[bold cyan]Creating new parameter profile: {name}[/bold cyan]")
        self.console.print()

        # Get description
        description = input("Description: ").strip()
        if not description:
            description = f"Custom profile: {name}"

        # Get current parameters as starting point
        current_params = self.model_manager.get_current_parameters()

        self.console.print()
        self.console.print("[yellow]Enter parameter values (press Enter to skip):[/yellow]")
        self.console.print("[dim]Available parameters:[/dim]")
        self.console.print("[dim]  temperature, max_tokens, top_p, num_ctx, top_k, min_p,[/dim]")
        self.console.print("[dim]  repeat_penalty, repeat_last_n, presence_penalty, frequency_penalty,[/dim]")
        self.console.print("[dim]  mirostat, mirostat_tau, mirostat_eta, seed[/dim]")
        self.console.print()

        settings = {}

        # Core parameters
        for param in ['temperature', 'top_p', 'top_k', 'min_p']:
            value_str = input(f"{param} [{current_params.get(param, '')}]: ").strip()
            if value_str:
                try:
                    settings[param] = float(value_str) if '.' in value_str else int(value_str)
                except ValueError:
                    self.console.print(f"[yellow]⚠ Invalid value for {param}, skipping[/yellow]")

        # Repetition control
        for param in ['repeat_penalty', 'presence_penalty', 'frequency_penalty']:
            value_str = input(f"{param} [{current_params.get(param, '')}]: ").strip()
            if value_str:
                try:
                    settings[param] = float(value_str)
                except ValueError:
                    self.console.print(f"[yellow]⚠ Invalid value for {param}, skipping[/yellow]")

        # Mirostat
        for param in ['mirostat', 'mirostat_tau', 'mirostat_eta']:
            value_str = input(f"{param} [{current_params.get(param, '')}]: ").strip()
            if value_str:
                try:
                    settings[param] = int(value_str) if param == 'mirostat' else float(value_str)
                except ValueError:
                    self.console.print(f"[yellow]⚠ Invalid value for {param}, skipping[/yellow]")

        if not settings:
            self.console.print("[red]❌ No parameters specified, profile not created[/red]")
            return

        # Create profile
        if self.model_manager.create_profile(name, description, settings):
            self.console.print()
            self.console.print(f"[green]✓ Created profile '{name}'[/green]")
            self.console.print("[dim]  Use /pprofile apply <name> to activate[/dim]")
        else:
            self.console.print()
            self.console.print(f"[red]❌ Failed to create profile '{name}'[/red]")

    def delete_pprofile(self, name: str):
        """Delete a parameter profile."""
        if not self.model_manager:
            self.console.print("[red]❌ Model manager not initialized[/red]")
            return

        # Confirm deletion
        confirm = input(f"Delete profile '{name}'? (yes/no): ").strip().lower()
        if confirm not in ['yes', 'y']:
            self.console.print("[yellow]Cancelled[/yellow]")
            return

        if self.model_manager.delete_profile(name):
            self.console.print(f"[green]✓ Deleted profile '{name}'[/green]")
        else:
            self.console.print(f"[red]❌ Failed to delete profile '{name}'[/red]")

    def export_pprofile(self, name: str, path: Optional[str] = None):
        """Export a parameter profile to JSON."""
        if not self.model_manager:
            self.console.print("[red]❌ Model manager not initialized[/red]")
            return

        if self.model_manager.export_profile(name, path):
            output_path = path or f"./{name}_profile.json"
            self.console.print(f"[green]✓ Exported profile '{name}' to {output_path}[/green]")
        else:
            self.console.print(f"[red]❌ Failed to export profile '{name}'[/red]")

    def import_pprofile(self, path: str):
        """Import a parameter profile from JSON."""
        if not self.model_manager:
            self.console.print("[red]❌ Model manager not initialized[/red]")
            return

        if self.model_manager.import_profile(path):
            self.console.print(f"[green]✓ Imported profile from {path}[/green]")
            self.console.print("[dim]  Use /pprofile list to see all profiles[/dim]")
        else:
            self.console.print(f"[red]❌ Failed to import profile from {path}[/red]")

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

    def find_symbol(self, query_str: str):
        """Find symbol definitions in the codebase."""
        if not self.symbol_lookup_tool:
            self.console.print("[red]❌ Symbol lookup tool not initialized[/red]")
            return

        if not self.symbol_lookup_tool.is_enabled():
            self.console.print("[yellow]⚠ Symbol lookup is disabled. Enable in config.yaml[/yellow]")
            return

        try:
            # Parse query string
            # Format: "symbol_name [type:function|class|method]"
            parts = query_str.split()
            symbol_name = parts[0]
            symbol_type = "all"

            # Check for type filter
            for part in parts[1:]:
                if part.startswith("type:"):
                    symbol_type = part.split(":")[1]

            self.console.print(f"\n[cyan]🔍 Finding: [bold]{symbol_name}[/bold]", end="")
            if symbol_type != "all":
                self.console.print(f" (type: {symbol_type})", end="")
            self.console.print("[/cyan]\n")

            # Perform lookup using the tool
            input_json = json.dumps({
                "symbol": symbol_name,
                "type": symbol_type
            })
            result_json = self.symbol_lookup_tool._run(input_json)
            result = json.loads(result_json)

            if not result['success']:
                self.console.print(f"[red]❌ Lookup failed: {result['error']}[/red]\n")
                return

            if result['count'] == 0:
                self.console.print(f"[yellow]No definitions found for '{symbol_name}'[/yellow]\n")
                return

            # Display results in a table
            table = Table(title=f"Symbol Definitions for '{symbol_name}'", box=box.ROUNDED)
            table.add_column("File", style="cyan", no_wrap=False)
            table.add_column("Type", style="magenta", width=10)
            table.add_column("Line", style="yellow", justify="right", width=8)
            table.add_column("Signature", style="green")

            for res in result['results']:
                file_path = res['file']
                sym_type = res['type']
                line = str(res['line'])
                signature = res['signature'][:80] + "..." if len(res['signature']) > 80 else res['signature']

                table.add_row(file_path, sym_type, line, signature)

            self.console.print(table)
            self.console.print()

            # Show detailed view of first result
            if result['count'] > 0:
                first = result['results'][0]
                self.console.print(f"[bold]First definition:[/bold] {first['file']}:{first['line']}\n")

                # Show code snippet
                snippet = first['code_snippet']
                try:
                    syntax = Syntax(snippet, "python", theme="monokai", line_numbers=True, start_line=first['line'])
                    self.console.print(syntax)
                except:
                    self.console.print(snippet)

                self.console.print()

                # Show docstring if available
                if first.get('docstring'):
                    self.console.print(f"[dim]Docstring:[/dim]\n{first['docstring']}\n")

            self.console.print(f"[dim]Found {result['count']} definition(s)[/dim]\n")

        except Exception as e:
            self.console.print(f"\n[red]❌ Lookup failed: {str(e)}[/red]\n")
            if self.logger:
                self.logger.error(f"Symbol lookup error: {e}")
            import traceback
            traceback.print_exc()

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

    # ========== Cross-Session Learning Commands ==========

    def handle_learn_command(self, command_str: str):
        """Handle /learn subcommands."""
        if not self.agent:
            self.console.print("[red]❌ Agent not initialized[/red]")
            return

        # Cross-session learning requires memory, feedback, and analytics
        if not hasattr(self.agent, 'long_term_memory') or not self.agent.long_term_memory:
            self.console.print("[yellow]⚠️  Cross-session learning requires long-term memory[/yellow]")
            self.console.print("[dim]Enable long_term_memory in config.yaml[/dim]")
            return

        # Initialize cross-session learning if not already done
        if not hasattr(self, 'cross_session_learning'):
            try:
                from memory.cross_session_learning import CrossSessionLearning

                self.cross_session_learning = CrossSessionLearning(
                    long_term_memory=self.agent.long_term_memory,
                    feedback_system=getattr(self.agent, 'feedback_system', None),
                    analytics=getattr(self.agent, 'performance_analytics', None),
                    storage_path=self.config.config.long_term_memory.storage_path,
                    min_occurrences=self.config.config.cross_session_learning.min_occurrences_for_pattern,
                    min_confidence=self.config.config.cross_session_learning.min_confidence,
                    auto_apply_insights=self.config.config.cross_session_learning.auto_apply_insights
                )
            except Exception as e:
                self.console.print(f"[red]❌ Failed to initialize cross-session learning: {e}[/red]")
                return

        parts = command_str.split(maxsplit=1)
        subcmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else None

        try:
            if subcmd == 'analyze':
                self.analyze_learning_sessions()
            elif subcmd == 'insights':
                self.show_learning_insights()
            elif subcmd == 'patterns':
                self.show_learning_patterns()
            elif subcmd == 'apply':
                if args:
                    self.apply_learning_insight(args)
                else:
                    self.console.print("[yellow]Usage: /learn apply <insight_id>[/yellow]")
            elif subcmd == 'summary':
                self.show_learning_summary()
            else:
                self.console.print(f"[red]❌ Unknown learn command: {subcmd}[/red]")
                self.console.print("[dim]Available: analyze, insights, patterns, apply, summary[/dim]")

        except Exception as e:
            self.console.print(f"[red]❌ Learning operation failed: {str(e)}[/red]")
            if self.logger:
                self.logger.error(f"Learning operation error: {e}")

    def analyze_learning_sessions(self):
        """Analyze recent sessions for patterns."""
        self.console.print("\n[cyan]🔍 Analyzing recent sessions for patterns...[/cyan]\n")

        lookback_days = self.config.config.cross_session_learning.lookback_days

        with self.console.status(f"[cyan]Analyzing last {lookback_days} days...[/cyan]"):
            insights = self.cross_session_learning.analyze_sessions(lookback_days=lookback_days)

        if insights:
            self.console.print(f"[green]✅ Generated {len(insights)} new insights[/green]\n")

            for insight in insights[:5]:  # Show first 5
                impact_color = {"high": "red", "medium": "yellow", "low": "dim"}[insight.impact]
                self.console.print(f"[bold]{insight.title}[/bold]")
                self.console.print(f"  [{impact_color}]Impact: {insight.impact.upper()}[/{impact_color}]")
                self.console.print(f"  {insight.description}")
                self.console.print(f"  [dim]ID: {insight.id}[/dim]")
                self.console.print()

            if len(insights) > 5:
                self.console.print(f"[dim]... and {len(insights)-5} more. Use /learn insights to see all.[/dim]\n")
        else:
            self.console.print("[dim]No new insights generated[/dim]\n")

    def show_learning_insights(self):
        """Show all generated insights."""
        self.console.print("\n[bold cyan]═══ Learning Insights ═══[/bold cyan]\n")

        insights = list(self.cross_session_learning.insights.values())

        if not insights:
            self.console.print("[dim]No insights yet. Run /learn analyze first.[/dim]\n")
            return

        # Sort by applied status and impact
        insights.sort(key=lambda i: (i.applied, {"high": 0, "medium": 1, "low": 2}[i.impact]))

        for insight in insights:
            status = "✅ APPLIED" if insight.applied else "⏳ Pending"
            impact_color = {"high": "red", "medium": "yellow", "low": "dim"}[insight.impact]

            self.console.print(f"[bold]{insight.title}[/bold] [{impact_color}]{status}[/{impact_color}]")
            self.console.print(f"  Type: {insight.insight_type} | Impact: {insight.impact}")
            self.console.print(f"  {insight.description}")
            if insight.actionable and not insight.applied:
                self.console.print(f"  [cyan]→ Apply with: /learn apply {insight.id}[/cyan]")
            self.console.print(f"  [dim]ID: {insight.id} | Created: {insight.created_at}[/dim]")
            self.console.print()

    def show_learning_patterns(self):
        """Show detected patterns."""
        self.console.print("\n[bold cyan]═══ Detected Patterns ═══[/bold cyan]\n")

        patterns = list(self.cross_session_learning.patterns.values())

        if not patterns:
            self.console.print("[dim]No patterns yet. Run /learn analyze first.[/dim]\n")
            return

        # Group by type
        from collections import defaultdict
        by_type = defaultdict(list)
        for pattern in patterns:
            by_type[pattern.pattern_type].append(pattern)

        for pattern_type, type_patterns in by_type.items():
            self.console.print(f"[bold yellow]{pattern_type.upper()} Patterns:[/bold yellow]")

            for pattern in sorted(type_patterns, key=lambda p: p.confidence, reverse=True)[:5]:
                self.console.print(f"  • {pattern.description}")
                self.console.print(f"    Occurrences: {pattern.occurrences} | Confidence: {pattern.confidence:.2f}")
                if pattern.examples:
                    self.console.print(f"    Examples: {pattern.examples[0][:80]}...")
                self.console.print()

    def apply_learning_insight(self, insight_id: str):
        """Apply a specific insight."""
        self.console.print(f"\n[cyan]📝 Applying insight...[/cyan]\n")

        result = self.cross_session_learning.apply_insight(insight_id)

        if result:
            insight = self.cross_session_learning.insights.get(insight_id)
            if insight:
                self.console.print(f"[green]✅ Insight applied: {insight.title}[/green]")
                self.console.print(f"[dim]{insight.description}[/dim]\n")
        else:
            self.console.print(f"[red]❌ Insight not found: {insight_id}[/red]\n")

    def show_learning_summary(self):
        """Show learning summary and statistics."""
        summary = self.cross_session_learning.get_learning_summary()

        self.console.print("\n[bold cyan]═══ Cross-Session Learning Summary ═══[/bold cyan]\n")

        # Basic stats
        self.console.print(f"[yellow]Total Patterns:[/yellow] {summary['total_patterns']}")
        self.console.print(f"[yellow]Insights Generated:[/yellow] {summary['insights_generated']}")
        self.console.print(f"[yellow]Insights Applied:[/yellow] {summary['insights_applied']}")
        self.console.print(f"[yellow]Learning Velocity:[/yellow] {summary['learning_velocity']:.2f} patterns/week")

        # Top patterns
        if summary['top_patterns']:
            self.console.print("\n[bold]Top Patterns (by confidence):[/bold]")
            for pattern in summary['top_patterns'][:3]:
                self.console.print(f"  • {pattern['description']}")
                self.console.print(f"    Confidence: {pattern['confidence']:.2f} | Occurrences: {pattern['occurrences']}")

        # Recent insights
        if summary['recent_insights']:
            self.console.print("\n[bold]Recent Insights:[/bold]")
            for insight in summary['recent_insights'][:3]:
                status = "✅" if insight['applied'] else "⏳"
                self.console.print(f"  {status} {insight['title']}")
                self.console.print(f"    Impact: {insight['impact']} | Type: {insight['insight_type']}")

        self.console.print()

    # ========== End Cross-Session Learning Commands ==========

    # ========== Project Template Commands ==========

    def handle_template_command(self, command_str: str):
        """Handle /template subcommands."""
        # Initialize template manager if not already done
        if not hasattr(self, 'template_manager'):
            from templates.template_manager import TemplateManager
            self.template_manager = TemplateManager()

        parts = command_str.split(maxsplit=2)
        subcmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        try:
            if subcmd == 'list':
                category = args[0] if args else None
                self.list_templates(category)
            elif subcmd == 'create':
                if len(args) >= 2:
                    template_id = args[0]
                    project_name = args[1]
                    self.create_from_template(template_id, project_name)
                else:
                    self.console.print("[yellow]Usage: /template create <template_id> <project_name>[/yellow]")
            elif subcmd == 'preview':
                if args:
                    self.preview_template(args[0])
                else:
                    self.console.print("[yellow]Usage: /template preview <template_id>[/yellow]")
            elif subcmd == 'categories':
                self.list_template_categories()
            else:
                self.console.print(f"[red]❌ Unknown template command: {subcmd}[/red]")
                self.console.print("[dim]Available: list, create, preview, categories[/dim]")

        except Exception as e:
            self.console.print(f"[red]❌ Template operation failed: {str(e)}[/red]")
            if self.logger:
                self.logger.error(f"Template operation error: {e}")

    def list_templates(self, category: str = None):
        """List available templates."""
        self.console.print("\n[bold cyan]═══ Available Templates ═══[/bold cyan]\n")

        templates = self.template_manager.list_templates(category=category)

        if not templates:
            msg = f"No templates found"
            if category:
                msg += f" in category '{category}'"
            self.console.print(f"[dim]{msg}[/dim]\n")
            return

        # Group by category
        from collections import defaultdict
        by_category = defaultdict(list)
        for template in templates:
            by_category[template.category].append(template)

        for cat in sorted(by_category.keys()):
            cat_templates = by_category[cat]
            self.console.print(f"[bold yellow]{cat.upper()}[/bold yellow]")

            for template in cat_templates:
                self.console.print(f"  [cyan]{template.id}[/cyan] - {template.name}")
                self.console.print(f"    {template.description}")
                if template.dependencies:
                    deps = ', '.join(template.dependencies[:3])
                    if len(template.dependencies) > 3:
                        deps += f", +{len(template.dependencies)-3} more"
                    self.console.print(f"    [dim]Dependencies: {deps}[/dim]")
                self.console.print()

    def create_from_template(self, template_id: str, project_name: str):
        """Create project from template."""
        self.console.print(f"\n[cyan]📦 Creating project '{project_name}' from template '{template_id}'...[/cyan]\n")

        # Prompt for variables
        variables = {}
        variables['author'] = input("Author name (press Enter to skip): ").strip() or None
        variables['email'] = input("Author email (press Enter to skip): ").strip() or None
        variables['description'] = input("Project description (press Enter to skip): ").strip() or None

        # Remove None values
        variables = {k: v for k, v in variables.items() if v}

        # Get output directory
        import os
        output_dir = input(f"Output directory (default: {os.getcwd()}): ").strip()
        if not output_dir:
            output_dir = os.getcwd()

        try:
            with self.console.status(f"[cyan]Creating project...[/cyan]"):
                project_path = self.template_manager.create_project(
                    template_id=template_id,
                    project_name=project_name,
                    output_dir=output_dir,
                    variables=variables
                )

            self.console.print(f"[green]✅ Project created successfully![/green]")
            self.console.print(f"[dim]Location: {project_path}[/dim]\n")

            # Show next steps
            template = self.template_manager.get_template(template_id)
            if template.setup_commands:
                self.console.print("[bold]Next steps:[/bold]")
                self.console.print(f"  cd {project_name}")
                for cmd in template.setup_commands:
                    self.console.print(f"  {cmd}")
                self.console.print()

        except ValueError as e:
            self.console.print(f"[red]❌ {str(e)}[/red]\n")
        except Exception as e:
            self.console.print(f"[red]❌ Failed to create project: {str(e)}[/red]\n")
            if self.logger:
                self.logger.error(f"Project creation failed: {e}")

    def preview_template(self, template_id: str):
        """Show template preview."""
        try:
            preview = self.template_manager.get_template_preview(template_id)
            self.console.print("\n" + preview + "\n")
        except ValueError as e:
            self.console.print(f"[red]❌ {str(e)}[/red]\n")

    def list_template_categories(self):
        """List template categories."""
        categories = self.template_manager.get_categories()

        self.console.print("\n[bold cyan]═══ Template Categories ═══[/bold cyan]\n")

        for category in categories:
            templates = self.template_manager.list_templates(category=category)
            count = len(templates)
            self.console.print(f"  [yellow]{category}[/yellow] ({count} template{'s' if count != 1 else ''})")

        self.console.print()

    # ========== End Project Template Commands ==========

    # ========== Configuration Profile Commands ==========

    def handle_profile_command(self, command_str: str):
        """Handle /profile subcommands."""
        # Initialize profile manager if not already done
        if not hasattr(self, 'profile_manager'):
            from config.profile_manager import ProfileManager
            self.profile_manager = ProfileManager(config_manager=self.config)

        parts = command_str.split(maxsplit=3)
        subcmd = parts[0].lower()

        if subcmd == 'list':
            # /profile list [category]
            category = parts[1] if len(parts) > 1 else None
            self.list_profiles(category)
        elif subcmd == 'use':
            # /profile use <id>
            if len(parts) < 2:
                self.console.print("[yellow]Usage: /profile use <id>[/yellow]")
                return
            self.activate_profile(parts[1])
        elif subcmd == 'current':
            # /profile current
            self.show_current_profile()
        elif subcmd == 'save':
            # /profile save <name> [description] [category]
            if len(parts) < 2:
                self.console.print("[yellow]Usage: /profile save <name> [description] [category][/yellow]")
                return
            name = parts[1]
            description = input("Profile description (press Enter to skip): ").strip() or f"Custom profile: {name}"
            category = input("Profile category (development/research/writing/general/custom) [custom]: ").strip() or "custom"
            self.save_current_profile(name, description, category)
        elif subcmd == 'compare':
            # /profile compare <id1> <id2>
            if len(parts) < 3:
                self.console.print("[yellow]Usage: /profile compare <id1> <id2>[/yellow]")
                return
            self.compare_profiles(parts[1], parts[2])
        elif subcmd == 'preview':
            # /profile preview <id>
            if len(parts) < 2:
                self.console.print("[yellow]Usage: /profile preview <id>[/yellow]")
                return
            self.preview_profile(parts[1])
        else:
            self.console.print(f"[red]Unknown profile command: {subcmd}[/red]")
            self.console.print("[yellow]Usage: /profile [list|use|current|save|compare|preview][/yellow]")

    def list_profiles(self, category: Optional[str] = None):
        """List available profiles."""
        self.console.print("\n[bold cyan]═══ Available Profiles ═══[/bold cyan]\n")

        profiles = self.profile_manager.list_profiles(category=category)

        if not profiles:
            msg = f"No profiles found"
            if category:
                msg += f" in category '{category}'"
            self.console.print(f"[yellow]{msg}[/yellow]\n")
            return

        # Create table
        table = Table(show_header=True, header_style="bold cyan", show_lines=True)
        table.add_column("ID", style="yellow")
        table.add_column("Name", style="green")
        table.add_column("Category", style="magenta")
        table.add_column("Description", style="dim")
        table.add_column("Usage", style="cyan", justify="right")

        for profile in profiles:
            # Mark active profile
            profile_id = f"[bold]{profile.id}[/bold]" if self.profile_manager.active_profile == profile.id else profile.id

            # Truncate description if too long
            desc = profile.description
            if len(desc) > 50:
                desc = desc[:47] + "..."

            # Built-in badge
            if profile.is_builtin:
                desc = f"🔒 {desc}"

            table.add_row(
                profile_id,
                profile.name,
                profile.category,
                desc,
                str(profile.usage_count)
            )

        self.console.print(table)
        self.console.print()

    def activate_profile(self, profile_id: str):
        """Activate a profile."""
        self.console.print(f"\n[cyan]📝 Activating profile '{profile_id}'...[/cyan]\n")

        try:
            self.profile_manager.activate_profile(profile_id)
            profile = self.profile_manager.get_profile(profile_id)

            self.console.print(f"[green]✅ Profile '{profile.name}' activated![/green]")
            self.console.print(f"[dim]Category: {profile.category}[/dim]")
            self.console.print(f"[dim]Description: {profile.description}[/dim]\n")

            # Show key configuration changes
            config = profile.config
            self.console.print("[bold]Configuration Highlights:[/bold]")
            self.console.print(f"  • Primary model: {config.get('models', {}).get('primary', 'N/A')}")
            self.console.print(f"  • Temperature: {config.get('models', {}).get('settings', {}).get('temperature', 'N/A')}")
            self.console.print(f"  • Web search: {'enabled' if config.get('tools', {}).get('web_search', {}).get('enabled') else 'disabled'}")
            self.console.print(f"  • Skills: {'enabled' if config.get('skills', {}).get('enabled') else 'disabled'}")
            self.console.print(f"  • Reflection: {'enabled' if config.get('reflection', {}).get('enabled') else 'disabled'}")
            self.console.print()

            self.console.print("[yellow]Note: Restart Meton for full profile changes to take effect[/yellow]\n")

        except ValueError as e:
            self.console.print(f"[red]❌ {str(e)}[/red]\n")

    def show_current_profile(self):
        """Show currently active profile."""
        active_profile = self.profile_manager.get_active_profile()

        if active_profile:
            self.console.print(f"\n[bold cyan]═══ Active Profile ═══[/bold cyan]\n")
            self.console.print(f"[green]✓ {active_profile.name}[/green]")
            self.console.print(f"  ID: {active_profile.id}")
            self.console.print(f"  Category: {active_profile.category}")
            self.console.print(f"  Description: {active_profile.description}")
            self.console.print(f"  Used {active_profile.usage_count} times")
            self.console.print(f"  Last used: {active_profile.last_used}\n")
        else:
            self.console.print("\n[yellow]No profile active - using default configuration[/yellow]\n")

    def save_current_profile(self, name: str, description: str, category: str):
        """Save current configuration as profile."""
        self.console.print(f"\n[cyan]💾 Saving current configuration as '{name}'...[/cyan]\n")

        try:
            # Get current config as dict
            current_config = self.config.config.__dict__.copy()

            profile_id = self.profile_manager.save_current_as_profile(
                name=name,
                description=description,
                category=category,
                current_config=current_config
            )

            self.console.print(f"[green]✅ Profile saved![/green]")
            self.console.print(f"[dim]Profile ID: {profile_id}[/dim]")
            self.console.print(f"[dim]Use '/profile use {profile_id}' to activate[/dim]\n")

        except ValueError as e:
            self.console.print(f"[red]❌ {str(e)}[/red]\n")

    def compare_profiles(self, profile_id1: str, profile_id2: str):
        """Compare two profiles."""
        self.console.print(f"\n[bold cyan]═══ Comparing Profiles ═══[/bold cyan]\n")

        try:
            differences = self.profile_manager.compare_profiles(profile_id1, profile_id2)

            profile1_name = differences["profile1"]["name"]
            profile2_name = differences["profile2"]["name"]

            self.console.print(f"[yellow]{profile1_name}[/yellow] vs [green]{profile2_name}[/green]\n")

            changes = differences["changes"]

            if not changes:
                self.console.print("[dim]No differences found[/dim]\n")
                return

            # Create table for differences
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Setting", style="yellow")
            table.add_column(profile1_name, style="magenta")
            table.add_column(profile2_name, style="green")

            for path, values in sorted(changes.items()):
                val1 = str(values["profile1"]) if values["profile1"] is not None else "[dim]not set[/dim]"
                val2 = str(values["profile2"]) if values["profile2"] is not None else "[dim]not set[/dim]"
                table.add_row(path, val1, val2)

            self.console.print(table)
            self.console.print()

        except ValueError as e:
            self.console.print(f"[red]❌ {str(e)}[/red]\n")

    def preview_profile(self, profile_id: str):
        """Show profile preview."""
        try:
            preview = self.profile_manager.get_profile_preview(profile_id)
            self.console.print("\n" + preview + "\n")
        except ValueError as e:
            self.console.print(f"[red]❌ {str(e)}[/red]\n")

    # ========== End Configuration Profile Commands ==========

    # ========== Export/Import Commands ==========

    def handle_export_command(self, command_str: str):
        """Handle /export subcommands."""
        # Initialize export manager if not already done
        if not hasattr(self, 'export_manager'):
            from export.export_manager import ExportManager
            self.export_manager = ExportManager()

        parts = command_str.split(maxsplit=1)
        subcmd = parts[0].lower()

        if subcmd == 'all':
            # /export all [output_file]
            output_file = parts[1] if len(parts) > 1 else None
            self.export_all_data(output_file)
        elif subcmd == 'config':
            # /export config [output_file]
            output_file = parts[1] if len(parts) > 1 else None
            self.export_config(output_file)
        elif subcmd == 'memories':
            # /export memories [output_file]
            output_file = parts[1] if len(parts) > 1 else None
            self.export_memories(output_file)
        elif subcmd == 'conversations':
            # /export conversations [output_file]
            output_file = parts[1] if len(parts) > 1 else None
            self.export_conversations(output_file)
        elif subcmd == 'analytics':
            # /export analytics [output_file]
            output_file = parts[1] if len(parts) > 1 else None
            self.export_analytics(output_file)
        elif subcmd == 'backup':
            # /export backup [name]
            backup_name = parts[1] if len(parts) > 1 else None
            self.create_backup(backup_name)
        else:
            self.console.print(f"[red]Unknown export command: {subcmd}[/red]")
            self.console.print("[yellow]Usage: /export [all|config|memories|conversations|analytics|backup][/yellow]")

    def handle_import_command(self, command_str: str):
        """Handle /import subcommands."""
        # Initialize import manager if not already done
        if not hasattr(self, 'import_manager'):
            from export.import_manager import ImportManager
            self.import_manager = ImportManager()

        parts = command_str.split(maxsplit=2)
        subcmd = parts[0].lower()

        if subcmd == 'all':
            # /import all <file> [--merge]
            if len(parts) < 2:
                self.console.print("[yellow]Usage: /import all <file> [--merge][/yellow]")
                return
            import_file = parts[1]
            merge = '--merge' in command_str.lower()
            self.import_all_data(import_file, merge)
        elif subcmd == 'config':
            # /import config <file>
            if len(parts) < 2:
                self.console.print("[yellow]Usage: /import config <file>[/yellow]")
                return
            import_file = parts[1]
            self.import_config(import_file)
        elif subcmd == 'memories':
            # /import memories <file> [--merge]
            if len(parts) < 2:
                self.console.print("[yellow]Usage: /import memories <file> [--merge][/yellow]")
                return
            import_file = parts[1]
            merge = '--merge' in command_str.lower()
            self.import_memories(import_file, merge)
        elif subcmd == 'conversations':
            # /import conversations <file>
            if len(parts) < 2:
                self.console.print("[yellow]Usage: /import conversations <file>[/yellow]")
                return
            import_file = parts[1]
            self.import_conversations(import_file)
        elif subcmd == 'backup':
            # /import backup <file>
            if len(parts) < 2:
                self.console.print("[yellow]Usage: /import backup <file>[/yellow]")
                return
            backup_file = parts[1]
            self.restore_backup(backup_file)
        elif subcmd == 'validate':
            # /import validate <file>
            if len(parts) < 2:
                self.console.print("[yellow]Usage: /import validate <file>[/yellow]")
                return
            import_file = parts[1]
            self.validate_import(import_file)
        else:
            self.console.print(f"[red]Unknown import command: {subcmd}[/red]")
            self.console.print("[yellow]Usage: /import [all|config|memories|conversations|backup|validate][/yellow]")

    def export_all_data(self, output_file: Optional[str]):
        """Export all Meton data."""
        self.console.print("\n[cyan]📦 Exporting complete Meton state...[/cyan]\n")

        try:
            with self.console.status("[cyan]Exporting data...[/cyan]"):
                export_path = self.export_manager.export_all(output_file)

            self.console.print(f"[green]✅ Export complete![/green]")
            self.console.print(f"[dim]Saved to: {export_path}[/dim]\n")

        except Exception as e:
            self.console.print(f"[red]❌ Export failed: {str(e)}[/red]\n")

    def export_config(self, output_file: Optional[str]):
        """Export configuration."""
        self.console.print("\n[cyan]📦 Exporting configuration...[/cyan]\n")

        try:
            export_path = self.export_manager.export_configuration(output_file)

            self.console.print(f"[green]✅ Configuration exported![/green]")
            self.console.print(f"[dim]Saved to: {export_path}[/dim]\n")

        except Exception as e:
            self.console.print(f"[red]❌ Export failed: {str(e)}[/red]\n")

    def export_memories(self, output_file: Optional[str]):
        """Export memories."""
        self.console.print("\n[cyan]📦 Exporting memories...[/cyan]\n")

        try:
            with self.console.status("[cyan]Exporting memories...[/cyan]"):
                export_path = self.export_manager.export_memories(output_file)

            self.console.print(f"[green]✅ Memories exported![/green]")
            self.console.print(f"[dim]Saved to: {export_path}[/dim]\n")

        except Exception as e:
            self.console.print(f"[red]❌ Export failed: {str(e)}[/red]\n")

    def export_conversations(self, output_file: Optional[str]):
        """Export conversations."""
        self.console.print("\n[cyan]📦 Exporting conversations...[/cyan]\n")

        try:
            with self.console.status("[cyan]Exporting conversations...[/cyan]"):
                export_path = self.export_manager.export_conversations(output_file)

            self.console.print(f"[green]✅ Conversations exported![/green]")
            self.console.print(f"[dim]Saved to: {export_path}[/dim]\n")

        except Exception as e:
            self.console.print(f"[red]❌ Export failed: {str(e)}[/red]\n")

    def export_analytics(self, output_file: Optional[str]):
        """Export analytics."""
        self.console.print("\n[cyan]📦 Exporting analytics...[/cyan]\n")

        try:
            with self.console.status("[cyan]Exporting analytics...[/cyan]"):
                export_path = self.export_manager.export_analytics(output_file)

            self.console.print(f"[green]✅ Analytics exported![/green]")
            self.console.print(f"[dim]Saved to: {export_path}[/dim]\n")

        except Exception as e:
            self.console.print(f"[red]❌ Export failed: {str(e)}[/red]\n")

    def create_backup(self, backup_name: Optional[str]):
        """Create backup archive."""
        self.console.print("\n[cyan]💾 Creating backup...[/cyan]\n")

        try:
            with self.console.status("[cyan]Creating backup archive...[/cyan]"):
                backup_path = self.export_manager.create_backup(backup_name)

            self.console.print(f"[green]✅ Backup created![/green]")
            self.console.print(f"[dim]Saved to: {backup_path}[/dim]\n")

        except Exception as e:
            self.console.print(f"[red]❌ Backup failed: {str(e)}[/red]\n")

    def import_all_data(self, import_file: str, merge: bool):
        """Import all Meton data."""
        self.console.print(f"\n[cyan]📥 Importing from {import_file}...[/cyan]\n")

        if merge:
            self.console.print("[yellow]Merge mode: Combining with existing data[/yellow]\n")
        else:
            self.console.print("[yellow]Replace mode: Overwriting existing data[/yellow]\n")

        try:
            with self.console.status("[cyan]Importing data...[/cyan]"):
                summary = self.import_manager.import_all(import_file, merge)

            self.console.print(f"[green]✅ Import complete![/green]\n")

            # Display summary
            self.console.print("[bold]Import Summary:[/bold]")
            for key, count in summary.get("counts", {}).items():
                self.console.print(f"  • {key}: {count} items")
            self.console.print()

        except Exception as e:
            self.console.print(f"[red]❌ Import failed: {str(e)}[/red]\n")

    def import_config(self, import_file: str):
        """Import configuration."""
        self.console.print(f"\n[cyan]📥 Importing configuration from {import_file}...[/cyan]\n")

        try:
            config = self.import_manager.import_configuration(import_file, apply=True)

            self.console.print(f"[green]✅ Configuration imported![/green]")
            self.console.print(f"[yellow]Note: Restart Meton for changes to take full effect[/yellow]\n")

        except Exception as e:
            self.console.print(f"[red]❌ Import failed: {str(e)}[/red]\n")

    def import_memories(self, import_file: str, merge: bool):
        """Import memories."""
        self.console.print(f"\n[cyan]📥 Importing memories from {import_file}...[/cyan]\n")

        try:
            count = self.import_manager.import_memories(import_file, merge)

            self.console.print(f"[green]✅ Imported {count} memories![/green]\n")

        except Exception as e:
            self.console.print(f"[red]❌ Import failed: {str(e)}[/red]\n")

    def import_conversations(self, import_file: str):
        """Import conversations."""
        self.console.print(f"\n[cyan]📥 Importing conversations from {import_file}...[/cyan]\n")

        try:
            count = self.import_manager.import_conversations(import_file, merge=True)

            self.console.print(f"[green]✅ Imported {count} conversations![/green]\n")

        except Exception as e:
            self.console.print(f"[red]❌ Import failed: {str(e)}[/red]\n")

    def restore_backup(self, backup_file: str):
        """Restore from backup."""
        self.console.print(f"\n[cyan]📥 Restoring from backup {backup_file}...[/cyan]\n")
        self.console.print("[yellow]⚠️  This will replace existing data![/yellow]\n")

        # Ask for confirmation
        confirm = input("Continue? (yes/no): ").strip().lower()
        if confirm != 'yes':
            self.console.print("[yellow]Restore cancelled[/yellow]\n")
            return

        try:
            with self.console.status("[cyan]Restoring backup...[/cyan]"):
                summary = self.import_manager.restore_backup(backup_file)

            self.console.print(f"[green]✅ Backup restored![/green]\n")

            # Display summary
            self.console.print("[bold]Restore Summary:[/bold]")
            for key, count in summary.get("counts", {}).items():
                self.console.print(f"  • {key}: {count} items")
            self.console.print()

            self.console.print("[yellow]⚠️  Restart Meton for changes to take full effect[/yellow]\n")

        except Exception as e:
            self.console.print(f"[red]❌ Restore failed: {str(e)}[/red]\n")

    def validate_import(self, import_file: str):
        """Validate import file."""
        self.console.print(f"\n[cyan]🔍 Validating {import_file}...[/cyan]\n")

        try:
            result = self.import_manager.validate_import_file(import_file)

            if result["valid"]:
                self.console.print("[green]✅ Import file is valid![/green]\n")
            else:
                self.console.print("[red]❌ Import file is invalid![/red]\n")

            # Show errors
            if result["errors"]:
                self.console.print("[bold red]Errors:[/bold red]")
                for error in result["errors"]:
                    self.console.print(f"  • {error}")
                self.console.print()

            # Show warnings
            if result["warnings"]:
                self.console.print("[bold yellow]Warnings:[/bold yellow]")
                for warning in result["warnings"]:
                    self.console.print(f"  • {warning}")
                self.console.print()

        except Exception as e:
            self.console.print(f"[red]❌ Validation failed: {str(e)}[/red]\n")

    # ========== End Export/Import Commands ==========

    # ========== Optimization Commands ==========

    def handle_optimize_command(self, command_str: str):
        """Handle optimization commands."""
        parts = command_str.split()
        subcommand = parts[0] if parts else ""

        if subcommand == "profile":
            self.show_performance_profile()
        elif subcommand == "cache" and len(parts) > 1:
            if parts[1] == "stats":
                self.show_cache_stats()
            elif parts[1] == "clear":
                self.clear_caches()
            else:
                self.console.print("[yellow]Usage: /optimize cache [stats|clear][/yellow]")
        elif subcommand == "report":
            self.show_optimization_report()
        elif subcommand == "benchmark":
            self.run_benchmarks()
        elif subcommand == "resources":
            self.show_resource_usage()
        else:
            self.console.print("[yellow]Usage: /optimize [profile|cache|report|benchmark|resources][/yellow]")

    def show_performance_profile(self):
        """Show performance profile."""
        self.console.print("\n[cyan]📊 Performance Profile[/cyan]\n")

        try:
            from optimization.profiler import get_profiler

            profiler = get_profiler()
            report = profiler.generate_profile_report()

            self.console.print(report)

        except Exception as e:
            self.console.print(f"[red]❌ Failed to generate profile: {str(e)}[/red]\n")

    def show_cache_stats(self):
        """Show cache statistics."""
        self.console.print("\n[cyan]📈 Cache Statistics[/cyan]\n")

        try:
            from optimization.cache_manager import get_cache_manager

            cache = get_cache_manager()
            stats = cache.get_stats()

            from rich.table import Table
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Enabled", "✅ Yes" if stats["enabled"] else "❌ No")
            table.add_row("Memory Cache Items", str(stats["memory_cache_items"]))
            table.add_row("Disk Cache Items", str(stats["disk_cache_items"]))
            table.add_row("Disk Cache Size", f"{stats['disk_cache_size_mb']:.2f} MB")
            table.add_row("Cache Hits", str(stats["hits"]))
            table.add_row("Cache Misses", str(stats["misses"]))
            table.add_row("Hit Rate", f"{stats['hit_rate_percent']:.1f}%")
            table.add_row("TTL", f"{stats['ttl_seconds']} seconds")

            self.console.print(table)
            self.console.print()

        except Exception as e:
            self.console.print(f"[red]❌ Failed to get cache stats: {str(e)}[/red]\n")

    def clear_caches(self):
        """Clear all caches."""
        self.console.print("\n[cyan]🗑️  Clearing caches...[/cyan]\n")

        try:
            from optimization.cache_manager import get_cache_manager

            cache = get_cache_manager()
            cache.clear()

            self.console.print("[green]✅ Caches cleared successfully![/green]\n")

        except Exception as e:
            self.console.print(f"[red]❌ Failed to clear caches: {str(e)}[/red]\n")

    def show_optimization_report(self):
        """Show comprehensive optimization report."""
        self.console.print("\n[cyan]📋 Optimization Report[/cyan]\n")

        try:
            from optimization.profiler import get_profiler
            from optimization.cache_manager import get_cache_manager
            from optimization.resource_monitor import get_resource_monitor

            profiler = get_profiler()
            cache = get_cache_manager()
            monitor = get_resource_monitor()

            # Profiler stats
            prof_stats = profiler.get_stats()
            self.console.print("[bold]Performance Profiling:[/bold]")
            self.console.print(f"  Function Profiles: {prof_stats['function_profiles']}")
            self.console.print(f"  Total Calls: {prof_stats['total_functions_called']}")
            self.console.print(f"  Avg Query Time: {prof_stats['avg_query_time']:.3f}s")

            # Cache stats
            cache_stats = cache.get_stats()
            self.console.print("\n[bold]Cache Performance:[/bold]")
            self.console.print(f"  Hit Rate: {cache_stats['hit_rate_percent']:.1f}%")
            self.console.print(f"  Memory Items: {cache_stats['memory_cache_items']}")
            self.console.print(f"  Disk Size: {cache_stats['disk_cache_size_mb']:.2f} MB")

            # Resource stats
            mon_stats = monitor.get_stats()
            usage = monitor.get_current_usage()
            self.console.print("\n[bold]Resource Usage:[/bold]")
            self.console.print(f"  CPU: {usage['cpu_percent']:.1f}%")
            self.console.print(f"  Memory: {usage['memory_mb']:.1f} MB ({usage['memory_percent']:.1f}%)")
            self.console.print(f"  Total Samples: {mon_stats['total_samples']}")

            # Bottlenecks
            bottlenecks = profiler.identify_bottlenecks(threshold_seconds=2.0)
            if bottlenecks:
                self.console.print("\n[bold yellow]⚠️  Bottlenecks:[/bold yellow]")
                for bottleneck in bottlenecks:
                    self.console.print(f"  • {bottleneck}")

            self.console.print()

        except Exception as e:
            self.console.print(f"[red]❌ Failed to generate report: {str(e)}[/red]\n")

    def run_benchmarks(self):
        """Run performance benchmarks."""
        self.console.print("\n[cyan]🏃 Running Performance Benchmarks...[/cyan]\n")
        self.console.print("[dim]This may take a minute...[/dim]\n")

        try:
            from optimization.benchmarks import run_benchmarks

            results = run_benchmarks()

            self.console.print("\n[green]✅ Benchmarks complete![/green]")
            self.console.print("[dim]Results displayed above[/dim]\n")

        except Exception as e:
            self.console.print(f"[red]❌ Benchmark failed: {str(e)}[/red]\n")

    def show_resource_usage(self):
        """Show current resource usage."""
        self.console.print("\n[cyan]💻 Resource Usage[/cyan]\n")

        try:
            from optimization.resource_monitor import get_resource_monitor

            monitor = get_resource_monitor()
            usage = monitor.get_current_usage()

            from rich.table import Table
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Resource", style="cyan")
            table.add_column("Current", style="green")

            table.add_row("CPU", f"{usage['cpu_percent']:.1f}%")
            table.add_row("Memory Used", f"{usage['memory_mb']:.1f} MB")
            table.add_row("Memory %", f"{usage['memory_percent']:.1f}%")
            table.add_row("Memory Available", f"{usage['memory_available_mb']:.1f} MB")
            table.add_row("Disk Usage", f"{usage['disk_usage_percent']:.1f}%")
            table.add_row("Disk Free", f"{usage['disk_free_gb']:.1f} GB")

            self.console.print(table)
            self.console.print()

            # Show peak if monitoring
            peak = monitor.get_peak_usage()
            if peak:
                self.console.print("[bold]Peak Usage:[/bold]")
                self.console.print(f"  CPU: {peak['peak_cpu_percent']:.1f}%")
                self.console.print(f"  Memory: {peak['peak_memory_mb']:.1f} MB ({peak['peak_memory_percent']:.1f}%)")
                self.console.print(f"  Samples: {peak['samples']}")
                self.console.print()

        except Exception as e:
            self.console.print(f"[red]❌ Failed to get resource usage: {str(e)}[/red]\n")

    # ========== End Optimization Commands ==========

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
