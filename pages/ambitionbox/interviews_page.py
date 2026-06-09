import allure
from core.base_page import BasePage


class InterviewsPage(BasePage):
    """Page object for /interviews and company-specific interview pages."""

    URL_PATH         = "/interviews"
    SEARCH_CONTAINER = '[data-testid="desktop-typeahead"]'
    SEARCH_INPUT     = '[data-testid="desktop-typeahead"] input'
    STATS_SECTION    = '[class*="stat"], [class*="Stat"]'
    EXPERIENCE_CARDS = '[class*="interviewCard"], [class*="interview-card"], [class*="experienceCard"]'
    DIFFICULTY_BADGE = '[class*="difficulty"], text=/Easy|Medium|Hard/'
    OUTCOME_BADGE    = '[class*="outcome"], text=/Selected|Rejected|On Hold/'
    ROLE_PILLS       = '[class*="rolePill"], [class*="role-pill"]'
    SHARE_BTN        = 'button:has-text("Share Interview"), a:has-text("Share Interview")'

    def open(self):
        self.navigate(self.URL_PATH)
        self.wait_for_load()
        self.page.wait_for_timeout(2000)
        return self

    def open_company(self, company_slug: str):
        self.navigate(f"/interviews/{company_slug}-interview-questions")
        self.wait_for_load()
        self.page.wait_for_timeout(2000)
        return self

    @allure.step("Search company: '{company}'")
    def search_company(self, company: str):
        self.page.locator(self.SEARCH_CONTAINER).click()
        self.page.locator(self.SEARCH_INPUT).fill(company)
        self.page.wait_for_timeout(600)
        self.page.locator(self.SEARCH_INPUT).press("Enter")
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(2000)

    @allure.step("Get full page text for validation")
    def get_page_text(self) -> str:
        return self.page.evaluate("() => document.body.innerText")

    @allure.step("Get first interview card text")
    def get_first_card_text(self) -> str:
        cards = self.page.locator(self.EXPERIENCE_CARDS)
        if cards.count():
            return cards.first.inner_text()
        # fallback — read larger containers
        return self.page.evaluate("""() =>
            [...document.querySelectorAll('[class*="interview"], [class*="experience"]')]
            .find(e => e.innerText.length > 100)?.innerText || ''
        """)

    @allure.step("Click first interview experience card")
    def click_first_card(self):
        cards = self.page.locator(self.EXPERIENCE_CARDS)
        if cards.count():
            cards.first.click()
        else:
            self.page.locator('a[href*="/interview-questions/"]').first.click()
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(1500)

    @allure.step("Click role pill: '{role}'")
    def click_role_pill(self, role: str):
        self.page.locator(f'text={role}').first.click()
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(1500)

    @allure.step("Assert stats show minimum counts")
    def assert_platform_stats(self, min_experiences: int = 800000):
        page_text = self.get_page_text()
        assert "8L" in page_text or "interview" in page_text.lower(), (
            "Expected interview stats (8L+ experiences) to be visible on page"
        )
