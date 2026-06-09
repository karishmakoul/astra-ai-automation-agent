import allure
from playwright.sync_api import Page, Locator, expect
from core.driver.driver_manager import DriverManager
from utils.logger import get_logger

log = get_logger(__name__)


class BasePage:
    """
    Parent class for all page objects.
    Wraps Playwright interactions with logging, Allure steps, and smart waits.
    Page objects never call self.page.locator() directly — they use these methods.
    """

    def __init__(self):
        self.driver_manager = DriverManager()
        self.page: Page = self.driver_manager.get_driver().page

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def dismiss_overlay(self):
        """Dismiss any coachmark / tutorial overlay that blocks clicks."""
        overlay_sel = '[data-testid*="coachmark-overlay"]'
        overlay = self.page.locator(overlay_sel).first
        if overlay.is_visible():
            overlay.click(force=True)
            # Wait until the overlay is gone
            try:
                self.page.locator(overlay_sel).wait_for(state="hidden", timeout=3000)
            except Exception:
                pass

    def navigate(self, path: str = ""):
        url = path if path.startswith("http") else f"{path}"
        log.info(f"Navigating to: {url}")
        with allure.step(f"Navigate to {url}"):
            self.page.goto(url, wait_until="domcontentloaded")
            self.page.wait_for_timeout(500)
            self.dismiss_overlay()

    def get_current_url(self) -> str:
        return self.page.url

    def get_title(self) -> str:
        return self.page.title()

    def go_back(self):
        log.debug("Navigating back")
        with allure.step("Go back"):
            self.page.go_back()

    def refresh(self):
        log.debug("Refreshing page")
        with allure.step("Refresh page"):
            self.page.reload(wait_until="domcontentloaded")

    # ------------------------------------------------------------------
    # Element retrieval
    # ------------------------------------------------------------------

    def get_element(self, locator: str) -> Locator:
        return self.page.locator(locator)

    def get_elements(self, locator: str) -> Locator:
        return self.page.locator(locator)

    # ------------------------------------------------------------------
    # Interactions
    # ------------------------------------------------------------------

    def click(self, locator: str, description: str = ""):
        label = description or locator
        log.info(f"Clicking: {label}")
        with allure.step(f"Click '{label}'"):
            self.page.locator(locator).click()

    def click_with_js(self, locator: str, description: str = ""):
        """Fallback click via JavaScript — for elements blocked by overlays."""
        label = description or locator
        log.info(f"JS click: {label}")
        with allure.step(f"JS Click '{label}'"):
            self.page.locator(locator).evaluate("el => el.click()")

    def fill(self, locator: str, value: str, description: str = ""):
        label = description or locator
        log.info(f"Filling '{label}' with: {value}")
        with allure.step(f"Fill '{label}' → '{value}'"):
            self.page.locator(locator).fill(value)

    def clear_and_fill(self, locator: str, value: str, description: str = ""):
        label = description or locator
        log.info(f"Clear and fill '{label}' with: {value}")
        with allure.step(f"Clear and fill '{label}' → '{value}'"):
            self.page.locator(locator).clear()
            self.page.locator(locator).fill(value)

    def press_key(self, locator: str, key: str):
        log.debug(f"Pressing key '{key}' on: {locator}")
        with allure.step(f"Press '{key}'"):
            self.page.locator(locator).press(key)

    def select_option(self, locator: str, value: str, description: str = ""):
        label = description or locator
        log.info(f"Selecting '{value}' in: {label}")
        with allure.step(f"Select '{value}' in '{label}'"):
            self.page.locator(locator).select_option(value)

    def hover(self, locator: str, description: str = ""):
        label = description or locator
        log.debug(f"Hovering on: {label}")
        with allure.step(f"Hover '{label}'"):
            self.page.locator(locator).hover()

    def scroll_into_view(self, locator: str):
        log.debug(f"Scrolling into view: {locator}")
        self.page.locator(locator).scroll_into_view_if_needed()

    def scroll_to_bottom(self):
        log.debug("Scrolling to page bottom")
        with allure.step("Scroll to page bottom"):
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

    # ------------------------------------------------------------------
    # Waits
    # ------------------------------------------------------------------

    def wait_for_visible(self, locator: str, timeout: int = None):
        log.debug(f"Waiting for visible: {locator}")
        kwargs = {"state": "visible"}
        if timeout:
            kwargs["timeout"] = timeout
        self.page.locator(locator).wait_for(**kwargs)

    def wait_for_hidden(self, locator: str, timeout: int = None):
        log.debug(f"Waiting for hidden: {locator}")
        kwargs = {"state": "hidden"}
        if timeout:
            kwargs["timeout"] = timeout
        self.page.locator(locator).wait_for(**kwargs)

    def wait_for_url(self, url_pattern: str):
        log.debug(f"Waiting for URL: {url_pattern}")
        self.page.wait_for_url(url_pattern)

    def wait_for_load(self):
        self.page.wait_for_load_state("domcontentloaded")

    # ------------------------------------------------------------------
    # Reading values
    # ------------------------------------------------------------------

    def get_text(self, locator: str) -> str:
        text = self.page.locator(locator).inner_text()
        log.debug(f"Text of '{locator}': {text}")
        return text

    def get_attribute(self, locator: str, attribute: str) -> str:
        return self.page.locator(locator).get_attribute(attribute)

    def get_value(self, locator: str) -> str:
        return self.page.locator(locator).input_value()

    def get_all_texts(self, locator: str) -> list[str]:
        return self.page.locator(locator).all_inner_texts()

    def get_count(self, locator: str) -> int:
        return self.page.locator(locator).count()

    # ------------------------------------------------------------------
    # State checks
    # ------------------------------------------------------------------

    def is_visible(self, locator: str) -> bool:
        return self.page.locator(locator).is_visible()

    def is_enabled(self, locator: str) -> bool:
        return self.page.locator(locator).is_enabled()

    def is_checked(self, locator: str) -> bool:
        return self.page.locator(locator).is_checked()

    # ------------------------------------------------------------------
    # Assertions (use Playwright's built-in auto-retry assertions)
    # ------------------------------------------------------------------

    def assert_visible(self, locator: str, message: str = ""):
        log.debug(f"Assert visible: {locator}")
        with allure.step(f"Assert visible: {message or locator}"):
            expect(self.page.locator(locator)).to_be_visible()

    def assert_hidden(self, locator: str, message: str = ""):
        log.debug(f"Assert hidden: {locator}")
        with allure.step(f"Assert hidden: {message or locator}"):
            expect(self.page.locator(locator)).to_be_hidden()

    def assert_text(self, locator: str, expected: str):
        log.debug(f"Assert text '{expected}' in: {locator}")
        with allure.step(f"Assert text = '{expected}'"):
            expect(self.page.locator(locator)).to_have_text(expected)

    def assert_text_contains(self, locator: str, expected: str):
        log.debug(f"Assert text contains '{expected}' in: {locator}")
        with allure.step(f"Assert text contains '{expected}'"):
            expect(self.page.locator(locator)).to_contain_text(expected)

    def assert_url_contains(self, partial_url: str):
        import re
        log.debug(f"Assert URL contains: {partial_url}")
        with allure.step(f"Assert URL contains '{partial_url}'"):
            expect(self.page).to_have_url(re.compile(re.escape(partial_url)))

    def assert_title_contains(self, partial_title: str):
        log.debug(f"Assert title contains: {partial_title}")
        with allure.step(f"Assert title contains '{partial_title}'"):
            expect(self.page).to_have_title(f"*{partial_title}*")

    def assert_count(self, locator: str, expected_count: int):
        log.debug(f"Assert count {expected_count} for: {locator}")
        with allure.step(f"Assert count = {expected_count}"):
            expect(self.page.locator(locator)).to_have_count(expected_count)

    # ------------------------------------------------------------------
    # Screenshot
    # ------------------------------------------------------------------

    def take_screenshot(self, name: str = "screenshot") -> bytes:
        return self.driver_manager.get_driver().take_screenshot(name)
