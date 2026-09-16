"""Calling external tools (simulator, linter, waveform viewer)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from . import ui
from .ui import Abort

# How to install the tool on Arch -- ends up in error messages.
INSTALL_HINTS = {
    "verilator": "pacman -S verilator",
    "iverilog": "pacman -S iverilog",
    "vvp": "pacman -S iverilog",
    "gtkwave": "pacman -S gtkwave",
    "surfer": "paru -S surfer-bin",
    "yosys": "pacman -S yosys",
}


VENV_DIRS = (".venv", "venv")


def venv_python(start: Path | None = None) -> Path | None:
    """Searches upwards for a venv and returns its interpreter."""
    current = (start or Path.cwd()).resolve()
    for directory in (current, *current.parents):
        for name in VENV_DIRS:
            candidate = directory / name / "bin" / "python3"
            if candidate.is_file():
                return candidate
    return None


def python(start: Path | None = None) -> str:
    """Interpreter for cocotb: the venv if there is one, else system python."""
    found = venv_python(start)
    return str(found) if found else "python3"


def find(name: str) -> str | None:
    return shutil.which(name)


def require(name: str) -> str:
    path = find(name)
    if path is None:
        hint = INSTALL_HINTS.get(name)
        raise Abort(
            f"'{name}' is not installed",
            hint=f"Install it with: {hint}" if hint else None,
        )
    return path


def run(argv: list[str], cwd: Path | None = None, log: Path | None = None,
        echo: bool = True) -> int:
    """Runs a command, shows its output and optionally records it."""
    if echo:
        ui.shell(argv)

    process = subprocess.Popen(
        [str(a) for a in argv],
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    captured: list[str] = []
    assert process.stdout is not None
    for line in process.stdout:
        captured.append(line)
        print("  " + line.rstrip())
    code = process.wait()

    if log is not None:
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text("".join(captured), encoding="utf-8")

    return code


def spawn(argv: list[str]) -> None:
    """Starts a GUI program detached from the terminal."""
    ui.shell(argv)
    subprocess.Popen(
        [str(a) for a in argv],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def python_module(name: str, start: Path | None = None,
                  cli: bool = False) -> str | None:
    """Version of a python module, or None if it cannot be imported.

    `cli=True` asks the interpreter `flow` itself runs on; otherwise the one
    used for simulating (the venv, if there is one).
    """
    code = (
        "import importlib.metadata as m, sys;"
        f"sys.stdout.write(m.version({name!r}))"
    )
    try:
        result = subprocess.run(
            [sys.executable if cli else python(start), "-c", code],
            capture_output=True, text=True, timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() if result.returncode == 0 else None
