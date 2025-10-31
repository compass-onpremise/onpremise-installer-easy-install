"""Ensure Docker service is enabled and running."""

from __future__ import annotations

import shutil
import subprocess
import sys
from typing import Optional


def ensure_docker_service(state, logger, i18n) -> str:
    """Start Docker service if needed and verify docker binary."""

    if state.dry_run:
        logger.info(i18n.t("docker.service.dry_run"))
        return "SKIP"

    docker_path = shutil.which("docker")
    if not docker_path:
        logger.error(i18n.t("docker.service.missing_binary"))
        logger.info(i18n.t("docker.service.hint"))
        sys.exit(2)

    logger.info(i18n.t("docker.service.path", path=docker_path))

    status = _ensure_service(logger, i18n)
    if status == "FAILED":
        logger.error(i18n.t("docker.service.fail"))
        sys.exit(2)

    if status == "STARTED":
        logger.info(i18n.t("docker.service.started"))
    elif status == "FOUND":
        logger.info(i18n.t("docker.service.active"))

    version_output = _docker_version(logger, i18n, docker_path)
    if version_output:
        logger.info(i18n.t("docker.service.version", version=version_output))

    swarm_status = _ensure_swarm(logger, i18n, docker_path)
    if swarm_status == "FAILED":
        logger.error(i18n.t("docker.swarm.fail"))
        sys.exit(2)
    elif swarm_status == "INIT":
        logger.info(i18n.t("docker.swarm.inited"))
    elif swarm_status == "FOUND":
        logger.info(i18n.t("docker.swarm.already"))

    result_status = "DONE"
    if status not in {"STARTED", "FOUND"} or swarm_status not in {"INIT", "FOUND"}:
        result_status = "WARN"
    return result_status


def _ensure_service(logger, i18n) -> str:
    """Try to ensure Docker daemon is running via systemctl/service."""

    # Attempt systemctl first
    if shutil.which("systemctl"):
        if _systemctl_is_active(logger):
            return "FOUND"
        logger.info(i18n.t("docker.service.systemctl_start"))
        if _run_cmd(["systemctl", "enable", "docker"], logger, i18n):
            if _run_cmd(["systemctl", "start", "docker"], logger, i18n):
                if _systemctl_is_active(logger):
                    return "STARTED"
        logger.warn(i18n.t("docker.service.systemctl_failed"))

    # Fallback to service command
    if shutil.which("service"):
        logger.info(i18n.t("docker.service.service_start"))
        if _run_cmd(["service", "docker", "start"], logger, i18n):
            return "STARTED"
        logger.warn(i18n.t("docker.service.service_failed"))

    return "FAILED"


def _systemctl_is_active(logger) -> bool:
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "docker"], capture_output=True, text=True, check=False
        )
        return result.returncode == 0 and result.stdout.strip() == "active"
    except Exception:
        return False


def _run_cmd(cmd, logger, i18n) -> bool:
    try:
        subprocess.run(cmd, check=True)
        logger.debug(i18n.t("docker.service.cmd_ok", command=" ".join(cmd)))
        return True
    except subprocess.CalledProcessError as exc:
        logger.warn(i18n.t("docker.service.cmd_fail", command=" ".join(cmd), code=exc.returncode))
    except FileNotFoundError:
        logger.warn(i18n.t("docker.service.cmd_missing", command=cmd[0]))
    except Exception as exc:  # pragma: no cover
        logger.warn(i18n.t("docker.service.cmd_fail", command=" ".join(cmd), code=str(exc)))
    return False


def _docker_version(logger, i18n, docker_path: str) -> Optional[str]:
    try:
        result = subprocess.run(
            [docker_path, "--version"], capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as exc:
        logger.warn(i18n.t("docker.service.version_fail", code=exc.returncode))
    except Exception as exc:  # pragma: no cover
        logger.warn(i18n.t("docker.service.version_error", error=str(exc)))
    return None


def _ensure_swarm(logger, i18n, docker_path: str) -> str:
    state = _swarm_state(logger, i18n, docker_path)
    if state in {"active", "locked"}:
        return "FOUND"
    if state == "error":
        return "FAILED"

    logger.info(i18n.t("docker.swarm.init"))
    if _run_cmd([docker_path, "swarm", "init"], logger, i18n):
        return "INIT"

    logger.warn(i18n.t("docker.swarm.init_fail"))
    return "FAILED"


def _swarm_state(logger, i18n, docker_path: str) -> str:
    try:
        result = subprocess.run(
            [docker_path, "info", "--format", "{{.Swarm.LocalNodeState}}"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip().lower()
    except subprocess.CalledProcessError as exc:
        logger.warn(i18n.t("docker.swarm.state_fail", code=exc.returncode))
    except Exception as exc:  # pragma: no cover
        logger.warn(i18n.t("docker.swarm.state_error", error=str(exc)))
    return "error"

