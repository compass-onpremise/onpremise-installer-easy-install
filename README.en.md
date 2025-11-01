# Compass On‑premise Installer

`easy-install.py` prepares a host for Compass On‑premise: removes AppArmor when needed, validates hardware, installs missing packages, issues TLS certificates, and runs the primary installer `install.py`. You can pass a domain (`--domain`) and enable Let’s Encrypt (`--le`); otherwise the configuration falls back to the host IP and a local Compass CA chain is issued.

## Overview

1. Verify Python version and re-execute if required.
2. Disable AppArmor.
3. Check CPU, RAM, storage, and run fio IOPS tests.
4. Detect the OS and install missing packages (nginx, docker, fio, etc.).
5. Enable Docker + Swarm and create the Python virtual environment.
6. Run `create_configs.py` to generate configuration templates.
7. Issue TLS certificates through Let’s Encrypt or the bundled intermediate CA.
8. Apply mandatory YAML patches.
9. Launch `install.py` (unless `--skip-install` is set).

## Requirements

**Minimum software:** `python3` must already be available. The installer pulls the rest (`nginx`, `docker`, `fio`, `acme.sh`, `ruamel.yaml`, etc.) automatically.

**Supported operating systems:**

- Debian family: Debian 10+, Ubuntu 20.04+.
- RPM family: RedOS 8+, AlmaLinux 9.6+, MSVSfera 9.6+, ALT Linux 11.0+, Fedora 36+.

**Hardware requirements (aligned with installer checks):**

- CPU: 8 vCPU / threads or more.
- RAM: 16 GB or more.
- Storage: 30 GB of free space on the data root and Docker data-root.

## Quick start

```bash
sudo apt update && sudo apt install -y git python3 python3-venv
git clone git@github.com:compass-onpremise/onpremise-installer-easy-install.git
cd onpremise-installer-easy-install
sudo python3 script/easy-install.py \
  --yes \
  --domain example.org \
  --le \
  --admin-email admin@example.org
```

> Both `--domain` and `--le` are optional. Without `--le` the installer issues a local Compass certificate; without `--domain` it configures services using the host IP address.

## Command-line options

| Option | Description |
| --- | --- |
| `-y, --yes` | Assume “Yes” for all prompts. |
| `-l, --lang {ru,en}` | Message language (default: ru). |
| `-d, --domain <FQDN>` | Domain for `global.yaml` and certificates. |
| `--le` | Request a Let’s Encrypt certificate (requires `--domain`). |
| `--root-mount <PATH>` | Application data directory (default `/opt/compass_data`). |
| `--admin-email <EMAIL>` | Administrator e-mail (patched into `team.yaml`). |
| `--admin-password <PWD>` | Administrator password (otherwise generated). |
| `--skip-checks` | Skip resource and IOPS checks. |
| `--skip-bench` | Skip only the IOPS benchmark. |
| `--bench-runtime <SECONDS>` | fio runtime per location (default 20s). |
| `--skip-install` | Do not launch `install.py` after preparation. |
| `--log-file <PATH>` | Custom log path (`logs/easy-install_<timestamp>.log` by default). |
| `--dry-run` | Show the execution plan without changing the system. |
| `--verbose` | Verbose logging. |

## After the run

- A summary is printed to stdout and the log (`summary.*`).
- Configuration templates are generated in `configs/` for further customization.
- Certificates reside under `/etc/nginx/ssl/`.
- If `install.py` was skipped, launch it manually when ready:

```bash
sudo python3 script/install.py --confirm-all
```

## Manual installation and docs

- Full deployment guide: [doc-onpremise.getcompass.ru](https://doc-onpremise.getcompass.ru/information.html).
- For manual setup without `easy-install.py`, follow the “Подготовка к развертыванию” sections in the documentation above.

Support: [Compass On-premise workspace](https://getcompass.com/join/wlSjdBJd/), [Telegram](https://t.me/getcompass), or [support@getcompass.ru](mailto:support@getcompass.ru).
