import * as vscode from 'vscode';
import { loadServerDefaults } from './common/setup';

export class FunctionCodelensProvider implements vscode.CodeLensProvider {
    private codeLenses: vscode.CodeLens[] = [];
    // Regex to match a module-level function definition in Python.
    private readonly regex: RegExp = /^def +([a-zA-Z_][a-zA-Z_0-9]*)/gm;
    public _onDidChangeCodeLenses: vscode.EventEmitter<void> = new vscode.EventEmitter<void>();
    public readonly onDidChangeCodeLenses: vscode.Event<void> = this._onDidChangeCodeLenses.event;

    constructor() {
        vscode.workspace.onDidChangeConfiguration((_) => {
            this._onDidChangeCodeLenses.fire();
        });
    }

    public provideCodeLenses(
        document: vscode.TextDocument,
        token: vscode.CancellationToken,
    ): vscode.CodeLens[] | Thenable<vscode.CodeLens[]> {
        this.codeLenses = [];
        const regex = new RegExp(this.regex);
        const text = document.getText();
        let matches;
        while ((matches = regex.exec(text)) !== null) {
            const runTestCodeLens = this.runTestCodeLens(document, matches);
            if (runTestCodeLens) {
                this.codeLenses.push(runTestCodeLens);
            }
        }
        return this.codeLenses;
    }

    /**
     * Create a CodeLens from the location of a function definition to run tests.
     */
    private runTestCodeLens(
        document: vscode.TextDocument,
        functionDefinition: RegExpExecArray,
    ): vscode.CodeLens | undefined {
        const line = document.lineAt(document.positionAt(functionDefinition.index).line);
        const range = this.getRange(document, line);
        if (range) {
            const command = this.getRunCommand(document, line, functionDefinition[1]);
            return new vscode.CodeLens(range, command);
        }
        return undefined;
    }

    /**
     * Convert a match for the function definition into a range.
     */
    private getRange(document: vscode.TextDocument, line: vscode.TextLine): vscode.Range | undefined {
        // Start from the end of "def".
        const position = new vscode.Position(line.lineNumber, 4);
        const range = document.getWordRangeAtPosition(position);
        return range;
    }

    /**
     * Create the relevant command for a function definition to run the test.
     */
    private getRunCommand(document: vscode.TextDocument, line: vscode.TextLine, functionName: string): vscode.Command {
        const serverInfo = loadServerDefaults();
        const command: vscode.Command = {
            title: `Run Code X-Ray `,
            command: `${serverInfo.module}.test`,
            arguments: [{ filepath: document.uri.path, lineno: line.lineNumber, functionName: functionName }],
        };
        return command;
    }

    public resolveCodeLens(
        codeLens: vscode.CodeLens,
        token: vscode.CancellationToken,
    ): vscode.ProviderResult<vscode.CodeLens> {
        return codeLens;
    }
}
