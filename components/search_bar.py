import allure
from playwright.sync_api import Page


class SearchBar:
    """
    Reusable search bar component.
    AmbitionBox uses the same search pattern (click container → fill input → Enter)
    on Home, Companies, Interviews and Jobs pages.
    """

    CONTAINER = '[data-testid="desktop-typeahead"]'
    INPUT     = '[data-testid="desktop-typeahead"] input'

    def __init__(self, page: Page):
        self.page = page

    @allure.step("Search for: '{query}'")
    def search(self, query: str):
        self.page.locator(self.CONTAINER).click()
        self.page.locator(self.INPUT).fill(query)
        self.page.wait_for_timeout(500)
        self.page.locator(self.INPUT).press("Enter")
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(1500)

    @allure.step("Search and select first suggestion for: '{query}'")
    def search_and_select_first(self, query: str):
        self.page.locator(self.CONTAINER).click()
        self.page.locator(self.INPUT).fill(query)
        self.page.wait_for_timeout(800)
        # Select first dropdown suggestion if it appears
        suggestion = self.page.locator('[class*="suggestion"], [class*="autocomplete"] li, [role="option"]').first
        if suggestion.is_visible():
            suggestion.click()
        else:
            self.page.locator(self.INPUT).press("Enter")
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(1500)

    def is_visible(self) -> bool:
        return self.page.locator(self.CONTAINER).is_visible()

    def get_current_value(self) -> str:
        return self.page.locator(self.INPUT).input_value()
