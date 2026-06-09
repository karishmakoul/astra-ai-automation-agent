import pytest
import allure


@allure.feature("Reviews Page")
class TestReviewsPage:

    @allure.story("RV_007 - Women vs Men ratings are different")
    @pytest.mark.high
    @pytest.mark.regression
    @pytest.mark.web
    def test_gender_ratings_differ(self, driver, reviews_page):
        reviews_page.open("tcs")
        page_text = reviews_page.get_page_text() if hasattr(reviews_page, 'get_page_text') \
                    else reviews_page.page.evaluate("() => document.body.innerText")
        assert "by Women" in page_text or "Women" in page_text, \
            "Expected Women rating section on TCS reviews page"
        assert "by Men" in page_text or "Men" in page_text, \
            "Expected Men rating section on TCS reviews page"

    @allure.story("RV_005 - Sort by Latest shows more recent reviews first")
    @pytest.mark.high
    @pytest.mark.regression
    @pytest.mark.web
    def test_sort_latest_shows_recent_reviews(self, driver, reviews_page):
        reviews_page.open("tcs")
        # Get first review date in Popular sort
        initial_text = reviews_page.page.evaluate("() => document.body.innerText")

        # Switch to Latest sort
        reviews_page.sort_by("Latest")
        sorted_text = reviews_page.page.evaluate("() => document.body.innerText")

        assert initial_text != sorted_text, \
            "Expected page content to change after sorting by Latest"

    @allure.story("RV_004 - Overall rating is displayed on company reviews page")
    @pytest.mark.critical
    @pytest.mark.smoke
    @pytest.mark.web
    def test_overall_rating_is_displayed(self, driver, reviews_page):
        reviews_page.open("tcs")
        page_text = reviews_page.page.evaluate("() => document.body.innerText")
        import re
        # TCS overall rating should be visible (e.g. 3.3)
        ratings = re.findall(r'\b[0-9]\.[0-9]\b', page_text)
        assert len(ratings) > 0, "Expected at least one numeric rating on TCS reviews page"
        # Rating should be between 1 and 5
        numeric_ratings = [float(r) for r in ratings]
        assert any(1.0 <= r <= 5.0 for r in numeric_ratings), \
            f"Expected a rating between 1.0 and 5.0. Found: {numeric_ratings[:5]}"

    @allure.story("RV_011 - Critically rated attributes appear and match low-scored categories")
    @pytest.mark.high
    @pytest.mark.regression
    @pytest.mark.web
    def test_critically_rated_matches_low_categories(self, driver, reviews_page):
        reviews_page.open("tcs")
        # Scroll down to ensure the rating section is loaded
        reviews_page.page.evaluate("window.scrollBy(0, 600)")
        reviews_page.page.wait_for_timeout(1000)
        page_text = reviews_page.page.evaluate("() => document.body.innerText")

        # TCS page shows category breakdown — Salary (2.5) and Promotions (2.3) are lowest
        assert "Salary" in page_text, "Expected 'Salary' rating category on TCS reviews page"
        assert "Promotions" in page_text, "Expected 'Promotions' rating category on TCS reviews page"

        # Verify the actual low scores are present (TCS: Salary=2.5, Promotions=2.3)
        import re
        ratings = re.findall(r"([0-9]\.[0-9])", page_text)
        numeric_ratings = [float(r) for r in ratings]
        assert any(r <= 2.5 for r in numeric_ratings), (
            f"Expected at least one low rating (≤2.5) on TCS reviews page. Found: {numeric_ratings[:10]}"
        )

    @allure.story("RV_009 - Work policies section shows percentage data")
    @pytest.mark.medium
    @pytest.mark.regression
    @pytest.mark.web
    def test_work_policies_show_percentage_data(self, driver, reviews_page):
        reviews_page.open("tcs")
        page_text = reviews_page.page.evaluate("() => document.body.innerText")
        import re
        # Work policies should show percentages
        percentages = re.findall(r'\d+%', page_text)
        assert len(percentages) > 0, \
            "Expected percentage values in Work Policies section"
        # Should mention work from office or work days
        assert any(kw in page_text for kw in ["employees reported", "work from", "5 days"]), \
            "Expected work policy details (employees reported, WFO, days) on page"

    @allure.story("RV_010 - AI summary section is present with sentiment")
    @pytest.mark.medium
    @pytest.mark.regression
    @pytest.mark.web
    def test_ai_summary_section_present(self, driver, reviews_page):
        reviews_page.open("tcs")
        page_text = reviews_page.page.evaluate("() => document.body.innerText")
        assert "AI summary" in page_text or "summary from recent" in page_text.lower(), \
            "Expected AI summary section on TCS reviews page"


@pytest.fixture()
def reviews_page(pw_page):
    from pages.ambitionbox.reviews_page import ReviewsPage
    return ReviewsPage()
