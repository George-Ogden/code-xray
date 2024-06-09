import * as vscode from 'vscode';

type Annotation = {
    timestamp: number;
    position: vscode.Position;
    summary: string;
    description: string;
};

type Annotations = {
    [line: number]: Annotation[];
};

export class AnnotationInsetProvider implements vscode.Disposable {
    private insets: vscode.WebviewEditorInset[] = [];
    public _onDidChangeCodeLenses: vscode.EventEmitter<void> = new vscode.EventEmitter<void>();
    public readonly onDidChangeCodeLenses: vscode.Event<void> = this._onDidChangeCodeLenses.event;
    public readonly onCodeLensRefreshRequest = (data: Annotations) => this._onCodeLensRefreshRequest(data);
    private data: Annotations = {};

    constructor() {}
    dispose() {
        this.removeInsets();
    }

    private _onCodeLensRefreshRequest(data: Annotations) {
        this.data = data;
        this.updateInsets();
    }

    private updateInsets(): void {
        this.removeInsets();
        this.createInsets();
    }

    private removeInsets(): void {
        for (const inset of this.insets) {
            inset.dispose();
        }
        this.insets = [];
    }

    private createInsets(): void {
        for (const [line, annotations] of Object.entries(this.data)) {
            const inset = this.createInset(Number(line), annotations);
            if (inset) {
                this.insets.push(inset);
            }
        }
    }

    private createInset(line: number, annotations: Annotation[]): vscode.WebviewEditorInset | undefined {
        const editor = vscode.window.activeTextEditor;
        if (editor) {
            const height = 1;
            const inset = vscode.window.createWebviewTextEditorInset(editor, line, height);
            const text = annotations.map((annotation) => annotation.summary).join(' | ');
            inset.webview.html = text;
            return inset;
        }
        return undefined;
    }
}
