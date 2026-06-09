import re
import allure
from core.base_page import BasePage


class SalariesPage(BasePage):
    """Page object for /salaries and company-specific salary pages."""

    URL_PATH         = "/salaries"
    SEARCH_CONTAINER = '[data-testid="desktop-typeahead"]'
    SEARCH_INPUT     = '[data-testid="desktop-typeahead"] input'
    SALARY_CARDS     = '[class*="salaryCard"], [class*="salary-card"]'
    UNLOCK_BTN       = 'text=Unlock'
    LOGIN_WALL       = 'text=Login to view'
    POPULAR_ROLES    = '[class*="popularRole"], a[href*="/salaries/"]'
    CALC_COMPANY     = 'input[placeholder*="Company"]'
    CALC_DESIGNATION = 'input[placeholder*="Designation"]'
    CALC_SALARY      = 'input[placeholder*="Annual Salary"], input[placeholder*="salary"]'
    CALC_BTN         = 'button:has-text("Calculate")'

    def open(self):
        self.navigate(self.URL_PATH)
        self.wait_for_load()
        self.page.wait_for_timeout(2000)
        return self

    def open_company(self, company_slug: str):
        self.navigate(f"/salaries/{company_slug}-salaries")
        self.wait_for_load()
        self.page.wait_for_timeout(2000)
        return self

    @allure.step("Search salary for: '{designation}'")
    def search_designation(self, designation: str):
        self.page.locator(self.SEARCH_CONTAINER).click()
        self.page.locator(self.SEARCH_INPUT).fill(designation)
        self.page.wait_for_timeout(600)
        self.page.locator(self.SEARCH_INPUT).press("Enter")
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(2000)

    @allure.step("Get salary range texts from visible cards")
    def get_salary_ranges(self) -> list[str]:
        """Returns all salary range strings (e.g. '₹9L–₹10L') visible on page."""
        texts = self.page.evaluate("""() =>
            [...document.querySelectorAll('*')]
            .map(e => e.innerText)
            .filter(t => t.match(/₹[0-9]+/))
            .slice(0, 20)
        """)
        return texts

    @allure.step("Get page text for salary data validation")
    def get_page_salary_text(self) -> str:
        return self.page.evaluate("() => document.body.innerText")

    @allure.step("Click Popular Role: '{role}'")
    def click_popular_role(self, role: str):
        self.page.locator(f'text={role}').first.click()
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(1500)

    @allure.step("Select department: '{department}'")
    def select_department(self, department: str):
        self.page.locator(f'text={department}').first.click()
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(1500)

    @allure.step("Use salary calculator: company={company}, role={role}, ctc={ctc}")
    def calculate_salary(self, company: str, role: str, ctc: str) -> str:
        self.page.locator(self.CALC_COMPANY).fill(company)
        self.page.wait_for_timeout(400)
        self.page.locator(self.CALC_DESIGNATION).fill(role)
        self.page.wait_for_timeout(400)
        self.page.locator(self.CALC_SALARY).fill(ctc)
        self.page.locator(self.CALC_BTN).click()
        self.page.wait_for_timeout(2000)
        return self.page.evaluate("() => document.body.innerText").strip()

    @allure.step("Assert login wall is shown for salary unlock")
    def assert_login_wall_shown(self):
        login_wall = self.page.locator(self.LOGIN_WALL).or_(self.page.locator(self.UNLOCK_BTN))
        assert login_wall.first.is_visible(), "Expected login wall or Unlock button to be visible"

    @allure.step("Get company-specific salary page content")
    def get_company_salary_text(self) -> str:
        return self.page.evaluate("() => document.body.innerText")
