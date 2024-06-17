import * as vscode from 'vscode';
import { traceLog } from './common/log/logging';

type Annotation = {
    text: string;
    hover: string | undefined;
};

// Annotation has a Time -> Block -> Time -> Block -> ... recursive structure.
type Annotations = TimeSlice;

type TimeSlice =
    | {
          [block: string]: Block;
      }
    | {
          [line: string]: LineAnnotation;
      };

type LineAnnotation = {
    position: vscode.Position;
    annotations: Annotation[][];
};

type Block = {
    [timeslice: string]: TimeSlice;
};

type Line = {
    html: string;
    length: number;
    position: vscode.Position;
};

type LineRender = {
    [key: number]: Line;
    maxLength: number;
};

type Inset = vscode.WebviewEditorInset;

export class AnnotationInsetProvider implements vscode.Disposable {
    private insets: { [lineno: number]: Inset } = {};
    public _onDidChangeInsets: vscode.EventEmitter<void> = new vscode.EventEmitter<void>();
    public readonly onDidChangeInsets: vscode.Event<void> = this._onDidChangeInsets.event;
    public readonly onCodeLensRefreshRequest = (data: Annotations) => this._onInsetRefreshRequest(data);
    private annotations: Annotations = {};
    static readonly timestampKey = 'timestamp_';
    static readonly lineKey = 'line_';
    static readonly blockKey = 'block_';

    constructor() {}
    dispose() {
        this.removeInsets();
    }

    private _onInsetRefreshRequest(data: Annotations) {
        this.annotations = data;
        this.updateInsets();
    }

    /**
     * Update insets to match the current data.
     */
    private updateInsets(): void {
        this.removeInsets();
        this.createInsets(this.annotations);
    }

    /**
     * Get rid of all insets that are currently active.
     */
    private removeInsets(): void {
        for (const inset of Object.values(this.insets)) {
            inset.dispose();
        }
        this.insets = {};
    }

    /**
     * Create insets for the given data.
     */
    private createInsets(annotations: Annotations) {
        const editor = vscode.window.activeTextEditor;
        if (editor) {
            // Generate line information.
            let lines = this.renderTimeslice(annotations, 0);
            traceLog('Rendering:', lines);
            // Create and store each new inset.
            for (const [key, line] of Object.entries(lines)) {
                const lineno = Number(key);
                const inset = this.createInset(editor, line as Line);
                if (inset) {
                    this.insets[Number(lineno)] = inset;
                }
            }
        }
        return this.insets;
    }
    /**
     * Create an inset for a given line.
     */
    private createInset(editor: vscode.TextEditor, line: Line): Inset | undefined {
        if (line.length == 0) {
            return undefined;
        }
        // Create inset.
        const height = 1;
        const inset = vscode.window.createWebviewTextEditorInset(editor, line.position.line, height);

        // Get the current editor font size + family.
        const editorConfig = vscode.workspace.getConfiguration('editor');
        const fontFamily = editorConfig.get<string>('fontFamily');
        const fontSize = editorConfig.get<number>('fontSize');
        // Add element to left with absolute position.
        const positioningElement = `<div style="position:absolute;left:0px">`;
        // Indent the correct amount.
        const spaceElement = `<span style="font: ${fontSize}px ${fontFamily}">${this.textToHTML(
            ' '.repeat(line.position.character),
        )}</span><span style="font-family: monospace">`;
        // Create the HTML.
        inset.webview.html = positioningElement + spaceElement + line.html;
        return inset;
    }

    private renderBlock(block: Block, depth: number): LineRender {
        let lines: LineRender = {
            maxLength: 0,
        };
        for (const [_, timeslice] of Object.entries(block)) {
            // Render each timeslice.
            const newLines = this.renderTimeslice(timeslice, depth);
            const maxLength = lines.maxLength;
            for (const [key, value] of Object.entries(newLines)) {
                const lineno = Number(key);
                if (isNaN(lineno)) continue;
                const line = value as Line;
                // Create line if it does not exist.
                if (!lines[lineno]) {
                    lines[lineno] = {
                        html: '',
                        length: 0,
                        position: line.position,
                    };
                }

                // Make sure this line is the same length.
                lines[lineno].html += this.textToHTML(' '.repeat(maxLength - lines[lineno].length));
                lines[lineno].length = maxLength;

                // Add a prefix.
                const prefix = '|'.repeat(depth) + ' ';
                lines[lineno].html += this.textToHTML(prefix);
                lines[lineno].length += prefix.length;

                // Update the length.
                lines[lineno].html += line.html;
                lines[lineno].length += line.length;

                // Update global max length (+1 for spacing).
                lines.maxLength = Math.max(lines.maxLength, lines[lineno].length + 1);
            }
        }
        return lines;
    }
    private renderTimeslice(timeslice: TimeSlice, depth: number): LineRender {
        let lines: LineRender = {
            maxLength: 0,
        };
        for (const [id, structure] of Object.entries(timeslice)) {
            if (id.startsWith(AnnotationInsetProvider.lineKey)) {
                // Render lines.
                const line = structure as LineAnnotation;
                const annotation = this.renderLine(line);
                // Store and update max length.
                const lineno = line.position.line;
                lines[lineno] = annotation;
                lines.maxLength = Math.max(lines.maxLength, annotation.length);
            } else if (id.startsWith(AnnotationInsetProvider.blockKey)) {
                // Render a block.
                const newLines = this.renderBlock(structure, depth + 1);
                // Store and update max length.
                Object.assign(lines, newLines);
                lines.maxLength = Math.max(lines.maxLength, newLines.maxLength);
            }
        }
        return lines;
    }
    private renderLine(lineAnnotations: LineAnnotation): Line {
        const separator = ', ';
        let annotationHTML = '';
        let length = 0;
        for (const [i, variableAnnotation] of lineAnnotations.annotations.entries()) {
            for (const annotation of variableAnnotation) {
                let hoverHTML = '';
                if (annotation.hover) {
                    // Add a tooltip if there is hover text.
                    hoverHTML = ` title="${annotation.hover}"`;
                }
                annotationHTML += `<span${hoverHTML}>${this.textToHTML(annotation.text)}</span>`;
                length += annotation.text.length;
            }
            // Add a separator if not at the end.
            if (i != lineAnnotations.annotations.length - 1) {
                annotationHTML += this.textToHTML(separator);
                length += separator.length;
            }
        }
        return {
            html: annotationHTML,
            length: length,
            position: lineAnnotations.position,
        };
    }
    /**
     * Escape text to html.
     */
    private textToHTML(text: string): string {
        // Taken from https://gist.github.com/thetallweeks/7c452e211f286e77b6f2?permalink_comment_id=3254565#gistcomment-3254565

        const entityMap = new Map<string, string>(
            Object.entries({
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#39;',
                '/': '&#x2F;',
                ' ': '&nbsp;',
            }),
        );

        return text.replace(/[&<>"'\/ ]/g, (s: string): string => entityMap.get(s)!);
    }
}
