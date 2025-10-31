"""Determine Docker data-root location with fallbacks."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Optional

DEFAULT_DOCKER_ROOT = Path("/var/lib/docker")


def ensure_docker_root(state, logger, i18n) -> Path:
    """Return docker data-root path, storing it in state."""

    if state.dry_run:
        return DEFAULT_DOCKER_ROOT

    if state.docker_data_root:
        path = Path(state.docker_data_root)
        logger.debug(i18n.t("docker.root.cached", path=str(path)))
        return path

    logger.info(i18n.t("docker.root.start"))
    path = (
        _from_docker_info(logger, i18n)
        or _from_daemon_json(logger, i18n)
        or _default_root(logger, i18n)
    )
    state.docker_data_root = str(path)
    logger.info(i18n.t("docker.root.result", path=str(path)))
    return path


def _from_docker_info(logger, i18n) -> Optional[Path]:
    try:
        result = subprocess.run(
            ["docker", "info", "--format", "{{.DockerRootDir}}"],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        logger.debug(i18n.t("docker.root.info_missing"))
        return None
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if exc.stderr else exc.stdout.strip()
        logger.warn(i18n.t("docker.root.info_fail", error=stderr or exc.returncode))
        return None
    except Exception as exc:  # pragma: no cover - defensive
        logger.warn(i18n.t("docker.root.info_fail", error=str(exc)))
        return None

    path_str = result.stdout.strip()
    if not path_str:
        logger.warn(i18n.t("docker.root.info_empty"))
        return None

    path = Path(path_str)
    logger.info(i18n.t("docker.root.info_success", path=str(path)))
    return path


def _from_daemon_json(logger, i18n) -> Optional[Path]:
    daemon_path = Path("/etc/docker/daemon.json")
    if not daemon_path.exists():
        logger.debug(i18n.t("docker.root.daemon_missing_file", path=str(daemon_path)))
        return None

    try:
        with daemon_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        logger.warn(i18n.t("docker.root.daemon_parse", error=str(exc)))
        return None
    except Exception as exc:  # pragma: no cover - defensive
        logger.warn(i18n.t("docker.root.daemon_parse", error=str(exc)))
        return None

    root = data.get("data-root")
    if not root:
        logger.warn(i18n.t("docker.root.daemon_no_key"))
        return None

    path = Path(root)
    logger.info(i18n.t("docker.root.daemon_success", path=str(path)))
    return path


def _default_root(logger, i18n) -> Path:
    logger.info(i18n.t("docker.root.default", path=str(DEFAULT_DOCKER_ROOT)))
    return DEFAULT_DOCKER_ROOT
