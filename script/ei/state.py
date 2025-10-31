# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class State:
    yes: bool
    lang: str
    domain: str | None
    le: bool
    root_mount: str
    admin_email: str | None
    admin_password: str | None
    skip_checks: bool
    skip_bench: bool
    bench_runtime: int
    log_file: str
    dry_run: bool
    verbose: bool
    os_type: str | None = None
    os_id: str | None = None
    os_name: str | None = None
    os_version: str | None = None
    docker_data_root: str | None = None
    host_ip: str | None = None
    skip_install: bool = False
    install_executed: bool = False
    venv_path: str | None = None
    venv_python: str | None = None
    venv_site_packages: str | None = None
