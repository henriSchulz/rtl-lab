"""Reporting: list modules, show configuration and filelists, check the setup."""

from __future__ import annotations

from . import tools, ui, verify, workspace
from .ui import Abort

# What the flow needs, and what for.
REQUIREMENTS = [
    ("verilator", "simulation and lint", True),
    ("iverilog", "alternative simulator", False),
    ("gtkwave", "waveform viewer", False),
    ("surfer", "waveform viewer (alternative)", False),
    ("yosys", "synthesis (later)", False),
]

# (module, purpose, required, interpreter) -- "sim" = the workspace venv,
# "cli" = the interpreter `flow` itself runs on.
PYTHON_REQUIREMENTS = [
    ("cocotb", "testbench framework", True, "sim"),
    ("pyyaml", "reading project.yaml", True, "cli"),
]


def _simulated(module: workspace.Module) -> bool:
    """True once a run left something behind -- cocotb XML or SV log."""
    return (module.rundir / "results.xml").is_file() or (module.rundir / verify.SIM_LOG).is_file()


def _test_count(module: workspace.Module) -> str:
    """cocotb test modules and/or an SV bench: '2', 'sv' or '2+sv'."""
    count = len(module.cfg["sim"]["modules"])
    if not module.top_tb:
        return str(count)
    return f"{count}+sv" if count else "sv"


def ls() -> int:
    ws = workspace.require_workspace()
    modules = ws.modules()

    if not modules:
        ui.step(f"Workspace {ws.name}")
        ui.note("No modules yet. Create one with: flow new <name>")
        return 0

    rows = []
    for module in modules:
        try:
            sources = str(len(module.sources("design").sources))
        except Abort:
            sources = "?"

        lint_log = module.lintdir / f"{module.name}.log"

        rows.append([
            module.name,
            module.top_design or "-",
            sources,
            module.cfg["sim"]["framework"],
            _test_count(module),
            "yes" if lint_log.is_file() else "-",
            "yes" if _simulated(module) else "-",
        ])

    ui.step(f"Workspace {ws.name}  ({len(modules)} module(s))")
    ui.table(rows, ["MODULE", "TOP", "RTL", "FRAMEWORK", "TESTS", "LINT", "SIM"])
    return 0


def info(module_name: str | None = None) -> int:
    ws, module = workspace.resolve(module_name)
    cfg = module.cfg

    ui.step(f"Module {module.name}")
    ui.note(str(module.root))
    if cfg.get("description"):
        ui.note(cfg["description"])
    if cfg.get("author") or cfg.get("created"):
        ui.note(f"created {cfg.get('created') or '?'} by {cfg.get('author') or '?'}")
    print()

    framework = cfg["sim"]["framework"]
    rows = [
        ["top.design", cfg["top"]["design"] or "-"],
        ["top.tb", cfg["top"]["tb"] or "-"],
        ["sim top", f"{module.sim_top(framework) or '-'}  (framework: {framework})"],
        ["simulator", cfg["sim"]["simulator"]],
        ["waves", cfg["sim"]["waves"]],
        ["timescale", cfg["sim"]["timescale"]],
        ["sim.modules", ", ".join(cfg["sim"]["modules"]) or "-"],
        ["lint.tool", cfg["lint"]["tool"]],
        ["lint.fatal", str(cfg["lint"]["fatal"])],
    ]
    ui.table(rows, ["KEY", "VALUE"])
    print()

    paths = []
    for label, key in (("filelist", "filelist"), ("design", "design"), ("tb", "tb")):
        entry = cfg["sources"][key]
        exists = module.path(entry).is_file()
        paths.append([label, entry, "ok" if exists else "missing"])
    testdir = cfg["sim"]["testdir"]
    paths.append([
        "testdir", testdir,
        "ok" if module.path(testdir).is_dir() else "missing",
    ])
    for label, path in (("rundir", module.rundir), ("lintdir", module.lintdir)):
        paths.append([label, str(path.relative_to(module.root)),
                      "ok" if path.is_dir() else "missing"])
    ui.table(paths, ["PATH", "LOCATION", "STATUS"])
    return 0


def files(module_name: str | None = None, which: str = "filelist") -> int:
    _, module = workspace.resolve(module_name)
    resolved = module.sources(which)

    ui.step(f"{module.name}: {module.cfg['sources'][which]} resolved")

    ui.note("filelists read:")
    for path in resolved.visited:
        print(f"    {path}")

    if resolved.incdirs:
        print()
        ui.note("+incdir+:")
        for path in resolved.incdirs:
            print(f"    {path}")

    if resolved.defines:
        print()
        ui.note("+define+:")
        for name, value in resolved.defines.items():
            print(f"    {name}" + (f"={value}" if value else ""))

    print()
    ui.note(f"source files ({len(resolved.sources)}):")
    for path in resolved.sources:
        try:
            shown = path.relative_to(module.root)
        except ValueError:
            shown = path
        print(f"    {shown}")

    if resolved.is_empty():
        print()
        ui.warn("No source files -- the lists hold nothing but comments.")
    return 0


def _install_hint(name: str, target: str) -> str:
    if target == "sim":
        return f".venv/bin/pip install {name}"
    return f"pacman -S python-{name.lower()}"


def doctor() -> int:
    ui.step("Checking the environment")

    rows = []
    missing_required = 0

    for name, purpose, required in REQUIREMENTS:
        path = tools.find(name)
        if path:
            status = "ok"
        elif required:
            status = "MISSING"
            missing_required += 1
        else:
            status = "-"
        rows.append([name, status, purpose, path or tools.INSTALL_HINTS.get(name, "")])

    ws_probe, _ = workspace.discover()
    base = ws_probe.root if ws_probe else None
    interpreter = tools.python(base)

    for name, purpose, required, target in PYTHON_REQUIREMENTS:
        version = tools.python_module(name, base if target == "sim" else None,
                                      cli=(target == "cli"))
        if version:
            status = "ok"
        elif required:
            status = "MISSING"
            missing_required += 1
        else:
            status = "-"
        where = "venv" if target == "sim" else "cli"
        rows.append([
            f"py:{name} ({where})",
            status,
            purpose,
            version or _install_hint(name, target),
        ])

    ui.table(rows, ["TOOL", "STATUS", "PURPOSE", "PATH / HINT"])
    print()

    ws, module = workspace.discover()
    ui.note(f"Python:    {interpreter}"
            + ("" if tools.venv_python(base) else "  (no venv -- system python)"))
    ui.note(f"Workspace: {ws.root if ws else 'none found'}")
    ui.note(f"Module:    {module.root if module else 'none (not inside a module)'}")

    if missing_required:
        print()
        ui.fail(f"{missing_required} required tool(s) missing")
        return 1

    print()
    ui.ok("All set")
    return 0
