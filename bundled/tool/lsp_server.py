# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Implementation of tool support over LSP."""
from __future__ import annotations

import contextlib
import importlib
import json
import os
import pathlib
import sys
from typing import Any, Optional


# **********************************************************
# Update sys.path before importing any bundled libraries.
# **********************************************************
def update_sys_path(path_to_add: str, strategy: str) -> None:
    """Add given path to `sys.path`."""
    if path_to_add not in sys.path and os.path.isdir(path_to_add):
        if strategy == "useBundled":
            sys.path.insert(0, path_to_add)
        elif strategy == "fromEnvironment":
            sys.path.append(path_to_add)


# Ensure that we can import LSP libraries, and other bundled libraries.
update_sys_path(
    os.fspath(pathlib.Path(__file__).parent.parent / "libs"),
    os.getenv("LS_IMPORT_STRATEGY", "useBundled"),
)

import lsp_jsonrpc as jsonrpc
import lsp_utils as utils
import lsprotocol.types as lsp
import xray
from pygls import server, uris, workspace

# **********************************************************
# Imports needed for the language server goes below this.
# **********************************************************
# pylint: disable=wrong-import-position,import-error
from xray.utils import LineNumber, Serializable

WORKSPACE_SETTINGS = {}
GLOBAL_SETTINGS = {}
RUNNER = pathlib.Path(__file__).parent / "lsp_runner.py"

MAX_WORKERS = 4
LSP_SERVER = server.LanguageServer(name="Code Xray", version="0.0", max_workers=MAX_WORKERS)


# **********************************************************
# Tool specific code goes below this.
# **********************************************************

# Reference:
#  LS Protocol:
#  https://microsoft.github.io/language-server-protocol/specifications/specification-3-16/
#
#  Sample implementations:
#  Pylint: https://github.com/microsoft/vscode-pylint/blob/main/bundled/tool
#  Black: https://github.com/microsoft/vscode-black-formatter/blob/main/bundled/tool
#  isort: https://github.com/microsoft/vscode-isort/blob/main/bundled/tool

TOOL_MODULE = "xray"
TOOL_DISPLAY = "Code Xray"


@LSP_SERVER.command(f"{TOOL_MODULE}.name")
@utils.argument_wrapper
def get_function(filepath: str, lineno: int):
    """Return a qualified name for a function."""
    line_number = LineNumber[0](lineno)

    document = workspace.text_document.TextDocument(filepath)
    source = document.source

    """Return a list of pytest tests."""
    with contextlib.redirect_stdout(sys.stderr):
        function_position = xray.get_function(source, line_number)
        return Serializable.serialize(function_position)


@LSP_SERVER.command(f"{TOOL_MODULE}.functions")
@utils.argument_wrapper
def list_functions(filepath: str):
    """Return a list of line numbers for pytest functions."""
    try:
        document = workspace.text_document.TextDocument(filepath)
        source = document.source
    except FileNotFoundError:
        return []
    with contextlib.redirect_stdout(sys.stderr):
        return [line.zero for line in xray.list_functions(source)]


@LSP_SERVER.command(f"{TOOL_MODULE}.list")
@utils.argument_wrapper
def list_tests(filename: str):
    """Return a list of pytest tests."""
    reload_modules(LSP_SERVER.lsp.workspace)
    with contextlib.redirect_stdout(sys.stderr):
        return xray.list_tests(filename)


@LSP_SERVER.command(f"{TOOL_MODULE}.annotate")
@utils.argument_wrapper
def annotate(filepath: str, lineno: int, test: str):
    """Annotate the function defined in `filepath` on line `lineno` (0-based indexed)."""
    line_number = LineNumber[0](lineno)

    document = workspace.text_document.TextDocument(filepath)
    source = document.source
    file = xray.File(filepath, source)

    function_node = xray.FunctionFinder.find_function(source, line_number)
    function_name = xray.get_function(source, line_number)
    log_to_output(f"Identified `{function_name}` @ {filepath}:{line_number.one}")

    dirname = os.path.dirname(filepath)
    test_name = os.path.abspath(os.path.join(dirname, test))
    xray_config = xray.TracingConfig(file=file, node=function_node, test=test_name)

    reload_modules(LSP_SERVER.lsp.workspace)
    annotations = run_xray(xray_config)
    serialized_annotations = Serializable.serialize(annotations)
    log_to_output(str(serialized_annotations))
    LSP_SERVER.lsp.send_request("workspace/inset/refresh", serialized_annotations)


