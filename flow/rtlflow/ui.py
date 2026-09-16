"""Terminal output: colours, symbols and consistent messages."""

from __future__ import annotations

import os
import shutil
import sys

_ENABLED = (
    sys.stdout.isatty()
    and os.environ.get("NO_COLOR") is None
    and os.environ.get("TERM") != "dumb"
)


def _sgr(code: str):
    def wrap(text: object) -> str:
        return f"\033[{code}m{text}\033[0m" if _ENABLED else str(text)

    return wrap


bold = _sgr("1")
dim = _sgr("2")
red = _sgr("31")
green = _sgr("32")
yellow = _sgr("33")
blue = _sgr("34")
cyan = _sgr("36")


class Abort(Exception):
    """An error reported cleanly to the user instead of as a traceback."""

    def __init__(self, message: str, hint: str | None = None):
        super().__init__(message)
        self.hint = hint


def step(msg: str) -> None:
    print(f"{cyan('==>')} {bold(msg)}")


def ok(msg: str) -> None:
    print(f"  {green('ok')}    {msg}")


def warn(msg: str) -> None:
    print(f"  {yellow('warn')}  {msg}")


def fail(msg: str) -> None:
    sys.stdout.flush()
    print(f"  {red('fail')}  {msg}", file=sys.stderr)
    sys.stderr.flush()


def note(msg: str) -> None:
    print(f"  {dim(msg)}")


def shell(argv) -> None:
    print(f"  {dim('$ ' + ' '.join(str(a) for a in argv))}")


def hrule() -> None:
    width = min(shutil.get_terminal_size((80, 24)).columns, 100)
    print(dim("-" * width))


def table(rows, headers) -> None:
    """Narrow, left-aligned table without borders."""
    if not rows:
        return
    cols = len(headers)
    widths = [len(str(h)) for h in headers]
    for row in rows:
        for i in range(cols):
            widths[i] = max(widths[i], len(str(row[i])))
    line = "  ".join(str(h).ljust(widths[i]) for i, h in enumerate(headers))
    print("  " + bold(line.rstrip()))
    for row in rows:
        line = "  ".join(str(row[i]).ljust(widths[i]) for i in range(cols))
        print("  " + line.rstrip())
