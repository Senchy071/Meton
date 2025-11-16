import * as vscode from 'vscode';
import { MetonClient } from '../metonClient';
import { MetonCodeActionProvider } from './codeActions';
import { MetonCompletionProvider } from './completions';
import { MetonHoverProvider } from './hover';

export class MetonLSPServer {
    private metonClient: MetonClient;

    constructor(context: vscode.ExtensionContext, metonClient: MetonClient) {
        this.metonClient = metonClient;
    }

    async start(context: vscode.ExtensionContext): Promise<void> {
        // For now, use direct VS Code APIs instead of full LSP server
        // Full LSP server would require separate Node.js process

        // Register providers directly
        this.registerDiagnostics(context);
        this.registerCodeActions(context);
        this.registerCompletions(context);
        this.registerHover(context);
    }

    private registerDiagnostics(context: vscode.ExtensionContext): void {
        const diagnosticCollection = vscode.languages.createDiagnosticCollection('meton');
        context.subscriptions.push(diagnosticCollection);

        // Run diagnostics on file open/save
        context.subscriptions.push(
            vscode.workspace.onDidOpenTextDocument(doc => this.updateDiagnostics(doc, diagnosticCollection))
        );
        context.subscriptions.push(
            vscode.workspace.onDidSaveTextDocument(doc => this.updateDiagnostics(doc, diagnosticCollection))
        );

        // Initial diagnostics for open documents
        vscode.workspace.textDocuments.forEach(doc => this.updateDiagnostics(doc, diagnosticCollection));
    }

    private async updateDiagnostics(
        document: vscode.TextDocument,
        collection: vscode.DiagnosticCollection
    ): Promise<void> {
        if (!this.shouldAnalyze(document)) {
            return;
        }

        try {
            const code = document.getText();
            const language = document.languageId;

            // Ask Meton to review code
            const review = await this.metonClient.reviewCode(code, language);

            // Parse review results into diagnostics
            const diagnostics = this.parseDiagnostics(review, document);
            collection.set(document.uri, diagnostics);
        } catch (error) {
            console.error('Failed to get diagnostics:', error);
        }
    }

    private parseDiagnostics(review: string, document: vscode.TextDocument): vscode.Diagnostic[] {
        const diagnostics: vscode.Diagnostic[] = [];

        // Parse review text for issues
        // Expected format: "Line X: [SEVERITY] message"
        const issueRegex = /Line (\d+): \[(CRITICAL|HIGH|MEDIUM|LOW)\] (.+)/g;
        let match;

        while ((match = issueRegex.exec(review)) !== null) {
            const lineNum = parseInt(match[1]) - 1;
            const severity = match[2];
            const message = match[3];

            const range = document.lineAt(Math.min(lineNum, document.lineCount - 1)).range;
            const diagnostic = new vscode.Diagnostic(
                range,
                message,
                this.severityToVSCode(severity)
            );
            diagnostic.source = 'Meton';
            diagnostics.push(diagnostic);
        }

        return diagnostics;
    }

    private severityToVSCode(severity: string): vscode.DiagnosticSeverity {
        switch (severity) {
            case 'CRITICAL':
            case 'HIGH':
                return vscode.DiagnosticSeverity.Error;
            case 'MEDIUM':
                return vscode.DiagnosticSeverity.Warning;
            case 'LOW':
                return vscode.DiagnosticSeverity.Information;
            default:
                return vscode.DiagnosticSeverity.Hint;
        }
    }

    private shouldAnalyze(document: vscode.TextDocument): boolean {
        // Only analyze code files
        const codeLanguages = ['python', 'javascript', 'typescript', 'java', 'cpp', 'c', 'go', 'rust'];
        return codeLanguages.includes(document.languageId) && document.uri.scheme === 'file';
    }

    private registerCodeActions(context: vscode.ExtensionContext): void {
        const provider = new MetonCodeActionProvider(this.metonClient);
        context.subscriptions.push(
            vscode.languages.registerCodeActionsProvider(
                { scheme: 'file', language: '*' },
                provider,
                { providedCodeActionKinds: MetonCodeActionProvider.providedCodeActionKinds }
            )
        );
    }

    private registerCompletions(context: vscode.ExtensionContext): void {
        const provider = new MetonCompletionProvider(this.metonClient);
        context.subscriptions.push(
            vscode.languages.registerCompletionItemProvider(
                { scheme: 'file', language: '*' },
                provider,
                '.'  // Trigger on dot
            )
        );
    }

    private registerHover(context: vscode.ExtensionContext): void {
        const provider = new MetonHoverProvider(this.metonClient);
        context.subscriptions.push(
            vscode.languages.registerHoverProvider(
                { scheme: 'file', language: '*' },
                provider
            )
        );
    }

    stop(): void {
        // Cleanup if needed
    }
}
