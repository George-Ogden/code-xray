import ast
import bdb
import copy
import enum
from typing import Union

from .config import File
from .control_index import ControlIndexBuilder
from .difference import *
from .indent_index import IndentIndex, IndentIndexBuilder
from .line_index import LineIndex, LineIndexBuilder
from .observations import Observations
from .utils import LineNumber, Position


class FrameState(enum.Enum):
    UNINITIALIZED = enum.auto()
    RETURNED = enum.auto()


class Debugger(bdb.Bdb):
    def __init__(self, file: File, node: ast.FunctionDef, skip=None) -> None:
        super().__init__(skip)
        # Canonicalize filename.
        self._filename = self.canonic(file.filepath)
        self._source = file.source
        self._line_number = LineNumber[1](node.lineno)
        self._end_line_number = LineNumber[1](node.end_lineno)

        # Initialise differences and previous lines.
        self.previous_position: Position
        self.observations = Observations()

        self.frame: Union[FrameState, "frame"] = FrameState.UNINITIALIZED

        # Build indices.
        self._line_index = self.precompute_line_index(node)
        self._indent_index = self.precompute_indent_index(file)
        self._control_index = self.precompute_control_index(node)

        # Initialise locals.
        self._locals = {}
        super().run("", self._locals)

    def precompute_line_index(self, node: ast.FunctionDef) -> LineIndex:
        return LineIndexBuilder.build_index(node)

    def precompute_control_index(self, node: ast.FunctionDef) -> LineIndex:
        return ControlIndexBuilder.build_index(node)

    def precompute_indent_index(self, file: File) -> IndentIndex:
        return IndentIndexBuilder.build_index(file.source)

    def frame_position(self, frame) -> Position:
        """Get the line number of the code."""
        line_number = LineNumber[1](frame.f_lineno)
        # * Lookup indent and line number in index.
        # Indent of current line.
        indent = self._indent_index[line_number]
        # Line number that finishes the expression.
        line_number = self._line_index[line_number]
        return Position(line_number, indent)

    def user_line(self, frame) -> None:
        # Potentially enter if call is not noticed.
        if self.frame is FrameState.UNINITIALIZED:
            line_number = LineNumber[1](frame.f_lineno)
            code = frame.f_code
            if (
                code.co_filename == self._filename
                and self._line_number <= line_number <= self._end_line_number
                and code.co_qualname != "<module>"
            ):
                # Store the frame if it matches.
                self.frame = frame
                # Use the function definition as the previous position.
                self.previous_position = Position(
                    self._line_number, self._indent_index[self._line_number]
                )

                locals = {k: self.copy(v) for k, v in frame.f_locals.items()}
                self.annotate_difference(self.previous_position, locals, self._locals)
                self._locals = locals

        if frame is self.frame:
            # Line number is the entering line, not the exiting one.
            locals = {k: self.copy(v) for k, v in frame.f_locals.items()}
            self.annotate_difference(self.previous_position, locals, self._locals)
            self._locals = locals

            # Update to the next line number.
            self.previous_position = self.frame_position(frame)
        return super().user_line(frame)

    def copy(self, v: any) -> any:
        try:
            return copy.deepcopy(v)
        except TypeError:
            return Original(v)

    def user_call(self, frame, argument_list) -> None:
        # Code must not have been called yet (avoid recursion).
        if self.frame is FrameState.UNINITIALIZED:
            code = frame.f_code
            if (
                code.co_filename == self._filename
                and LineNumber[1](code.co_firstlineno) == self._line_number
                and code.co_qualname != "<module>"
            ):
                # Store the frame if it matches.
                self.frame = frame
                self.previous_position = self.frame_position(frame)

                locals = {k: self.copy(v) for k, v in frame.f_locals.items()}
                self.annotate_difference(self.previous_position, locals, self._locals)
                self._locals = locals

        return super().user_call(frame, argument_list)

    def user_return(self, frame, return_value) -> None:
        if frame is self.frame:
            position = self.frame_position(frame)
            source_lines = self._source.splitlines()

            locals = {k: self.copy(v) for k, v in frame.f_locals.items()}
            self.annotate_difference(position, locals, self._locals)

            # Check if the list instruction was a return.
            if source_lines[position.line.zero][position.character :].startswith("return"):
                observation = Return(return_value)
                self.log_observation(observation, position)

            # Mark as returned.
            self.frame = FrameState.RETURNED
        return super().user_return(frame, return_value)

    def user_exception(self, frame, exc_info) -> None:
        if frame is self.frame:
            position = self.frame_position(frame)

            # Find the exception value.
            exception, value, traceback = exc_info
            observation = Exception_(value)
            self.log_observation(observation, position)
        return super().user_exception(frame, exc_info)

    def annotate_difference(
        self,
        position: Position,
        new_variables: dict[str, any],
        old_variables: dict[str, any],
    ):
        """Log the change of state in the variables."""
        difference = Difference.dict_difference(old_variables, new_variables, collect=False).rename(
            r"^\['([a-z0-9_]+)'\]", r"\1"
        )
        self.log_observation(difference, position)

    def log_observation(self, observation: Observation, position: Position):
        """Store the observation and its position."""
        self.observations.add(position, observation)

    def get_annotations(self):
        return self.observations.to_annotations(self._control_index)
