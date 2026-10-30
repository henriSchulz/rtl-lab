"""Source discovery: `sources.rtl` / `sources.tb` in project.yaml -> file lists.

There are no filelists. A module names directories (searched recursively),
files or globs, relative to the module root, and the flow scans them itself.
Tools only ever see absolute paths.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from .ui import Abort

SOURCE_SUFFIXES = {".sv", ".v"}
HEADER_SUFFIXES = {".svh", ".vh"}

_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.S)
_LINE_COMMENT = re.compile(r"//[^\n]*")
_PACKAGE_DEF = re.compile(r"^\s*package\s+(?:automatic\s+|static\s+)?(\w+)\s*;", re.M)
_PACKAGE_USE = re.compile(r"\b(\w+)\s*::")


@dataclass
class Sources:
    """The resolved result of one or more source entries."""

    sources: list[Path] = field(default_factory=list)
    incdirs: list[Path] = field(default_factory=list)
    defines: dict[str, str | None] = field(default_factory=dict)

    def merge(self, other: "Sources") -> None:
        for src in other.sources:
            if src not in self.sources:
                self.sources.append(src)
        for inc in other.incdirs:
            if inc not in self.incdirs:
                self.incdirs.append(inc)
        self.defines.update(other.defines)

    def is_empty(self) -> bool:
        return not self.sources


def _strip_comments(text: str) -> str:
    return _LINE_COMMENT.sub("", _BLOCK_COMMENT.sub("", text))


def _order(files: list[Path]) -> list[Path]:
    """Packages first (dependencies before users), everything else by path.

    Compilers that read files in order need a package before the first use.
    """
    texts = {p: _strip_comments(p.read_text(encoding="utf-8", errors="replace"))
             for p in files}
    defines = {p: set(_PACKAGE_DEF.findall(t)) for p, t in texts.items()}
    owner = {name: p for p, names in defines.items() for name in names}

    packages = sorted(p for p in files if defines[p])
    others = sorted(p for p in files if not defines[p])
    deps = {
        p: {owner[n] for n in set(_PACKAGE_USE.findall(texts[p]))
            if n in owner and owner[n] != p}
        for p in packages
    }

    ordered: list[Path] = []
    state: dict[Path, int] = {}

    def visit(p: Path, chain: tuple[Path, ...]) -> None:
        if state.get(p) == 2:
            return
        if state.get(p) == 1:
            cycle = " -> ".join(q.name for q in (*chain, p))
            raise Abort(f"Packages depend on each other in a cycle: {cycle}")
        state[p] = 1
        for dep in sorted(deps[p]):
            visit(dep, (*chain, p))
        state[p] = 2
        ordered.append(p)

    for p in packages:
        visit(p, ())
    return ordered + others


def scan(root: Path, entries: list[str], key: str = "sources.rtl") -> Sources:
    """Expands `entries` (dirs, files, globs below `root`) into sources."""
    result = Sources()
    found_files: list[Path] = []

    def add_incdir(path: Path) -> None:
        if path not in result.incdirs:
            result.incdirs.append(path)

    for entry in entries:
        pattern = os.path.expandvars(os.path.expanduser(entry))
        target = root / pattern
        if any(ch in pattern for ch in "*?["):
            matches = sorted(p for p in root.glob(pattern) if p.is_file())
            if not matches:
                raise Abort(f"{key}: '{entry}' matches no file")
        elif target.is_dir():
            matches = sorted(p for p in target.rglob("*") if p.is_file())
            add_incdir(target.resolve())
        elif target.is_file():
            matches = [target]
        else:
            raise Abort(f"{key}: '{entry}' does not exist",
                        hint=f"Expected at {target.resolve()}")

        for path in matches:
            path = path.resolve()
            if path.suffix in HEADER_SUFFIXES:
                add_incdir(path.parent)
            elif path.suffix in SOURCE_SUFFIXES and path not in found_files:
                found_files.append(path)

    result.sources = _order(found_files)
    return result
