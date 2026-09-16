"""Values for the generated file header: author, date, tool.

The author is resolved in this order:

    $RTL_AUTHOR  ->  workspace.yaml (defaults.author)  ->  git config  ->  login name

That way the header can be pinned per workspace and overridden for a single
call, without anything having to be maintained by hand.
"""

from __future__ import annotations

import getpass
import os
import subprocess
from datetime import datetime
from pathlib import Path

from . import __version__


def _git(root: Path | None, key: str) -> str | None:
    """`git config --get <key>`; None if git is missing or has no value."""
    try:
        result = subprocess.run(
            ["git", "config", "--get", key],
            cwd=str(root) if root else None,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    value = result.stdout.strip()
    return value if result.returncode == 0 and value else None


def _login() -> str:
    try:
        return getpass.getuser()
    except (OSError, KeyError):  # pragma: no cover -- container without a passwd entry
        return "unknown"


def author(root: Path | None = None, configured: str | None = None) -> str:
    return (
        os.environ.get("RTL_AUTHOR")
        or (str(configured) if configured else None)
        or _git(root, "user.name")
        or _login()
    )


def email(root: Path | None = None, configured: str | None = None) -> str:
    return (
        os.environ.get("RTL_EMAIL")
        or (str(configured) if configured else None)
        or _git(root, "user.email")
        or ""
    )


def fields(root: Path | None = None, defaults: dict | None = None,
           **extra: str) -> dict[str, str]:
    """Placeholders for the file header, plus everything in `extra`.

    Available in every template: {{author}}, {{email}}, {{creator}},
    {{date}}, {{time}}, {{year}}, {{tool}}.
    """
    cfg = defaults or {}
    now = datetime.now()

    name = author(root, cfg.get("author"))
    mail = email(root, cfg.get("email"))

    values = {
        "author": name,
        "email": mail or "-",
        "creator": f"{name} <{mail}>" if mail else name,
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M"),
        "year": now.strftime("%Y"),
        "tool": f"flow {__version__}",
    }
    values.update({key: str(value) for key, value in extra.items() if value is not None})
    return values
