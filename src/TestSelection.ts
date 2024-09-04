/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { commands, ExtensionContext, window } from 'vscode';
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
            map[test] = fileDistance * 2 + nameDistance;
            return map;
        },
        {} as { [test: string]: number },
    );
    return tests.sort((a, b) => distances[a] - distances[b]);
}

// Modified from https://github.com/microsoft/vscode-extension-samples/tree/main/quickinput-sample
export async function selectTest(
    context: ExtensionContext,
    serverId: string,
    filename: string,
    functionName: string,
): Promise<string | undefined> {
    let tests: string[] = await commands.executeCommand(`${serverId}.list`, { filename: filename });
    tests = sortTests(tests, filename, functionName);
    const key = `test_history:${filename}:${functionName}`;
    let previousTests: string[] = context.workspaceState.get(key, []);
    for (let test of previousTests) {
        const index = tests.indexOf(test);
        if (index != -1) {
            tests.splice(index, 1);
        }
    }
    const result = await window.showQuickPick(previousTests.reverse().concat(tests), {
        placeHolder: 'Enter test name',
        title: 'Select test to run',
    });
    if (result != undefined) {
        const index = previousTests.indexOf(result);
        if (index != -1) {
            previousTests.splice(index, 1);
        }
        previousTests.push(result);
    }
    context.workspaceState.update(key, previousTests);

    return result;
}
