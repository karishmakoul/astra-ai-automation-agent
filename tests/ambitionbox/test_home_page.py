import pytest
import allure
from utils.config import Config


@allure.feature("Home Page")
class TestHomePage:

    @allure.story("HP_005 - Left nav links navigate to correct URLs")
    @pytest.mark.smoke
    @pytest.mark.web
    def test_nav_links_navigate_to_correct_urls(self, driver, home_page, left_nav):
        expected = {
            "companies":  "list-of-companies",
            "reviews":    "reviews",
            "salaries":   "salaries",
            "interviews": "interviews",
            "jobs":       "jobs",
        }
        overlay_sel = '[data-testid="home-feed-tabs-coachmark-overlay"]'
        for section, url_fragment in expected.items():
            url = left_nav.go_to(section)
            assert url_fragment in url, (
                f"Expected URL to contain '{url_fragment}' after clicking '{section}' nav. Got: {url}"
            )
            # Return to home page and dismiss overlay before next iteration
            home_page.navigate("/")
            home_page.page.wait_for_timeout(800)
            overlay = home_page.page.locator(overlay_sel).first
            if overlay.is_visible():
                overlay.click(force=True)
                home_page.page.wait_for_timeout(500)

    @allure.story("HP_001 - Search by company name navigates to correct company page")
    @pytest.mark.regression
    @pytest.mark.web
    def test_search_company_navigates_correctly(self, driver, home_page, search_bar):
        search_bar.search("Accenture")
        url   = home_page.get_current_url()
        title = home_page.get_title().lower()
        assert "accenture" in url.lower() or "accenture" in title, (
            f"Expected 'accenture' in URL or title. URL='{url}' Title='{title}'"
        )

    @allure.story("HP_002 - Search by designation returns relevant results")
    @pytest.mark.regression
    @pytest.mark.web
    def test_search_designation_returns_results(self, driver, home_page, search_bar):
        search_bar.search("Software Engineer")
        page_text = home_page.page.evaluate("() => document.body.innerText").lower()
        assert "software engineer" in page_text, (
            "Expected 'Software Engineer' results on the search page"
        )

    @allure.story("HP_006 - Tools nav: Compare Companies link opens compare page")
    @pytest.mark.regression
    @pytest.mark.web
    def test_compare_companies_tool_navigates_correctly(self, driver, home_page, left_nav):
        url = left_nav.click_tool("Compare Companies")
        assert "compare" in url.lower(), (
            f"Expected URL to contain 'compare'. Got: {url}"
        )

    @allure.story("HP_007 - Tools nav: Salary Calculator opens calculator page")
    @pytest.mark.regression
    @pytest.mark.web
    def test_salary_calculator_tool_navigates_correctly(self, driver, home_page, left_nav):
        url = left_nav.click_tool("Salary Calculator")
        assert "salary" in url.lower() or "calculator" in url.lower(), (
            f"Expected URL to contain 'salary' or 'calculator'. Got: {url}"
        )

    @allure.story("HP_003 - Popular feed tab loads, switching tab changes content")
    @pytest.mark.regression
    @pytest.mark.web
    def test_home_feed_tabs_switch_content(self, driver, home_page):
        # Popular tab should be selected by default
        popular_tab = home_page.page.locator('[data-testid="homeFeedTab-0"]')
        assert popular_tab.get_attribute("aria-selected") == "true", \
            "Expected 'Popular' tab to be selected by default"

        popular_content = home_page.page.evaluate("() => document.body.innerText")

        # Switch to My Company tab
        home_page.page.locator('[data-testid="homeFeedTab-1"]').click()
        home_page.page.wait_for_timeout(1500)
        my_company_content = home_page.page.evaluate("() => document.body.innerText")

        assert popular_content != my_company_content, \
            "Expected content to change when switching from Popular to My Company tab"
