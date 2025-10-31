"""Wrapper for running create_configs.py and verifying output."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent
CONFIGS_DIR = SCRIPT_DIR.parent / "configs"


def run_create_configs(state, logger, i18n) -> str:
    if state.dry_run:
        logger.info(i18n.t("configs.dry_run", path=str(CONFIGS_DIR)))
        return "SKIP"

    script_path = SCRIPT_DIR / "create_configs.py"
    if not script_path.exists():
        logger.error(i18n.t("configs.missing_script", path=str(script_path)))
        sys.exit(2)

    logger.info(i18n.t("configs.run", path=str(script_path)))
    try:
        subprocess.run([sys.executable, str(script_path)], check=True)
    except subprocess.CalledProcessError as exc:
        logger.error(i18n.t("configs.run_fail", code=exc.returncode))
        sys.exit(exc.returncode or 2)
    except FileNotFoundError:
        logger.error(i18n.t("configs.python_missing"))
        sys.exit(2)

    if not CONFIGS_DIR.exists() or not any(CONFIGS_DIR.iterdir()):
        logger.error(i18n.t("configs.no_output", path=str(CONFIGS_DIR)))
        sys.exit(2)

    logger.info(i18n.t("configs.success", path=str(CONFIGS_DIR)))
    return "DONE"
