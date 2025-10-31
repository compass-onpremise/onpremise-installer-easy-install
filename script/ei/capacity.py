"""Resource checks (CPU/RAM/Disk) for easy-install."""

from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from .docker_root import ensure_docker_root

CPU_MIN = 8
RAM_MIN_GIB = 16
DISK_MIN_GIB = 30
DEFAULT_DOCKER_ROOT = Path("/var/lib/docker")

GiB = 1024 ** 3


@dataclass
class DiskCheckResult:
    requested: Path
    checked: Path
    free_gib: Optional[float]
    required_gib: float
    ok: bool


def check_capacity(state, logger, i18n) -> str:
    """Run capacity checks. Returns status string for logger.status."""

    if state.skip_checks:
        logger.info(i18n.t("capacity.skip"))
        return "SKIP"

    logger.info(i18n.t("capacity.start"))

    warnings: List[str] = []

    cpu_count = os.cpu_count() or 0
    logger.info(i18n.t("capacity.cpu", actual=cpu_count, required=CPU_MIN))
    if cpu_count == 0:
        warnings.append(i18n.t("capacity.cpu_unknown"))
        logger.warn(warnings[-1])
    elif cpu_count < CPU_MIN:
        warnings.append(i18n.t("capacity.cpu_warn", actual=cpu_count, required=CPU_MIN))
        logger.warn(warnings[-1])

    ram_total = _read_mem_total_gib()
    if ram_total is None:
        warnings.append(i18n.t("capacity.ram_unknown"))
        logger.warn(warnings[-1])
    else:
        logger.info(i18n.t("capacity.ram", actual=f"{ram_total:.2f}", required=RAM_MIN_GIB))
        if ram_total < RAM_MIN_GIB:
            warnings.append(i18n.t("capacity.ram_warn", actual=f"{ram_total:.2f}", required=RAM_MIN_GIB))
            logger.warn(warnings[-1])

    docker_root = ensure_docker_root(state, logger, i18n)
    disk_checks = _gather_disk_checks(state, docker_root)
    for res in disk_checks:
        if res.requested != res.checked:
            logger.info(i18n.t("capacity.disk.lookup", requested=str(res.requested), checked=str(res.checked)))

        if res.free_gib is None:
            msg = i18n.t("capacity.disk_unknown", path=str(res.requested))
            warnings.append(msg)
            logger.warn(msg)
        else:
            logger.info(i18n.t("capacity.disk", path=str(res.checked), free=f"{res.free_gib:.2f}", required=res.required_gib))
            if not res.ok:
                msg = i18n.t("capacity.disk_warn", path=str(res.requested), free=f"{res.free_gib:.2f}", required=res.required_gib)
                warnings.append(msg)
                logger.warn(msg)

    if not warnings:
        logger.info(i18n.t("capacity.ok"))
        return "DONE"

    logger.warn(i18n.t("capacity.summary_warn", count=len(warnings)))

    if state.yes:
        logger.info(i18n.t("capacity.auto_proceed"))
        return "PROCEED_WITH_WARNINGS"

    try:
        answer = _prompt(i18n)
    except KeyboardInterrupt:
        logger.info(i18n.t("capacity.user_abort"))
        sys.exit(130)

    if answer:
        return "PROCEED_WITH_WARNINGS"

    logger.info(i18n.t("capacity.aborted"))
    sys.exit(2)


def _gather_disk_checks(state, docker_root: Path) -> List[DiskCheckResult]:
    targets: List[Tuple[Path, float]] = [
        (Path(state.root_mount), DISK_MIN_GIB),
        (docker_root, DISK_MIN_GIB),
    ]

    results: List[DiskCheckResult] = []
    for path, required in targets:
        checked = _existing_parent(path)
        free_gib = _disk_free_gib(checked)
        ok = free_gib is not None and free_gib >= required
        results.append(DiskCheckResult(path, checked, free_gib, required, ok))
    return results


def _existing_parent(path: Path) -> Path:
    current = path
    while not current.exists():
        if current.parent == current:
            return current
        current = current.parent
    return current


def _disk_free_gib(path: Path) -> Optional[float]:
    try:
        usage = shutil.disk_usage(path)
    except FileNotFoundError:
        return None
    return usage.free / GiB


def _read_mem_total_gib() -> Optional[float]:
    meminfo = Path("/proc/meminfo")
    try:
        with meminfo.open("r", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("MemTotal:"):
                    parts = line.split()
                    if len(parts) >= 2:
                        kb = float(parts[1])
                        return kb * 1024 / GiB
    except (OSError, ValueError):
        return None
    return None


def _prompt(i18n) -> bool:
    prompt = i18n.t("capacity.confirm") + " "
    answer = input(prompt).strip().lower()
    return answer in {"y", "yes", "д", "да"}
