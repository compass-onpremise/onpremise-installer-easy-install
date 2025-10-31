"""Apply YAML patches according to specification."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List

from config_manager.yaml_io import load_yaml, dump_yaml
from config_manager.patches import get_patches, apply_patch


CONFIGS_DIR = Path(__file__).resolve().parent.parent / "configs"


def apply_patches(state, logger, i18n) -> str:
    if state.dry_run:
        logger.info(i18n.t("patch.dry_run", path=str(CONFIGS_DIR)))
        return "SKIP"

    warnings: List[str] = []

    for spec in get_patches():
        target = CONFIGS_DIR / spec.filename
        if not target.exists():
            logger.error(i18n.t("patch.missing", path=str(target)))
            sys.exit(2)

        data = load_yaml(target)
        spec_warnings = apply_patch(spec.filename, data, state, logger, i18n)
        dump_yaml(data, target)

        if spec_warnings:
            for message in spec_warnings:
                logger.warn(message)
            warnings.extend(spec_warnings)

        logger.info(i18n.t("patch.applied", path=str(target)))

    return "PROCEED_WITH_WARNINGS" if warnings else "DONE"
