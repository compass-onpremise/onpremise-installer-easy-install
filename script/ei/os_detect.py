"""OS detection helpers."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List


class OSType(Enum):
    DEB = "deb"
    RPM = "rpm"
    UNKNOWN = "unknown"


@dataclass
class OsInfo:
    os_type: OSType
    os_id: str
    name: str
    version: str
    id_like: List[str]

    @property
    def type_label(self) -> str:
        if self.os_type == OSType.DEB:
            return "os.type.deb"
        if self.os_type == OSType.RPM:
            return "os.type.rhel"
        return "os.type.unknown"


def detect_os(logger, i18n) -> OsInfo:
    logger.info(i18n.t("os.detect.start"))
    data = _read_os_release()
    os_id = data.get("ID", "").lower()
    name = data.get("NAME", os_id) or os_id or "Unknown"
    version = data.get("VERSION_ID", data.get("VERSION", "")) or ""
    id_like_raw = data.get("ID_LIKE", "")
    id_like = [part.lower() for part in id_like_raw.replace("\t", " ").split() if part]

    os_type = _classify(os_id, id_like)
    info = OsInfo(os_type=os_type, os_id=os_id, name=name, version=version, id_like=id_like)

    if os_type == OSType.UNKNOWN:
        logger.error(i18n.t("os.detect.unsupported", os_id=os_id or "unknown"))
        logger.info(i18n.t("os.detect.expected.deb"))
        logger.info(i18n.t("os.detect.expected.rhel"))
        logger.info(i18n.t("os.detect.exit"))
        sys.exit(2)

    logger.info(i18n.t("os.detect.result", name=name, version=version or "?", os_id=os_id, os_type=i18n.t(info.type_label)))
    return info


def _read_os_release() -> Dict[str, str]:
    path = Path("/etc/os-release")
    data: Dict[str, str] = {}
    if not path.exists():
        return data

    with path.open("r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            value = value.strip().strip('"').strip("'")
            data[key.strip()] = value
    return data


def _classify(os_id: str, id_like: List[str]) -> OSType:
    deb_ids = {"debian", "ubuntu"}
    rpm_ids = {"rhel", "centos", "rocky", "almalinux", "fedora", "amzn", "ol"}

    if os_id in deb_ids:
        return OSType.DEB
    if os_id in rpm_ids:
        return OSType.RPM

    if any(x in deb_ids for x in id_like):
        return OSType.DEB
    if any(x in rpm_ids for x in id_like):
        return OSType.RPM

    return OSType.UNKNOWN
