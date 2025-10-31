#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, sys, os
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# local imports
from ei.python_gate import ensure_python
from ei.capacity import check_capacity
from ei.bench import run_benchmarks
from ei.os_detect import detect_os
from ei.apparmor import handle_apparmor
from ei.pkg_manager import ensure_packages
from ei.docker_service import ensure_docker_service
from ei.venv_manager import ensure_virtualenv
from ei.run_create_configs import run_create_configs
from ei.certs import ensure_certificates
from ei.install_runner import run_install
from ei.summary import print_summary
from ei.i18n import I18N
from ei.logger import Logger
from ei.state import State


def apply_config_patches(state, logger, i18n):
    if state.venv_site_packages and state.venv_site_packages not in sys.path:
        sys.path.insert(0, state.venv_site_packages)
    from config_manager.apply import apply_patches as _apply_patches

    return _apply_patches(state, logger, i18n)

def build_parser(i18n: I18N) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=i18n.t("cli.help"))
    p.add_argument("-y", "--yes", action="store_true", help=i18n.t("cli.opt.yes"))
    p.add_argument("-l", "--lang", choices=["ru","en"], default="ru", help=i18n.t("cli.opt.lang"))
    p.add_argument("-d", "--domain", default=None, help=i18n.t("cli.opt.domain"))
    p.add_argument("--le", action="store_true", help=i18n.t("cli.opt.le"))
    p.add_argument("--root-mount", default="/opt/compass_data", help=i18n.t("cli.opt.root_mount"))
    p.add_argument("--admin-email", default=None, help=i18n.t("cli.opt.admin_email"))
    p.add_argument("--admin-password", default=None, help=i18n.t("cli.opt.admin_password"))
    p.add_argument("--skip-checks", action="store_true", help=i18n.t("cli.opt.skip_checks"))
    p.add_argument("--skip-bench", action="store_true", help=i18n.t("cli.opt.skip_bench"))
    p.add_argument("--bench-runtime", type=int, default=20, help=i18n.t("cli.opt.bench_runtime"))
    p.add_argument("--log-file", default=None, help=i18n.t("cli.opt.log_file"))
    p.add_argument("--dry-run", action="store_true", help=i18n.t("cli.opt.dry_run"))
    p.add_argument("--verbose", action="store_true", help=i18n.t("cli.opt.verbose"))
    p.add_argument("--skip-install", action="store_true", help=i18n.t("cli.opt.skip_install"))
    return p

def default_log_path() -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return REPO_ROOT / "logs" / f"easy-install_{ts}.log"

