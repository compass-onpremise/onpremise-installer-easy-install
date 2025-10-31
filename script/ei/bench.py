"""IOPS benchmark routines (fio-based)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .docker_root import ensure_docker_root

GiB = 1024 ** 3

DEFAULT_DOCKER_ROOT = Path("/var/lib/docker")
TEST_FILENAME = "easy-install-fio-test.bin"
READ_LIMITS = {"avg": 600.0, "min": 288.0}
WRITE_LIMITS = {"avg": 600.0, "min": 324.0}


@dataclass
class BenchmarkMetrics:
    location: Path
    mode: str
    avg: float
    minimum: float


def run_benchmarks(state, logger, i18n) -> str:
    """Execute fio benchmarks. Returns status string."""

    if state.skip_checks or state.skip_bench:
        logger.info(i18n.t("bench.skip"))
        return "SKIP"

    if state.dry_run:
        logger.info(i18n.t("bench.dry_run"))
        return "SKIP"

    fio_path = shutil.which("fio")
    if not fio_path:
        logger.warn(i18n.t("bench.no_fio"))
        logger.info(i18n.t("bench.install_hint"))
        if state.yes:
            logger.info(i18n.t("bench.auto_skip"))
            return "SKIP fio"
        if not _prompt_continue(i18n):
            logger.info(i18n.t("bench.aborted"))
            sys.exit(2)
        logger.info(i18n.t("bench.manual_skip"))
        return "SKIP fio"

    logger.info(i18n.t("bench.start"))

    docker_root = ensure_docker_root(state, logger, i18n)
    locations = _collect_locations(state, docker_root)
    warnings: List[str] = []

    for location in locations:
        location = location.resolve()
        try:
            location.mkdir(parents=True, exist_ok=True)
        except Exception as exc:  # pragma: no cover - defensive
            msg = i18n.t("bench.mkdir_fail", path=str(location), error=str(exc))
            logger.warn(msg)
            warnings.append(msg)
            continue

        test_file = location / TEST_FILENAME

        write_success = False
        for mode in ("randwrite", "randread"):
            if mode == "randread" and not write_success:
                # skip read if write failed
                continue

            metrics, err_msg = _run_single(fio_path, test_file, mode, state.bench_runtime, i18n)
            if err_msg:
                logger.warn(err_msg)
                warnings.append(err_msg)
                if mode == "randwrite":
                    write_success = False
                continue

            assert metrics is not None
            if mode == "randwrite":
                write_success = True

            limits = READ_LIMITS if mode == "randread" else WRITE_LIMITS
            logger.info(i18n.t("bench.metrics", path=str(location), mode=mode, avg=f"{metrics.avg:.2f}", min=f"{metrics.minimum:.2f}", req_avg=f"{limits['avg']:.0f}", req_min=f"{limits['min']:.0f}"))

            if metrics.avg < limits["avg"] or metrics.minimum < limits["min"]:
                warn = i18n.t("bench.warn", path=str(location), mode=mode, avg=f"{metrics.avg:.2f}", min=f"{metrics.minimum:.2f}", req_avg=f"{limits['avg']:.0f}", req_min=f"{limits['min']:.0f}")
                logger.warn(warn)
                warnings.append(warn)

        try:
            if test_file.exists():
                test_file.unlink()
        except Exception:
            pass

    if not warnings:
        logger.info(i18n.t("bench.ok"))
        return "DONE"

    logger.warn(i18n.t("bench.summary_warn", count=len(warnings)))

    if state.yes:
        logger.info(i18n.t("bench.auto_proceed"))
        return "PROCEED_WITH_WARNINGS"

    if _prompt_continue(i18n):
        return "PROCEED_WITH_WARNINGS"

    logger.info(i18n.t("bench.aborted"))
    sys.exit(2)


def _collect_locations(state, docker_root: Path) -> List[Path]:
    roots = [Path(state.root_mount), docker_root]
    unique: Dict[str, Path] = {}
    for path in roots:
        unique[str(path.resolve())] = path
    return list(unique.values())


def _run_single(fio_path: str, filename: Path, mode: str, runtime: int, i18n) -> tuple[Optional[BenchmarkMetrics], Optional[str]]:
    cmd = [
        fio_path,
        f"--name=easy_install_{mode}",
        f"--filename={str(filename)}",
        f"--rw={mode}",
        "--bs=4k",
        "--iodepth=16",
        "--numjobs=1",
        "--direct=1",
        f"--runtime={max(runtime, 1)}",
        "--time_based=1",
        "--size=1G",
        "--ioengine=libaio",
        "--group_reporting=1",
        "--output-format=json",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if exc.stderr else exc.stdout
        return None, i18n.t("bench.exec_error", mode=mode, error=stderr)
    except FileNotFoundError:
        return None, i18n.t("bench.no_fio")
    except Exception as exc:  # pragma: no cover - defensive
        return None, i18n.t("bench.exec_error", mode=mode, error=str(exc))

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return None, i18n.t("bench.parse_error", mode=mode, error=str(exc))

    jobs = data.get("jobs") or []
    if not jobs:
        return None, i18n.t("bench.parse_error", mode=mode, error="jobs array empty")

    job = jobs[0]
    stats_key = "read" if mode == "randread" else "write"
    stats = job.get(stats_key) or {}
    avg = float(stats.get("iops", 0.0))
    minimum = float(stats.get("iops_min", 0.0) or 0.0)

    return BenchmarkMetrics(filename.parent, mode, avg, minimum), None


def _prompt_continue(i18n) -> bool:
    answer = input(i18n.t("bench.confirm") + " ").strip().lower()
    return answer in {"y", "yes", "д", "да"}
