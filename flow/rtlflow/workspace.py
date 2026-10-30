"""Finding the workspace and the module -- starting from the current directory.

There is deliberately no stored state ("active module"). Where you stand
decides what is worked on; from outside you append the module name. Same
model as git or cargo.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import config, sources
from .ui import Abort


@dataclass
class Module:
    name: str
    root: Path
    cfg: dict[str, Any]

    @property
    def cfg_path(self) -> Path:
        return self.root / config.CONFIG_NAME

    def path(self, relative: str) -> Path:
        return (self.root / relative).resolve()

    @property
    def rundir(self) -> Path:
        return self.path(self.cfg["sim"]["rundir"])

    @property
    def lintdir(self) -> Path:
        return self.path(self.cfg["lint"]["rundir"])

    @property
    def top_design(self) -> str | None:
        return self.cfg["top"]["design"]

    @property
    def top_tb(self) -> str | None:
        """Top of the SystemVerilog testbench (framework: sv)."""
        return self.cfg["top"]["tb"]

    def sim_top(self, framework: str | None = None) -> str | None:
        """The top module the simulation runs against.

        cocotb attaches directly to the design (top.design), a plain
        SystemVerilog run drives the testbench (top.tb). Both can live
        side by side in the same module.
        """
        which = framework or self.cfg["sim"]["framework"]
        if which == "sv":
            return self.cfg["top"]["tb"]
        return self.cfg["top"]["design"]

    def entries(self, which: str) -> list[str]:
        """The `sources.<which>` list (rtl | tb)."""
        value = self.cfg["sources"].get(which) or []
        if isinstance(value, str):
            value = [value]
        return [str(entry) for entry in value]

    def dependency(self, entry: str) -> "Module":
        """Resolves a `dependencies` entry: a workspace module name, a module
        directory or a path to a project.yaml (relative to this module)."""
        path = (self.root / entry).resolve()
        if path.is_file() and path.name.endswith((".yaml", ".yml")):
            return Module.load(path.parent, path.name)
        if (path / config.CONFIG_NAME).is_file():
            return Module.load(path)
        ws, _ = discover(self.root)
        if ws is not None and entry in ws.module_names():
            return ws.get(entry)
        raise Abort(
            f"{self.name}: dependency '{entry}' not found",
            hint="Use a module name from this workspace or a path to its project.yaml.",
        )

    def dependencies(self, _stack: tuple[Path, ...] = ()) -> "list[Module]":
        """All modules this one depends on, transitively, dependencies first."""
        if self.root in _stack:
            chain = " -> ".join(p.name for p in (*_stack, self.root))
            raise Abort(f"Modules depend on each other in a cycle: {chain}")
        result: list[Module] = []
        for entry in self.cfg.get("dependencies") or []:
            dep = self.dependency(str(entry))
            for sub in (*dep.dependencies((*_stack, self.root)), dep):
                if all(sub.root != seen.root for seen in result):
                    result.append(sub)
        return result

    def sources(self, which: str = "all") -> sources.Sources:
        """Scans the sources. `which` is all | rtl | tb.

        RTL of dependencies is part of `rtl` (and `all`); their testbenches
        are not.
        """
        kinds = ("rtl", "tb") if which == "all" else (which,)
        result = sources.Sources()
        for kind in kinds:
            if kind == "rtl":
                for dep in self.dependencies():
                    result.merge(sources.scan(dep.root, dep.entries("rtl"),
                                              f"{dep.name}: sources.rtl", sort=False))
            result.merge(sources.scan(self.root, self.entries(kind),
                                      f"sources.{kind}", sort=kind != "rtl"))
        if "rtl" in kinds:
            result.sources = sources.order(result.sources)
        return result

    @classmethod
    def load(cls, root: Path, filename: str = config.CONFIG_NAME) -> "Module":
        cfg = config.load(root / filename)
        return cls(name=cfg.get("project") or root.name, root=root, cfg=cfg)


@dataclass
class Workspace:
    root: Path

    @property
    def cfg(self) -> dict[str, Any]:
        """workspace.yaml, read once and remembered."""
        cached = getattr(self, "_cfg", None)
        if cached is None:
            cached = config.load_workspace(self.root / config.WORKSPACE_NAME)
            self._cfg = cached
        return cached

    @property
    def name(self) -> str:
        return self.cfg.get("workspace") or self.root.name

    @property
    def defaults(self) -> dict[str, Any]:
        """The defaults block from workspace.yaml, e.g. author and email."""
        value = self.cfg.get("defaults")
        return value if isinstance(value, dict) else {}

    @property
    def modules_dir(self) -> Path:
        return self.root / "modules"

    @property
    def templates_dir(self) -> Path:
        return self.root / "templates"

    def module_names(self) -> list[str]:
        if not self.modules_dir.is_dir():
            return []
        return sorted(
            entry.name
            for entry in self.modules_dir.iterdir()
            if (entry / config.CONFIG_NAME).is_file()
        )

    def modules(self) -> list[Module]:
        return [Module.load(self.modules_dir / name) for name in self.module_names()]

    def get(self, name: str) -> Module:
        root = self.modules_dir / name
        if not (root / config.CONFIG_NAME).is_file():
            known = ", ".join(self.module_names()) or "none"
            raise Abort(
                f"Module '{name}' does not exist",
                hint=f"Available: {known}. Create it with `flow new {name}`.",
            )
        return Module.load(root)


def discover(start: Path | None = None) -> tuple[Workspace | None, Module | None]:
    """Searches upwards from `start` for a module and a workspace."""
    current = (start or Path.cwd()).resolve()
    workspace: Workspace | None = None
    module: Module | None = None

    for directory in (current, *current.parents):
        if module is None and (directory / config.CONFIG_NAME).is_file():
            module = Module.load(directory)
        if (directory / config.WORKSPACE_NAME).is_file():
            workspace = Workspace(directory)
            break

    return workspace, module


def resolve(name: str | None, start: Path | None = None) -> tuple[Workspace | None, Module]:
    """Works out which module is being worked on.

    With `name` it is looked up in the workspace, without one the current
    directory decides.
    """
    workspace, module = discover(start)

    if name:
        if workspace is None:
            raise Abort(
                f"No workspace found -- '{name}' cannot be resolved",
                hint=f"A workspace is a directory holding {config.WORKSPACE_NAME}.",
            )
        return workspace, workspace.get(name)

    if module is None:
        if workspace is not None:
            known = ", ".join(workspace.module_names()) or "none yet"
            raise Abort(
                "No module -- you are in the workspace, not inside a module",
                hint=f"Name the module (`flow <command> <module>`) or cd into it. Available: {known}.",
            )
        raise Abort(
            f"No {config.CONFIG_NAME} in this or any parent directory",
            hint="cd into a module, or create one with `flow new <name>`.",
        )

    return workspace, module


def require_workspace(start: Path | None = None) -> Workspace:
    workspace, _ = discover(start)
    if workspace is None:
        raise Abort(
            f"No workspace found ({config.WORKSPACE_NAME} is missing)",
            hint="Create one here with `flow init`.",
        )
    return workspace
