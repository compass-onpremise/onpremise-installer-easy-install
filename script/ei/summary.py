"""Final summary output for easy-install."""

from __future__ import annotations

from pathlib import Path


def print_summary(state, logger, i18n) -> str:
    if state.dry_run:
        logger.info(i18n.t("summary.dry_run"))
        return "SKIP"

    logger.info(i18n.t("summary.header"))

    logger.info(i18n.t("summary.domain", domain=state.domain or i18n.t("summary.none")))
    logger.info(i18n.t("summary.host_ip", host_ip=state.host_ip or i18n.t("summary.unknown")))
    logger.info(i18n.t("summary.root_mount", path=state.root_mount))
    configs_path = (Path(__file__).resolve().parent.parent.parent / "configs").resolve()
    logger.info(i18n.t("summary.configs", path=str(configs_path)))
    logger.info(i18n.t("summary.certs", bundle="/etc/nginx/ssl/compass.bundle.crt", cert_key="/etc/nginx/ssl/compass.key"))

    if state.admin_email:
        logger.info(i18n.t("summary.admin_email", email=state.admin_email))
    else:
        logger.info(i18n.t("summary.admin_email_default"))

    if state.admin_password:
        logger.info(i18n.t("summary.admin_password_cli"))
    else:
        logger.info(i18n.t("summary.admin_password_generated"))
    team_path = (configs_path / "team.yaml").resolve()
    logger.info(i18n.t("summary.admin_password_location", path=str(team_path)))

    logger.info(i18n.t("summary.log_file", path=state.log_file))
    if state.install_executed:
        logger.info(i18n.t("summary.footer_installed"))
    elif state.skip_install:
        logger.info(i18n.t("summary.footer_pending_skip"))
    else:
        logger.info(i18n.t("summary.footer_pending"))
    return "DONE"
