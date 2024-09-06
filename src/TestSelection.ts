/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { commands, ExtensionContext, QuickPickItem, QuickPickItemKind, window } from 'vscode';
import Distance from './Distance';
import path = require('path');
import { loadServerDefaults } from './common/setup';

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
    filename: string,
    functionName: string,
): Promise<string | undefined> {
    const serverInfo = loadServerDefaults();
    const serverId = serverInfo.module;
    let tests: string[] = await commands.executeCommand(`${serverId}.list`, { filename: filename });
    tests = sortTests(tests, filename, functionName);
    const key = `test_history:${filename}:${functionName}`;
    let previousTests: string[] = context.workspaceState.get(key, []);
    for (let test of previousTests) {
        const index = tests.indexOf(test);
        if (index !== -1) {
            tests.splice(index, 1);
        }
    }

    const quickPick = window.createQuickPick();
    const toItem = (text: string): QuickPickItem => ({ label: text });
    quickPick.items = [{ label: 'Previously Run', kind: QuickPickItemKind.Separator } as QuickPickItem]
        .concat(previousTests.reverse().map(toItem))
        .concat({
            label: 'Not yet run',
            kind: QuickPickItemKind.Separator,
        })
        .concat(tests.map(toItem));
    quickPick.placeholder = 'Enter test name';
    quickPick.title = `Select test to call ${functionName}`;
    quickPick.show();
    return new Promise<string | undefined>((resolve) => {
        quickPick.onDidAccept(() => {
            const selectedItem = quickPick.selectedItems[0];
            if (selectedItem) {
                const result = selectedItem.label;
                // Update previous tests list
                const index = previousTests.indexOf(result);
                if (index !== -1) {
                    previousTests.splice(index, 1);
                }
                previousTests.push(result);
                context.workspaceState.update(key, previousTests);
                resolve(result);
            } else {
                resolve(undefined);
            }
            quickPick.dispose();
        });

        quickPick.onDidHide(() => {
            quickPick.dispose();
            resolve(undefined);
        });

        quickPick.show();
    });
}
