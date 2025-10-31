"""Utilities for validating and re-executing Python interpreter."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

MIN_VERSION: Tuple[int, int, int] = (3, 8, 0)


class PythonRuntimeStatus(Tuple[str, str]):
    """Tuple-like container describing current and required versions."""

    __slots__ = ()

    def __new__(cls, current: str, required: str) -> "PythonRuntimeStatus":
        return tuple.__new__(cls, (current, required))

    @property
    def current(self) -> str:
        return self[0]

    @property
    def required(self) -> str:
        return self[1]


def ensure_python(i18n, script_path: Path) -> PythonRuntimeStatus:
    """Ensure current interpreter meets the minimal requirement or re-exec."""

    required_str = _format_version(MIN_VERSION)
    current_tuple = sys.version_info[:3]
    current_str = _format_version(current_tuple)

    if current_tuple >= MIN_VERSION:
        return PythonRuntimeStatus(current_str, required_str)

    _emit(i18n.t("python.version.too_old", current=current_str, required=required_str))
    _emit(i18n.t("python.search.start", required=required_str))

    for candidate in _candidate_interpreters():
        version = _detect_version(candidate, i18n)
        if version is None:
            continue

        version_str = _format_version(version)
        _emit(i18n.t("python.search.candidate", candidate=candidate, version=version_str))

        if version >= MIN_VERSION:
            _emit(i18n.t("python.search.reexec", candidate=candidate, version=version_str))
            _reexec(candidate, script_path)

    _emit(i18n.t("python.search.failed", required=required_str))
    _emit(i18n.t("python.install.instructions", required=required_str))
    _emit(i18n.t("python.exit.code", code=10))
    sys.exit(10)


def _candidate_interpreters() -> Iterable[str]:
    names: List[str] = []
    for minor in range(13, 7, -1):
        names.append(f"python3.{minor}")
    names.extend(["python3", "python"])

    seen: set[str] = set()
    for name in names:
        path = shutil.which(name)
        if not path or path in seen:
            continue
        seen.add(path)
        yield path


def _detect_version(executable: str, i18n) -> Optional[Tuple[int, int, int]]:
    try:
        result = subprocess.run(
            [executable, "-c", "import sys; print('.'.join(map(str, sys.version_info[:3])))"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, PermissionError):
        return None
    except subprocess.CalledProcessError as exc:
        _emit(i18n.t("python.search.error", candidate=executable, error=str(exc)))
        return None
    except Exception as exc:  # pragma: no cover - defensive
        _emit(i18n.t("python.search.error", candidate=executable, error=str(exc)))
        return None

    output = result.stdout.strip().splitlines()
    if not output:
        return None

    parts = output[0].strip().split(".")
    try:
        major = int(parts[0])
        minor = int(parts[1])
        micro = int(parts[2]) if len(parts) > 2 else 0
    except (ValueError, IndexError):
        return None

    return major, minor, micro


def _reexec(executable: str, script_path: Path) -> None:
    argv: List[str] = [executable, str(script_path), *sys.argv[1:]]
    os.execv(executable, argv)


def _format_version(version: Sequence[int]) -> str:
    return ".".join(str(part) for part in version)


def _emit(message: str) -> None:
    sys.stdout.write(f"{message}\n")
    sys.stdout.flush()

