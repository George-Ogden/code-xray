import bdb
import copy
import enum
import re
from typing import Union

from .annotation import Position
from .config import File
from .difference import *
from .differences import Differences
from .indent_index import IndentIndex
from .line_index import LineIndex, LineIndexBuilder
from .utils import LineNumber


class FrameState(enum.Enum):
    UNINITIALIZED = enum.auto()
    RETURNED = enum.auto()


class Debugger(bdb.Bdb):
    def __init__(self, file: File, method_lineno: LineNumber, skip=None) -> None:
        super().__init__(skip)
        # Canonicalize filename.
        self._filename = self.canonic(file.filepath)
        self._source = file.source
        self._line_number = method_lineno

        # Initialise differences and previous lines.
        self.previous_line: int
        self.differences = Differences()

        self.frame: Union[FrameState, "frame"] = FrameState.UNINITIALIZED

        # Build indices.
        self._line_index = self.precompute_line_index(file)
        self._indent_index = self.precompute_indent_index(file)

        # Initialise locals.
        self._locals = {}
        super().run("", self._locals)

    def precompute_line_index(self, file: File) -> LineIndex:
        return LineIndexBuilder.build_index(file.source, self._line_number)

    def precompute_indent_index(self, file: File) -> IndentIndex:
        # Compute the number of spaces at the beginning of each line.
        spaces = [re.match(r"^ *", line).group(0) for line in file.source.splitlines()]
        indent_index = {LineNumber[0](i): len(space) for i, space in enumerate(spaces)}
        return indent_index

    def frame_line_number(self, frame) -> int:
        """Get the line number of the code."""
        line_number = LineNumber[1](frame.f_lineno)
        return self._line_index[line_number]

    def trace_dispatch(self, frame, event, arg):
        return super().trace_dispatch(frame, event, arg)

    def user_line(self, frame) -> None:
        if frame is self.frame:
            # Line number is the entering line, not the exiting one.
            self.annotate_difference(self.previous_line, frame.f_locals, self._locals)
            self._locals = copy.deepcopy(frame.f_locals)

            # Update to the next line number.
            self.previous_line = self.frame_line_number(frame)
        return super().user_line(frame)

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
                self.previous_line = self.frame_line_number(frame)

                self.annotate_difference(self.previous_line, frame.f_locals, self._locals)
                self._locals = copy.deepcopy(frame.f_locals)

        return super().user_call(frame, argument_list)

    def user_return(self, frame, return_value) -> None:
        if frame is self.frame:
            line_number = self.frame_line_number(frame)
            difference = Return(return_value)
            self.save_difference(difference, line_number)
            self.frame = FrameState.RETURNED
        return super().user_return(frame.f_code.co_filename, return_value)

    def user_exception(self, frame, exc_info) -> None:
        if frame is self.frame:
            line_number = self.frame_line_number(frame)
            exception, value, traceback = exc_info
            difference = Exception_(value)
            self.save_difference(difference, line_number)
            self.frame = FrameState.RETURNED
        return super().user_exception(frame, exc_info)

    def annotate_difference(
        self,
        line_number: int,
        new_variables: dict[str, any],
        old_variables: dict[str, any],
    ):
        """Log the change of state in the variables."""
        difference = Difference.difference(old_variables, new_variables).rename(
            r"^\['([a-z0-9_]+)'\]", r"\1"
        )
        self.save_difference(difference, line_number)

    def save_difference(self, difference: Difference, line_number: LineNumber):
        """Save the difference."""
        self.differences.add(Position(line_number, self._indent_index[line_number]), difference)
