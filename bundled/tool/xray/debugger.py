import bdb
import copy
import enum
from collections import defaultdict
from typing import Dict, Union

from .difference import *


class FrameState(enum.Enum):
    UNINITIALIZED = enum.auto()
    RETURNED = enum.auto()


class Debugger(bdb.Bdb):
    prefix = "# "

    def __init__(self, filename: str, method_lineno: int, skip=None) -> None:
        super().__init__(skip)
        # Canonicalize filename.
        self._filename = self.canonic(filename)
        self._line_number = method_lineno

        # Initialise annotations and previous lines.
        self.previous_line: int
        self.difference_annotations: dict[int, list[str]] = defaultdict(
            list
        )  # Map from line numbers to logs.

        self.frame: Union[FrameState, "frame"] = FrameState.UNINITIALIZED

        # Initialise locals.
        self._locals = {}
        super().run("", self._locals)

    def user_line(self, frame) -> None:
        if frame is self.frame:
            # Line number is the entering line, not the exiting one.
            self.annotate_difference(self.previous_line, frame.f_locals, self._locals)
            self._locals = copy.deepcopy(frame.f_locals)

            # Update to the next line number.
            self.previous_line = frame.f_lineno
        return super().user_line(frame)

    def user_call(self, frame, argument_list) -> None:
        # Code must not have been called yet (avoid recursion).
        if self.frame is FrameState.UNINITIALIZED:
            code = frame.f_code
            if (
                code.co_filename == self._filename
                and code.co_firstlineno == self._line_number
                and code.co_qualname != "<module>"
            ):
                # Store the frame if it matches.
                self.frame = frame
                self.previous_line = frame.f_lineno

                self.annotate_difference(frame.f_lineno, frame.f_locals, self._locals)
                self._locals = copy.deepcopy(frame.f_locals)

        return super().user_call(frame, argument_list)

    def user_return(self, frame, return_value) -> None:
        if frame is self.frame:
            line_number = frame.f_lineno
            difference_string = repr(Return(return_value))
            self.difference_annotations[line_number].append(difference_string)
            self.frame = FrameState.RETURNED
        return super().user_return(frame.f_code.co_filename, return_value)

    def user_exception(self, frame, exc_info) -> None:
        if frame is self.frame:
            exception, value, traceback = exc_info
            line_number = frame.f_lineno
            difference_string = repr(Exception_(value))
            self.difference_annotations[line_number].append(difference_string)
            self.frame = FrameState.RETURNED
        return super().user_exception(frame, exc_info)

    def annotate_difference(
        self,
        line_number: int,
        new_variables: dict[str, any],
        old_variables: dict[str, any],
    ):
        """Log the change of state in the variables."""
        # Convert difference to toplevel string.
        difference = Difference.difference(old_variables, new_variables).rename(
            r"^\['([a-z0-9_]+)'\]", r"\1"
        )
        difference_string = repr(difference)
        if difference_string:
            # Store in annotations.
            self.difference_annotations[line_number].append(difference_string)

    @property
    def annotations(self) -> Dict[int, str]:
        """Return annotations for each line."""
        # TODO: implement full method
        return {k: "; ".join(v) for k, v in self.difference_annotations.items()}

        # TODO: implement full method
        return {k: "; ".join(v) for k, v in self.difference_annotations.items()}
