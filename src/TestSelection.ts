/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { commands, ExtensionContext, QuickPickItem, QuickPickItemKind, window } from 'vscode';
import Distance from './Distance';
import path = require('path');
import { loadServerDefaults } from './common/setup';
import { unescapeColons } from './Colon';

function sortTests(tests: (undefined | string)[], sourceFilepath: string, functionName: string): string[] {
    const filtered_tests: string[] = tests.filter((test): test is string => test !== undefined);

    const distances = filtered_tests.reduce(
        (map, test) => {
            let [testFilename, testName] = test.split('::');
            testFilename = unescapeColons(testFilename);
            testName = unescapeColons(testName);
            const testDirname = path.dirname(testFilename);
            const testFilepath = path.join(testDirname, path.basename(testFilename));
            const fileDistance = Distance.filepathDistance(sourceFilepath, testFilepath);
            const nameDistance = Distance.functionNameDistance(functionName, testName);
            map[test] = fileDistance * 2 + nameDistance;
            return map;
        },
        {} as { [test: string]: number },
    );
    return filtered_tests.sort((a, b) => distances[a] - distances[b]);
}

interface TestQuickPickItem extends QuickPickItem {
    test: string | undefined;
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
    let remainingPreviousTests = [];
    for (let test of previousTests) {
        const index = tests.indexOf(test);
        if (index !== -1) {
            tests.splice(index, 1);
            remainingPreviousTests.push(test);
        }
    }

    const quickPick = window.createQuickPick<TestQuickPickItem>();
    const toItem = (test: string): TestQuickPickItem => ({
        label: test
            .split('::')
            .map((name) => unescapeColons(name))
            .join(':'),
        test: test,
    });
    quickPick.items = [
        { label: 'Previously Run', test: undefined, kind: QuickPickItemKind.Separator } as TestQuickPickItem,
    ]
        .concat(remainingPreviousTests.reverse().map(toItem))
        .concat({
            label: 'Not yet run',
            kind: QuickPickItemKind.Separator,
            test: undefined,
        })
        .concat(tests.map(toItem));
    quickPick.placeholder = 'Enter test name';
    quickPick.title = `Select test to call ${functionName}`;

    return new Promise<string | undefined>((resolve) => {
        quickPick.onDidAccept(() => {
            const selectedItem = quickPick.selectedItems[0];
            if (selectedItem && selectedItem.test !== undefined) {
                const result = selectedItem.test;
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
