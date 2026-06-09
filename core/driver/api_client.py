import httpx
from utils.config import Config
from utils.logger import get_logger

log = get_logger(__name__)


class APIClient:
    """
    Wraps httpx for API testing.
    Shares the same interface contract as WebDriver so DriverFactory
    can return either without the caller caring which one it got.
    """

    def __init__(self):
        self._client: httpx.Client = None

    def start(self) -> "APIClient":
        log.info(f"Starting API client | base_url={Config.BASE_URL}")
        self._client = httpx.Client(
            base_url=Config.BASE_URL,
            timeout=Config.TIMEOUT / 1000,  # httpx uses seconds, not ms
            headers={"Content-Type": "application/json"},
        )
        return self

    def quit(self):
        log.info("Closing API client")
        if self._client:
            self._client.close()

    def get(self, endpoint: str, **kwargs) -> httpx.Response:
        log.debug(f"GET {endpoint}")
        response = self._client.get(endpoint, **kwargs)
        log.debug(f"Response: {response.status_code}")
        return response

    def post(self, endpoint: str, **kwargs) -> httpx.Response:
        log.debug(f"POST {endpoint}")
        response = self._client.post(endpoint, **kwargs)
        log.debug(f"Response: {response.status_code}")
        return response

    def put(self, endpoint: str, **kwargs) -> httpx.Response:
        log.debug(f"PUT {endpoint}")
        response = self._client.put(endpoint, **kwargs)
        log.debug(f"Response: {response.status_code}")
        return response

    def delete(self, endpoint: str, **kwargs) -> httpx.Response:
        log.debug(f"DELETE {endpoint}")
        response = self._client.delete(endpoint, **kwargs)
        log.debug(f"Response: {response.status_code}")
        return response

    @property
    def page(self):
        raise NotImplementedError("API client has no page. Use get/post/put/delete methods.")