def main() -> int:
    script_path = Path(__file__).resolve()

    # preliminary i18n to show parser help in default lang
    i18n = I18N(REPO_ROOT / "locales", "ru")
    python_status = ensure_python(i18n, script_path)
    parser = build_parser(i18n)

    # peek lang early to rebuild parser with correct language if needed
    argv = sys.argv[1:]
    try:
        lang_idx = next(i for i,a in enumerate(argv) if a in ("-l","--lang"))
        lang_val = argv[lang_idx+1]
        i18n = I18N(REPO_ROOT / "locales", lang_val)
        parser = build_parser(i18n)
    except StopIteration:
        pass
    except Exception:
        # ignore malformed, argparse will handle
        pass

    args = parser.parse_args()

    # finalize i18n and logger
    i18n = I18N(REPO_ROOT / "locales", args.lang)
    log_path = Path(args.log_file) if args.log_file else default_log_path()
    logger = Logger(log_path, verbose=args.verbose)

    logger.info(i18n.t("log.file_path", path=str(log_path)))
    logger.info(i18n.t("python.version.ok", current=python_status.current, required=python_status.required))
    logger.info(i18n.t("log.start", lang=i18n.lang))
    logger.debug(i18n.t("log.args", args=vars(args)))

    # require root privileges early
    if hasattr(os, "geteuid"):
        is_root = os.geteuid() == 0
    else:
        is_root = False
    if not is_root:
        logger.error(i18n.t("err.root_required"))
        logger.info(i18n.t("exit.root", code=2))
        return 2

    # validation
    if args.le and not args.domain:
        logger.error(i18n.t("err.le_without_domain"))
        logger.info(i18n.t("exit.validation", code=3))
        return 3

    state = State(
        yes=args.yes,
        lang=i18n.lang,
        domain=args.domain,
        le=args.le,
        root_mount=args.root_mount,
        admin_email=args.admin_email,
        admin_password=args.admin_password,
        skip_checks=args.skip_checks,
        skip_bench=args.skip_bench,
        bench_runtime=args.bench_runtime,
        log_file=str(log_path),
        dry_run=args.dry_run,
        verbose=args.verbose,
        skip_install=args.skip_install
    )

    # Dry-run plan (list stages; implementation will be added in next steps)
    plan = [
        i18n.t("step.python_check"),
        i18n.t("step.capacity_check"),
        i18n.t("step.apparmor"),
        i18n.t("step.iops_bench"),
        i18n.t("step.os_detect"),
        i18n.t("step.pkg_install"),
        i18n.t("step.docker"),
        i18n.t("step.venv"),
        i18n.t("step.configs"),
        i18n.t("step.cert"),
        i18n.t("step.yaml_patch"),
        i18n.t("step.install"),
        i18n.t("step.summary")
    ]
    logger.info(i18n.t("log.summary",
        yes=state.yes,
        domain=state.domain,
        le=state.le,
        root_mount=state.root_mount,
        admin=state.admin_email,
        skip_checks=state.skip_checks,
        skip_bench=state.skip_bench,
        bench_runtime=state.bench_runtime,
        verbose=state.verbose
    ))
    logger.info(i18n.t("log.plan"))
    total = len(plan)
    for idx, name in enumerate(plan, start=1):
        logger.info(i18n.t("log.plan.item", i=idx, n=total, name=name))

    # steps execution (partially implemented)
    os_info = None
    step_idx = 1
    logger.step(step_idx, total, i18n.t("step.python_check"))
    logger.status("DONE")

    step_idx += 1
    logger.step(step_idx, total, i18n.t("step.capacity_check"))
    if state.dry_run:
        logger.info(i18n.t("capacity.dry_run"))
        logger.status("SKIP")
    else:
        status = check_capacity(state, logger, i18n)
        logger.status(status)

    step_idx += 1
    logger.step(step_idx, total, i18n.t("step.apparmor"))
    status = handle_apparmor(state, logger, i18n)
    logger.status(status)

    step_idx += 1
    logger.step(step_idx, total, i18n.t("step.iops_bench"))
    if state.dry_run:
        logger.info(i18n.t("bench.dry_run"))
        logger.status("SKIP")
    else:
        status = run_benchmarks(state, logger, i18n)
        logger.status(status)

    step_idx += 1
    logger.step(step_idx, total, i18n.t("step.os_detect"))
    if state.dry_run:
        logger.info(i18n.t("os.dry_run"))
        logger.status("SKIP")
    else:
        os_info = detect_os(logger, i18n)
        state.os_type = os_info.os_type.value
        state.os_id = os_info.os_id
        state.os_name = os_info.name
        state.os_version = os_info.version
        logger.status("DONE")

    step_idx += 1
    logger.step(step_idx, total, i18n.t("step.pkg_install"))
    if state.dry_run:
        logger.info(i18n.t("pkg.dry_run"))
        logger.status("SKIP")
    else:
        if os_info is None:
            os_info = detect_os(logger, i18n)
            state.os_type = os_info.os_type.value
            state.os_id = os_info.os_id
            state.os_name = os_info.name
            state.os_version = os_info.version
        status = ensure_packages(state, logger, i18n, os_info)
        logger.status(status)

    step_idx += 1
    logger.step(step_idx, total, i18n.t("step.docker"))
    status = ensure_docker_service(state, logger, i18n)
    logger.status(status)

    step_idx += 1
    logger.step(step_idx, total, i18n.t("step.venv"))
    status = ensure_virtualenv(state, logger, i18n)
    logger.status(status)

    step_idx += 1
    logger.step(step_idx, total, i18n.t("step.configs"))
    status = run_create_configs(state, logger, i18n)
    logger.status(status)

    step_idx += 1
    logger.step(step_idx, total, i18n.t("step.cert"))
    status = ensure_certificates(state, logger, i18n)
    logger.status(status)

    step_idx += 1
    logger.step(step_idx, total, i18n.t("step.yaml_patch"))
    if state.dry_run:
        logger.info(i18n.t("patch.dry_run", path=str(REPO_ROOT / "configs")))
        logger.status("SKIP")
    else:
        status = apply_config_patches(state, logger, i18n)
        logger.status(status)

    step_idx += 1
    logger.step(step_idx, total, i18n.t("step.install"))
    status = run_install(state, logger, i18n)
    logger.status(status)

    step_idx += 1
    logger.step(step_idx, total, i18n.t("step.summary"))
    status = print_summary(state, logger, i18n)
    logger.status(status)

    # Пока только каркас (Этап 1). Реализация следующих шагов появится далее.
    return 0

if __name__ == "__main__":
    sys.exit(main())
