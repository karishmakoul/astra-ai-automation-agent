import re
import allure
from core.base_page import BasePage


class ReviewsPage(BasePage):
    """Page object for company reviews pages (e.g. /reviews/tcs-reviews)."""

    # ── Locators ────────────────────────────────────────────────
    OVERALL_RATING      = 'text=/^[0-9]\\.[0-9]$/'
    WRITE_REVIEW_BTN    = 'button:has-text("Write a Review"), a:has-text("Write a Review")'
    FILTER_DEPARTMENT   = 'text=Department'
    FILTER_DESIGNATION  = 'text=Designation'
    FILTER_LOCATION     = 'text=Location'
    SORT_DROPDOWN       = '[class*="sort"], select[name*="sort"]'
    REVIEW_CARDS        = '[class*="reviewCard"], [class*="review-card"], [class*="Review"]'
    REVIEW_DATE         = '[class*="date"], [class*="Date"]'
    CATEGORY_RATINGS    = '[class*="categoryRating"], [class*="category-rating"]'
    WORK_POLICIES       = '[class*="workPolicy"], [class*="work-policy"]'
    AI_SUMMARY          = '[class*="aiSummary"], [class*="ai-summary"], text=AI summary'
    WOMEN_RATING        = 'text=/by Women/'
    MEN_RATING          = 'text=/by Men/'
    CRITICALLY_RATED    = 'text=CRITICALLY RATED FOR'
    HIGHLY_RATED        = 'text=HIGHLY RATED FOR'
    RATING_BREAKDOWN    = '[class*="ratingBreakdown"], [class*="rating-breakdown"]'

    def open(self, company_slug: str = "tcs"):
        url = f"/reviews/{company_slug}-reviews"
        self.navigate(url)
        self.wait_for_load()
        self.page.wait_for_timeout(2000)
        return self

    @allure.step("Get overall company rating text")
    def get_overall_rating(self) -> float:
        rating_text = self.page.locator("text=/^[0-9]\\.[0-9]/").first.inner_text().strip()
        return float(re.search(r"[0-9]\.[0-9]", rating_text).group())

    @allure.step("Get rating for category: '{category}'")
    def get_category_rating(self, category: str) -> float:
        """
        Extracts numeric rating next to a category name from the rating breakdown.
        category: 'Job Security' | 'Work-Life Balance' | 'Salary' | 'Promotions' etc.
        """
        section = self.page.locator(f"text={category}").first
        parent_text = section.evaluate("e => e.closest('tr, div[class]')?.innerText || ''")
        matches = re.findall(r"([0-9]\.[0-9])", parent_text)
        if not matches:
            raise AssertionError(f"Could not find numeric rating for category '{category}'")
        return float(matches[0])

    @allure.step("Get Women's overall rating")
    def get_women_rating(self) -> float:
        text = self.page.locator(self.WOMEN_RATING).first.inner_text()
        match = re.search(r"([0-9]\.[0-9])", text)
        return float(match.group()) if match else 0.0

    @allure.step("Get Men's overall rating")
    def get_men_rating(self) -> float:
        text = self.page.locator(self.MEN_RATING).first.inner_text()
        match = re.search(r"([0-9]\.[0-9])", text)
        return float(match.group()) if match else 0.0

    @allure.step("Apply review filter: '{filter_name}' = '{value}'")
    def apply_filter(self, filter_name: str, value: str):
        """
        filter_name: 'Department' | 'Designation' | 'Location' | 'Overall Rating'
        """
        self.page.locator(f"text={filter_name}").first.click()
        self.page.wait_for_timeout(600)
        self.page.locator(f"text={value}").first.click()
        self.page.wait_for_timeout(1500)

    @allure.step("Change sort order to: '{sort_value}'")
    def sort_by(self, sort_value: str):
        """sort_value: 'Popular' | 'Latest' | 'Detailed'"""
        sort_btn = self.page.locator('text=Sort By').first
        sort_btn.click()
        self.page.wait_for_timeout(400)
        self.page.locator(f"text={sort_value}").first.click()
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(1500)

    @allure.step("Get dates of first {n} review cards")
    def get_review_dates(self, n: int = 3) -> list[str]:
        date_els = self.page.locator("text=/\\d+ (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[,]? \\d{4}/").all()
        return [el.inner_text().strip() for el in date_els[:n]]

    @allure.step("Get text of first {n} review cards")
    def get_review_texts(self, n: int = 3) -> list[str]:
        cards = self.page.locator('[class*="reviewCard"], [class*="review-card"]').all()
        return [c.inner_text()[:300] for c in cards[:n]]

    @allure.step("Get 'Critically Rated For' attributes")
    def get_critically_rated_attrs(self) -> list[str]:
        el = self.page.locator(self.CRITICALLY_RATED).first
        parent = el.evaluate("e => e.closest('div[class]')?.innerText || e.parentElement?.innerText || ''")
        # Strip the label and split remaining text
        cleaned = parent.replace("CRITICALLY RATED FOR", "").strip()
        return [a.strip() for a in cleaned.split(",") if a.strip()]

    @allure.step("Assert Write Review button is visible")
    def assert_write_review_visible(self):
        self.assert_visible(self.WRITE_REVIEW_BTN, "Write a Review button")

    @allure.step("Assert women and men ratings are different")
    def assert_gender_ratings_differ(self):
        women = self.get_women_rating()
        men   = self.get_men_rating()
        assert women != men, f"Expected Women ({women}) and Men ({men}) ratings to differ"
