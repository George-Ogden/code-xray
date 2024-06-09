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

            const leftmostPosition = Math.min(
                ...annotations.map((annotation: Annotation): number => annotation.position.character),
            );
            const editorConfig = vscode.workspace.getConfiguration('editor');
            const fontFamily = editorConfig.get<string>('fontFamily');
            const fontSize = editorConfig.get<number>('fontSize');
            const positioningElement = `<div style="position:absolute;left:0px;">`;
            const spaceElement = `<span style="font: ${fontSize}px ${fontFamily};whitespace:pre">${'&nbsp;'.repeat(
                leftmostPosition,
            )}</span>`;
            const annotationElement = `<span>${annotations
                .map((annotation): string => annotation.summary)
                .join(' | ')}</span>`;
            inset.webview.html = positioningElement + spaceElement + annotationElement;
            return inset;
        }
        return undefined;
    }
}
