"""Launch main install.py from easy-install."""

from __future__ import annotations

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
    try:
        subprocess.run([python_exec, str(install_script), "--confirm-all"], check=True)
    except subprocess.CalledProcessError as exc:
        logger.error(i18n.t("install.fail", code=exc.returncode))
        sys.exit(exc.returncode or 2)

    logger.info(i18n.t("install.done"))
    state.install_executed = True
    return "DONE"
