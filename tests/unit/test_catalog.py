"""Unit tests for test discovery (GUI) and specification traceability."""
import importlib.util
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load_traceability():
    spec = importlib.util.spec_from_file_location("traceability", ROOT / "tools" / "traceability.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["traceability"] = module  # dataclasses resolve their module through sys.modules
    spec.loader.exec_module(module)
    return module


def test_gui_discovers_every_test_module():
    pytest.importorskip("PyQt6")
    from Scripts.UI.app import discover_tests

    suites = discover_tests()
    files = {s.file.rsplit("/", 1)[-1] for s in suites}
    assert files == {p.name for p in (ROOT / "Scripts" / "TestCases").glob("test_*.py")}
    names = [s.short_name for s in suites]
    assert "Connection Setup" in names and "REST API" in names
    hw = [t for s in suites for t in s.tests if "hardware" in t.markers]
    assert hw, "hardware-marked tests should be discovered with their markers"
    assert not any("spec" in t.markers for s in suites for t in s.tests), "spec is not a user-facing tag"


def test_spec_ids_are_unique_and_complete():
    trace = _load_traceability()
    items = trace.load_spec()
    assert len(items) > 150
    assert len({i.id for i in items.values()}) == len(items)
    assert set(trace.SECTION_PREFIX) == {i.section for i in items.values()}


def test_tests_only_reference_existing_spec_ids():
    trace = _load_traceability()
    _, unknown = trace.build()
    assert not unknown, f"Tests reference unknown spec IDs: {unknown}"
