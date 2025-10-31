# -*- coding: utf-8 -*-
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict

class I18N:
    def __init__(self, locales_dir: Path, lang: str = "ru"):
        self.locales_dir = Path(locales_dir)
        self.lang = lang if lang in ("ru", "en") else "ru"
        self._cache: Dict[str, str] = {}
        self.load()

    def load(self) -> None:
        file = self.locales_dir / f"{self.lang}.json"
        if not file.exists():
            # fallback to ru
            file = self.locales_dir / "ru.json"
            self.lang = "ru"
        with file.open("r", encoding="utf-8") as f:
            self._cache = json.load(f)

    def t(self, key: str, **kwargs) -> str:
        s = self._cache.get(key, key)
        try:
            return s.format(**kwargs)
        except Exception:
            return s
