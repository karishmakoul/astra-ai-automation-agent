import allure
from core.base_page import BasePage


class CompaniesPage(BasePage):
    """
    Page object for https://www.ambitionbox.com/list-of-companies
    """

    URL_PATH = "/list-of-companies"

    # --- Locators ---
    SEARCH_BAR = '[data-testid="desktop-typeahead"]'
    SEARCH_INPUT = '[data-testid="desktop-typeahead"] input'
    COMPANY_CARD_LINKS = 'a[href*="/reviews/"]'
    PAGE_HEADING = 'h1'

    # --- Actions ---

    @allure.step("Open Companies listing page")
    def open(self):
        self.navigate(self.URL_PATH)
        self.wait_for_visible(self.SEARCH_BAR)
        # Allow Vue filter components to fully initialize
        self.page.wait_for_timeout(2000)
        return self

    @allure.step("Search for company: {company_name}")
    def search_company(self, company_name: str):
        self.click(self.SEARCH_BAR, "Search bar")
        self.fill(self.SEARCH_INPUT, company_name, "Company search input")
        self.press_key(self.SEARCH_INPUT, "Enter")
        return self

    @allure.step("Get all visible company names")
    def get_company_names(self) -> list[str]:
        self.wait_for_visible(self.COMPANY_CARD_LINKS)
        return self.get_all_texts(self.COMPANY_CARD_LINKS)

    @allure.step("Get count of company cards")
    def get_company_count(self) -> int:
        return self.get_count(self.COMPANY_CARD_LINKS)

    @allure.step("Click on company: {company_name}")
    def click_company(self, company_name: str):
        locator = f'a[href*="/reviews/"]:has-text("{company_name}")'
        self.click(locator, f"Company card: {company_name}")
        return self

    # --- Assertions ---

    @allure.step("Assert companies page is loaded")
    def assert_page_loaded(self):
        self.assert_visible(self.SEARCH_BAR, "Search bar")
        self.assert_url_contains("list-of-companies")

    @allure.step("Assert at least {min_count} companies are listed")
    def assert_companies_listed(self, min_count: int = 1):
        count = self.get_company_count()
        assert count >= min_count, (
            f"Expected at least {min_count} company cards, found {count}"
        )
