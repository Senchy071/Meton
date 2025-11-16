import * as vscode from 'vscode';

export class MetonStatusBar {
    public statusBarItem: vscode.StatusBarItem;

    constructor() {
        this.statusBarItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Right,
            100
        );
        this.statusBarItem.command = 'meton.chat';
        this.setDisconnected();
        this.statusBarItem.show();
    }

    setConnected(): void {
        this.statusBarItem.text = '$(check) Meton';
        this.statusBarItem.tooltip = 'Meton: Connected';
        this.statusBarItem.backgroundColor = undefined;
    }

    setDisconnected(): void {
        this.statusBarItem.text = '$(x) Meton';
        this.statusBarItem.tooltip = 'Meton: Disconnected';
        this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
    }

    setProcessing(): void {
        this.statusBarItem.text = '$(sync~spin) Meton';
        this.statusBarItem.tooltip = 'Meton: Processing...';
        this.statusBarItem.backgroundColor = undefined;
    }

    setIndexing(): void {
        this.statusBarItem.text = '$(database) Meton';
        this.statusBarItem.tooltip = 'Meton: Indexing workspace...';
        this.statusBarItem.backgroundColor = undefined;
    }
}
