/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { commands, window } from 'vscode';
import Distance from './Distance';
import path = require('path');

function sortTests(tests: string[], sourceFilepath: string, functionName: string): string[] {
    const distances = tests.reduce(
        (map, test) => {
            const testDirname = path.dirname(test);
            const testName = path.basename(test).split(':')[1];
            const testFilepath = path.join(testDirname, path.basename(test).split(':')[0]);
            const fileDistance = Distance.filepathDistance(sourceFilepath, testFilepath);
            const nameDistance = Distance.functionNameDistance(functionName, testName);
            map[test] = fileDistance + 2 * nameDistance;
            return map;
        },
        {} as { [test: string]: number },
    );
    return tests.sort((a, b) => distances[a] - distances[b]);
}

// Modified from https://github.com/microsoft/vscode-extension-samples/tree/main/quickinput-sample
export async function selectTest(
    serverId: string,
    filename: string,
    functionName: string,
): Promise<string | undefined> {
    let tests: string[] = await commands.executeCommand(`${serverId}.list`, { filename: filename });
    tests = sortTests(tests, filename, functionName);
    const result = await window.showQuickPick(tests, {
        placeHolder: 'Enter test name',
    });
    return result;
}
