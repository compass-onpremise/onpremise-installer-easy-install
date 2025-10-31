"""Package management helpers."""

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import List, Optional, Sequence

from .os_detect import OSType, OsInfo


@dataclass
class PackageRequest:
    names: Sequence[str]
    optional: bool = False

    @property
    def primary(self) -> str:
        return self.names[0]


@dataclass
class PackageResult:
    request: PackageRequest
    installed_name: Optional[str]

    @property
    def is_installed(self) -> bool:
        return self.installed_name is not None


def ensure_packages(state, logger, i18n, os_info: OsInfo) -> str:
    logger.info(i18n.t("pkg.start", os_type=i18n.t(os_info.type_label)))

    requests = _build_requests(state, os_info)
    results: List[PackageResult] = []

    for request in requests:
        installed = _check_request(request, os_info)
        results.append(installed)
        if installed.is_installed:
            logger.info(i18n.t("pkg.found", name=installed.installed_name))
        elif request.optional:
            logger.warn(i18n.t("pkg.optional_missing", name=request.primary))
        else:
            logger.warn(i18n.t("pkg.missing", name=request.primary))

    missing_required = [r.request.names[0] for r in results if not r.is_installed and not r.request.optional]

    if not missing_required:
        warnings = [r for r in results if not r.is_installed and r.request.optional]
        if warnings:
            logger.warn(i18n.t("pkg.optional_summary", count=len(warnings)))
            return "PROCEED_WITH_WARNINGS"
        logger.info(i18n.t("pkg.ok"))
        return "DONE"

    if not state.yes:
        logger.info(i18n.t("pkg.install.prompt", packages=", ".join(missing_required)))
        if not _prompt(i18n):
            logger.info(i18n.t("pkg.commands", command=_install_command_preview(os_info, missing_required)))
            logger.info(i18n.t("pkg.exit"))
            sys.exit(2)

    _install_packages(logger, i18n, os_info, missing_required)

    post_results = [_check_request(r.request, os_info) for r in results]
    if all(r.is_installed or r.request.optional for r in post_results):
        logger.info(i18n.t("pkg.ok"))
        optional_missing = [r for r in post_results if not r.is_installed and r.request.optional]
        if optional_missing:
            logger.warn(i18n.t("pkg.optional_summary", count=len(optional_missing)))
            return "PROCEED_WITH_WARNINGS"
        return "DONE"

    failed = [r.request.primary for r in post_results if not r.is_installed and not r.request.optional]
    logger.error(i18n.t("pkg.install.fail", packages=", ".join(failed)))
    sys.exit(2)


def _build_requests(state, os_info: OsInfo) -> List[PackageRequest]:
    base = []
    if os_info.os_type == OSType.DEB:
        base = [
            PackageRequest(["nginx"]),
            PackageRequest(["docker.io", "docker-ce"]),
            PackageRequest(["python3"]),
            PackageRequest(["python3-venv"]),
            PackageRequest(["python3-pip"]),
            PackageRequest(["openssl"]),
        ]
        if state.le:
            base.append(PackageRequest(["certbot"]))
        need_fio = not state.skip_checks and not state.skip_bench
        base.append(PackageRequest(["fio"], optional=not need_fio))
    elif os_info.os_type == OSType.RPM:
        base = [
            PackageRequest(["nginx"]),
            PackageRequest(["docker", "moby-engine"]),
            PackageRequest(["python3"]),
            PackageRequest(["python3-pip"]),
            PackageRequest(["python3-virtualenv", "python3-venv"]),
            PackageRequest(["openssl"]),
        ]
        if state.le:
            base.append(PackageRequest(["certbot"]))
        need_fio = not state.skip_checks and not state.skip_bench
        base.append(PackageRequest(["fio"], optional=not need_fio))
    else:
        base = []
    return base


def _check_request(request: PackageRequest, os_info: OsInfo) -> PackageResult:
    for name in request.names:
        if _is_installed(name, os_info):
            return PackageResult(request=request, installed_name=name)
    return PackageResult(request=request, installed_name=None)


def _is_installed(name: str, os_info: OsInfo) -> bool:
    try:
        if os_info.os_type == OSType.DEB:
            result = subprocess.run(
                ["dpkg-query", "-W", "-f=${Status}", name],
                capture_output=True,
                text=True,
                check=False,
            )
            return result.returncode == 0 and "install ok installed" in result.stdout
        if os_info.os_type == OSType.RPM:
            result = subprocess.run(["rpm", "-q", name], capture_output=True, text=True, check=False)
            return result.returncode == 0
    except FileNotFoundError:
        return False
    return False


def _prompt(i18n) -> bool:
    answer = input(i18n.t("pkg.install.ask") + " ").strip().lower()
    return answer in {"y", "yes", "д", "да"}


def _install_command_preview(os_info: OsInfo, packages: Sequence[str]) -> str:
    if os_info.os_type == OSType.DEB:
        return f"apt-get install {' '.join(packages)}"
    if os_info.os_type == OSType.RPM:
        return f"dnf install {' '.join(packages)}"
    return ""


def _install_packages(logger, i18n, os_info: OsInfo, packages: Sequence[str]) -> None:
    if not packages:
        return

    if os_info.os_type == OSType.DEB:
        cmd = ["apt-get", "install", "-y", *packages]
    elif os_info.os_type == OSType.RPM:
        installer = _find_rpm_installer()
        cmd = [installer, "install", "-y", *packages]
    else:
        raise RuntimeError("Unsupported OS type for installation")

    logger.info(i18n.t("pkg.install.running", command=" ".join(cmd)))
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        logger.error(i18n.t("pkg.install.cmd_missing", command=cmd[0]))
        sys.exit(2)
    except subprocess.CalledProcessError as exc:
        logger.error(i18n.t("pkg.install.error", returncode=exc.returncode))
        sys.exit(exc.returncode or 2)


def _find_rpm_installer() -> str:
    for candidate in ("dnf", "yum"):
        if shutil.which(candidate):
            return candidate
    return "dnf"
