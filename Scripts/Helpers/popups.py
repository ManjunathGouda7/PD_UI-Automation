"""
Handling of the application's custom popups (`.modal-backdrop .custom-scroll-popup`).

The C2 UI raises informational alerts at arbitrary times (e.g. "Controller Calibration
Alert", "V-DPWR-EPR Path Update"). They cover the whole page and intercept every click.
PopupGuard registers a Playwright locator handler that:
  * auto-acknowledges popups that have a single "Ok" button (pure information), and
  * never touches popups with more than one button (confirmations / prompts such as
    "Download File ... Ok / Cancel"), because pressing Ok there performs an action.
Every popup seen is recorded so tests and reports can show what the app reported.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from playwright.sync_api import Locator, Page

from Scripts.Helpers.Locators import AppLocators
from Scripts.Helpers.logger import logger


@dataclass
class PopupRecord:
    title: str
    message: str
    buttons: list[str]
    auto_dismissed: bool


@dataclass
class PopupGuard:
    page: Page
    seen: list[PopupRecord] = field(default_factory=list)
    _installed: bool = False

    def install(self) -> PopupGuard:
        if not self._installed:
            self.page.add_locator_handler(
                self.page.locator(AppLocators.POPUP_OK),
                self._on_popup,
                no_wait_after=True,
            )
            self._installed = True
        return self

    def read_current(self) -> PopupRecord | None:
        popup = self.page.locator(AppLocators.POPUP).first
        if not popup.is_visible():
            return None
        title = self._safe_text(self.page.locator(AppLocators.POPUP_TITLE).first)
        message = self._safe_text(self.page.locator(AppLocators.POPUP_MESSAGE).first)
        if not message:
            message = self._safe_text(popup)
        buttons = [b.strip() for b in self.page.locator(AppLocators.POPUP_BUTTONS).all_inner_texts()]
        return PopupRecord(title=title, message=message, buttons=buttons, auto_dismissed=False)

    def dismiss_informational(self, max_popups: int = 5) -> list[PopupRecord]:
        """Explicitly acknowledges any stacked single-button popups (used after page load)."""
        dismissed: list[PopupRecord] = []
        for _ in range(max_popups):
            record = self.read_current()
            if record is None or len(record.buttons) != 1:
                break
            self._acknowledge(record)
            dismissed.append(record)
        return dismissed

    def _on_popup(self, _ok: Locator | None = None) -> None:
        record = self.read_current()
        if record is None:
            return
        if len(record.buttons) == 1:
            self._acknowledge(record)
            return
        if not self.seen or self.seen[-1] != record:
            logger.warning(
                f"Confirmation popup left for the test to answer: "
                f"'{record.title}' - {record.message!r} buttons={record.buttons}"
            )
            self.seen.append(record)

    def _acknowledge(self, record: PopupRecord) -> None:
        record.auto_dismissed = True
        self.seen.append(record)
        logger.warning(f"App popup acknowledged: '{record.title}' - {record.message!r}")
        # Track this specific button: popups can stack, so `.first` may re-resolve to the next one.
        handle = self.page.locator(AppLocators.POPUP_OK).first.element_handle(timeout=2000)
        if handle is None:
            return
        handle.click()
        handle.wait_for_element_state("hidden", timeout=5000)

    @staticmethod
    def _safe_text(locator: Locator) -> str:
        try:
            if locator.count():
                return " ".join(locator.inner_text(timeout=1000).split())
        except Exception:
            pass
        return ""
