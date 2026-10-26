"""
Locator health check - run this first against a new GRL software build.

Loads the web UI (read-only: only clicks the left navigation) and reports, for every locator in
Scripts/Helpers/Locators.py, whether it still matches an element. Locators that only exist in a
certain state (popups, open dropdown menus, a connected tester) are reported as "conditional"
instead of failing.

Usage:  python tools/locator_check.py [--headed]
Exit code 1 when an always-present locator is missing.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from playwright.sync_api import sync_playwright  # noqa: E402

from Scripts.Helpers import Locators as L  # noqa: E402
from Scripts.Helpers.config import Config  # noqa: E402
from Scripts.Helpers.popups import PopupGuard  # noqa: E402
from Scripts.Pages.app_page import AppPage  # noqa: E402

# Present only in some states: open popup, open dropdown, connected tester, empty plot, ...
CONDITIONAL = {
    "AppLocators.POPUP", "AppLocators.POPUP_TITLE", "AppLocators.POPUP_MESSAGE", "AppLocators.POPUP_INPUT",
    "AppLocators.POPUP_BUTTONS", "AppLocators.POPUP_OK", "AppLocators.POPUP_CANCEL",
    "TestConfigLocators.TEST_TREE", "TestConfigLocators.TREE_SUITE_NODE", "TestConfigLocators.TREE_NODE",
    "TestConfigLocators.TREE_NODE_LABEL", "ConnectionLocators.LICENSE_ROWS",
}
CLASSES = ["AppLocators", "NavigationLocators", "ConnectionLocators", "ProductCapLocators", "TestConfigLocators",
           "ResultsLocators", "ReportLocators", "ConfigureLocators", "LoopBackLocators", "HelpLocators"]


def collect() -> list[tuple[str, str]]:
    found = []
    for cls_name in CLASSES:
        cls = getattr(L, cls_name)
        for attr, value in vars(cls).items():
            if attr.startswith("_") or not attr.isupper():
                continue
            if isinstance(value, str):
                found.append((f"{cls_name}.{attr}", value))
            elif isinstance(value, dict):
                found += [(f"{cls_name}.{attr}[{k}]", v) for k, v in value.items() if isinstance(v, str)]
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args()

    locators = collect()
    missing, conditional, ok = [], [], 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        PopupGuard(page).install()
        app = AppPage(page).load()
        print(f"GRL software {app.header_version()} at {page.url}\n")
        for name, selector in locators:
            try:
                count = page.locator(selector).count()
            except Exception as e:  # invalid selector syntax
                missing.append((name, selector, f"invalid selector: {e}".splitlines()[0]))
                continue
            if count:
                ok += 1
            elif name.split("[")[0] in CONDITIONAL:
                conditional.append((name, selector))
            else:
                missing.append((name, selector, "no match"))
        browser.close()

    print(f"OK: {ok}   missing: {len(missing)}   conditional (not checked in this state): {len(conditional)}")
    for name, selector, why in missing:
        print(f"  MISSING  {name:55s} {selector}  ({why})")
    for name, selector in conditional:
        print(f"  cond.    {name:55s} {selector}")
    return 1 if missing else 0


if __name__ == "__main__":
    Config.base_url()  # resolve the versioned page once
    sys.exit(main())
