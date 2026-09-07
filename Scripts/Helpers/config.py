"""
Centralized Configuration Manager for GRL-V-DPWR-EPR (USB PD C2).
Supports tiered fallback: Environment variables -> Inputs.json -> Defaults.
"""
import os
from pathlib import Path
from typing import Any
import orjson
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT_DIR / "Configurations" / ".env")


class Config:
    _cached_inputs: dict[str, Any] | None = None
    _cached_resolved_url: str | None = None

    _KEY_ALIASES: dict[str, list[str]] = {
        "BASE_URL": ["BaseURL", "base_url", "BASE_URL", "Url", "URL"],
        "DUT_IP": ["DefaultIP", "DUT_IP", "dut_ip", "IP", "ip"],
        "DUT_PORT": ["Port", "DUT_PORT", "dut_port", "port"],
        "DUT_TYPE": ["DUTType", "DUT_TYPE", "dut_type"],
        "CABLE_MODEL": ["CableModel", "CABLE_MODEL", "cable_model"],
        "AUTO_DETECT_VERSION": ["AutoDetectVersion", "auto_detect_version", "AUTO_DETECT_VERSION"],
        "HEADLESS": ["HEADLESS", "Headless", "headless"],
    }

    @classmethod
    def get_inputs(cls) -> dict[str, Any]:
        if cls._cached_inputs is None:
            inputs_file = ROOT_DIR / "jsons" / "Inputs.json"
            if inputs_file.exists():
                try:
                    with open(inputs_file, "rb") as f:
                        cls._cached_inputs = orjson.loads(f.read())
                except Exception:
                    cls._cached_inputs = {}
            else:
                cls._cached_inputs = {}
        return cls._cached_inputs

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        # 1. Environment variable check
        env_val = os.getenv(key)
        if env_val is not None:
            if env_val.lower() in ("true", "1", "yes"):
                return True
            if env_val.lower() in ("false", "0", "no"):
                return False
            return env_val

        # 2. Inputs.json check with alias support
        inputs = cls.get_inputs()
        pd_config = inputs.get("GRL-V-DPWR-EPR", {}).get("PD", {})
        if key in pd_config:
            return pd_config[key]

        aliases = cls._KEY_ALIASES.get(key, [])
        for alias in aliases:
            if alias in pd_config:
                return pd_config[alias]

        # Case-insensitive fallback
        normalized = key.lower().replace("_", "")
        for k, v in pd_config.items():
            if k.lower().replace("_", "") == normalized:
                return v

        return default

    @classmethod
    def get_url_version_extension(cls, host_url: str) -> str | None:
        """
        Dynamically query GRL software endpoint /api/App/GetURLVersionExtension
        to resolve dynamic version extensions (e.g. 'v1.1.1').
        """
        import urllib.request
        clean_host = host_url.rstrip("/")
        if clean_host.endswith(".html"):
            clean_host = "/".join(clean_host.split("/")[:-1])

        api_url = f"{clean_host}/api/App/GetURLVersionExtension"
        try:
            req = urllib.request.Request(api_url, headers={"User-Agent": "GRL-Automation"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                if resp.status == 200:
                    ver = resp.read().decode("utf-8").strip().strip('"').strip("'")
                    if ver:
                        return ver
        except Exception:
            pass
        return None

    @classmethod
    def base_url(cls) -> str:
        if cls._cached_resolved_url:
            return cls._cached_resolved_url

        raw_url = str(cls.get("BASE_URL", "http://localhost:5003"))
        auto_detect = cls.get("AUTO_DETECT_VERSION", True)

        resolved_url = raw_url

        if auto_detect:
            version = cls.get_url_version_extension(raw_url)
            if version:
                clean_host = raw_url.rstrip("/")
                if clean_host.endswith(".html"):
                    clean_host = "/".join(clean_host.split("/")[:-1])
                resolved_url = f"{clean_host}/{version}.html"

        if not resolved_url.endswith(".html"):
            resolved_url = f"{resolved_url.rstrip('/')}/v1.1.1.html"

        cls._cached_resolved_url = resolved_url
        return cls._cached_resolved_url

    @classmethod
    def dut_ip(cls) -> str:
        return str(cls.get("DUT_IP", "192.168.102.76"))

    @classmethod
    def dut_port(cls) -> str:
        return str(cls.get("DUT_PORT", "5003"))

    @classmethod
    def is_headless(cls) -> bool:
        val = cls.get("HEADLESS", False)
        return bool(val)

    @classmethod
    def api_host(cls) -> str:
        """Returns the base API host, e.g. http://localhost:5003"""
        raw_url = str(cls.get("BASE_URL", "http://localhost:5003")).rstrip("/")
        if raw_url.endswith(".html"):
            raw_url = "/".join(raw_url.split("/")[:-1])
        return raw_url

    @classmethod
    def get_api_endpoint(cls, key: str, default: str = "") -> str:
        """
        Returns full URL for configured API key or builds from api_host.
        Supports:
          - Direct alias: get_api_endpoint("sw_version")
          - Controller dot notation: get_api_endpoint("App.GetSoftwareVersion")
          - Controller slash notation: get_api_endpoint("App/GetSoftwareVersion")
          - Endpoint search across all controllers: get_api_endpoint("GetSoftwareVersion")
        """
        inputs = cls.get_inputs()
        apis = inputs.get("GRL-V-DPWR-EPR", {}).get("PD", {}).get("apis", {})
        if key in apis and isinstance(apis[key], str):
            return str(apis[key])

        normalized_key = key.replace("/", ".")
        if "." in normalized_key:
            controller, subkey = normalized_key.split(".", 1)
            if controller in apis and isinstance(apis[controller], dict):
                if subkey in apis[controller]:
                    return str(apis[controller][subkey])

        for val in apis.values():
            if isinstance(val, dict) and key in val:
                return str(val[key])

        if not default and key:
            return f"{cls.api_host()}/api/{key.lstrip('/')}"
        return default


