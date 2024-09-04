// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

import * as vscode from 'vscode';
import { checkIfConfigurationChanged, getInterpreterFromSetting } from './common/settings';
import {
    checkVersion,
    getInterpreterDetails,
    initializePython,
    onDidChangePythonInterpreter,
    resolveInterpreter,
} from './common/python';
import { createOutputChannel, onDidChangeConfiguration, registerCommand } from './common/vscodeapi';
import { registerLogger, traceError, traceLog, traceVerbose } from './common/log/logging';
import { AnnotationInsetProvider } from './InsetProvider';
import { commands } from 'vscode';
import { FunctionCodelensProvider } from './FunctionCodelensProvider';
import { getLSClientTraceLevel } from './common/utilities';
import { LanguageClient } from 'vscode-languageclient/node';
import { loadServerDefaults } from './common/setup';
import { restartServer } from './common/server';
import { selectTest } from './TestSelection';

let lsClient: LanguageClient | undefined;
export async function activate(context: vscode.ExtensionContext): Promise<void> {
    // This is required to get server name and module. This should be
    // the first thing that we do in this extension.
    const serverInfo = loadServerDefaults();
    const serverName = serverInfo.name;
    const serverId = serverInfo.module;

    // Setup logging
    const outputChannel = createOutputChannel(serverName);
    context.subscriptions.push(outputChannel, registerLogger(outputChannel));

    const changeLogLevel = async (c: vscode.LogLevel, g: vscode.LogLevel) => {
        const level = getLSClientTraceLevel(c, g);
        await lsClient?.setTrace(level);
    };

    context.subscriptions.push(
        outputChannel.onDidChangeLogLevel(async (e) => {
            await changeLogLevel(e, vscode.env.logLevel);
        }),
        vscode.env.onDidChangeLogLevel(async (e) => {
            await changeLogLevel(outputChannel.logLevel, e);
        }),
    );

    // Log Server information
    traceLog(`Name: ${serverInfo.name}`);
    traceLog(`Module: ${serverInfo.module}`);
    traceVerbose(`Full Server Info: ${JSON.stringify(serverInfo)}`);

    // Register CodeLens providers.
    const functionCodeLensProvider = new FunctionCodelensProvider();
    vscode.languages.registerCodeLensProvider('*', functionCodeLensProvider);

    // Create a provider for insets.
    const insetProvider = new AnnotationInsetProvider();
    const registerInsetRefreshHandler = () => {
        if (lsClient) {
            lsClient.onRequest('workspace/inset/refresh', insetProvider.onCodeLensRefreshRequest);
        }
    };

    const runServer = async () => {
        const interpreter = getInterpreterFromSetting(serverId);
        if (interpreter && interpreter.length > 0) {
            if (checkVersion(await resolveInterpreter(interpreter))) {
                traceVerbose(`Using interpreter from ${serverInfo.module}.interpreter: ${interpreter.join(' ')}`);
                lsClient = await restartServer(serverId, serverName, outputChannel, lsClient);
            }
            registerInsetRefreshHandler();
            return;
        }

        const interpreterDetails = await getInterpreterDetails();
        if (interpreterDetails.path) {
            traceVerbose(`Using interpreter from Python extension: ${interpreterDetails.path.join(' ')}`);
            lsClient = await restartServer(serverId, serverName, outputChannel, lsClient);
            registerInsetRefreshHandler();
            return;
        }

        traceError(
            'Python interpreter missing:\r\n' +
                '[Option 1] Select python interpreter using the ms-python.python.\r\n' +
                `[Option 2] Set an interpreter using "${serverId}.interpreter" setting.\r\n` +
                'Please use Python 3.8 or greater.',
        );
    };

    context.subscriptions.push(
        onDidChangePythonInterpreter(async () => {
            await runServer();
        }),
        onDidChangeConfiguration(async (e: vscode.ConfigurationChangeEvent) => {
            if (checkIfConfigurationChanged(e, serverId)) {
                await runServer();
            }
        }),
        registerCommand(`${serverId}.restart`, async () => {
            await runServer();
        }),
        registerCommand(`${serverId}.test`, async (args: { filepath: string; lineno: number }) => {
            const functionName: string = await commands.executeCommand(`${serverId}.name`, {
                filepath: args.filepath,
                lineno: args.lineno,
            });
            const test = await selectTest(context, serverId, args.filepath, functionName);
            if (test) {
                commands.executeCommand(`${serverId}.annotate`, {
                    test: test,
                    filepath: args.filepath,
                    lineno: args.lineno,
                });
            }
        }),
        registerCommand(`${serverId}.select`, async (filename: string, functionName: string) => {
            selectTest(context, serverId, filename, functionName).catch(console.error);
        }),
    );

    setImmediate(async () => {
        const interpreter = getInterpreterFromSetting(serverId);
        if (interpreter === undefined || interpreter.length === 0) {
            traceLog(`Python extension loading`);
            await initializePython(context.subscriptions);
            traceLog(`Python extension loaded`);
        } else {
            await runServer();
        }
    });
}

export async function deactivate(): Promise<void> {
    if (lsClient) {
        await lsClient.stop();
    }
}
