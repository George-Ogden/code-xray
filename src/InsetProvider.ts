import * as vscode from 'vscode';
import { JSDOM } from 'jsdom';
import { traceLog } from './common/log/logging';

type AnnotationPart = {
    text: string;
    hover: string | undefined;
};

type Annotation = AnnotationPart[];

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
    annotations: Annotation[];
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
    private nextBlockId: number = 0;

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
            this.nextBlockId = 0;
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
     * Remove duplicated blocks from the HTML.
     */
    private removeDuplicateBlocks(html: string): string {
        const dom = new JSDOM(html);
        const document = dom.window.document;

        for (let i = 0; i < this.nextBlockId; i++) {
            const elements = document.querySelectorAll(`#block_${i}`);
            // Keep the first one and remove the rest
            elements.forEach((element, index: number) => {
                if (index > 0) {
                    element.remove();
                }
            });
        }
        return document.body.innerHTML;
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
        const style = `<style>body{overflow:hidden;}.line{visibility:hidden;height:0;display:flex}.line.line_${line.position.line}{visibility:visible;height:auto}.block{width:max-content;display:flex;flex-direction:column;vertical-align:top}</style><div style="position:absolute;left:0px">`;
        // Add element to left with absolute position.
        const positioningElement = style;
        // Indent the correct amount.
        const spaceElement = `<span style="font: ${fontSize}px ${fontFamily};display:inline-block;height:0">${this.textToHTML(
            ' '.repeat(line.position.character),
        )}</span><span style="position:absolute">`;
        // Create the HTML.
        const lineHTML = this.removeDuplicateBlocks(line.html);
        inset.webview.html = positioningElement + spaceElement + lineHTML;
        return inset;
    }

    private renderBlock(block: Block, depth: number): LineRender {
        let lines: LineRender = {};
        let blockHTML = '';
        for (const [_, timeslice] of Object.entries(block)) {
            // Render each timeslice.
            const newLines = this.renderTimeslice(timeslice, depth);
            let timesliceHTML = '';
            for (const [key, value] of Object.entries(newLines)) {
                const lineno = Number(key);
                const line = value as Line;
                // Create line if it does not exist.
                if (!lines[lineno]) {
                    lines[lineno] = {
                        html: '',
                        length: 0,
                        position: line.position,
                    };
                }

                // Add a prefix.
                const prefix = this.textToHTML('|'.repeat(depth) + ' ');
                timesliceHTML += `<span class="line line_${lineno}"><span style="margin-left:.5em">${prefix}</span>${line.html}</span>`;
                // Update the length.
                lines[lineno].length += line.length;
            }
            blockHTML += `<div class=block>${timesliceHTML}</div>`;
        }
        const blockId = this.nextBlockId++;
        const html = `<div style=display:flex id=block_${blockId}>${blockHTML}</div>`;
        for (const line of Object.keys(lines)) {
            lines[Number(line)].html = html;
        }
        return lines;
    }
    private renderTimeslice(timeslice: TimeSlice, depth: number): LineRender {
        let lines: LineRender = {};
        for (const [id, structure] of Object.entries(timeslice)) {
            if (id.startsWith(AnnotationInsetProvider.lineKey)) {
                // Render lines.
                const line = structure as LineAnnotation;
                const annotation = this.renderLine(line);
                // Store and update max length.
                const lineno = line.position.line;
                lines[lineno] = annotation;
            } else if (id.startsWith(AnnotationInsetProvider.blockKey)) {
                // Render a block.
                const newLines = this.renderBlock(structure, depth + 1);
                // Store and update max length.
                Object.assign(lines, newLines);
            }
        }
        return lines;
    }
    private renderLine(lineAnnotations: LineAnnotation): Line {
        const separator = ', ';
        let annotationHTML = '';
        let length = 0;
        for (const [i, annotation] of lineAnnotations.annotations.entries()) {
            for (const annotationPart of annotation) {
                let hoverHTML = '';
                if (annotationPart.hover) {
                    // Add a tooltip if there is hover text.
                    hoverHTML = ` title="${annotationPart.hover}"`;
                }
                annotationHTML += `<span${hoverHTML}>${this.textToHTML(annotationPart.text)}</span>`;
                length += annotationPart.text.length;
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