def reload_modules(workspace: workspace.Workspace):
    """Remove any imported modules that are in the workspace."""
    # File paths of all the folders in the workspace.
    workspace_folders = [uris.to_fs_path(folder.uri) for folder in workspace.folders.values()]
    workspace_modules = []
    for module in sys.modules.values():
        try:
            # Check whether any of the folders contain the file.
            if any(
                os.path.commonpath((folder, module.__file__)) == folder
                for folder in workspace_folders
            ):
                workspace_modules.append(module)
        except (AttributeError, TypeError):
            continue

    # Reload these modules.
    for module in workspace_modules:
        log_to_output(f"Reloading {module}")
        importlib.reload(module)


def run_xray(xray_config: xray.TracingConfig):
    with contextlib.redirect_stdout(sys.stderr):
        result, annotations = xray.annotate(xray_config)
        return {"result": result, "annotations": annotations}


# **********************************************************
# Required Language Server Initialization and Exit handlers.
# **********************************************************
@LSP_SERVER.feature(lsp.INITIALIZE)
def initialize(params: lsp.InitializeParams) -> None:
    """LSP handler for initialize request."""
    log_to_output(f"CWD Server: {os.getcwd()}")

    paths = "\r\n   ".join(sys.path)
    log_to_output(f"sys.path used to run Server:\r\n   {paths}")

    GLOBAL_SETTINGS.update(**params.initialization_options.get("globalSettings", {}))

    settings = params.initialization_options["settings"]
    _update_workspace_settings(settings)
    log_to_output(
        f"Settings used to run Server:\r\n{json.dumps(settings, indent=4, ensure_ascii=False)}\r\n"
    )
    log_to_output(
        f"Global settings:\r\n{json.dumps(GLOBAL_SETTINGS, indent=4, ensure_ascii=False)}\r\n"
    )


@LSP_SERVER.feature(lsp.EXIT)
def on_exit(_params: Optional[Any] = None) -> None:
    """Handle clean up on exit."""
    jsonrpc.shutdown_json_rpc()


@LSP_SERVER.feature(lsp.SHUTDOWN)
def on_shutdown(_params: Optional[Any] = None) -> None:
    """Handle clean up on shutdown."""
    jsonrpc.shutdown_json_rpc()


def _get_global_defaults():
    return {
        "path": GLOBAL_SETTINGS.get("path", []),
        "interpreter": GLOBAL_SETTINGS.get("interpreter", [sys.executable]),
        "args": GLOBAL_SETTINGS.get("args", []),
        "importStrategy": GLOBAL_SETTINGS.get("importStrategy", "useBundled"),
        "showNotifications": GLOBAL_SETTINGS.get("showNotifications", "off"),
    }


def _update_workspace_settings(settings):
    if not settings:
        key = os.getcwd()
        WORKSPACE_SETTINGS[key] = {
            "cwd": key,
            "workspaceFS": key,
            "workspace": uris.from_fs_path(key),
            **_get_global_defaults(),
        }
        return

    for setting in settings:
        key = uris.to_fs_path(setting["workspace"])
        WORKSPACE_SETTINGS[key] = {
            "cwd": key,
            **setting,
            "workspaceFS": key,
        }


# *****************************************************
# Logging and notification.
# *****************************************************
def log_to_output(message: str, msg_type: lsp.MessageType = lsp.MessageType.Log) -> None:
    LSP_SERVER.show_message_log(message, msg_type)


def log_error(message: str) -> None:
    LSP_SERVER.show_message_log(message, lsp.MessageType.Error)
    if os.getenv("LS_SHOW_NOTIFICATION", "off") in ["onError", "onWarning", "always"]:
        LSP_SERVER.show_message(message, lsp.MessageType.Error)


def log_warning(message: str) -> None:
    LSP_SERVER.show_message_log(message, lsp.MessageType.Warning)
    if os.getenv("LS_SHOW_NOTIFICATION", "off") in ["onWarning", "always"]:
        LSP_SERVER.show_message(message, lsp.MessageType.Warning)


def log_always(message: str) -> None:
    LSP_SERVER.show_message_log(message, lsp.MessageType.Info)
    if os.getenv("LS_SHOW_NOTIFICATION", "off") in ["always"]:
        LSP_SERVER.show_message(message, lsp.MessageType.Info)


# *****************************************************
# Start the server.
# *****************************************************
if __name__ == "__main__":
    LSP_SERVER.start_io()
