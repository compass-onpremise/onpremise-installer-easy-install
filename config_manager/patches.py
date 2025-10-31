"""Patch definitions for config YAML files."""

from __future__ import annotations

import secrets
import string
from dataclasses import dataclass
from typing import Callable, List, Any

from ruamel.yaml.comments import CommentedSeq
from ruamel.yaml.scalarstring import DoubleQuotedScalarString

from script.ei.network import get_primary_ip


@dataclass
class PatchSpec:
    filename: str
    handler: Callable[[Any, Any, Any, Any], List[str]]  # data, state, logger, i18n


def _flow_seq(values: List[str]) -> CommentedSeq:
    seq = CommentedSeq([DoubleQuotedScalarString(v) for v in values])
    seq.fa.set_flow_style()
    return seq


def _generate_password() -> str:
    alphabet = string.ascii_letters + string.digits
    while True:
        pwd = "".join(secrets.choice(alphabet) for _ in range(12))
        if any(c.islower() for c in pwd) and any(c.isupper() for c in pwd) and any(c.isdigit() for c in pwd):
            return pwd


def _patch_auth(data, state, logger, i18n) -> List[str]:
    data["available_methods"] = _flow_seq(["mail"])
    data["available_guest_methods"] = _flow_seq(["mail"])
    data["mail.registration_2fa_enabled"] = False
    data["mail.authorization_2fa_enabled"] = False
    data["smtp.host"] = DoubleQuotedScalarString("smtp.example.com")
    data["smtp.port"] = 587
    data["smtp.username"] = DoubleQuotedScalarString("no-reply@example.com")
    data["smtp.password"] = DoubleQuotedScalarString("change-me")
    data["smtp.encryption"] = DoubleQuotedScalarString("tls")
    data["smtp.from"] = DoubleQuotedScalarString("compass@example.com")
    logger.info(i18n.t("patch.auth"))
    return []


def _patch_captcha(data, state, logger, i18n) -> List[str]:
    data["captcha.enabled"] = False
    logger.info(i18n.t("patch.captcha"))
    return []


def _patch_team(data, state, logger, i18n) -> List[str]:
    warnings: List[str] = []
    data["root_user.full_name"] = DoubleQuotedScalarString("Администратор")

    admin_mail = state.admin_email or "admin@example.com"
    data["root_user.mail"] = DoubleQuotedScalarString(admin_mail)
    if state.admin_email:
        logger.info(i18n.t("patch.team.mail_cli"))
    else:
        warnings.append(i18n.t("patch.team.mail_default"))

    if state.admin_password:
        password = state.admin_password
        logger.info(i18n.t("patch.team.password_cli"))
    else:
        password = _generate_password()
        state.admin_password = password
        logger.info(i18n.t("patch.team.password_generated"))
    data["root_user.password"] = DoubleQuotedScalarString(password)

    return warnings


def _patch_global(data, state, logger, i18n) -> List[str]:
    warnings: List[str] = []
    data["nginx.ssl_crt"] = DoubleQuotedScalarString("compass.bundle.crt")
    data["nginx.ssl_key"] = DoubleQuotedScalarString("compass.key")

    domain = state.domain or ""
    data["domain"] = DoubleQuotedScalarString(domain)

    host_ip = state.host_ip or get_primary_ip()
    if host_ip:
        data["host_ip"] = DoubleQuotedScalarString(host_ip)
        state.host_ip = host_ip
        logger.info(i18n.t("patch.global.ip", ip=host_ip))
    else:
        warnings.append(i18n.t("patch.global.ip_warn"))

    data["root_mount_path"] = DoubleQuotedScalarString(state.root_mount)

    return warnings


PATCHES: List[PatchSpec] = [
    PatchSpec("auth.yaml", _patch_auth),
    PatchSpec("captcha.yaml", _patch_captcha),
    PatchSpec("team.yaml", _patch_team),
    PatchSpec("global.yaml", _patch_global),
]


def apply_patch(filename: str, data, state, logger, i18n) -> List[str]:
    for spec in PATCHES:
        if spec.filename == filename:
            return spec.handler(data, state, logger, i18n)
    return []


def get_patches() -> List[PatchSpec]:
    return PATCHES
