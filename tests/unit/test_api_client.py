"""Unit tests for the API client's safety rails."""
import re

import pytest

from Scripts.Helpers.api_client import READ_ONLY_GET_ENDPOINTS, C2ApiClient

RISKY = re.compile(r"^(Set|Clear|Delete|Stop|Start|Update|Discover|Scan|Save|Try|Generate|Force|Send|Attach|Detach"
                   r"|Download|Reset|Write|Put|Post)|OnScan$|Flip$", re.IGNORECASE)


def test_read_only_list_has_no_risky_names():
    """The action name (after an optional 'Get') must not start with a state-changing verb."""
    # 'GetConfigSendMessage' only reads the stored message configuration
    allowed = {"api/ConfigControl/GetConfigSendMessage"}
    risky = [e for e in READ_ONLY_GET_ENDPOINTS
             if e not in allowed and RISKY.search(e.rsplit("/", 1)[-1].removeprefix("Get"))]
    assert not risky, f"Endpoints that look state-changing in the read-only list: {risky}"


def test_read_only_list_is_unique():
    assert len(set(READ_ONLY_GET_ENDPOINTS)) == len(READ_ONLY_GET_ENDPOINTS)


def test_get_raw_refuses_unlisted_endpoints():
    client = C2ApiClient(base_url="http://127.0.0.1:9")
    with pytest.raises(ValueError, match="not in READ_ONLY_GET_ENDPOINTS"):
        client.get_raw("api/ReportsGeneration/GetDeleteAllTestData")


@pytest.mark.parametrize("dangerous", ["api/ReportsGeneration/GetDeleteAllTestData", "api/App/GetUpdateSystemFirmware",
                                       "api/C2Api/SetQCVoltageIncrementRequest_200mV", "api/TestConfiguration/GetEloadsOnScan"])
def test_risky_rule_catches_known_dangerous_gets(dangerous):
    assert RISKY.search(dangerous.rsplit("/", 1)[-1].removeprefix("Get"))
