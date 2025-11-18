#!/usr/bin/env python3
"""
Gradio Web UI for Meton AI Assistant.

Provides a browser-based interface with:
- Chat interface with message history
- File upload and management
- Real-time settings control
- Tool toggling
- Conversation export
- Performance metrics
"""

import gradio as gr
import tempfile
import shutil
import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, asdict

# Meton components
from core.config import Config
from core.models import ModelManager
from core.conversation import ConversationManager
from core.agent import MetonAgent
from tools.file_ops import FileOperationsTool
from tools.code_executor import CodeExecutorTool
from tools.web_search import WebSearchTool
from tools.codebase_search import CodebaseSearchTool


@dataclass
class ConversationMessage:
    """Single message in conversation."""
    role: str  # user or assistant
    content: str
    timestamp: str
    metadata: Optional[Dict] = None


class MetonWebUI:
    """Gradio-based web interface for Meton."""

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize Meton Web UI.

        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = Config(config_path)

        # Meton components (lazy-initialized)
        self.model_manager: Optional[ModelManager] = None
        self.conversation: Optional[ConversationManager] = None
        self.agent: Optional[MetonAgent] = None

        # Tools
        self.file_tool: Optional[FileOperationsTool] = None
        self.code_tool: Optional[CodeExecutorTool] = None
        self.web_tool: Optional[WebSearchTool] = None
        self.codebase_search_tool: Optional[CodebaseSearchTool] = None

        # Session state
        self.conversation_history = []
        self.uploaded_files = []
        self.temp_dir = tempfile.mkdtemp(prefix="meton_web_")

        # Current settings
        self.current_model = self.config.config.models.primary
        self.tools_enabled = {
            "web_search": False,
            "reflection": False,
            "chain_of_thought": False,
            "parallel_execution": False
        }

        # Status
        self.agent_status = "Not initialized"

    def initialize_agent(self) -> str:
        """
        Initialize Meton agent.

        Returns:
            Status message
        """
        try:
            # Initialize Model Manager
            self.model_manager = ModelManager(self.config)

            # Initialize Conversation Manager
            self.conversation = ConversationManager(self.config)

            # Initialize Tools
            self.file_tool = FileOperationsTool(self.config)
            self.code_tool = CodeExecutorTool(self.config)
            self.web_tool = WebSearchTool(self.config)
            self.codebase_search_tool = CodebaseSearchTool(self.config)

            # Initialize Agent
            self.agent = MetonAgent(
                config=self.config,
                model_manager=self.model_manager,
                conversation=self.conversation,
                tools=[self.file_tool, self.code_tool, self.web_tool, self.codebase_search_tool],
                verbose=False
            )

            self.agent_status = "Ready"
            return "Agent initialized successfully"

        except Exception as e:
            self.agent_status = f"Error: {str(e)}"
            return f"Failed to initialize agent: {str(e)}"

    def process_message(
        self,
        message: str,
        history: List[Tuple[str, str]]
    ) -> Tuple[List[Tuple[str, str]], str]:
        """
        Process user message and return updated history.

        Args:
            message: User message
            history: Current conversation history (list of [user_msg, bot_msg])

        Returns:
            Tuple of (updated_history, empty_string_for_input)
        """
        if not message or not message.strip():
            return history, ""

        try:
            # Initialize agent if needed
            if self.agent is None or self.agent_status == "Not initialized":
                init_msg = self.initialize_agent()
                if "Failed" in init_msg:
                    history.append((message, f"❌ {init_msg}"))
                    return history, ""

            # Update status
            self.agent_status = "Processing..."

            # Process message with real agent
            response = self.agent.run(message)

            # Add to conversation
            msg_record = ConversationMessage(
                role="user",
                content=message,
                timestamp=datetime.now().isoformat(),
                metadata={"tools_enabled": self.tools_enabled.copy()}
            )
            self.conversation_history.append(msg_record)

            response_record = ConversationMessage(
                role="assistant",
                content=response,
                timestamp=datetime.now().isoformat(),
                metadata={"model": self.current_model}
            )
            self.conversation_history.append(response_record)

            # Update Gradio history
            history.append((message, response))

            # Update status
            self.agent_status = "Ready"

            return history, ""

        except Exception as e:
            error_msg = f"❌ Error processing message: {str(e)}"
            history.append((message, error_msg))
            self.agent_status = "Error"
            return history, ""

    def _simulate_agent_response(self, message: str) -> str:
        """
        Simulate agent response for testing.

        In production, this is replaced by actual agent call.

        Args:
            message: User message

        Returns:
            Simulated response
        """
        # Simple keyword-based responses for testing
        message_lower = message.lower()

        if "hello" in message_lower or "hi" in message_lower:
            return "Hello! I'm Meton, your local AI coding assistant. How can I help you today?"

        elif "files" in message_lower or "upload" in message_lower:
            if self.uploaded_files:
                files_list = "\n".join([f"- {f}" for f in self.uploaded_files])
                return f"**Uploaded Files:**\n{files_list}\n\nI can help you analyze or work with these files."
            else:
                return "No files uploaded yet. You can upload files using the file upload panel on the right."

        elif "code" in message_lower:
            return "I can help you with:\n- Writing code\n- Debugging issues\n- Code review\n- Refactoring\n- Testing\n\nWhat would you like to work on?"

        elif "help" in message_lower:
            return """**Meton Capabilities:**

📁 **File Operations:** Upload and analyze code files
🔍 **Code Search:** Semantic search through codebase
🐛 **Debugging:** Find and fix issues
♻️ **Refactoring:** Improve code quality
✅ **Testing:** Generate tests
📝 **Documentation:** Generate docs

Use the settings panel to enable additional tools like web search and reflection."""

        else:
            return f"You said: {message}\n\n(This is a simulated response. In production, the actual Meton agent would process this query using available tools and models.)"

    def upload_file(self, files: List) -> Tuple[str, str]:
        """
        Handle file upload.

        Args:
            files: List of uploaded file objects

        Returns:
            Tuple of (file_list_text, status_message)
        """
        if not files:
            return "", "No files selected"

        try:
            uploaded_count = 0

            for file_obj in files:
                if file_obj is None:
                    continue

                # Get file info
                file_path = file_obj.name if hasattr(file_obj, 'name') else str(file_obj)
                file_name = Path(file_path).name

                # Check file size
                max_size_mb = self.config.get("web_ui", {}).get("max_file_size_mb", 10)
                file_size = os.path.getsize(file_path)

                if file_size > max_size_mb * 1024 * 1024:
                    return self._get_file_list(), f"❌ File {file_name} exceeds {max_size_mb}MB limit"

                # Copy to temp directory
                dest_path = Path(self.temp_dir) / file_name
                shutil.copy2(file_path, dest_path)

                # Add to uploaded files list
                if file_name not in self.uploaded_files:
                    self.uploaded_files.append(file_name)
                    uploaded_count += 1

            file_list = self._get_file_list()
            status = f"✅ Uploaded {uploaded_count} file(s)" if uploaded_count > 0 else "Files already uploaded"

            return file_list, status

        except Exception as e:
            return self._get_file_list(), f"❌ Upload failed: {str(e)}"

    def _get_file_list(self) -> str:
        """Get formatted list of uploaded files."""
        if not self.uploaded_files:
            return "No files uploaded"

        return "\n".join([f"📄 {file}" for file in self.uploaded_files])

    def delete_file(self, file_name: str) -> Tuple[str, str]:
        """
        Delete uploaded file.

        Args:
            file_name: Name of file to delete

        Returns:
            Tuple of (updated_file_list, status_message)
        """
        try:
            if file_name in self.uploaded_files:
                # Remove from list
                self.uploaded_files.remove(file_name)

                # Delete from temp dir
                file_path = Path(self.temp_dir) / file_name
                if file_path.exists():
                    file_path.unlink()

                return self._get_file_list(), f"✅ Deleted {file_name}"
            else:
                return self._get_file_list(), f"❌ File {file_name} not found"

        except Exception as e:
            return self._get_file_list(), f"❌ Delete failed: {str(e)}"

    def toggle_tool(self, tool_name: str, enabled: bool) -> str:
        """
        Enable/disable a tool.

        Args:
            tool_name: Name of tool to toggle
            enabled: Enable or disable

        Returns:
            Status message
        """
        if tool_name in self.tools_enabled:
            self.tools_enabled[tool_name] = enabled
            status = "enabled" if enabled else "disabled"
            return f"✅ {tool_name.replace('_', ' ').title()}: {status}"
        else:
            return f"❌ Unknown tool: {tool_name}"

    def update_model(self, model_name: str) -> str:
        """
        Update current model.

        Args:
            model_name: Model to switch to

        Returns:
            Status message
        """
        self.current_model = model_name
        return f"✅ Model updated: {model_name}"

    def clear_conversation(self) -> List[Tuple[str, str]]:
        """
        Clear conversation history.

        Returns:
            Empty conversation history
        """
        self.conversation_history = []
        self.agent_status = "Ready"
        return []

    def export_conversation(self, format: str = "markdown") -> str:
        """
        Export conversation to file.

        Args:
            format: Export format (markdown, json, txt)

        Returns:
            Path to exported file
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if format == "markdown":
                filename = f"conversation_{timestamp}.md"
                filepath = Path(self.temp_dir) / filename

                with open(filepath, 'w') as f:
                    f.write(f"# Meton Conversation - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                    for msg in self.conversation_history:
                        role_emoji = "👤" if msg.role == "user" else "🤖"
                        f.write(f"## {role_emoji} {msg.role.title()}\n")
                        f.write(f"*{msg.timestamp}*\n\n")
                        f.write(f"{msg.content}\n\n")
                        f.write("---\n\n")

            elif format == "json":
                filename = f"conversation_{timestamp}.json"
                filepath = Path(self.temp_dir) / filename

                data = [asdict(msg) for msg in self.conversation_history]

                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)

            elif format == "txt":
                filename = f"conversation_{timestamp}.txt"
                filepath = Path(self.temp_dir) / filename

                with open(filepath, 'w') as f:
                    f.write(f"Meton Conversation - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 60 + "\n\n")

                    for msg in self.conversation_history:
                        f.write(f"[{msg.role.upper()}] {msg.timestamp}\n")
                        f.write(f"{msg.content}\n")
                        f.write("-" * 60 + "\n\n")

            else:
                return f"❌ Unsupported format: {format}"

            return str(filepath)

        except Exception as e:
            return f"❌ Export failed: {str(e)}"

    def get_status(self) -> Dict[str, Any]:
        """
        Get current UI status.

        Returns:
            Status dictionary
        """
        return {
            "agent_status": self.agent_status,
            "current_model": self.current_model,
            "tools_enabled": self.tools_enabled.copy(),
            "uploaded_files_count": len(self.uploaded_files),
            "conversation_messages": len(self.conversation_history)
        }

    def cleanup(self):
        """Clean up temporary files."""
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"Warning: Failed to clean up temp directory: {e}")

    def build_interface(self) -> gr.Blocks:
        """
        Build Gradio interface.

        Returns:
            Gradio Blocks interface
        """
        theme_name = self.config.get("web_ui", {}).get("theme", "soft")

        # Map theme names to Gradio themes
        theme_map = {
            "soft": gr.themes.Soft(),
            "default": gr.themes.Default(),
            "monochrome": gr.themes.Monochrome()
        }
        theme = theme_map.get(theme_name, gr.themes.Soft())

        with gr.Blocks(theme=theme, title="Meton AI Assistant") as demo:
            gr.Markdown("# 🤖 Meton - Local AI Coding Assistant")
            gr.Markdown("*Powered by local LLMs with RAG, skills, and advanced agent features*")

            with gr.Row():
                # Left column: Chat
                with gr.Column(scale=2):
                    chatbot = gr.Chatbot(
                        height=500,
                        label="Conversation",
                        show_label=True,
                        avatar_images=(None, "🤖")
                    )

                    with gr.Row():
                        msg = gr.Textbox(
                            placeholder="Ask me anything about code, debugging, refactoring...",
                            show_label=False,
                            scale=4,
                            lines=1
                        )
                        send_btn = gr.Button("Send", variant="primary", scale=1)

                    with gr.Row():
                        clear_btn = gr.Button("🗑️ Clear", size="sm")
                        export_md_btn = gr.Button("📄 Export MD", size="sm")
                        export_json_btn = gr.Button("📋 Export JSON", size="sm")

                # Right column: Controls
                with gr.Column(scale=1):
                    # Model settings
                    gr.Markdown("### ⚙️ Settings")
                    model_dropdown = gr.Dropdown(
                        choices=["qwen2.5:32b-instruct-q5_K_M", "llama3.1:8b", "mistral:latest"],
                        value="qwen2.5:32b-instruct-q5_K_M",
                        label="Model",
                        interactive=True
                    )

                    # Tool toggles
                    gr.Markdown("### 🛠️ Tools")
                    web_toggle = gr.Checkbox(label="Web Search", value=False)
                    reflect_toggle = gr.Checkbox(label="Self-Reflection", value=False)
                    cot_toggle = gr.Checkbox(label="Chain-of-Thought", value=False)
                    parallel_toggle = gr.Checkbox(label="Parallel Execution", value=False)

                    # File upload
                    gr.Markdown("### 📁 Files")
                    file_upload = gr.File(
                        label="Upload Files",
                        file_count="multiple",
                        file_types=[".py", ".js", ".txt", ".md", ".json", ".yaml", ".yml"]
                    )
                    file_list = gr.Textbox(
                        label="Uploaded Files",
                        value="No files uploaded",
                        interactive=False,
                        lines=5
                    )

                    # Status
                    gr.Markdown("### 📊 Status")
                    status_text = gr.Textbox(
                        label="Agent Status",
                        value="Not initialized",
                        interactive=False
                    )

            # Hidden components for exports
            export_file = gr.File(label="Download", visible=False)

            # Event handlers
            def send_message(msg, history):
                result_history, empty = self.process_message(msg, history)
                return result_history, empty, self.agent_status

            # Send button
            send_btn.click(
                fn=send_message,
                inputs=[msg, chatbot],
                outputs=[chatbot, msg, status_text]
            )

            # Enter key
            msg.submit(
                fn=send_message,
                inputs=[msg, chatbot],
                outputs=[chatbot, msg, status_text]
            )

            # Clear conversation
            clear_btn.click(
                fn=self.clear_conversation,
                outputs=[chatbot]
            )

            # File upload
            def handle_upload(files):
                file_list_text, status = self.upload_file(files)
                return file_list_text, status

            file_upload.change(
                fn=handle_upload,
                inputs=[file_upload],
                outputs=[file_list, status_text]
            )

            # Tool toggles
            web_toggle.change(
                fn=lambda enabled: self.toggle_tool("web_search", enabled),
                inputs=[web_toggle],
                outputs=[status_text]
            )

            reflect_toggle.change(
                fn=lambda enabled: self.toggle_tool("reflection", enabled),
                inputs=[reflect_toggle],
                outputs=[status_text]
            )

            cot_toggle.change(
                fn=lambda enabled: self.toggle_tool("chain_of_thought", enabled),
                inputs=[cot_toggle],
                outputs=[status_text]
            )

            parallel_toggle.change(
                fn=lambda enabled: self.toggle_tool("parallel_execution", enabled),
                inputs=[parallel_toggle],
                outputs=[status_text]
            )

            # Model change
            model_dropdown.change(
                fn=self.update_model,
                inputs=[model_dropdown],
                outputs=[status_text]
            )

            # Export handlers
            def export_md():
                filepath = self.export_conversation("markdown")
                if not filepath.startswith("❌"):
                    return gr.File.update(value=filepath, visible=True)
                else:
                    return gr.File.update(visible=False)

            def export_json():
                filepath = self.export_conversation("json")
                if not filepath.startswith("❌"):
                    return gr.File.update(value=filepath, visible=True)
                else:
                    return gr.File.update(visible=False)

            export_md_btn.click(
                fn=export_md,
                outputs=[export_file]
            )

            export_json_btn.click(
                fn=export_json,
                outputs=[export_file]
            )

        return demo

    def launch(
        self,
        share: bool = False,
        auth: Optional[Tuple[str, str]] = None,
        **kwargs
    ):
        """
        Launch Gradio interface.

        Args:
            share: Enable Gradio sharing
            auth: Optional tuple of (username, password)
            **kwargs: Additional Gradio launch arguments
        """
        # Build interface
        demo = self.build_interface()

        # Get config
        web_config = self.config.get("web_ui", {})
        host = web_config.get("host", "127.0.0.1")
        port = web_config.get("port", 7860)

        # Launch
        try:
            demo.queue()  # Enable queueing for better concurrency
            demo.launch(
                server_name=host,
                server_port=port,
                share=share,
                auth=auth,
                show_error=True,
                **kwargs
            )
        finally:
            # Cleanup on exit
            self.cleanup()
