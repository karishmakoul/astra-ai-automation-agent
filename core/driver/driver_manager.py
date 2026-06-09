from utils.logger import get_logger

log = get_logger(__name__)


class DriverManager:
    """
    Singleton Pattern: guarantees one driver instance per test session.
    All page objects call DriverManager.get_driver() — they all get the same object.
    """

    _instance = None
    _driver = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            log.debug("DriverManager instance created")
        return cls._instance

    def set_driver(self, driver):
        self._driver = driver
        log.debug(f"DriverManager: driver set → {type(driver).__name__}")

    def get_driver(self):
        if self._driver is None:
            raise RuntimeError(
                "Driver not initialised. "
                "Ensure conftest.py calls DriverManager().set_driver() before tests run."
            )
        return self._driver

    def quit_driver(self):
        if self._driver:
            self._driver.quit()
            self._driver = None
            log.debug("DriverManager: driver quit and cleared")

    @classmethod
    def reset(cls):
        """Clears the singleton — used between test sessions in the same process."""
        cls._instance = None
        cls._driver = None
