"""Unit tests for popup classification and per-test tracking."""
from Scripts.Helpers.popups import PopupGuard, PopupRecord


def _rec(message, title="GRL-V-DPWR-EPR"):
    return PopupRecord(title=title, message=message, buttons=["Ok"], auto_dismissed=True)


def test_connectivity_alerts_are_recognised():
    assert _rec("Error detected in ethernet communication. Check the ethernet connectivity").is_connectivity_alert
    assert _rec("The controller calibration has expired.", "Controller Calibration Alert").is_connectivity_alert
    assert not _rec("Error: invalid marker position").is_connectivity_alert


def test_errors_in_test_only_counts_current_test_and_skips_connectivity():
    guard = PopupGuard(page=None)  # page is not used by the bookkeeping
    guard.seen.append(_rec("Error: from an earlier test"))
    guard.start_test()
    guard.seen.append(_rec("Error detected in ethernet communication"))
    assert guard.errors_in_test() == []
    guard.seen.append(_rec("Error: zoom failed"))
    assert [p.message for p in guard.errors_in_test()] == ["Error: zoom failed"]
