import * as vscode from 'vscode';
export class AnnotationCodeLensProvider implements vscode.CodeLensProvider {
    private codeLenses: vscode.CodeLens[] = [];
    public _onDidChangeCodeLenses: vscode.EventEmitter<void> = new vscode.EventEmitter<void>();
    public readonly onDidChangeCodeLenses: vscode.Event<void> = this._onDidChangeCodeLenses.event;
    public readonly onCodeLensRefreshRequest = (data: Object) => this._onCodeLensRefreshRequest(data);
    private data: Object = {};

    constructor() {}

    public _onCodeLensRefreshRequest(data: Object) {
        this.data = data;
        this._onDidChangeCodeLenses.fire();
    }

    public provideCodeLenses(
        document: vscode.TextDocument,
        token: vscode.CancellationToken,
    ): vscode.CodeLens[] | Thenable<vscode.CodeLens[]> {
        this.codeLenses = [];
        for (const [lineno, annotation] of Object.entries(this.data)) {
            const codeLens = this.annotationCodeLens(Number(lineno), annotation);
            this.codeLenses.push(codeLens);
        }
        return this.codeLenses;
    }

    /**
     * Create code lens to display an annotation.
     */
    private annotationCodeLens(lineno: number, annotation: string): vscode.CodeLens {
        const range = this.getRange(lineno, annotation);
        const command = this.getCommand(annotation);
        return new vscode.CodeLens(range, command);
    }

    /**
     * Get the range for an annotation.
     */
    private getRange(lineno: number, annotation: string): vscode.Range {
        const startPosition = new vscode.Position(lineno, 0);
        const endPosition = new vscode.Position(lineno, annotation.length);
        return new vscode.Range(startPosition, endPosition);
    }

    /**
     * Generate a command from the code lens string.
     */
    private getCommand(annotation: string): vscode.Command {
        return {
            title: annotation,
            command: '',
        };
    }

    public resolveCodeLens(
        codeLens: vscode.CodeLens,
        token: vscode.CancellationToken,
    ): vscode.ProviderResult<vscode.CodeLens> {
        return codeLens;
    }
}
