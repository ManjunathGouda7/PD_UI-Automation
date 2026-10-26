"""Unit tests for Scripts.Helpers.swagger_contract."""
from Scripts.Helpers.swagger_contract import SwaggerContract

SPEC = {
    "paths": {
        "/api/App/GetAppState": {"get": {"responses": {"200": {"schema": {"$ref": "#/definitions/State"}}}}},
        "/api/ConnectionSetup/{controllerIndex}/{IpAddress}": {"get": {}},
    },
    "definitions": {
        "State": {"type": "object", "properties": {
            "appState": {"type": "string", "enum": ["READY", "BUSY"]},
            "count": {"type": "integer"},
            "items": {"type": "array", "items": {"$ref": "#/definitions/Item"}},
        }},
        "Item": {"type": "object", "properties": {"ok": {"type": "boolean"}}},
    },
}


def test_valid_response_has_no_errors():
    c = SwaggerContract(SPEC)
    value = {"appState": "READY", "count": 2, "items": [{"ok": True}]}
    assert c.validate(value, c.response_schema("/api/App/GetAppState")) == []


def test_reports_type_enum_and_nested_errors():
    c = SwaggerContract(SPEC)
    value = {"appState": "BROKEN", "count": "2", "items": [{"ok": "yes"}]}
    errors = c.validate(value, c.response_schema("/api/App/GetAppState"))
    assert any("$.appState" in e and "enum" in e for e in errors)
    assert any("$.count" in e and "integer" in e for e in errors)
    assert any("$.items[0].ok" in e and "boolean" in e for e in errors)


def test_bool_is_not_accepted_as_integer_and_null_is_tolerated():
    c = SwaggerContract(SPEC)
    assert c.validate(True, {"type": "integer"})
    assert c.validate(None, {"type": "integer"}) == []


def test_has_operation_ignores_case_and_param_names():
    c = SwaggerContract(SPEC)
    assert c.has_operation("GET", "api/app/getappstate")
    assert c.has_operation("GET", "api/ConnectionSetup/{controller_index}/{ip_address}")
    assert not c.has_operation("POST", "api/App/GetAppState")
    assert not c.has_operation("GET", "api/App/Missing")
