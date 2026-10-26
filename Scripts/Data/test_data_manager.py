"""
Centralized test data access (jsons/test_data.json).
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import orjson

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_FILE = ROOT_DIR / "jsons" / "test_data.json"


class TestDataManager:
    __test__ = False

    @staticmethod
    @lru_cache(maxsize=1)
    def load() -> dict[str, Any]:
        return orjson.loads(DATA_FILE.read_bytes())

    def section(self, name: str) -> dict[str, Any]:
        data = self.load()
        if name not in data:
            raise KeyError(f"Section '{name}' missing from {DATA_FILE}")
        return data[name]

    def get_profile(self, name: str) -> dict[str, Any]:
        profiles = self.section("dut_profiles")
        if name not in profiles:
            raise KeyError(f"DUT profile '{name}' not found; available: {sorted(profiles)}")
        return profiles[name]


test_data_manager = TestDataManager()
