# rtl-lab

Workspace for SystemVerilog practice modules. Every module stands on its own;
the `flow` CLI takes care of creating, linting and simulating them.

## Layout

```
rtl-lab/
├── workspace.yaml        marks the workspace root
├── flow/                 source of the CLI (`flow`)
├── templates/            templates for `flow new` (edit them here)
└── modules/
    └── alu/
        ├── project.yaml  top modules, simulator, paths
        ├── src/
        │   ├── files.f   -f design.f  +  -f tb.f
        │   ├── design.f  synthesizable RTL
        │   ├── tb.f      SystemVerilog testbench sources
        │   ├── rtl/      alu_pkg.sv, alu.sv
        │   └── tb/       SV benches (tb_*.sv)
        │       └── cocotb/   cocotb tests (test_*.py)
        ├── lint/         lint logs + waivers.vlt
        ├── sim/run/      build, waveform, results
        └── docs/
```

## Commands

| Command | Effect |
|---|---|
| `flow init [name]` | create a workspace |
| `flow new <name>` | create a module from the template, RTL and testbench included |
| `flow new <name> --tb sv\|cocotb\|both\|none` | pick the testbench kind (default: cocotb) |
| `flow add rtl <name>` | create a `.sv` and list it in `design.f` |
| `flow add tb <name> [--cocotb\|--sv]` | create a testbench; without a flag it follows `sim.framework` |
| `flow ls` | modules in the workspace with their status |
| `flow info` | resolved configuration of a module |
| `flow files` | show the resolved filelist (`--design`, `--tb`) |
| `flow lint` | verilator lint over `design.f`, log into `lint/` |
| `flow sim` | run the tests; `-t` a single test, `-w` open the waveform, `--framework`, `--dry-run` |
| `flow wave` | last waveform in a viewer |
| `flow clean` | empty `sim/run` and `lint` (`--all` for every module) |
| `flow doctor` | check which tools are missing |

The module follows from the directory you are standing in. From the workspace
root you append its name: `flow sim alu`.

## Testbenches: cocotb or plain SystemVerilog

Both are first-class, and a module can hold both at once.

| | cocotb | SystemVerilog |
|---|---|---|
| `sim.framework` | `cocotb` | `sv` |
| files | `src/tb/cocotb/test_<name>.py` | `src/tb/tb_<name>.sv` |
| registered in | `sim.modules` in `project.yaml` | `src/tb.f` |
| directory | `sim.testdir` (default `src/tb/cocotb`) | next to `tb.f`, i.e. `src/tb/` |
| toplevel | `top.design` (cocotb drives the DUT directly) | `top.tb` |
| single test | `flow sim -t test_reset` | `flow sim -t test_reset` → `+TESTCASE=test_reset` |
| verdict | cocotb's `results.xml` | `TEST PASSED` / `TEST FAILED` + `$fatal` |

```bash
flow new alu --tb both         # both kinds side by side
flow sim                       # runs whatever sim.framework says
flow sim --framework sv        # this one run against the SV testbench
flow add tb decoder --sv alu   # add an SV bench to an existing module
```

Python and SystemVerilog stay apart: cocotb tests live one level down in
`src/tb/cocotb/`, so `tb.f` and the `.sv` benches never share a folder with
`__pycache__`. `sim.testdir` points there and is what cocotb imports from --
move it and the tests move with it.

A SystemVerilog testbench reports its result on stdout: the generated template
counts errors, prints `TEST PASSED` or `TEST FAILED` and calls `$fatal(1)` on
failure. `flow sim` reads those lines plus the exit code. Keep that contract in
your own benches, otherwise the run ends in "outcome unclear".

Waveforms work in both flows. For SV benches `flow sim` defines `WAVES` and
`WAVE_FILE` while `sim.waves` is on; the template dumps into `sim/run/<top>.fst`
from there.

## Generated files

`flow` writes these; everything else is yours.

| Command | Files |
|---|---|
| `flow init` | `workspace.yaml`, `templates/`, `modules/` |
| `flow new` | the module tree: `project.yaml`, `src/files.f`, `src/design.f`, `src/tb.f`, `lint/waivers.vlt`, plus `src/rtl/<name>.sv` and the testbench(es) |
| `flow add` | one `src/rtl/<name>.sv`, `src/tb/cocotb/test_<name>.py` or `src/tb/tb_<name>.sv`, and its entry in `design.f` / `sim.modules` / `tb.f` |
| `flow lint` | `lint/<module>.log` |
| `flow sim` | `sim/run/`: `run_sim.py` (cocotb) or `sim.log` (SV), `build/`, `results.xml`, the waveform |

`sim/run/` and `lint/` are regenerated on every run and are not in git —
`flow clean` empties them, keeping only `.gitkeep` and `waivers.vlt`.

### File headers

Every generated file starts with a header carrying description, workspace,
module, author, creation date and the tool version:

```systemverilog
// ---------------------------------------------------------------------------
// alu.sv  --  Combinational ALU: arithmetic, logic, shift and compare
//
//   Workspace:  rtl-lab
//   Module:     alu
//   Author:     Ada Lovelace <ada@example.org>
//   Created:    2026-09-10 22:04  (flow 0.1.0)
// ---------------------------------------------------------------------------
```

The same data lands in `project.yaml` as `author:` and `created:`, and
`flow info` shows it. The author is resolved in this order:

```
$RTL_AUTHOR  ->  workspace.yaml (defaults.author)  ->  git config user.name  ->  login name
```

`$RTL_EMAIL` and `defaults.email` do the same for the address.

The header lives in the templates, not in the code: every file under
`templates/` may use `{{name}}`, `{{description}}`, `{{module}}`,
`{{workspace}}`, `{{author}}`, `{{email}}`, `{{creator}}`, `{{date}}`,
`{{time}}`, `{{year}}` and `{{tool}}`. Change the templates and every module
created from then on follows.

## Conventions

- **Filelists** are parsed by the CLI itself; relative paths resolve
  **relative to the `.f` file** they appear in. Tools only ever see absolute
  paths, so they all behave the same.
- **`tb.f` holds SystemVerilog only.** cocotb tests live in `project.yaml`
  under `sim.modules` — the compiler never sees them.
- **`design.f` is the synthesis view:** whatever is listed there has to pass
  synthesis. Everything non-synthesizable belongs in `tb.f`.

## Installation

`flow` is a symlink in `~/.local/bin`:

```bash
ln -sf ~/Projects/rtl-lab/flow/flow.py ~/.local/bin/flow
```

Tools (Arch):

```bash
sudo pacman -S verilator gtkwave
```

cocotb goes into a venv inside the workspace. Arch marks the system python as
`EXTERNALLY-MANAGED`, so `pip install --user` fails there:

```bash
python3 -m venv .venv
.venv/bin/pip install cocotb
```

`flow` finds the venv on its own (upwards from the module directory, `.venv` or
`venv`) and simulates with it. The CLI itself runs on the system python and
only needs `pyyaml` there. `flow doctor` shows both interpreters separately.

A plain SystemVerilog run needs no python at all: verilator (`--binary`) or
icarus (`iverilog` + `vvp`) is enough. With icarus the flow writes VCD even if
`sim.waves` says `fst`.

## Waveforms

`sim.waves` in `project.yaml` picks the format: `fst` (default), `vcd` or
`none`. The file ends up as `sim/run/<top>.<format>` — cocotb would otherwise
write it into the test directory.

`flow sim -w` opens it right after the run, `flow wave` later on. The viewer is
chosen automatically (surfer before gtkwave), `--viewer` forces one.
