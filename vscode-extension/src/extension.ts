import * as vscode from 'vscode';
import { MetonClient } from './metonClient';
import { registerCommands } from './commands';
import { MetonStatusBar } from './statusBar';
import { MetonLSPServer } from './lsp/server';
import { ChatPanelProvider } from './webview/chatPanel';

let metonClient: MetonClient;
let statusBar: MetonStatusBar;
let lspServer: MetonLSPServer;

export function activate(context: vscode.ExtensionContext) {
    console.log('Meton extension is now active');

    // Initialize Meton client
    const config = vscode.workspace.getConfiguration('meton');
    const serverUrl = config.get<string>('serverUrl', 'http://localhost:8000');
    metonClient = new MetonClient(serverUrl);

    // Initialize status bar
    statusBar = new MetonStatusBar();
    context.subscriptions.push(statusBar.statusBarItem);

    // Register commands
    registerCommands(context, metonClient, statusBar);

    // Register LSP commands
    registerLSPCommands(context, metonClient);

    // Start LSP server
    lspServer = new MetonLSPServer(context, metonClient);
    lspServer.start(context);

    // Register chat panel
    const chatProvider = new ChatPanelProvider(context.extensionUri, metonClient);
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(
            ChatPanelProvider.viewType,
            chatProvider
        )
    );

    // Auto-index workspace if enabled
    if (config.get<boolean>('autoIndex', true)) {
        indexWorkspace();
    }

    // Check server connection
    checkServerConnection();
}

export function deactivate() {
    if (lspServer) {
        lspServer.stop();
    }
    if (metonClient) {
        metonClient.disconnect();
    }
}

function registerLSPCommands(context: vscode.ExtensionContext, client: MetonClient) {
    // Suggest Fix
    context.subscriptions.push(
        vscode.commands.registerCommand('meton.suggestFix', async (document: vscode.TextDocument, diagnostic: vscode.Diagnostic) => {
            const code = document.getText(diagnostic.range);
            const language = document.languageId;
            const query = `How do I fix this ${language} issue: ${diagnostic.message}\n\nCode:\n${code}`;

            try {
                const suggestion = await client.sendQuery(query);
                vscode.window.showInformationMessage(suggestion, { modal: true });
            } catch (error) {
                vscode.window.showErrorMessage(`Failed to get fix suggestion: ${error}`);
            }
        })
    );

    // Extract Method
    context.subscriptions.push(
        vscode.commands.registerCommand('meton.extractMethod', async (document: vscode.TextDocument, range: vscode.Range) => {
            const code = document.getText(range);
            const language = document.languageId;
            const query = `Extract this ${language} code into a method:\n\n${code}`;

            try {
                const suggestion = await client.sendQuery(query);
                const panel = vscode.window.createWebviewPanel(
                    'metonRefactor',
                    'Extract Method',
                    vscode.ViewColumn.Beside,
                    {}
                );
                panel.webview.html = `<pre>${suggestion}</pre>`;
            } catch (error) {
                vscode.window.showErrorMessage(`Failed to extract method: ${error}`);
            }
        })
    );

    // Simplify Code
    context.subscriptions.push(
        vscode.commands.registerCommand('meton.simplifyCode', async (document: vscode.TextDocument, range: vscode.Range) => {
            const code = document.getText(range);
            const language = document.languageId;
            const query = `Simplify this ${language} code:\n\n${code}`;

            try {
                const suggestion = await client.sendQuery(query);
                const panel = vscode.window.createWebviewPanel(
                    'metonRefactor',
                    'Simplify Code',
                    vscode.ViewColumn.Beside,
                    {}
                );
                panel.webview.html = `<pre>${suggestion}</pre>`;
            } catch (error) {
                vscode.window.showErrorMessage(`Failed to simplify code: ${error}`);
            }
        })
    );
}

async function checkServerConnection() {
    const isConnected = await metonClient.checkConnection();
    if (isConnected) {
        statusBar.setConnected();
        vscode.window.showInformationMessage('Meton: Connected to server');
    } else {
        statusBar.setDisconnected();
        vscode.window.showErrorMessage('Meton: Cannot connect to server. Please start Meton.');
    }
}

async function indexWorkspace() {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders) {
        return;
    }

    statusBar.setIndexing();
    try {
        await metonClient.indexWorkspace(workspaceFolders[0].uri.fsPath);
        statusBar.setConnected();
        vscode.window.showInformationMessage('Meton: Workspace indexed successfully');
    } catch (error) {
        statusBar.setDisconnected();
        vscode.window.showErrorMessage(`Meton: Failed to index workspace - ${error}`);
    }
}
