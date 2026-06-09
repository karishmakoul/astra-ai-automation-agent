import allure
from playwright.sync_api import Page


class CompanyCard:
    """
    Reusable company card reader.
    Shared by Companies page, Salaries page.
    """

    CARD_LINK      = 'a[href*="/reviews/"]'
    CARD_RATING    = '[class*="rating"], [class*="Rating"]'
    CARD_INDUSTRY  = '[class*="industry"], [class*="Industry"]'

    def __init__(self, page: Page):
        self.page = page

    @allure.step("Get count of visible company cards")
    def count(self) -> int:
        return self.page.locator(self.CARD_LINK).count()

    @allure.step("Get all company hrefs on the page")
    def get_hrefs(self) -> list[str]:
        cards = self.page.locator(self.CARD_LINK).all()
        return [c.get_attribute("href") or "" for c in cards]

    @allure.step("Get all text content from company cards")
    def get_all_card_texts(self) -> list[str]:
        """Returns inner text of every company card link."""
        return self.page.locator(self.CARD_LINK).all_inner_texts()

    @allure.step("Click company card for: '{company_name}'")
    def click(self, company_name: str):
        slug = company_name.lower().replace(" ", "-")
        link = self.page.locator(f'a[href*="/{slug}-reviews"]').first
        link.scroll_into_view_if_needed()
        link.click()
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(1500)

    def assert_all_cards_contain(self, expected_text: str):
        """
        Asserts that all visible company cards contain the expected text
        (used to validate filter results — e.g. all cards show 'IT Services').
        """
        card_texts = self.get_all_card_texts()
        failures = [t for t in card_texts if expected_text.lower() not in t.lower()]
        assert not failures, (
            f"Expected all cards to contain '{expected_text}'.\n"
            f"Non-matching cards ({len(failures)}):\n" +
            "\n".join(f"  - {t[:120]}" for t in failures[:5])
        )

    def assert_all_ratings_above(self, min_rating: float):
        """
        Parses rating numbers from card text and asserts all are >= min_rating.
        """
        import re
        card_texts = self.get_all_card_texts()
        for text in card_texts:
            matches = re.findall(r'\b([0-9]\.[0-9])\b', text)
            if matches:
                rating = float(matches[0])
                assert rating >= min_rating, (
                    f"Found rating {rating} which is below minimum {min_rating}.\n"
                    f"Card text: {text[:100]}"
                )
