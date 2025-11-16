import * as vscode from 'vscode';
import { MetonClient } from './metonClient';
import { MetonStatusBar } from './statusBar';

export function registerCommands(
    context: vscode.ExtensionContext,
    client: MetonClient,
    statusBar: MetonStatusBar
) {
    // Explain Code
    context.subscriptions.push(
        vscode.commands.registerCommand('meton.explainCode', async () => {
            await handleCodeCommand(client, statusBar, 'explain');
        })
    );

    // Review Code
    context.subscriptions.push(
        vscode.commands.registerCommand('meton.reviewCode', async () => {
            await handleCodeCommand(client, statusBar, 'review');
        })
    );

    // Generate Tests
    context.subscriptions.push(
        vscode.commands.registerCommand('meton.generateTests', async () => {
            await handleCodeCommand(client, statusBar, 'tests');
        })
    );

    // Refactor
    context.subscriptions.push(
        vscode.commands.registerCommand('meton.refactor', async () => {
            await handleCodeCommand(client, statusBar, 'refactor');
        })
    );

    // Chat
    context.subscriptions.push(
        vscode.commands.registerCommand('meton.chat', async () => {
            const query = await vscode.window.showInputBox({
                prompt: 'Ask Meton anything',
                placeHolder: 'Enter your question...'
            });

            if (query) {
                statusBar.setProcessing();
                try {
                    const response = await client.sendQuery(query);
                    showResponse(response);
                    statusBar.setConnected();
                } catch (error) {
                    vscode.window.showErrorMessage(`Meton error: ${error}`);
                    statusBar.setDisconnected();
                }
            }
        })
    );

    // Index Workspace
    context.subscriptions.push(
        vscode.commands.registerCommand('meton.indexWorkspace', async () => {
            const workspaceFolders = vscode.workspace.workspaceFolders;
            if (!workspaceFolders) {
                vscode.window.showErrorMessage('No workspace folder open');
                return;
            }

            statusBar.setIndexing();
            try {
                await client.indexWorkspace(workspaceFolders[0].uri.fsPath);
                vscode.window.showInformationMessage('Workspace indexed successfully');
                statusBar.setConnected();
            } catch (error) {
                vscode.window.showErrorMessage(`Indexing failed: ${error}`);
                statusBar.setDisconnected();
            }
        })
    );
}

async function handleCodeCommand(
    client: MetonClient,
    statusBar: MetonStatusBar,
    action: 'explain' | 'review' | 'tests' | 'refactor'
) {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showErrorMessage('No active editor');
        return;
    }

    const selection = editor.selection;
    const code = editor.document.getText(selection);
    if (!code) {
        vscode.window.showErrorMessage('No code selected');
        return;
    }

    const language = editor.document.languageId;

    statusBar.setProcessing();
    try {
        let response: string;
        switch (action) {
            case 'explain':
                response = await client.explainCode(code, language);
                break;
            case 'review':
                response = await client.reviewCode(code, language);
                break;
            case 'tests':
                response = await client.generateTests(code, language);
                break;
            case 'refactor':
                response = await client.suggestRefactorings(code, language);
                break;
        }
        showResponse(response);
        statusBar.setConnected();
    } catch (error) {
        vscode.window.showErrorMessage(`Meton error: ${error}`);
        statusBar.setDisconnected();
    }
}

function showResponse(response: string) {
    const panel = vscode.window.createWebviewPanel(
        'metonResponse',
        'Meton Response',
        vscode.ViewColumn.Beside,
        { enableScripts: true }
    );

    panel.webview.html = getWebviewContent(response);
}

function getWebviewContent(content: string): string {
    // Convert markdown to HTML (simplified)
    const html = content.replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');

    return `<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Meton Response</title>
        <style>
            body {
                font-family: var(--vscode-font-family);
                padding: 20px;
                line-height: 1.6;
            }
            pre {
                background: var(--vscode-textBlockQuote-background);
                padding: 10px;
                border-radius: 4px;
                overflow-x: auto;
            }
            code {
                font-family: var(--vscode-editor-font-family);
            }
            h1, h2, h3 {
                color: var(--vscode-foreground);
            }
        </style>
    </head>
    <body>
        ${html}
    </body>
    </html>`;
}
