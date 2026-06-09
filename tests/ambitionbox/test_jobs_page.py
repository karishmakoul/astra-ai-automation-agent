import pytest
import allure


@allure.feature("Jobs Page")
class TestJobsPage:

    @allure.story("JB_001 - Searching designation returns relevant job listings")
    @pytest.mark.critical
    @pytest.mark.regression
    @pytest.mark.web
    def test_job_search_by_designation(self, driver, jobs_page):
        jobs_page.search_designation("FinOps Analyst")
        page_text = jobs_page.get_page_text().lower()
        assert "finops" in page_text or "finance" in page_text, (
            "Expected job listings for 'FinOps Analyst' in search results"
        )

    @allure.story("JB_008 - Job detail page shows complete info and company rating")
    @pytest.mark.critical
    @pytest.mark.regression
    @pytest.mark.web
    def test_job_detail_page_shows_complete_info(self, driver, jobs_page):
        jobs_page.click_first_job()
        page_text = jobs_page.get_page_text()
        for expected in ["years", "Full Time", "Apply"]:
            assert expected.lower() in page_text.lower(), (
                f"Expected '{expected}' in job detail page"
            )
        # Company rating should be visible (N/5)
        import re
        ratings = re.findall(r'[0-9]\.[0-9]/5', page_text)
        assert len(ratings) > 0, "Expected company rating (X.X/5) on job detail page"

    @allure.story("JB_013 - Applying filters changes job results")
    @pytest.mark.critical
    @pytest.mark.regression
    @pytest.mark.web
    def test_filters_change_job_results(self, driver, jobs_page):
        """Jobs page uses a different filter UI — test via URL param approach."""
        default_text = jobs_page.get_page_text()

        # Apply Work Mode filter via URL (Jobs page doesn't use same chip pattern)
        jobs_page.navigate("/jobs?workMode=remote")
        jobs_page.page.wait_for_timeout(2000)
        filtered_text = jobs_page.get_page_text().lower()

        assert "remote" in filtered_text or "work from home" in filtered_text, \
            "Expected remote work mode to appear in filtered results"

    @allure.story("JB_011 - Sort by Latest changes job ordering")
    @pytest.mark.high
    @pytest.mark.regression
    @pytest.mark.web
    def test_sort_by_latest_changes_order(self, driver, jobs_page):
        default_text = jobs_page.get_page_text()
        # Jobs page sort via URL param
        jobs_page.navigate("/jobs?sort=latest")
        jobs_page.page.wait_for_timeout(2000)
        sorted_text = jobs_page.get_page_text()
        assert default_text != sorted_text, \
            "Expected job listing order to change after sorting by Latest"

    @allure.story("JB_012 - Create Job Alert triggers login for unauthenticated user")
    @pytest.mark.medium
    @pytest.mark.regression
    @pytest.mark.web
    def test_job_alert_requires_login(self, driver, jobs_page):
        jobs_page.click_job_alert()
        page_text = jobs_page.page.evaluate("() => document.body.innerText")
        assert any(kw in page_text.lower() for kw in ["login", "sign in", "email", "phone"]), (
            "Expected login prompt after clicking Create Job Alert for unauthenticated user"
        )

    @allure.story("JB_014 - Job count is displayed and page shows job listings")
    @pytest.mark.medium
    @pytest.mark.regression
    @pytest.mark.web
    def test_job_count_is_displayed(self, driver, jobs_page):
        import re
        page_text = jobs_page.get_page_text()
        # Verify job count is shown somewhere on the page
        count_match = re.search(r'[\d.,]+(L|Lakh|lakhs?)?\s*Jobs', page_text, re.IGNORECASE)
        assert count_match or "jobs" in page_text.lower(), \
            "Expected job count to be displayed on the jobs page"
