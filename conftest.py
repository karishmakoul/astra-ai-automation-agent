import pytest
from core.driver.driver_factory import DriverFactory
from core.driver.driver_manager import DriverManager
from pages.ambitionbox.home_page import HomePage
from pages.ambitionbox.companies_page import CompaniesPage
from pages.ambitionbox.reviews_page import ReviewsPage
from pages.ambitionbox.salaries_page import SalariesPage
from pages.ambitionbox.interviews_page import InterviewsPage
from pages.ambitionbox.jobs_page import JobsPage
from components.nav import LeftNav
from components.search_bar import SearchBar
from components.filter_panel import FilterPanel
from components.company_card import CompanyCard


# ── pytest hook — makes rep_call available in fixtures ─────────────────────
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


# ── Driver lifecycle — one browser per test function ───────────────────────
@pytest.fixture()
def driver():
    """Boots the browser, registers in singleton, tears down after test."""
    d = DriverFactory.get_driver()
    DriverManager().set_driver(d)
    yield d
    DriverManager().quit_driver()


# ── Raw Playwright page (derived from driver) ──────────────────────────────
@pytest.fixture()
def pw_page(driver):
    """Raw Playwright Page object — used by components that need it directly."""
    return driver.page


# ── Screenshot on failure (attached to Allure) ─────────────────────────────
@pytest.fixture(autouse=True)
def screenshot_on_failure(request, driver):
    yield
    if request.node.rep_call and request.node.rep_call.failed:
        try:
            import allure
            from utils.config import Config
            if Config.SCREENSHOT_ON_FAILURE:
                shot = driver.take_screenshot(request.node.name)
                allure.attach(shot, name=f"FAIL_{request.node.name}",
                              attachment_type=allure.attachment_type.PNG)
        except Exception:
            pass


# ── Page object fixtures ────────────────────────────────────────────────────
@pytest.fixture()
def home_page(pw_page) -> HomePage:
    page = HomePage()
    page.open()
    return page


@pytest.fixture()
def companies_page(pw_page) -> CompaniesPage:
    page = CompaniesPage()
    page.open()
    return page


@pytest.fixture()
def reviews_page(pw_page) -> ReviewsPage:
    return ReviewsPage()


@pytest.fixture()
def salaries_page(pw_page) -> SalariesPage:
    page = SalariesPage()
    page.open()
    return page


@pytest.fixture()
def interviews_page(pw_page) -> InterviewsPage:
    page = InterviewsPage()
    page.open()
    return page


@pytest.fixture()
def jobs_page(pw_page) -> JobsPage:
    page = JobsPage()
    page.open()
    return page


# ── Component fixtures (reusable across any page) ──────────────────────────
@pytest.fixture()
def left_nav(pw_page) -> LeftNav:
    return LeftNav(pw_page)


@pytest.fixture()
def search_bar(pw_page) -> SearchBar:
    return SearchBar(pw_page)


@pytest.fixture()
def filter_panel(pw_page) -> FilterPanel:
    return FilterPanel(pw_page)


@pytest.fixture()
def company_card(pw_page) -> CompanyCard:
    return CompanyCard(pw_page)
