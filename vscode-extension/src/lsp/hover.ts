import * as vscode from 'vscode';
import { MetonClient } from '../metonClient';

export class MetonHoverProvider implements vscode.HoverProvider {
    constructor(private metonClient: MetonClient) {}

    async provideHover(
        document: vscode.TextDocument,
        position: vscode.Position,
        token: vscode.CancellationToken
    ): Promise<vscode.Hover | undefined> {
        // Get word at position
        const wordRange = document.getWordRangeAtPosition(position);
        if (!wordRange) {
            return undefined;
        }

        const word = document.getText(wordRange);
        const language = document.languageId;

        try {
            // Get context
            const lineText = document.lineAt(position.line).text;

            // Ask Meton to explain
            const query = `Briefly explain what "${word}" does in this ${language} context: ${lineText}`;
            const explanation = await this.metonClient.sendQuery(query);

            const markdown = new vscode.MarkdownString();
            markdown.appendMarkdown(`**Meton Explanation:**\n\n${explanation}`);
            markdown.isTrusted = true;

            return new vscode.Hover(markdown, wordRange);
        } catch (error) {
            return undefined;
        }
    }
}
