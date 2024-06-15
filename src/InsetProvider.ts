import * as vscode from 'vscode';
import { traceLog } from './common/log/logging';

type Annotation = {
    text: string;
    hover: string | undefined;
};

type Annotations = TimeSlice;

type TimeSlice =
    | {
          [block: string]: Block;
      }
    | {
          [line: string]: LineAnnotation;
      };

type LineAnnotation = {
    indent: number;
    annotations: Annotation[][];
};

type Block = {
    [timeslice: string]: TimeSlice;
};

type Line = {
    html: string;
    indent: number;
    length: number;
};

type LineRender = {
    [key: number]: Line;
    maxLength: number;
};

export class AnnotationInsetProvider implements vscode.Disposable {
    private insets: { [lineno: number]: vscode.WebviewEditorInset } = {};
    public _onDidChangeCodeLenses: vscode.EventEmitter<void> = new vscode.EventEmitter<void>();
    public readonly onDidChangeCodeLenses: vscode.Event<void> = this._onDidChangeCodeLenses.event;
    public readonly onCodeLensRefreshRequest = (data: Annotations) => this._onCodeLensRefreshRequest(data);
    private annotations: Annotations = {};
    static readonly timestampKey = 'timestamp_';
    static readonly lineKey = 'line_';
    static readonly blockKey = 'block_';

    constructor() {}
    dispose() {
        this.removeInsets();
    }

    private _onCodeLensRefreshRequest(data: Annotations) {
        this.annotations = data;
        this.updateInsets();
    }

    private updateInsets(): void {
        this.clearInsets();
        this.createInsets(this.annotations);
        this.removeEmptyInsets();
    }

    /**
     * Make all insets have no html.
     */
    private clearInsets(): void {
        for (const inset of Object.values(this.insets)) {
            inset.webview.html = '';
        }
    }

    /**
     * Get rid of all insets that are currently empty.
     */
    private removeEmptyInsets(): void {
        for (const [lineno, inset] of Object.entries(this.insets)) {
            if (!inset.webview.html) {
                inset.dispose();
                delete this.insets[Number(lineno)];
            }
        }
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
            let lines = this.renderTimeslice(annotations, 0);
            traceLog('Rendering:', lines);
            for (const [key, value] of Object.entries(lines)) {
                const lineno = Number(key);
                if (isNaN(lineno)) continue;
                if (!this.insets[lineno]) {
                    const height = 1;
                    this.insets[lineno] = vscode.window.createWebviewTextEditorInset(editor, Number(lineno), height);
                }
                const inset = this.insets[lineno];
                const line = value as Line;
                const editorConfig = vscode.workspace.getConfiguration('editor');
                const fontFamily = editorConfig.get<string>('fontFamily');
                const fontSize = editorConfig.get<number>('fontSize');
                const positioningElement = `<div style="position:absolute;left:0px">`;
                const spaceElement = `<span style="font: ${fontSize}px ${fontFamily}">${this.textToHTML(
                    ' '.repeat(line.indent),
                )}</span><span style="font-family: monospace">`;
                inset.webview.html = positioningElement + spaceElement + line.html;
                this.insets[Number(lineno)] = inset;
            }
        }
        return this.insets;
    }
    renderBlock(block: Block, depth: number): LineRender {
        let lines: LineRender = {
            maxLength: 0,
        };
        for (const [_, timeslice] of Object.entries(block)) {
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
                        indent: line.indent,
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
    renderTimeslice(timeslice: TimeSlice, depth: number): LineRender {
        let lines: LineRender = {
            maxLength: 0,
        };
        for (const [id, structure] of Object.entries(timeslice)) {
            if (id.startsWith(AnnotationInsetProvider.lineKey)) {
                const lineno = parseInt(id.substring(AnnotationInsetProvider.lineKey.length));
                const annotation = this.renderLine(structure);
                lines[lineno] = annotation;
                lines.maxLength = Math.max(lines.maxLength, annotation.length);
            } else if (id.startsWith(AnnotationInsetProvider.blockKey)) {
                const newLines = this.renderBlock(structure, depth + 1);
                Object.assign(lines, newLines);
                lines.maxLength = Math.max(lines.maxLength, newLines.maxLength);
            }
        }
        return lines;
    }
    renderLine(lineAnnotations: LineAnnotation): Line {
        const separator = ', ';
        let annotationHTML = '';
        let length = 0;
        for (const [i, variableAnnotation] of lineAnnotations.annotations.entries()) {
            for (const annotation of variableAnnotation) {
                let hoverHTML = '';
                if (annotation.hover) {
                    hoverHTML = ` title="${annotation.hover}"`;
                }
                annotationHTML += `<span${hoverHTML}>${this.textToHTML(annotation.text)}</span>`;
                length += annotation.text.length;
            }
            if (i != lineAnnotations.annotations.length - 1) {
                annotationHTML += this.textToHTML(separator);
                length += separator.length;
            }
        }
        return {
            html: annotationHTML,
            length: length,
            indent: lineAnnotations.indent,
        };
    }
    /**
     * Escape text to html.
     */
    textToHTML(text: string): string {
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
