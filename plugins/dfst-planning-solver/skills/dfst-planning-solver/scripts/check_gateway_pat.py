#!/usr/bin/env python3

"""Report Gateway PAT readiness without exposing the credential."""

from __future__ import annotations

import json
import os
from pathlib import Path


VARIABLE = "GATEWAY_MCP_PAT"


def emit(configured: bool, source: str, loaded_in_process: bool) -> None:
    print(
        json.dumps(
            {
                "configured": configured,
                "source": source,
                "loaded_in_process": loaded_in_process,
            },
            separators=(",", ":"),
        )
    )


def dotenv_has_nonempty_value(path: Path) -> bool:
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, separator, value = line.partition("=")
        if separator and key.strip() == VARIABLE:
            value = value.strip()
            return bool(value and value not in {'""', "''"})
    return False


def main() -> None:
    if os.environ.get(VARIABLE, "").strip():
        emit(True, "environment", True)
        return

    dotenv_path = Path.cwd() / ".env"
    if dotenv_path.is_file():
        try:
            if dotenv_has_nonempty_value(dotenv_path):
                emit(True, "project_dotenv", False)
                return
        except (OSError, UnicodeError):
            emit(False, "project_dotenv_unreadable", False)
            return

    emit(False, "missing", False)


if __name__ == "__main__":
    main()
