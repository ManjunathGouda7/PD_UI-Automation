"""
Centralized Test Data Manager for USB PD C2 UI Automation.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import orjson

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

@dataclass
class TestDataManager:
    __test__ = False
    _data: dict[str, Any] | None = None

    @classmethod
    def load(cls) -> dict[str, Any]:
        if cls._data is None:
            data_file = ROOT_DIR / "jsons" / "test_data.json"
            if data_file.exists():
                with open(data_file, "rb") as f:
                    cls._data = orjson.loads(f.read())
            else:
                cls._data = {}
        return cls._data

    @classmethod
    def get_profile(cls, name: str = "provider_epr") -> dict[str, Any]:
        profiles = cls.load().get("dut_profiles", {})
        return profiles.get(name, {})

    @classmethod
    def get_connection_defaults(cls) -> dict[str, Any]:
        return cls.load().get("connection_defaults", {
            "ip": "192.168.102.76",
            "port": "5003",
            "device_serial": "GRL-V-DPWR-EPR-0002"
        })

test_data_manager = TestDataManager()
