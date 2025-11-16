import * as vscode from 'vscode';
import { MetonClient } from './metonClient';
import { registerCommands } from './commands';
import { MetonStatusBar } from './statusBar';

let metonClient: MetonClient;
let statusBar: MetonStatusBar;

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

    // Auto-index workspace if enabled
    if (config.get<boolean>('autoIndex', true)) {
        indexWorkspace();
    }

    // Check server connection
    checkServerConnection();
}

export function deactivate() {
    if (metonClient) {
        metonClient.disconnect();
    }
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
