from core.driver.web_driver import WebDriver
from core.driver.api_client import APIClient
from utils.logger import get_logger

log = get_logger(__name__)

# Registry maps platform name → driver class
# Adding a new platform = adding one line here, nothing else changes
_DRIVER_REGISTRY = {
    "web": WebDriver,
    "api": APIClient,
    # "app": AppDriver,  # plug in when mobile support is needed
}


class DriverFactory:
    """
    Factory Pattern: creates and returns the correct driver based on platform.
    Callers never import WebDriver or APIClient directly — only DriverFactory.
    """

    @staticmethod
    def get_driver(platform: str = None):
        from utils.config import Config

        platform = (platform or Config.PLATFORM).lower()
        driver_class = _DRIVER_REGISTRY.get(platform)

        if not driver_class:
            available = list(_DRIVER_REGISTRY.keys())
            raise ValueError(
                f"Unknown platform: '{platform}'. Available: {available}"
            )

        log.info(f"DriverFactory: creating driver for platform='{platform}'")
        return driver_class().start()
