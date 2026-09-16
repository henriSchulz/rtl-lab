"""project.yaml: load it, fill in defaults, patch single keys."""

from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any

import yaml

from .ui import Abort

CONFIG_NAME = "project.yaml"
WORKSPACE_NAME = "workspace.yaml"

DEFAULTS: dict[str, Any] = {
    "project": None,
    "description": "",
    "author": None,
    "created": None,
    "top": {"design": None, "tb": None},
    "sources": {
        "filelist": "src/files.f",
        "design": "src/design.f",
        "tb": "src/tb.f",
    },
    "sim": {
        "simulator": "verilator",
        "framework": "cocotb",  # cocotb | sv
        "rundir": "sim/run",
        "testdir": "src/tb/cocotb",
        "modules": [],
        "waves": "fst",
        "timescale": "1ns/1ps",
        "defines": [],
        "plusargs": [],
        "build_args": [],
    },
    "lint": {
        "tool": "verilator",
        "rundir": "lint",
        "waivers": "lint/waivers.vlt",
        "fatal": True,
        "args": [],
    },
    "docs": {"dir": "docs"},
}


def _deep_merge(base: dict, override: dict) -> dict:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if value is None and key in result and isinstance(result[key], (dict, list)):
            continue
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load(path: Path) -> dict[str, Any]:
    """Reads a project.yaml and fills missing fields from DEFAULTS."""
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise Abort(f"{path} is not valid YAML", hint=str(exc)) from exc
    if not isinstance(raw, dict):
        raise Abort(f"{path}: a mapping is expected at the top level")
    return _deep_merge(DEFAULTS, raw)


def load_workspace(path: Path) -> dict[str, Any]:
    """Reads workspace.yaml. Missing or empty leaves it at {}."""
    if not path.is_file():
        return {}
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise Abort(f"{path} is not valid YAML", hint=str(exc)) from exc
    if not isinstance(raw, dict):
        raise Abort(f"{path}: a mapping is expected at the top level")
    return raw


# ---------------------------------------------------------------------------
# Targeted edits that keep comments and formatting intact.
# A pyyaml roundtrip would throw both away, hence the line-based approach.
# ---------------------------------------------------------------------------

_KEY = r"^(?P<indent>\s*)(?P<key>{key}):(?P<rest>.*)$"


def _find_key(lines: list[str], key: str, indent: int, start: int, stop: int) -> int:
    pattern = re.compile(_KEY.format(key=re.escape(key)))
    for index in range(start, stop):
        match = pattern.match(lines[index])
        if match and len(match.group("indent")) == indent:
            return index
    return -1


def _block_end(lines: list[str], start: int, indent: int) -> int:
    for index in range(start + 1, len(lines)):
        line = lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if len(line) - len(line.lstrip()) <= indent:
            return index
    return len(lines)


def _locate(lines: list[str], dotted: str) -> int:
    """Line index of the key 'a.b.c', or -1."""
    parts = dotted.split(".")
    start, stop, indent = 0, len(lines), 0
    index = -1
    for depth, part in enumerate(parts):
        index = _find_key(lines, part, indent, start, stop)
        if index < 0:
            return -1
        if depth < len(parts) - 1:
            stop = _block_end(lines, index, indent)
            start = index + 1
            indent += 2
    return index


def _split_comment(rest: str) -> tuple[str, str]:
    """Splits the value from a trailing '#' comment."""
    match = re.search(r"\s+#", rest)
    if match:
        return rest[: match.start()], rest[match.start() :]
    return rest, ""


def _recompose(indent: str, key: str, pad: str, value: str,
               old_body: str, comment: str) -> str:
    """Rebuilds the line, keeping the comment in its original column."""
    line = f"{indent}{key}:{pad}{value}"
    if not comment:
        return line
    column = len(indent) + len(key) + 1 + len(old_body) + (len(comment) - len(comment.lstrip()))
    return line.ljust(column) + comment.lstrip() if len(line) < column else line + "  " + comment.lstrip()


def _pad(rest: str) -> str:
    return " " * max(1, len(rest) - len(rest.lstrip()))


def set_scalar(path: Path, dotted: str, value: Any) -> bool:
    """Sets the project.yaml key 'a.b' to `value`. True on success."""
    lines = path.read_text(encoding="utf-8").splitlines()
    index = _locate(lines, dotted)
    if index < 0:
        return False

    match = re.match(_KEY.format(key=re.escape(dotted.split(".")[-1])), lines[index])
    body, comment = _split_comment(match.group("rest"))
    rendered = "~" if value is None else str(value)

    lines[index] = _recompose(
        match.group("indent"), match.group("key"), _pad(match.group("rest")),
        rendered, body, comment,
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True


def append_to_list(path: Path, dotted: str, value: str) -> bool:
    """Appends `value` to a YAML list -- flow style or block style."""
    lines = path.read_text(encoding="utf-8").splitlines()
    index = _locate(lines, dotted)
    if index < 0:
        return False

    match = re.match(_KEY.format(key=re.escape(dotted.split(".")[-1])), lines[index])
    body, comment = _split_comment(match.group("rest"))
    stripped = body.strip()

    if stripped.startswith("[") and stripped.endswith("]"):
        items = [i.strip() for i in stripped[1:-1].split(",") if i.strip()]
        if value in items:
            return True
        items.append(value)
        lines[index] = _recompose(
            match.group("indent"), match.group("key"), _pad(match.group("rest")),
            f"[{', '.join(items)}]", body, comment,
        )
    elif not stripped:
        indent = " " * (len(match.group("indent")) + 2)
        end = _block_end(lines, index, len(match.group("indent")))
        existing = [
            line.strip()[2:].strip()
            for line in lines[index + 1 : end]
            if line.strip().startswith("- ")
        ]
        if value in existing:
            return True
        lines.insert(index + 1 + len(existing), f"{indent}- {value}")
    else:
        return False

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True
