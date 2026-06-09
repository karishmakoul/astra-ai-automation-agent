import allure
from core.base_page import BasePage


class HomePage(BasePage):
    """
    Page object for https://www.ambitionbox.com (home page).
    All locators use data-testid where available — most stable against UI changes.
    """

    # --- Locators ---
    SEARCH_BAR = '[data-testid="desktop-typeahead"]'
    SEARCH_INPUT = '[data-testid="desktop-typeahead"] input'
    LOGIN_BUTTON = '#ab_main-header [data-testid="login"]'
    NAV_HOME = '[data-testid="nav-group-link-home"]'
    NAV_COMPANIES = '[data-testid="nav-group-link-companies"]'
    NAV_REVIEWS = '[data-testid="nav-group-link-reviews"]'
    NAV_SALARIES = '[data-testid="nav-group-link-salaries"]'
    NAV_INTERVIEWS = '[data-testid="nav-group-link-interview-questions"]'
    NAV_JOBS = '[data-testid="nav-group-link-jobs"]'
    LEFT_NAV = '[data-testid="left-navigation-bar"]'

    # --- Actions ---

    @allure.step("Open AmbitionBox home page")
    def open(self):
        self.navigate("/")
        self.wait_for_visible(self.SEARCH_BAR)
        return self

    @allure.step("Search for: {query}")
    def search(self, query: str):
        self.click(self.SEARCH_BAR, "Search bar")
        self.fill(self.SEARCH_INPUT, query, "Search input")
        self.press_key(self.SEARCH_INPUT, "Enter")
        return self

    @allure.step("Click Login button")
    def click_login(self):
        self.click(self.LOGIN_BUTTON, "Login button")
        return self

    @allure.step("Navigate to Companies via left nav")
    def go_to_companies(self):
        self.click(self.NAV_COMPANIES, "Companies nav link")
        return self

    @allure.step("Navigate to Reviews via left nav")
    def go_to_reviews(self):
        self.click(self.NAV_REVIEWS, "Reviews nav link")
        return self

    @allure.step("Navigate to Salaries via left nav")
    def go_to_salaries(self):
        self.click(self.NAV_SALARIES, "Salaries nav link")
        return self

    @allure.step("Navigate to Interview Questions via left nav")
    def go_to_interviews(self):
        self.click(self.NAV_INTERVIEWS, "Interview Questions nav link")
        return self

    @allure.step("Navigate to Jobs via left nav")
    def go_to_jobs(self):
        self.click(self.NAV_JOBS, "Jobs nav link")
        return self

    # --- Assertions ---

    @allure.step("Assert home page is loaded")
    def assert_page_loaded(self):
        self.assert_visible(self.SEARCH_BAR, "Search bar")
        self.assert_visible(self.LEFT_NAV, "Left navigation bar")
        self.assert_visible(self.LOGIN_BUTTON, "Login button")

    @allure.step("Assert all nav links are visible")
    def assert_nav_links_visible(self):
        self.assert_visible(self.NAV_HOME, "Home nav link")
        self.assert_visible(self.NAV_COMPANIES, "Companies nav link")
        self.assert_visible(self.NAV_REVIEWS, "Reviews nav link")
        self.assert_visible(self.NAV_SALARIES, "Salaries nav link")
        self.assert_visible(self.NAV_INTERVIEWS, "Interview Questions nav link")
        self.assert_visible(self.NAV_JOBS, "Jobs nav link")

    @allure.step("Assert login button is visible")
    def assert_login_button_visible(self):
        self.assert_visible(self.LOGIN_BUTTON, "Login button")
