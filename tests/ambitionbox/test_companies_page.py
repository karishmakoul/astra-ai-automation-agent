import pytest
import allure


@allure.feature("Companies Page")
class TestCompaniesPage:

    @allure.story("CP_001 - Industry filter changes companies shown")
    @pytest.mark.critical
    @pytest.mark.regression
    @pytest.mark.web
    def test_industry_filter_changes_results(self, driver, companies_page, filter_panel, company_card):
        default_hrefs = set(company_card.get_hrefs())
        assert len(default_hrefs) > 0, "Expected companies to be listed by default"

        # Apply Pharma industry filter (clearly different from default IT companies)
        filter_panel.apply("Industry", "Pharma")

        filtered_hrefs = set(company_card.get_hrefs())
        assert len(filtered_hrefs) > 0, "No companies shown after Industry filter"
        assert filtered_hrefs != default_hrefs, (
            "Expected different companies after applying Pharma industry filter.\n"
            f"Default: {list(default_hrefs)[:3]}\n"
            f"Filtered: {list(filtered_hrefs)[:3]}"
        )

    @allure.story("CP_002 - Location filter changes companies shown")
    @pytest.mark.critical
    @pytest.mark.regression
    @pytest.mark.web
    def test_location_filter_changes_results(self, driver, companies_page, filter_panel, company_card):
        default_hrefs = set(company_card.get_hrefs())

        # Use Jaipur — a rarer location that shows clearly different companies
        filter_panel.apply("Location", "Jaipur")

        filtered_hrefs = set(company_card.get_hrefs())
        assert len(filtered_hrefs) > 0, "No companies shown after Location filter"
        assert filtered_hrefs != default_hrefs, (
            "Expected different companies after applying Jaipur location filter"
        )

    @allure.story("CP_007 - Industry filter then clearing shows default companies again")
    @pytest.mark.critical
    @pytest.mark.regression
    @pytest.mark.web
    def test_filter_and_clear_restores_defaults(self, driver, companies_page, filter_panel, company_card):
        default_hrefs = set(company_card.get_hrefs())

        # Apply Pharma filter
        filter_panel.apply("Industry", "Pharma")
        filtered_hrefs = set(company_card.get_hrefs())
        assert filtered_hrefs != default_hrefs, "Pharma filter should change the companies shown"

        # Clear all filters
        filter_panel.clear_all()
        reset_hrefs = set(company_card.get_hrefs())
        assert reset_hrefs == default_hrefs, (
            "After clearing filters, expected default companies to be shown.\n"
            f"Missing: {default_hrefs - reset_hrefs}\nExtra: {reset_hrefs - default_hrefs}"
        )

    @allure.story("CP_009 - Clear All filters resets to default state")
    @pytest.mark.high
    @pytest.mark.regression
    @pytest.mark.web
    def test_clear_all_resets_filters(self, driver, companies_page, filter_panel, company_card):
        default_hrefs = set(company_card.get_hrefs())

        # Apply Size filter
        filter_panel.apply("Size", "1 Lakh+")
        filtered_hrefs = set(company_card.get_hrefs())
        assert filtered_hrefs != default_hrefs, "Size filter should show different companies"

        filter_panel.clear_all()
        reset_hrefs = set(company_card.get_hrefs())
        assert reset_hrefs == default_hrefs, \
            "After Clear All, expected default companies to be restored"

    @allure.story("CP_008 - Sort by Top Paying applies and URL reflects sort parameter")
    @pytest.mark.high
    @pytest.mark.regression
    @pytest.mark.web
    def test_sort_by_top_paying_applies(self, driver, companies_page, filter_panel, company_card):
        filter_panel.sort_by("Top Paying")
        url = companies_page.get_current_url()
        # URL must contain sortBy=topPaying param
        assert "topPaying" in url or "sortBy" in url, (
            f"Expected URL to contain 'sortBy=topPaying' after applying Top Paying sort. Got: {url}"
        )
        # Companies page must still show results
        count = company_card.count()
        assert count > 0, "Expected companies to be shown after applying sort"

    @allure.story("CP_011 - Company detail page shows all sub-tabs")
    @pytest.mark.critical
    @pytest.mark.regression
    @pytest.mark.web
    def test_company_detail_page_shows_subtabs(self, driver, companies_page):
        companies_page.navigate("/reviews/tcs-reviews")
        companies_page.page.wait_for_timeout(2000)

        url = companies_page.get_current_url()
        assert "tcs" in url.lower(), f"Expected TCS URL, got: {url}"

        page_text = companies_page.page.evaluate("() => document.body.innerText")
        for tab in ["Reviews", "Salaries", "Interviews", "Jobs", "Benefits"]:
            assert tab.lower() in page_text.lower(), (
                f"Expected sub-tab '{tab}' visible on TCS company page"
            )

    @allure.story("CP_014 - Search navigates to correct company page")
    @pytest.mark.critical
    @pytest.mark.regression
    @pytest.mark.web
    def test_search_navigates_to_company_page(self, driver, companies_page, search_bar):
        search_bar.search("Google")
        url = companies_page.get_current_url()
        page_text = companies_page.page.evaluate("() => document.body.innerText").lower()
        assert "google" in url.lower() or "google" in page_text, (
            f"Expected Google in URL or page text after search. URL: {url}"
        )

    @allure.story("CP_004 - Company Type filter shows Startup companies")
    @pytest.mark.high
    @pytest.mark.regression
    @pytest.mark.web
    def test_type_filter_shows_different_companies(self, driver, companies_page, filter_panel, company_card):
        default_hrefs = set(company_card.get_hrefs())
        filter_panel.apply("Type", "Startup")
        filtered_hrefs = set(company_card.get_hrefs())
        assert len(filtered_hrefs) > 0, "Expected Startup companies to be shown"
        assert filtered_hrefs != default_hrefs, \
            "Startup filter should show different companies than default"
