from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from utils.config import Config
from utils.logger import get_logger

log = get_logger(__name__)


class WebDriver:
    """
    Wraps Playwright browser lifecycle.
    One instance per test session — managed by DriverManager (Singleton).
    """

    def __init__(self):
        self._playwright = None
        self._browser: Browser = None
        self._context: BrowserContext = None
        self._page: Page = None

    def start(self) -> "WebDriver":
        log.info(f"Starting browser: {Config.BROWSER} | headless={Config.HEADLESS}")
        self._playwright = sync_playwright().start()

        browser_launcher = getattr(self._playwright, Config.BROWSER)
        self._browser = browser_launcher.launch(
            headless=Config.HEADLESS,
            slow_mo=Config.SLOW_MO,
        )
        self._context = self._browser.new_context(
            base_url=Config.BASE_URL,
            viewport={"width": 1440, "height": 900},
            record_video_dir="reports/videos/" if Config.VIDEO_ON_FAILURE else None,
        )
        self._context.set_default_timeout(Config.TIMEOUT)
        self._page = self._context.new_page()
        log.info("Browser started successfully")
        return self

    def quit(self):
        log.info("Closing browser")
        if self._page:
            self._page.close()
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    def take_screenshot(self, name: str = "screenshot") -> bytes:
        path = f"reports/screenshots/{name}.png"
        self._page.screenshot(path=path, full_page=True)
        log.info(f"Screenshot saved: {path}")
        return self._page.screenshot(full_page=True)

    @property
    def page(self) -> Page:
        if not self._page:
            raise RuntimeError("Browser not started. Call start() first.")
        return self._page
