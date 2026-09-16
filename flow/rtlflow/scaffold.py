"""Creating workspaces, modules and single source files."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from . import config, meta, ui, workspace
from .ui import Abort

IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
TEXT_SUFFIXES = {".yaml", ".yml", ".f", ".sv", ".svh", ".v", ".vh", ".py", ".md", ".vlt"}

# In YAML the placeholders sit inside double quotes, so a description holding
# ": " or a "#" cannot break the file.
YAML_SUFFIXES = {".yaml", ".yml"}

# What `flow new --tb` accepts.
TB_KINDS = ("cocotb", "sv", "both", "none")

# Where testbenches live. SystemVerilog benches sit next to the .f list that
# names them (src/tb/, matching the `tb/...` entries in tb.f); cocotb tests
# get their own directory one level down -- sim.testdir in project.yaml --
# so python and SystemVerilog never share a folder.


def check_identifier(name: str, what: str = "Name") -> str:
    if not IDENTIFIER.fullmatch(name):
        raise Abort(
            f"{what} '{name}' is not a valid SystemVerilog identifier",
            hint="Allowed: letters, digits and _, starting with a letter or _.",
        )
    return name


def template_root(ws: workspace.Workspace | None) -> Path:
    """The workspace's own templates win over the packaged ones."""
    if ws is not None and ws.templates_dir.is_dir():
        return ws.templates_dir
    return Path(__file__).parent / "templates"


def fields(ws: workspace.Workspace | None, name: str, description: str,
           module: str | None = None) -> dict[str, str]:
    """Placeholders for a generated file, file header included."""
    return meta.fields(
        ws.root if ws is not None else Path.cwd(),
        ws.defaults if ws is not None else {},
        name=name,
        description=description,
        module=module or name,
        workspace=ws.name if ws is not None else "-",
    )


def escape(suffix: str, values: dict[str, str]) -> dict[str, str]:
    """Escapes the values for the file type they are rendered into."""
    if suffix not in YAML_SUFFIXES:
        return values
    return {
        key: value.replace("\\", "\\\\").replace('"', '\\"')
        for key, value in values.items()
    }


def render(text: str, **values: str) -> str:
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def render_tree(root: Path, **values: str) -> None:
    """Replaces {{placeholders}} in every text file below `root`."""
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in TEXT_SUFFIXES:
            original = path.read_text(encoding="utf-8")
            updated = render(original, **escape(path.suffix, values))
            if updated != original:
                path.write_text(updated, encoding="utf-8")


def write_from_template(source: Path, target: Path, **values: str) -> None:
    if target.exists():
        raise Abort(f"Already there: {target}")
    if not source.is_file():
        raise Abort(f"Template missing: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        render(source.read_text(encoding="utf-8"), **escape(target.suffix, values)),
        encoding="utf-8",
    )


def append_source(filelist_path: Path, entry: str) -> bool:
    """Appends a source path to a .f list, skipping duplicates."""
    text = filelist_path.read_text(encoding="utf-8") if filelist_path.exists() else ""
    for line in text.splitlines():
        stripped = re.sub(r"(^|\s)(//|#).*$", "", line).strip()
        if stripped == entry:
            return False
    if text and not text.endswith("\n"):
        text += "\n"
    filelist_path.write_text(f"{text}{entry}\n", encoding="utf-8")
    return True


# ---------------------------------------------------------------------------
# Single files -- shared by `flow new` and `flow add`.
# ---------------------------------------------------------------------------

def _emit_rtl(root: Path, cfg_path: Path, design_f: Path, templates: Path,
              name: str, values: dict[str, str], set_top: bool) -> None:
    target = root / "src" / "rtl" / f"{name}.sv"
    write_from_template(templates / "rtl_module.sv", target, **values)
    ui.ok(target.relative_to(root))

    if append_source(design_f, f"rtl/{name}.sv"):
        ui.ok(f"{design_f.name}: added rtl/{name}.sv")
    if set_top:
        config.set_scalar(cfg_path, "top.design", name)
        ui.ok(f"top.design = {name}")


def _emit_cocotb_test(root: Path, cfg_path: Path, testdir: str, templates: Path,
                      name: str, values: dict[str, str]) -> None:
    target = root / testdir / f"test_{name}.py"
    write_from_template(templates / "cocotb_test.py", target, **values)
    ui.ok(target.relative_to(root))

    if config.append_to_list(cfg_path, "sim.modules", f"test_{name}"):
        ui.ok(f"sim.modules += test_{name}")
    else:
        ui.warn("could not extend sim.modules automatically")


def _emit_sv_tb(root: Path, cfg_path: Path, tb_f: Path, templates: Path,
                name: str, values: dict[str, str], set_top: bool) -> None:
    # tb.f addresses its sources as tb/<file>, so that is where they go.
    target = tb_f.parent / "tb" / f"tb_{name}.sv"
    write_from_template(templates / "sv_tb.sv", target, **values)
    ui.ok(target.relative_to(root))

    if append_source(tb_f, f"tb/tb_{name}.sv"):
        ui.ok(f"{tb_f.name}: added tb/tb_{name}.sv")
    if set_top:
        config.set_scalar(cfg_path, "top.tb", f"tb_{name}")
        ui.ok(f"top.tb = tb_{name}")


# ---------------------------------------------------------------------------
# flow init
# ---------------------------------------------------------------------------

