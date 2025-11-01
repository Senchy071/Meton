#!/usr/bin/env python3
"""Interactive CLI for Meton coding assistant.

This module provides a beautiful, interactive command-line interface using Rich.
It integrates the Model Manager, Conversation Manager, Agent, and Tools.
"""

import sys
import signal
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax

from core.config import Config
from core.models import ModelManager
from core.conversation import ConversationManager
from core.agent import MetonAgent
from tools.file_ops import FileOperationsTool
from tools.code_executor import CodeExecutorTool
from tools.web_search import WebSearchTool
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

        # CLI state
        self.running = True
        self.verbose = False
        
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

            # Initialize Agent
            self.console.print("  [dim]Loading agent...[/dim]")
            self.agent = MetonAgent(
                config=self.config,
                model_manager=self.model_manager,
                conversation=self.conversation,
                tools=[self.file_tool, self.code_tool, self.web_tool],
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
║  🧠 METON - Local Coding Assistant                                           ║
║  Wisdom in Action                                                            ║
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
        table.add_column("Command", style="yellow", width=20)
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
        
        status_text = f"""[cyan]Model:[/cyan]        {info['model']}
[cyan]Session:[/cyan]      {session_id}
[cyan]Messages:[/cyan]     {info['conversation_messages']}
[cyan]Tools:[/cyan]        {', '.join(info['tools'])}
[cyan]Max Iter:[/cyan]     {info['max_iterations']}
[cyan]Verbose:[/cyan]      {'ON' if info['verbose'] else 'OFF'}"""
        
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
