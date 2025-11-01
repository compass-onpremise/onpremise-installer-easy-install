"""Handle AppArmor presence before installation."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import List


_APPARMOR_INIT = Path("/etc/init.d/apparmor")


def handle_apparmor(state, logger, i18n) -> str:
    if state.dry_run or state.skip_checks:
        logger.info(i18n.t("apparmor.skip"))
        return "SKIP"

    if not _is_present():
        logger.info(i18n.t("apparmor.not_found"))
        return "SKIP"

    if not state.yes:
        try:
            answer = input(i18n.t("apparmor.prompt") + " ").strip().lower()
        except KeyboardInterrupt:
            logger.info(i18n.t("apparmor.abort"))
            sys.exit(130)
        if answer not in {"y", "yes", "д", "да"}:
            logger.info(i18n.t("apparmor.decline"))
            return "WARN"

    commands: List[List[str]] = [
        ["/etc/init.d/apparmor", "stop"],
        ["update-rc.d", "-f", "apparmor", "remove"],
        ["apt-get", "remove", "-y", "apparmor"],
    ]

    for cmd in commands:
        logger.info(i18n.t("apparmor.cmd", command=" ".join(cmd)))
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as exc:
            logger.error(i18n.t("apparmor.fail", command=" ".join(cmd), code=exc.returncode))
            sys.exit(exc.returncode or 2)

    logger.info(i18n.t("apparmor.removed"))
    return "DONE"


def _is_present() -> bool:
    if _APPARMOR_INIT.exists():
        return True
    if shutil.which("apparmor_status"):
        return True
    # systemd unit check
    try:
        result = subprocess.run(
            ["systemctl", "list-unit-files", "apparmor.service"],
            capture_output=True,
            text=True,
            check=False,
        )
        return "apparmor.service" in (result.stdout or "")
    except Exception:
        return False


