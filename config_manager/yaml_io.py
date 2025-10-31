"""YAML IO helpers preserving comments and order."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ruamel.yaml import YAML


_yaml = YAML()
_yaml.default_flow_style = False
_yaml.indent(mapping=2, sequence=4, offset=2)


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return _yaml.load(fh)


def dump_yaml(data: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        _yaml.dump(data, fh)
