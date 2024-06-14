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
    maxWidth: number;
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
            let lines = this.renderTimeslice(annotations);
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
                )}</span>`;
                inset.webview.html = positioningElement + spaceElement + line.html;
                this.insets[Number(lineno)] = inset;
            }
        }
        return this.insets;
    }
    renderBlock(block: Block): LineRender {
        let lines: LineRender = {
            maxWidth: 0,
        };
        for (const [timestamp_id, timeslice] of Object.entries(block)) {
            const newLines = this.renderTimeslice(timeslice);
            const timestamp = parseInt(timestamp_id.substring(AnnotationInsetProvider.timestampKey.length));
            if (`${AnnotationInsetProvider.timestampKey}${timestamp + 1}` in block) {
                this.endLine(timeslice, newLines);
            }
            for (const [key, value] of Object.entries(newLines)) {
                const lineno = Number(key);
                if (isNaN(lineno)) continue;
                const line = value as Line;
                if (!lines[lineno]) {
                    lines[lineno] = {
                        html: this.textToHTML(' '.repeat(lines.maxWidth)),
                        length: lines.maxWidth,
                        indent: line.indent,
                    };
                }
                lines[lineno].html += line.html;
                lines[lineno].length += line.length;
            }
            lines.maxWidth += newLines.maxWidth;
        }
        return lines;
    }
    renderTimeslice(timeslice: TimeSlice): LineRender {
        let lines: LineRender = {
            maxWidth: 0,
        };
        for (const [id, structure] of Object.entries(timeslice)) {
            if (id.startsWith(AnnotationInsetProvider.lineKey)) {
                const lineno = parseInt(id.substring(AnnotationInsetProvider.lineKey.length));
                const annotation = this.renderLine(structure);
                lines[lineno] = annotation;
                lines.maxWidth = Math.max(lines.maxWidth, annotation.length);
            } else if (id.startsWith(AnnotationInsetProvider.blockKey)) {
                const newLines = this.renderBlock(structure);
                Object.assign(lines, newLines);
                lines.maxWidth = Math.max(lines.maxWidth, newLines.maxWidth);
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

    endLine(timeslice: TimeSlice, lines: LineRender, depth: number = 1) {
        let maxWidth = 0;
        for (const [id, structure] of Object.entries(timeslice)) {
            if (id.startsWith(AnnotationInsetProvider.lineKey)) {
                const lineno = parseInt(id.substring(AnnotationInsetProvider.lineKey.length));
                const suffix = `${' '.repeat(lines.maxWidth - lines[lineno].length)} ${'|'.repeat(depth)} `;
                maxWidth = Math.max(maxWidth, lines[lineno].length + suffix.length);
                lines[lineno].html += this.textToHTML(suffix);
            } else if (id.startsWith(AnnotationInsetProvider.blockKey)) {
                const block = structure as Block;
                const [_, nextTimeslice] = Object.entries(block).reduce(
                    ([id0, structure0], [id1, structure1]): [string, TimeSlice] =>
                        parseInt(id0.substring(AnnotationInsetProvider.timestampKey.length)) >
                        parseInt(id1.substring(AnnotationInsetProvider.timestampKey.length))
                            ? [id0, structure0]
                            : [id1, structure1],
                );
                const width = this.endLine(nextTimeslice, lines, depth + 1);
                maxWidth = Math.max(maxWidth, width);
            }
        }
        return maxWidth;
    }
}
