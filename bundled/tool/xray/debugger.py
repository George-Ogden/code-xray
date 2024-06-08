import bdb
import copy
import enum
from typing import Union

from .annotation import Annotations, Position, Timestamp
from .difference import *
from .utils import LineNumber


class FrameState(enum.Enum):
    UNINITIALIZED = enum.auto()
    RETURNED = enum.auto()


class Debugger(bdb.Bdb):
    def __init__(self, filename: str, method_lineno: LineNumber, skip=None) -> None:
        super().__init__(skip)
        # Canonicalize filename.
        self._filename = self.canonic(filename)
        self._line_number = method_lineno

        # Initialise annotations and previous lines.
        self.previous_line: int
        self.annotations = Annotations()  # Map from line numbers to logs.

        self.frame: Union[FrameState, "frame"] = FrameState.UNINITIALIZED

        # Initialise timestamp.
        self._timestamp: Timestamp = Timestamp()

        # Initialise locals.
        self._locals = {}
        super().run("", self._locals)

    @property
    def timestamp(self) -> Timestamp:
        return self._timestamp

    def frame_line_number(self, frame) -> int:
        """Get the line number of the code."""
        line_number = LineNumber[1](frame.f_lineno)
        if line_number == self._line_number:
            line_number += 1
        return line_number

    def trace_dispatch(self, frame, event, arg):
        self._timestamp += 1
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
        # Convert differences to annotations.
        difference = Difference.difference(old_variables, new_variables).rename(
            r"^\['([a-z0-9_]+)'\]", r"\1"
        )
        self.save_difference(difference, line_number)

    def save_difference(self, difference: Difference, line_number: LineNumber):
        for annotation in difference.to_annotations(self.timestamp, Position(line_number, 0)):
            self.annotations += annotation
