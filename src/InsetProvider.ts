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
    private annotations: Annotations = {};

    constructor() {}
    dispose() {
        this.removeInsets();
    }

    private _onCodeLensRefreshRequest(data: Annotations) {
        this.annotations = data;
        this.updateInsets();
    }

    private updateInsets(): void {
        this.removeInsets();
        this.createInsets(this.annotations);
    }

    /**
     * Get rid of all insets that are currently active.
     */
    private removeInsets(): void {
        for (const inset of this.insets) {
            inset.dispose();
        }
        this.insets = [];
    }

    /**
     * Create insets for the given data.
     */
    private createInsets(annotations: Annotations): void {
        for (const [line, lineAnnotations] of Object.entries(annotations)) {
            const inset = this.createInset(Number(line), lineAnnotations);
            if (inset) {
                this.insets.push(inset);
            }
        }
    }

    /**
     * Create the inset on a line for an annotation.
     */
    private createInset(line: number, annotations: Annotation[]): vscode.WebviewEditorInset | undefined {
        const editor = vscode.window.activeTextEditor;
        if (editor) {
            const height = 1;
            const inset = vscode.window.createWebviewTextEditorInset(editor, line, height);
            const text = annotations.map((annotation): string => annotation.summary).join(' | ');
            inset.webview.html = text;
            return inset;
        }
        return undefined;
    }
}
