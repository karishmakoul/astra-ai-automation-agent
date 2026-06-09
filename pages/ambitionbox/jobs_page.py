import allure
from core.base_page import BasePage


class JobsPage(BasePage):
    """Page object for /jobs page."""

    URL_PATH         = "/jobs"
    SEARCH_CONTAINER = '[data-testid="desktop-typeahead"]'
    SEARCH_INPUT     = '[data-testid="desktop-typeahead"] input'
    JOB_CARDS        = '[class*="jobCard"], [class*="job-card"]'
    JOB_COUNT_HEADER = '[class*="jobCount"], [class*="resultsCount"]'
    SORT_RELEVANCE   = 'text=Relevance'
    SORT_LATEST      = 'text=Latest'
    JOB_ALERT_BTN    = 'text=Create Job Alert'
    APPLY_BTN        = 'text=Apply on, a:has-text("Apply")'

    def open(self):
        self.navigate(self.URL_PATH)
        self.wait_for_load()
        self.page.wait_for_timeout(2000)
        return self

    @allure.step("Search jobs for designation: '{designation}'")
    def search_designation(self, designation: str):
        self.page.locator(self.SEARCH_CONTAINER).click()
        self.page.locator(self.SEARCH_INPUT).fill(designation)
        self.page.wait_for_timeout(600)
        self.page.locator(self.SEARCH_INPUT).press("Enter")
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(2000)

    @allure.step("Get page text for job data validation")
    def get_page_text(self) -> str:
        return self.page.evaluate("() => document.body.innerText")

    @allure.step("Get text of all visible job cards")
    def get_job_card_texts(self) -> list[str]:
        cards = self.page.locator(self.JOB_CARDS).all()
        if cards:
            return [c.inner_text()[:400] for c in cards[:10]]
        # Fallback — generic job listing containers
        return self.page.evaluate("""() =>
            [...document.querySelectorAll('[class*="job"], [class*="Job"]')]
            .filter(e => e.innerText.length > 80 && e.innerText.length < 600)
            .slice(0, 10)
            .map(e => e.innerText)
        """)

    @allure.step("Click first job card")
    def click_first_job(self):
        cards = self.page.locator(self.JOB_CARDS)
        if cards.count():
            cards.first.click()
        else:
            self.page.locator('a[href*="/jobs/"]').first.click()
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(1500)

    @allure.step("Change sort to: '{sort_value}'")
    def sort_by(self, sort_value: str):
        self.page.locator(f'text={sort_value}').first.click()
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(1500)

    @allure.step("Get displayed job count text")
    def get_job_count_text(self) -> str:
        return self.page.evaluate("""() => {
            const el = document.querySelector('[class*="count"], [class*="Count"]');
            return el ? el.innerText : document.body.innerText.match(/[0-9.]+\\s*(Lakh|lakhs?|L)\\s*Jobs/i)?.[0] || '';
        }""")

    @allure.step("Click Create Job Alert button")
    def click_job_alert(self):
        self.page.locator(self.JOB_ALERT_BTN).first.click()
        self.page.wait_for_timeout(1000)
