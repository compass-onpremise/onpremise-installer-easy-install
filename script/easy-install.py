#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, sys, os
from pathlib import Path
from datetime import datetime

# local imports
from ei.i18n import I18N
from ei.logger import Logger
from ei.state import State

REPO_ROOT = Path(__file__).resolve().parent.parent

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
    return p

def default_log_path() -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return REPO_ROOT / "logs" / f"easy-install_{ts}.log"

def main() -> int:
    # preliminary i18n to show parser help in default lang
    i18n = I18N(REPO_ROOT / "locales", "ru")
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
    logger.info(i18n.t("log.start", lang=i18n.lang))
    logger.debug(i18n.t("log.args", args=vars(args)))

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
        verbose=args.verbose
    )

    # Dry-run plan (list stages; implementation will be added in next steps)
    plan = [
        i18n.t("step.00a"),
        i18n.t("step.00b"),
        i18n.t("step.00c"),
        i18n.t("step.1"),
        i18n.t("step.2"),
        i18n.t("step.3"),
        i18n.t("step.4"),
        i18n.t("step.5"),
        i18n.t("step.6"),
        i18n.t("step.7"),
        i18n.t("step.8")
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

    # Пока только каркас (Этап 1). Реализация шагов — на следующих этапах.
    return 0

if __name__ == "__main__":
    sys.exit(main())
