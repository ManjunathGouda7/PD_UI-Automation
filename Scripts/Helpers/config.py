"""
Centralized Configuration Manager for GRL-V-DPWR-EPR (USB PD C2).

Resolution order for every key: environment variable -> jsons/Inputs.json -> default.
"""
import os
from pathlib import Path
from typing import Any
import urllib.request

from dotenv import load_dotenv
import orjson

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT_DIR / "Configurations" / ".env")

_TRUE = ("true", "1", "yes", "on")
_FALSE = ("false", "0", "no", "off")


class Config:
    _cached_inputs: dict[str, Any] | None = None
    _cached_resolved_url: str | None = None

    _KEY_ALIASES: dict[str, list[str]] = {
        "BASE_URL": ["BaseURL", "base_url", "Url", "URL"],
        "DUT_IP": ["DefaultIP", "dut_ip", "IP", "ip"],
        "DUT_PORT": ["Port", "dut_port", "port"],
        "DUT_TYPE": ["DUTType", "dut_type"],
        "CABLE_MODEL": ["CableModel", "cable_model"],
        "AUTO_DETECT_VERSION": ["AutoDetectVersion", "auto_detect_version"],
        "HEADLESS": ["Headless", "headless"],
    }

    @classmethod
    def get_inputs(cls) -> dict[str, Any]:
        if cls._cached_inputs is None:
            inputs_file = ROOT_DIR / "jsons" / "Inputs.json"
            try:
                cls._cached_inputs = orjson.loads(inputs_file.read_bytes())
            except (OSError, orjson.JSONDecodeError):
                cls._cached_inputs = {}
        return cls._cached_inputs

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Returns the raw value for `key` (strings stay strings; use get_bool for flags)."""
        env_val = os.getenv(key)
        if env_val is not None and env_val != "":
            return env_val

        pd_config = cls.get_inputs().get("GRL-V-DPWR-EPR", {}).get("PD", {})
        for candidate in [key, *cls._KEY_ALIASES.get(key, [])]:
            if candidate in pd_config and pd_config[candidate] not in (None, ""):
                return pd_config[candidate]
        return default

    @classmethod
    def get_bool(cls, key: str, default: bool = False) -> bool:
        val = cls.get(key, default)
        if isinstance(val, bool):
            return val
        text = str(val).strip().lower()
        if text in _TRUE:
            return True
        if text in _FALSE:
            return False
        return default

    @classmethod
    def get_int(cls, key: str, default: int) -> int:
        try:
            return int(cls.get(key, default))
        except (TypeError, ValueError):
            return default

    # ------------------------------------------------------------------
    # URLs
    # ------------------------------------------------------------------

    @classmethod
    def api_host(cls) -> str:
        """Base host of the C2 backend, e.g. http://localhost:5003 (no page suffix)."""
        raw_url = str(cls.get("BASE_URL", "http://localhost:5003")).rstrip("/")
        if raw_url.endswith(".html"):
            raw_url = raw_url.rsplit("/", 1)[0]
        return raw_url

    @classmethod
    def get_url_version_extension(cls, host_url: str | None = None) -> str | None:
        """Queries /api/App/GetURLVersionExtension (e.g. 'v1.1.4'); None when unreachable."""
        api_url = f"{(host_url or cls.api_host()).rstrip('/')}/api/App/GetURLVersionExtension"
        try:
            req = urllib.request.Request(api_url, headers={"User-Agent": "GRL-Automation"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                ver = resp.read().decode("utf-8").strip().strip('"').strip("'")
                return ver or None
        except OSError:
            return None

    @classmethod
    def base_url(cls) -> str:
        """
        URL of the web UI. An explicit *.html BASE_URL is used as-is. Otherwise the
        versioned page is resolved from the backend; if that fails the host root is
        used, which redirects to the current versioned page by itself.
        """
        if cls._cached_resolved_url:
            return cls._cached_resolved_url

        raw_url = str(cls.get("BASE_URL", "http://localhost:5003")).rstrip("/")
        resolved = raw_url
        if not raw_url.endswith(".html"):
            version = cls.get_url_version_extension() if cls.get_bool("AUTO_DETECT_VERSION", True) else None
            resolved = f"{raw_url}/{version}.html" if version else f"{raw_url}/"

        cls._cached_resolved_url = resolved
        return resolved

    # ------------------------------------------------------------------
    # Hardware / run settings
    # ------------------------------------------------------------------

    @classmethod
    def dut_ip(cls) -> str:
        return str(cls.get("DUT_IP", "192.168.255.1"))

    @classmethod
    def dut_port(cls) -> str:
        return str(cls.get("DUT_PORT", "5003"))

    @classmethod
    def is_headless(cls) -> bool:
        return cls.get_bool("HEADLESS", True)

    SUPPORTED_BROWSERS = ("chromium", "msedge", "chrome", "firefox")

    @classmethod
    def browser(cls) -> str:
        """Browser engine for UI tests: chromium (Playwright's bundled build), msedge, chrome or firefox."""
        name = str(cls.get("BROWSER", "chromium")).strip().lower()
        aliases = {"edge": "msedge", "ms-edge": "msedge", "google-chrome": "chrome"}
        name = aliases.get(name, name)
        if name not in cls.SUPPORTED_BROWSERS:
            raise ValueError(f"Unsupported BROWSER={name!r}; use one of {cls.SUPPORTED_BROWSERS}")
        return name

    @classmethod
    def is_mock_mode(cls) -> bool:
        """True when the run targets the offline API mock instead of the real C2 backend."""
        return cls.get_bool("MOCK_SERVER", False)

    @classmethod
    def allow_hw_actions(cls) -> bool:
        """
        Gate for tests that change tester/backend state (connect, scan, apply config,
        attach/detach, read device data, ...). Off by default so a normal run is read-only.
        """
        return cls.get_bool("ALLOW_HW_ACTIONS", False)

    @classmethod
    def strict_hardware(cls) -> bool:
        """When true, tests needing a connected tester fail instead of skipping if it is offline."""
        return cls.get_bool("STRICT_HARDWARE", False)

    @classmethod
    def ui_timeout_ms(cls) -> int:
        return cls.get_int("UI_TIMEOUT_MS", 10000)

    @classmethod
    def page_load_timeout_ms(cls) -> int:
        return cls.get_int("PAGE_LOAD_TIMEOUT_MS", 30000)

    @classmethod
    def get_api_endpoint(cls, key: str, default: str = "") -> str:
        """
        Returns full URL for a configured API key or builds it from api_host.
        Supports direct alias ("sw_version"), controller notation ("App.GetSoftwareVersion"
        or "App/GetSoftwareVersion") and bare endpoint search ("GetSoftwareVersion").
        """
        apis = cls.get_inputs().get("GRL-V-DPWR-EPR", {}).get("PD", {}).get("apis", {})
        if key in apis and isinstance(apis[key], str):
            return str(apis[key])

        normalized_key = key.replace("/", ".")
        if "." in normalized_key:
            controller, subkey = normalized_key.split(".", 1)
            if isinstance(apis.get(controller), dict) and subkey in apis[controller]:
                return str(apis[controller][subkey])

        for val in apis.values():
            if isinstance(val, dict) and key in val:
                return str(val[key])

        if not default and key:
            return f"{cls.api_host()}/api/{key.lstrip('/')}"
        return default
