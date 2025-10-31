"""Certificate issuance helpers (Let's Encrypt and local CA)."""

from __future__ import annotations

import ipaddress
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List

from .network import get_primary_ip


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CERT_DIR = Path("/etc/nginx/ssl")
BUNDLE_NAME = "compass.bundle.crt"
KEY_NAME = "compass.key"
INTERMEDIATE_CERT = REPO_ROOT / "packages" / "ca" / "intermediate.crt"
INTERMEDIATE_KEY = REPO_ROOT / "packages" / "ca" / "intermediate.key"


class CertError(Exception):
    """Generic certificate issuance error."""


def ensure_certificates(state, logger, i18n) -> str:
    if state.dry_run:
        logger.info(i18n.t("certs.dry_run", path=str(CERT_DIR)))
        return "SKIP"

    CERT_DIR.mkdir(parents=True, exist_ok=True)
    bundle_path = CERT_DIR / BUNDLE_NAME
    key_path = CERT_DIR / KEY_NAME

    if state.le and state.domain:
        try:
            logger.info(i18n.t("certs.mode_le", domain=state.domain))
            _issue_letsencrypt(state.domain, bundle_path, key_path, logger, i18n)
            _secure_files(bundle_path, key_path)
            logger.info(i18n.t("certs.done", bundle=str(bundle_path), cert_key=str(key_path)))
            return "DONE"
        except CertError as exc:
            logger.warn(i18n.t("certs.le_failed", error=str(exc)))
            if state.yes:
                logger.info(i18n.t("certs.auto_fallback"))
            else:
                if not _prompt_continue(i18n):
                    logger.info(i18n.t("certs.abort"))
                    sys.exit(2)
                logger.info(i18n.t("certs.manual_fallback"))

    logger.info(i18n.t("certs.mode_local"))
    _issue_local(state.domain, bundle_path, key_path, logger, i18n)
    _secure_files(bundle_path, key_path)
    logger.info(i18n.t("certs.done", bundle=str(bundle_path), cert_key=str(key_path)))
    return "DONE"


def _issue_local(domain: str | None, bundle_path: Path, key_path: Path, logger, i18n) -> None:
    if not INTERMEDIATE_CERT.exists() or not INTERMEDIATE_KEY.exists():
        raise CertError(i18n.t("certs.intermediate_missing"))

    ip_value = get_primary_ip()
    if ip_value is None:
        raise CertError(i18n.t("certs.ip_missing"))

    logger.info(i18n.t("certs.local_prepare", ip=ip_value, domain=domain or ""))

    try:
        from cryptography import x509
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives.serialization import load_pem_private_key
        from cryptography.x509.oid import NameOID
    except ImportError as exc:
        raise CertError(f"cryptography module required: {exc}")

    with INTERMEDIATE_CERT.open("rb") as fh:
        ca_cert = x509.load_pem_x509_certificate(fh.read(), backend=default_backend())
    with INTERMEDIATE_KEY.open("rb") as fh:
        ca_key = load_pem_private_key(fh.read(), password=None, backend=default_backend())

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())

    subject_name = domain or ip_value
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, subject_name)])
    basic_constraints = x509.BasicConstraints(ca=False, path_length=None)
    key_usage = x509.KeyUsage(
        digital_signature=True,
        key_encipherment=True,
        content_commitment=False,
        data_encipherment=False,
        key_agreement=False,
        key_cert_sign=False,
        crl_sign=False,
        encipher_only=False,
        decipher_only=False,
    )

    alt_names: List[x509.GeneralName] = [x509.IPAddress(ipaddress.ip_address(ip_value))]
    if domain:
        alt_names.append(x509.DNSName(domain))

    now = datetime.now(timezone.utc)
    cert_builder = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(ca_cert.subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(days=365))
        .add_extension(basic_constraints, False)
        .add_extension(key_usage, True)
        .add_extension(x509.SubjectAlternativeName(alt_names), False)
    )

    cert = cert_builder.sign(private_key=ca_key, algorithm=hashes.SHA256(), backend=default_backend())

    key_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    cert_pem = cert.public_bytes(encoding=serialization.Encoding.PEM)
    with INTERMEDIATE_CERT.open("rb") as fh:
        intermediate_pem = fh.read()

    bundle_path.write_bytes(cert_pem + intermediate_pem)
    key_path.write_bytes(key_pem)