def init(name: str | None = None, directory: Path | None = None) -> None:
    root = (directory or Path.cwd()).resolve()
    marker = root / config.WORKSPACE_NAME
    if marker.is_file():
        raise Abort(f"There is a workspace here already: {marker}")

    root.mkdir(parents=True, exist_ok=True)
    label = name or root.name

    ui.step(f"Creating workspace '{label}'")
    packaged = Path(__file__).parent / "templates"
    shutil.copytree(packaged, root / "templates", dirs_exist_ok=True)
    (root / "modules").mkdir(exist_ok=True)
    (root / "modules" / ".gitkeep").touch()

    values = meta.fields(root, name=label, workspace=label)
    marker.write_text(
        render(
            (packaged / "workspace.yaml").read_text(encoding="utf-8")
            if (packaged / "workspace.yaml").is_file()
            else "workspace: {{name}}\n\nlayout:\n  modules:   modules\n  templates: templates\n",
            **escape(".yaml", values),
        ),
        encoding="utf-8",
    )

    ui.ok(f"{root}")
    ui.note("Next step: flow new <module>")


# ---------------------------------------------------------------------------
# flow new
# ---------------------------------------------------------------------------

def new(name: str, description: str | None = None, bare: bool = False,
        tb: str = "cocotb") -> None:
    check_identifier(name, "Module name")
    if tb not in TB_KINDS:
        raise Abort(f"Unknown testbench kind '{tb}'",
                    hint=f"Possible: {', '.join(TB_KINDS)}")
    if bare:
        tb = "none"

    ws = workspace.require_workspace()
    target = ws.modules_dir / name

    if target.exists():
        raise Abort(
            f"Module '{name}' exists already",
            hint=f"It lives in {target}",
        )

    source = template_root(ws) / "module"
    if not source.is_dir():
        raise Abort(f"Module template missing: {source}")

    text = description or f"SystemVerilog module {name}"
    values = fields(ws, name, text)
    ui.step(f"Creating module '{name}'")

    ws.modules_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)
    try:
        _fill(ws, target, name, values, bare, tb)
    except Exception:
        # Anything half-created is worse than nothing -- start over cleanly.
        shutil.rmtree(target, ignore_errors=True)
        raise

    if bare:
        ui.note(f"Next: flow add rtl <name> {name}")
    else:
        ui.note(f"Next: cd modules/{name} && flow sim")


def _fill(ws: workspace.Workspace, target: Path, name: str, values: dict[str, str],
          bare: bool, tb: str) -> None:
    """Renders the copied tree and adds the RTL and testbench skeletons."""
    render_tree(target, **values)

    cfg_path = target / config.CONFIG_NAME
    testdir = config.load(cfg_path)["sim"]["testdir"]
    ui.ok(f"{target.relative_to(ws.root)}/")

    if bare:
        # No RTL yet, so top.design stays open -- `flow add rtl` fills it in.
        return

    templates = template_root(ws)
    _emit_rtl(target, cfg_path, target / "src" / "design.f", templates,
              name, values, set_top=True)

    if tb in ("cocotb", "both"):
        _emit_cocotb_test(target, cfg_path, testdir, templates, name, values)
    if tb in ("sv", "both"):
        _emit_sv_tb(target, cfg_path, target / "src" / "tb.f", templates,
                    name, values, set_top=True)
    if tb == "sv":
        config.set_scalar(cfg_path, "sim.framework", "sv")
        ui.ok("sim.framework = sv")
    if tb == "both":
        ui.note("sim.framework = cocotb; a single SV run: `flow sim --framework sv`")


# ---------------------------------------------------------------------------
# flow add
# ---------------------------------------------------------------------------

def add(kind: str, name: str, module_name: str | None = None,
        framework: str | None = None) -> None:
    check_identifier(name, "File name")
    ws, module = workspace.resolve(module_name)
    templates = template_root(ws)
    values = fields(
        ws,
        name,
        f"RTL module {name}" if kind == "rtl" else f"Tests for {name}",
        module=module.name,
    )

    if kind == "rtl":
        ui.step(f"Adding RTL module '{name}' to {module.name}")
        _emit_rtl(
            module.root,
            module.cfg_path,
            module.path(module.cfg["sources"]["design"]),
            templates,
            name,
            values,
            set_top=module.top_design is None,
        )

    elif kind == "tb":
        which = framework or module.cfg["sim"]["framework"]
        if which not in ("cocotb", "sv"):
            raise Abort(f"Unknown framework '{which}'", hint="Possible: cocotb, sv")

        if which == "cocotb":
            ui.step(f"Adding cocotb test 'test_{name}' to {module.name}")
            _emit_cocotb_test(module.root, module.cfg_path,
                              module.cfg["sim"]["testdir"], templates, name, values)
        else:
            ui.step(f"Adding SystemVerilog testbench 'tb_{name}' to {module.name}")
            _emit_sv_tb(
                module.root,
                module.cfg_path,
                module.path(module.cfg["sources"]["tb"]),
                templates,
                name,
                values,
                set_top=module.top_tb is None,
            )
            if module.cfg["sim"]["framework"] != "sv":
                ui.note("sim.framework is cocotb -- SV run: `flow sim --framework sv`")

    else:
        raise Abort(f"Unknown kind '{kind}'", hint="Possible: rtl, tb")
