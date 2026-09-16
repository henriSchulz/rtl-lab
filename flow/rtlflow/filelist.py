"""Parser for .f filelists.

The common simulators treat relative paths inside a .f file differently
(sometimes relative to the working directory, sometimes to the file). So
this module resolves them itself -- consistently **relative to the directory
the .f file lives in** -- and hands the tool absolute paths only. That way
the flow behaves the same everywhere.

Supported:
    -f FILE / -F FILE      include another filelist
    +incdir+DIR[+DIR...]   include paths
    +define+NAME[=VALUE]   macros
    -y DIR                 library directory
    // ... and # ...       comments
    $VAR / ${VAR}          environment variables
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from .ui import Abort

_COMMENT = re.compile(r"(^|\s)(//|#).*$")


@dataclass
class Filelist:
    """The resolved result of a .f tree."""

    sources: list[Path] = field(default_factory=list)
    incdirs: list[Path] = field(default_factory=list)
    libdirs: list[Path] = field(default_factory=list)
    defines: dict[str, str | None] = field(default_factory=dict)
    visited: list[Path] = field(default_factory=list)

    def merge(self, other: "Filelist") -> None:
        for src in other.sources:
            if src not in self.sources:
                self.sources.append(src)
        for inc in other.incdirs:
            if inc not in self.incdirs:
                self.incdirs.append(inc)
        for lib in other.libdirs:
            if lib not in self.libdirs:
                self.libdirs.append(lib)
        self.defines.update(other.defines)
        self.visited.extend(other.visited)

    def is_empty(self) -> bool:
        return not self.sources


def _tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for raw in text.splitlines():
        line = _COMMENT.sub("", raw).strip()
        if line:
            tokens.extend(line.split())
    return tokens


def _expand(token: str) -> str:
    return os.path.expandvars(os.path.expanduser(token))


def parse(path: Path, _stack: tuple[Path, ...] = ()) -> Filelist:
    """Reads `path` and every list pulled in via -f, recursively."""
    path = path.resolve()
    if path in _stack:
        chain = " -> ".join(p.name for p in (*_stack, path))
        raise Abort(f"Cycle in the filelists: {chain}")
    if not path.is_file():
        raise Abort(f"Filelist not found: {path}")

    base = path.parent
    result = Filelist(visited=[path])
    tokens = _tokenize(path.read_text(encoding="utf-8"))

    index = 0
    while index < len(tokens):
        token = _expand(tokens[index])
        index += 1

        if token in ("-f", "-F", "-file"):
            if index >= len(tokens):
                raise Abort(f"{path}: '{token}' without a file name after it")
            nested = (base / _expand(tokens[index])).resolve()
            index += 1
            result.merge(parse(nested, (*_stack, path)))

        elif token in ("-y", "-v"):
            if index >= len(tokens):
                raise Abort(f"{path}: '{token}' without a directory after it")
            target = (base / _expand(tokens[index])).resolve()
            index += 1
            if token == "-y":
                result.libdirs.append(target)
            else:
                result.sources.append(target)

        elif token.startswith("+incdir+"):
            for part in token[len("+incdir+") :].split("+"):
                if part:
                    result.incdirs.append((base / _expand(part)).resolve())

        elif token.startswith("+define+"):
            for part in token[len("+define+") :].split("+"):
                if not part:
                    continue
                name, _, value = part.partition("=")
                result.defines[name] = value or None

        elif token.startswith(("+", "-")):
            # Passing unknown switches through unchanged would be risky --
            # better to be loud than to swallow something silently.
            raise Abort(
                f"{path}: unknown option '{token}'",
                hint="Supported are -f, -F, -y, -v, +incdir+, +define+.",
            )

        else:
            source = (base / token).resolve()
            if not source.exists():
                raise Abort(
                    f"{path}: source file missing: {token}",
                    hint=f"Expected at {source}",
                )
            result.sources.append(source)

    return result
