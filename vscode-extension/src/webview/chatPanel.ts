import * as vscode from 'vscode';
import { MetonClient } from '../metonClient';

export class ChatPanelProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'metonChat';
    private _view?: vscode.WebviewView;
    private chatHistory: Array<{role: string, content: string}> = [];

    constructor(
        private readonly _extensionUri: vscode.Uri,
        private metonClient: MetonClient
    ) {}

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken
    ) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };

        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

        // Handle messages from webview
        webviewView.webview.onDidReceiveMessage(async (data) => {
            switch (data.type) {
                case 'sendMessage':
                    await this.handleMessage(data.message);
                    break;
                case 'clearChat':
                    this.chatHistory = [];
                    this.updateChat();
                    break;
            }
        });
    }

    private async handleMessage(message: string) {
        // Add user message to history
        this.chatHistory.push({ role: 'user', content: message });
        this.updateChat();

        try {
            // Get response from Meton
            const response = await this.metonClient.sendQuery(message);

            // Add assistant message to history
            this.chatHistory.push({ role: 'assistant', content: response });
            this.updateChat();
        } catch (error) {
            this.chatHistory.push({
                role: 'assistant',
                content: `Error: ${error}`
            });
            this.updateChat();
        }
    }

    private updateChat() {
        if (this._view) {
            this._view.webview.postMessage({
                type: 'updateChat',
                history: this.chatHistory
            });
        }
    }

    private _getHtmlForWebview(webview: vscode.Webview): string {
        return `<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Meton Chat</title>
            <style>
                body {
                    font-family: var(--vscode-font-family);
                    padding: 10px;
                    margin: 0;
                }
                #chat-container {
                    height: calc(100vh - 100px);
                    overflow-y: auto;
                    padding: 10px;
                }
                .message {
                    margin-bottom: 15px;
                    padding: 10px;
                    border-radius: 5px;
                }
                .user {
                    background: var(--vscode-input-background);
                    text-align: right;
                }
                .assistant {
                    background: var(--vscode-editor-background);
                }
                #input-container {
                    position: fixed;
                    bottom: 0;
                    left: 0;
                    right: 0;
                    padding: 10px;
                    background: var(--vscode-editor-background);
                }
                #message-input {
                    width: calc(100% - 80px);
                    padding: 10px;
                    background: var(--vscode-input-background);
                    color: var(--vscode-input-foreground);
                    border: 1px solid var(--vscode-input-border);
                    border-radius: 3px;
                }
                button {
                    padding: 10px 15px;
                    background: var(--vscode-button-background);
                    color: var(--vscode-button-foreground);
                    border: none;
                    border-radius: 3px;
                    cursor: pointer;
                }
                button:hover {
                    background: var(--vscode-button-hoverBackground);
                }
            </style>
        </head>
        <body>
            <div id="chat-container"></div>
            <div id="input-container">
                <input type="text" id="message-input" placeholder="Ask Meton anything..." />
                <button id="send-btn">Send</button>
                <button id="clear-btn">Clear</button>
            </div>
            <script>
                const vscode = acquireVsCodeApi();
                const chatContainer = document.getElementById('chat-container');
                const messageInput = document.getElementById('message-input');
                const sendBtn = document.getElementById('send-btn');
                const clearBtn = document.getElementById('clear-btn');

                sendBtn.addEventListener('click', sendMessage);
                clearBtn.addEventListener('click', () => {
                    vscode.postMessage({ type: 'clearChat' });
                });

                messageInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') sendMessage();
                });

                function sendMessage() {
                    const message = messageInput.value.trim();
                    if (!message) return;

                    vscode.postMessage({
                        type: 'sendMessage',
                        message: message
                    });

                    messageInput.value = '';
                }

                window.addEventListener('message', (event) => {
                    const message = event.data;
                    if (message.type === 'updateChat') {
                        renderChat(message.history);
                    }
                });

                function renderChat(history) {
                    chatContainer.innerHTML = history.map(msg =>
                        \`<div class="message \${msg.role}">
                            <strong>\${msg.role === 'user' ? 'You' : 'Meton'}:</strong><br/>
                            \${msg.content}
                        </div>\`
                    ).join('');
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }
            </script>
        </body>
        </html>`;
    }
}
