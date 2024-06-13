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
    annotations: Annotation[];
};

type Block = {
    [timeslice: string]: TimeSlice;
};

type Line = {
    text: string;
    indent: number;
    length: number;
};

type LineRender = {
    [key: number]: Line;
    maxWidth: number;
};

export class AnnotationInsetProvider implements vscode.Disposable {
    private insets: vscode.WebviewEditorInset[] = [];
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
        traceLog(`Rendering annotations: ${JSON.stringify(this.annotations)}`);
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
    private createInsets(annotations: Annotations) {
        const editor = vscode.window.activeTextEditor;
        let insets: vscode.WebviewEditorInset[] = [];
        if (editor) {
            let lines = this.renderTimeslice(annotations);
            for (const [lineno, value] of Object.entries(lines)) {
                if (typeof lineno == 'number') continue;
                const line = value as Line;
                const height = 1;
                const inset = vscode.window.createWebviewTextEditorInset(editor, Number(lineno), height);
                const editorConfig = vscode.workspace.getConfiguration('editor');
                const fontFamily = editorConfig.get<string>('fontFamily');
                const fontSize = editorConfig.get<number>('fontSize');
                const positioningElement = `<div style="position:absolute;left:0px;whitespace:pre">`;
                const spaceElement = `<span style="font: ${fontSize}px ${fontFamily}">${'&nbsp;'.repeat(
                    line.indent,
                )}</span>`;
                const annotationElement = `<span>${line.text}</span>`;
                inset.webview.html = positioningElement + spaceElement + annotationElement;
                insets.push(inset);
            }
        }
        return insets;
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
                if (!isNaN(Number(key))) {
                    const lineno = Number(key);
                    const line = value as Line;
                    if (!lines[lineno]) {
                        lines[lineno] = {
                            text: ' '.repeat(lines.maxWidth),
                            length: lines.maxWidth,
                            indent: line.indent,
                        };
                    }
                    lines[lineno].text += line.text;
                    lines[lineno].length += line.length;
                }
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
    renderLine(annotations: LineAnnotation): Line {
        const annotation = annotations.annotations.map((annotation): string => annotation.text).join(', ');
        return {
            text: annotation,
            length: annotation.length,
            indent: annotations.indent,
        };
    }

    endLine(timeslice: TimeSlice, lines: LineRender, depth: number = 1) {
        let maxWidth = 0;
        for (const [id, structure] of Object.entries(timeslice)) {
            if (id.startsWith(AnnotationInsetProvider.lineKey)) {
                const lineno = parseInt(id.substring(AnnotationInsetProvider.lineKey.length));
                const suffix = `${' '.repeat(lines.maxWidth - lines[lineno].length)} ${'|'.repeat(depth)} `;
                maxWidth = Math.max(maxWidth, lines[lineno].length + suffix.length);
                lines[lineno].text += suffix;
            } else if (id.startsWith(AnnotationInsetProvider.blockKey)) {
                const block: Block = structure[id];
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
