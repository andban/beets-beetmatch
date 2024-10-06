import contextlib
import sys
from io import StringIO
from typing import List


class InputError(Exception):
    def __init__(self, output=None):
        self.output = output

    def __str__(self):
        msg = "Attempt to read when no input available."
        if self.output is not None:
            msg += f" Output: {self.output!r}"

        return msg


class DummyOutput:
    encoding = "utf-8"

    def __init__(self):
        self.buf = []

    def write(self, s: str):
        self.buf.append(s)

    def get(self):
        return "".join(self.buf)

    def flush(self):
        self.clear()

    def clear(self):
        self.buf = []


class DummyInput:
    encoding = "utf-8"

    buf: List[str]
    reads: int
    out: DummyOutput

    def __init__(self, out=None):
        self.buf = []
        self.reads = 0
        self.out = out

    def add(self, s: str):
        self.buf.append(s + "\n")

    def close(self):
        pass

    def readline(self):
        if not self.buf:
            if self.out:
                raise InputError(self.out.get())
            else:
                raise InputError()

        self.reads += 1
        return self.buf.pop(0)


class DummyIO:
    """Mock for input/output streams for testing TUI code."""

    def __init__(self):
        self.stdout = DummyOutput()
        self.stdin = DummyInput(self.stdout)

    def add_input(self, s: str):
        self.stdin.add(s)

    def get_output(self):
        result = self.stdout.get()
        self.stdout.clear()
        return result

    def get_read_count(self):
        return self.stdin.reads

    def install(self):
        sys.stdin = self.stdin
        sys.stdout = self.stdout

    def restore(self):
        sys.stdin = sys.__stdin__
        sys.stdout = sys.__stdout__


@contextlib.contextmanager
def control_stdin(input=None):
    original = sys.stdin
    sys.stdin = StringIO(input)
    try:
        yield sys.stdin
    finally:
        sys.stdin = original


@contextlib.contextmanager
def capture_stdout():
    original = sys.stdout
    sys.stdout = capture = StringIO()
    try:
        yield sys.stdout
    finally:
        sys.stdout = original
        print(capture.getvalue())