def _issue_letsencrypt(domain: str, bundle_path: Path, key_path: Path, logger, i18n) -> None:
    le_dir = CERT_DIR / "letsencrypt"
    le_dir.mkdir(parents=True, exist_ok=True)

    acme_path = le_dir / "acme.sh"
    if not acme_path.exists():
        logger.info(i18n.t("certs.le_download"))
        subprocess.run([
            "wget", "-O", str(acme_path),
            "https://raw.githubusercontent.com/acmesh-official/acme.sh/3.0.7/acme.sh"
        ], check=True)
        subprocess.run(["chmod", "+x", str(acme_path)], check=True)

    _run_acme([str(acme_path), "--home", str(le_dir), "--set-default-ca", "--server", "letsencrypt"], i18n)
    _run_acme([str(acme_path), "--upgrade", "--home", str(le_dir)], i18n)

    register_cmd = [str(acme_path), "--register-account", "--home", str(le_dir)]
    reg = subprocess.run(register_cmd, check=False, text=True, capture_output=True)
    if reg.returncode not in {0, 2}:  # acme.sh returns 2 if account exists
        raise CertError(i18n.t("certs.le_register_fail", code=reg.returncode, output=(reg.stdout or "") + (reg.stderr or "")))

    reg_out = (reg.stdout or "") + (reg.stderr or "")
    match = re.search(r"ACCOUNT_THUMBPRINT='([^']+)'", reg_out)
    thumbprint = match.group(1) if match else None

    snippets_dir = Path("/etc/nginx/compass_snippets")
    snippets_dir.mkdir(parents=True, exist_ok=True)
    acme_snippet = snippets_dir / "acme_stateless.conf"
    if thumbprint:
        acme_snippet.write_text(
            """location ~ ^/\\.well-known/acme-challenge/([-_a-zA-Z0-9]+)$ {{
    default_type text/plain;
    return 200 "\\"$1.{thumbprint}\\"";
}}
""".format(thumbprint=thumbprint)
        )

    acme_conf_path = Path("/etc/nginx/conf.d")
    acme_conf_path.mkdir(parents=True, exist_ok=True)
    acme_conf_file = acme_conf_path / "acme.easy-install.conf"
    acme_conf_file.write_text(
        f"""server {{
    listen 80;
    return 404;
}}

server {{
    listen 80;
    server_name {domain};

    location ~ ^/\\.well-known/acme-challenge/([-_a-zA-Z0-9]+)$ {{
        default_type text/plain;
        return 200 \"$1.{thumbprint or ''}\";
    }}

    location / {{
        return 301 https://$host$request_uri;
    }}
}}
"""
    )

    _run_acme(["/usr/sbin/nginx", "-t"], i18n)
    _run_acme(["/usr/sbin/nginx", "-s", "reload"], i18n)

    cert_subdir = le_dir / f"{domain}_ecc"
    final_crt = cert_subdir / "fullchain.cer"
    final_key = cert_subdir / f"{domain}.key"

    if not final_crt.exists() or not final_key.exists():
        logger.info(i18n.t("certs.le_issue", domain=domain))
        _run_acme([
            str(acme_path), "--home", str(le_dir), "--issue", "--force", "--stateless", "-d", domain
        ], i18n)

    bundle_path.write_bytes(final_crt.read_bytes())
    key_path.write_bytes(final_key.read_bytes())

    renew_cmd = f"{acme_path} --home {le_dir} --renew --force --stateless -d {domain}"
    nginx_reload_cmd = "/usr/sbin/nginx -t && /usr/sbin/nginx -s reload"

    _run_acme([
        "bash", "-c",
        f'(crontab -l 2>/dev/null | grep -v -F "{renew_cmd}"); echo "0 0 15 * * {renew_cmd}" | crontab -'
    ], i18n)
    _run_acme([
        "bash", "-c",
        f'(crontab -l 2>/dev/null | grep -v -F "{nginx_reload_cmd}"); echo "0 3 15 * * {nginx_reload_cmd}" | crontab -'
    ], i18n)


def _secure_files(bundle_path: Path, key_path: Path) -> None:
    os.chmod(bundle_path, 0o600)
    os.chmod(key_path, 0o600)


def _prompt_continue(i18n) -> bool:
    answer = input(i18n.t("certs.prompt_fallback") + " ").strip().lower()
    return answer in {"y", "yes", "д", "да"}


def _run_acme(cmd: List[str], i18n) -> None:
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        output = (exc.stdout or "") + (exc.stderr or "") if hasattr(exc, "stdout") else ""
        raise CertError(i18n.t("certs.le_cmd_fail", command=" ".join(cmd), code=exc.returncode, output=output))
