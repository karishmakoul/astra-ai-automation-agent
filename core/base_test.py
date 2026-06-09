import allure
import pytest
from core.driver.driver_factory import DriverFactory
from core.driver.driver_manager import DriverManager
from utils.logger import get_logger

log = get_logger(__name__)


class BaseTest:
    """
    Parent class for all test classes.
    Handles driver setup/teardown and screenshot capture on failure.
    Every test class inherits this — no boilerplate needed in individual tests.
    """

    @pytest.fixture(autouse=True)
    def setup_driver(self, request):
        """
        autouse=True — runs automatically for every test in any class that inherits BaseTest.
        Yields to the test, then tears down after.
        """
        log.info(f"--- START: {request.node.name} ---")

        driver = DriverFactory.get_driver()
        DriverManager().set_driver(driver)

        yield  # test runs here

        # --- Teardown ---
        if request.node.rep_call and request.node.rep_call.failed:
            self._capture_failure_screenshot(request.node.name)

        DriverManager().quit_driver()
        log.info(f"--- END: {request.node.name} ---")

    def _capture_failure_screenshot(self, test_name: str):
        from utils.config import Config
        if not Config.SCREENSHOT_ON_FAILURE:
            return
        try:
            driver = DriverManager().get_driver()
            screenshot_bytes = driver.take_screenshot(test_name)
            allure.attach(
                screenshot_bytes,
                name=f"failure_{test_name}",
                attachment_type=allure.attachment_type.PNG,
            )
            log.info(f"Failure screenshot attached to Allure: {test_name}")
        except Exception as e:
            log.warning(f"Could not capture screenshot: {e}")


# Pytest hook — makes request.node.rep_call available in fixtures
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
