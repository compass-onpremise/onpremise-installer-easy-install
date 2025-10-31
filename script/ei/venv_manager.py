"""Virtual environment management for easy-install."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


SCRIPT_DIR = Path(__file__).resolve().parent.parent
VENV_DIR = SCRIPT_DIR / ".venv"
BIN_DIR = "Scripts" if os.name == "nt" else "bin"


@dataclass
class Dependency:
    pip_name: str
    preferred: str
    accepted: Iterable[str]


DEPENDENCIES: List[Dependency] = [
    Dependency("PyYAML", "6.0.2", ["6.0.2", "6.0.1"]),
    Dependency("ruamel.yaml", "0.18.5", ["0.18.5", "0.18.4", "0.17.35", "0.17.34"]),
    Dependency("pyopenssl", "24.0.0", ["24.0.0"]),
    Dependency("docker", "7.1.0", ["7.1.0"]),
    Dependency("mysql-connector-python", "8.2.0", ["8.2.0"]),
    Dependency("python-dotenv", "1.0.0", ["1.0.0"]),
    Dependency("psutil", "5.9.6", ["5.9.6"]),
    Dependency("pycryptodome", "3.21.0", ["3.21.0"]),
]


def ensure_virtualenv(state, logger, i18n) -> str:
    if state.dry_run:
        logger.info(i18n.t("venv.dry_run", path=str(VENV_DIR)))
        return "SKIP"

    venv_python = _ensure_venv_created(logger, i18n)
    state.venv_path = str(VENV_DIR)
    state.venv_python = str(venv_python)
    site_packages = _detect_site_packages()
    if site_packages is not None:
        state.venv_site_packages = str(site_packages)
        if str(site_packages) not in sys.path:
            sys.path.insert(0, str(site_packages))
    issues = False

    for dep in DEPENDENCIES:
        installed = _get_installed_version(venv_python, dep.pip_name)
        if installed and installed in dep.accepted:
            logger.info(i18n.t("venv.pkg.present", name=dep.pip_name, version=installed))
            continue

        target_version = dep.preferred
        logger.info(i18n.t("venv.pkg.install", name=dep.pip_name, version=target_version))
        if not _pip_install(venv_python, dep.pip_name, target_version, logger, i18n):
            issues = True
            continue

        post_version = _get_installed_version(venv_python, dep.pip_name)
        if post_version == target_version:
            logger.info(i18n.t("venv.pkg.installed", name=dep.pip_name, version=post_version))
        elif post_version in dep.accepted:
            logger.warn(i18n.t("venv.pkg.accepted", name=dep.pip_name, version=post_version))
        else:
            logger.warn(i18n.t("venv.pkg.mismatch", name=dep.pip_name, version=str(post_version)))
            issues = True

    return "WARN" if issues else "DONE"


def _ensure_venv_created(logger, i18n) -> Path:
    python_path = VENV_DIR / BIN_DIR / ("python.exe" if os.name == "nt" else "python")
    if VENV_DIR.exists() and python_path.exists():
        logger.info(i18n.t("venv.exists", path=str(VENV_DIR)))
        return python_path

    logger.info(i18n.t("venv.create", path=str(VENV_DIR)))
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", "--system-site-packages", str(VENV_DIR)],
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        logger.error(i18n.t("venv.create_fail", code=exc.returncode))
        sys.exit(exc.returncode or 2)
    except FileNotFoundError:
        logger.error(i18n.t("venv.create_missing"))
        sys.exit(2)

    if not python_path.exists():
        logger.error(i18n.t("venv.missing_python", path=str(python_path)))
        sys.exit(2)

    logger.info(i18n.t("venv.created", path=str(VENV_DIR)))
    return python_path


def _get_installed_version(venv_python: Path, package: str) -> str | None:
    try:
        result = subprocess.run(
            [str(venv_python), "-c", _VERSION_SNIPPET, package],
            capture_output=True,
            text=True,
            check=True,
        )
        value = result.stdout.strip()
        return value if value else None
    except subprocess.CalledProcessError:
        return None


_VERSION_SNIPPET = (
    "import importlib.metadata, sys;"
    "pkg=sys.argv[1];"
    "print(importlib.metadata.version(pkg))"
)


def _pip_install(venv_python: Path, package: str, version: str, logger, i18n) -> bool:
    try:
        subprocess.run(
            [
                str(venv_python),
                "-m",
                "pip",
                "install",
                "--no-input",
                f"{package}=={version}",
            ],
            check=True,
        )
        return True
    except subprocess.CalledProcessError as exc:
        logger.error(i18n.t("venv.pip_fail", package=package, code=exc.returncode))
    except FileNotFoundError:
        logger.error(i18n.t("venv.pip_missing"))
    except Exception as exc:  # pragma: no cover
        logger.error(i18n.t("venv.pip_error", error=str(exc)))
    return False


def _detect_site_packages() -> Path | None:
    if os.name == "nt":
        candidate = VENV_DIR / "Lib" / "site-packages"
    else:
        candidate = (
            VENV_DIR
            / "lib"
            / f"python{sys.version_info.major}.{sys.version_info.minor}"
            / "site-packages"
        )
    return candidate
