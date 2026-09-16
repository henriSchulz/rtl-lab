"""Command line of `flow`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__, inspect, scaffold, ui, verify, workspace
from .ui import Abort

EPILOG = """\
Typical flow:

  flow new fifo                 create a module (RTL skeleton + cocotb test)
  flow new fifo --tb sv         same, but with a SystemVerilog testbench
  cd modules/fifo
  flow lint                     verilator lint over src/design.f
  flow sim                      run the tests, waveform lands in sim/run/
  flow sim -t test_reset        a single test only
  flow sim --framework sv       run the SV testbench instead of cocotb
  flow sim -w                   simulate and open the waveform
  flow wave                     look at the last waveform again

The module follows from the directory you are standing in. From the
workspace root you append its name: `flow sim fifo`.
"""


def _module_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "module",
        nargs="?",
        help="module name; without one, the current directory decides",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flow",
        description="Flow tool for SystemVerilog modules: create, lint, simulate.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-V", "--version", action="version", version=f"flow {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    # -- create -------------------------------------------------------------
    p_init = sub.add_parser("init", help="create a workspace in the current directory")
    p_init.add_argument("name", nargs="?", help="workspace name (default: directory name)")
    p_init.add_argument("--dir", type=Path, help="target directory (default: here)")

    p_new = sub.add_parser("new", help="create a module from the template")
    p_new.add_argument("name", help="module name (valid SV identifier)")
    p_new.add_argument("-d", "--description", help="short description for project.yaml")
    p_new.add_argument(
        "--tb",
        choices=list(scaffold.TB_KINDS),
        default="cocotb",
        help="testbench to generate: cocotb (default), sv, both or none",
    )
    p_new.add_argument(
        "--bare",
        action="store_true",
        help="directory structure only, no .sv and no testbench",
    )

    p_add = sub.add_parser("add", help="add a source file to a module")
    p_add.add_argument("kind", choices=["rtl", "tb"], metavar="{rtl,tb}",
                       help="rtl = SystemVerilog module, tb = testbench")
    p_add.add_argument("name", help="name of the new file (without extension)")
    _module_arg(p_add)
    kind = p_add.add_mutually_exclusive_group()
    kind.add_argument("--cocotb", dest="framework", action="store_const", const="cocotb",
                      help="tb: cocotb test in Python (test_<name>.py)")
    kind.add_argument("--sv", dest="framework", action="store_const", const="sv",
                      help="tb: SystemVerilog testbench (tb_<name>.sv)")
    p_add.set_defaults(framework=None)

    # -- inspect ------------------------------------------------------------
    sub.add_parser("ls", help="list the modules in the workspace")

    p_info = sub.add_parser("info", help="show a module's configuration")
    _module_arg(p_info)

    p_files = sub.add_parser("files", help="show the resolved filelist")
    _module_arg(p_files)
    group = p_files.add_mutually_exclusive_group()
    group.add_argument("--design", action="store_true", help="src/design.f only")
    group.add_argument("--tb", action="store_true", help="src/tb.f only")

    sub.add_parser("doctor", help="check which tools are installed")

    # -- check --------------------------------------------------------------
    p_lint = sub.add_parser("lint", help="verilator lint over the RTL")
    _module_arg(p_lint)
    p_lint.add_argument("--all", action="store_true", help="every module in the workspace")
    p_lint.add_argument("--no-top", action="store_true",
                        help="run without --top-module (check every module on its own)")

    p_sim = sub.add_parser("sim", help="run the simulation (cocotb or SystemVerilog)")
    _module_arg(p_sim)
    p_sim.add_argument("-t", "--test", help="run this test case only")
    p_sim.add_argument("-w", "--waves", action="store_true",
                       help="open the waveform after the run")
    p_sim.add_argument("--framework", choices=list(verify.FRAMEWORKS),
                       help="override sim.framework for this run")
    p_sim.add_argument("--dry-run", action="store_true",
                       help="show what would run, execute nothing")

    p_wave = sub.add_parser("wave", help="open the last waveform in a viewer")
    _module_arg(p_wave)
    p_wave.add_argument("--viewer", help="force gtkwave or surfer")

    p_clean = sub.add_parser("clean", help="empty sim/run and lint")
    _module_arg(p_clean)
    p_clean.add_argument("--all", action="store_true", help="every module in the workspace")

    return parser


def dispatch(args: argparse.Namespace) -> int:
    command = args.command

    if command == "init":
        scaffold.init(args.name, args.dir)
        return 0

    if command == "new":
        scaffold.new(args.name, args.description, args.bare, args.tb)
        return 0

    if command == "add":
        scaffold.add(args.kind, args.name, args.module, args.framework)
        return 0

    if command == "ls":
        return inspect.ls()

    if command == "info":
        return inspect.info(args.module)

    if command == "files":
        which = "design" if args.design else "tb" if args.tb else "filelist"
        return inspect.files(args.module, which)

    if command == "doctor":
        return inspect.doctor()

    if command == "lint":
        if args.all:
            ws = workspace.require_workspace()
            names = ws.module_names()
            if not names:
                ui.warn("No modules in the workspace")
                return 0
            worst = 0
            for name in names:
                worst = verify.lint(name, fix_top=not args.no_top) or worst
            return worst
        return verify.lint(args.module, fix_top=not args.no_top)

    if command == "sim":
        return verify.sim(args.module, args.test, args.waves, args.dry_run, args.framework)

    if command == "wave":
        return verify.wave(args.module, args.viewer)

    if command == "clean":
        return verify.clean(args.module, args.all)

    raise Abort(f"Unknown command: {command}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    try:
        return dispatch(args)
    except Abort as exc:
        ui.fail(str(exc))
        if exc.hint:
            ui.note(exc.hint)
        return 1
    except KeyboardInterrupt:
        print()
        ui.warn("aborted")
        return 130


if __name__ == "__main__":
    sys.exit(main())
