"""Launch main install.py from easy-install."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def run_install(state, logger, i18n) -> str:
    if state.dry_run or state.skip_install:
        logger.info(i18n.t("install.skip"))
        return "SKIP"

    if not state.yes:
        try:
            answer = input(i18n.t("install.prompt") + " ").strip().lower()
        except KeyboardInterrupt:
            logger.info(i18n.t("install.decline"))
            return "SKIP"
        if answer not in {"y", "yes", "д", "да"}:
            logger.info(i18n.t("install.decline"))
            return "SKIP"

    install_script = REPO_ROOT / "script" / "install.py"
    if not install_script.exists():
        logger.error(i18n.t("install.missing", path=str(install_script)))
        sys.exit(2)

    logger.info(i18n.t("install.start"))
    python_exec = state.venv_python or sys.executable
    env = os.environ.copy()
    if state.venv_bin:
        env_path = env.get("PATH", "")
        env["PATH"] = f"{state.venv_bin}:{env_path}" if env_path else state.venv_bin
    if state.venv_path:
        env["VIRTUAL_ENV"] = state.venv_path
    if state.venv_site_packages:
        extra_pp = state.venv_site_packages
        current_pp = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = f"{extra_pp}:{current_pp}" if current_pp else extra_pp
    try:
        subprocess.run([python_exec, str(install_script), "--confirm-all"], check=True, env=env)
    except subprocess.CalledProcessError as exc:
        logger.error(i18n.t("install.fail", code=exc.returncode))
        sys.exit(exc.returncode or 2)

    logger.info(i18n.t("install.done"))
    state.install_executed = True
    return "DONE"
