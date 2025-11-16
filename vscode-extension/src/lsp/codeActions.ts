import * as vscode from 'vscode';
import { MetonClient } from '../metonClient';

export class MetonCodeActionProvider implements vscode.CodeActionProvider {
    public static readonly providedCodeActionKinds = [
        vscode.CodeActionKind.QuickFix,
        vscode.CodeActionKind.Refactor
    ];

    constructor(private metonClient: MetonClient) {}

    async provideCodeActions(
        document: vscode.TextDocument,
        range: vscode.Range | vscode.Selection,
        context: vscode.CodeActionContext,
        token: vscode.CancellationToken
    ): Promise<vscode.CodeAction[]> {
        const actions: vscode.CodeAction[] = [];

        // Add quick fixes for diagnostics
        for (const diagnostic of context.diagnostics) {
            if (diagnostic.source === 'Meton') {
                actions.push(this.createFixAction(document, diagnostic));
            }
        }

        // Add refactoring actions if code is selected
        if (!range.isEmpty) {
            actions.push(...this.createRefactorActions(document, range));
        }

        return actions;
    }

    private createFixAction(
        document: vscode.TextDocument,
        diagnostic: vscode.Diagnostic
    ): vscode.CodeAction {
        const action = new vscode.CodeAction(
            'Ask Meton for fix suggestion',
            vscode.CodeActionKind.QuickFix
        );

        action.command = {
            command: 'meton.suggestFix',
            title: 'Get fix suggestion',
            arguments: [document, diagnostic]
        };

        action.diagnostics = [diagnostic];
        action.isPreferred = false;

        return action;
    }

    private createRefactorActions(
        document: vscode.TextDocument,
        range: vscode.Range
    ): vscode.CodeAction[] {
        const actions: vscode.CodeAction[] = [];

        // Extract method
        const extractMethod = new vscode.CodeAction(
            'Extract to method',
            vscode.CodeActionKind.RefactorExtract
        );
        extractMethod.command = {
            command: 'meton.extractMethod',
            title: 'Extract to method',
            arguments: [document, range]
        };
        actions.push(extractMethod);

        // Simplify code
        const simplify = new vscode.CodeAction(
            'Simplify code',
            vscode.CodeActionKind.RefactorRewrite
        );
        simplify.command = {
            command: 'meton.simplifyCode',
            title: 'Simplify code',
            arguments: [document, range]
        };
        actions.push(simplify);

        return actions;
    }
}
