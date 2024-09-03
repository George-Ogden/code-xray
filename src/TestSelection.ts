/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { commands, window } from 'vscode';

// Modified from https://github.com/microsoft/vscode-extension-samples/tree/main/quickinput-sample
export async function selectTest(
    serverId: string,
    filename: string,
    functionName: string,
): Promise<string | undefined> {
    let tests: string[] = await commands.executeCommand(`${serverId}.list`, { filename: filename });
    const result = await window.showQuickPick(tests, {
        placeHolder: 'Enter test name',
    });
    return result;
}
