import * as vscode from 'vscode';
import { MetonClient } from '../metonClient';

export class MetonCompletionProvider implements vscode.CompletionItemProvider {
    constructor(private metonClient: MetonClient) {}

    async provideCompletionItems(
        document: vscode.TextDocument,
        position: vscode.Position,
        token: vscode.CancellationToken,
        context: vscode.CompletionContext
    ): Promise<vscode.CompletionItem[]> {
        // Get context around cursor
        const linePrefix = document.lineAt(position).text.substr(0, position.character);

        // Only provide completions for specific triggers
        if (!this.shouldProvideCompletions(linePrefix, context)) {
            return [];
        }

        try {
            // Get code context (previous lines)
            const contextLines = this.getContext(document, position, 10);
            const language = document.languageId;

            // Ask Meton for suggestions
            const query = `Given this ${language} code context, suggest completions for: "${linePrefix}"\n\nContext:\n${contextLines}`;
            const suggestions = await this.metonClient.sendQuery(query);

            // Parse suggestions into completion items
            return this.parseCompletions(suggestions);
        } catch (error) {
            console.error('Completion error:', error);
            return [];
        }
    }

    private shouldProvideCompletions(linePrefix: string, context: vscode.CompletionContext): boolean {
        // Only trigger on specific patterns
        return (
            context.triggerKind === vscode.CompletionTriggerKind.TriggerCharacter ||
            linePrefix.includes('def ') ||
            linePrefix.includes('class ') ||
            linePrefix.includes('import ')
        );
    }

    private getContext(document: vscode.TextDocument, position: vscode.Position, lines: number): string {
        const startLine = Math.max(0, position.line - lines);
        const range = new vscode.Range(startLine, 0, position.line, position.character);
        return document.getText(range);
    }

    private parseCompletions(suggestions: string): vscode.CompletionItem[] {
        const items: vscode.CompletionItem[] = [];

        // Simple parsing - look for code blocks
        const codeBlockRegex = /```(?:\w+)?\n(.*?)```/gs;
        let match;

        while ((match = codeBlockRegex.exec(suggestions)) !== null) {
            const code = match[1].trim();
            const item = new vscode.CompletionItem(code, vscode.CompletionItemKind.Snippet);
            item.detail = 'Meton suggestion';
            item.insertText = new vscode.SnippetString(code);
            items.push(item);
        }

        return items;
    }
}
