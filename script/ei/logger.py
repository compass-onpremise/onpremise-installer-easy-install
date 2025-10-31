# -*- coding: utf-8 -*-
from __future__ import annotations
import logging, sys
from pathlib import Path
from datetime import datetime

RESET = "\033[0m"
DIM = "\033[2m"
BOLD = "\033[1m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"

class Logger:
    def __init__(self, logfile: Path, verbose: bool = False):
        self.logfile = Path(logfile)
        self.verbose = verbose
        self._setup()

    def _setup(self):
        self.logfile.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger("easy-install")
        self.logger.setLevel(logging.DEBUG)

        # file handler
        fh = logging.FileHandler(self.logfile, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        ffmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        fh.setFormatter(ffmt)
        self.logger.addHandler(fh)

        # console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG if self.verbose else logging.INFO)
        cfmt = logging.Formatter("%(message)s")
        ch.setFormatter(cfmt)
        self.logger.addHandler(ch)

    def info(self, msg: str):
        self.logger.info(msg)

    def debug(self, msg: str):
        self.logger.debug(msg)

    def warn(self, msg: str):
        self.logger.warning(f"{YELLOW}⚠ {msg}{RESET}")

    def error(self, msg: str):
        self.logger.error(f"{RED}✖ {msg}{RESET}")

    def step(self, i: int, n: int, label: str):
        self.info(f"{CYAN}⏳ [{i}/{n}] {label}{RESET}")

    def status(self, status: str):
        upper = status.upper()
        if upper in ("DONE", "FOUND") or upper.startswith("SKIP"):
            color = GREEN
        elif upper in ("WARN", "PROCEED_WITH_WARNINGS"):
            color = YELLOW
        else:
            color = RED
        self.info(f"{color}✔ {status}{RESET}")
