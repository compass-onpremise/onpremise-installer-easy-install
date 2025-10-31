# Compass On‑premise Installer

`easy-install.py` prepares a host for Compass On‑premise: removes AppArmor, validates hardware, installs system packages, issues TLS certificates and runs the main `install.py` bootstrapper.

## Quick start

```bash
sudo apt update && sudo apt install -y git python3 python3-venv
git clone https://github.com/getCompass/onpremise-installer.git
cd onpremise-installer
sudo python3 script/easy-install.py \
  --yes \
  --domain example.org \
  --le \
  --admin-email admin@example.org
```

The script performs the following steps:

1. Detects and removes AppArmor (with confirmation).
2. Checks CPU/RAM/disk capacity and runs fio IOPS tests.
3. Detects the OS, installs required packages (nginx, docker, certbot, fio, etc.).
4. Enables Docker + Swarm, creates a Python virtual environment with dependencies.
5. Generates template configuration files in `configs/`.
6. Issues a Let’s Encrypt certificate or a local certificate signed by the bundled intermediate CA.
7. Applies mandatory YAML patches (auth/captcha/team/global).
8. Launches `install.py --confirm-all` unless `--skip-install` is provided.

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

- A summary block is printed to the console and log (domain, IP, paths, next steps).
- Configuration files are located in `configs/`. For advanced setup follow the [official documentation](https://doc-onpremise.getcompass.ru/information.html).
- Certificates are placed under `/etc/nginx/ssl/`. Replace them with your own if required.
- If `install.py` was skipped, run it manually when ready:

```bash
sudo python3 script/install.py --confirm-all
```

## Further reading

Full deployment and configuration guide: [doc-onpremise.getcompass.ru](https://doc-onpremise.getcompass.ru/information.html).

Support: [Compass On-premise workspace](https://getcompass.com/join/wlSjdBJd/), [Telegram](https://t.me/getcompass) or [support@getcompass.ru](mailto:support@getcompass.ru).
