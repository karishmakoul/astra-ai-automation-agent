import pytest
import allure

@allure.feature("Jobs Page")
class TestJobsPage:

    @allure.story("JB_003 - Filter by Location shows jobs only in the selected city")
    @pytest.mark.critical
    @pytest.mark.regression
    @pytest.mark.web
    def test_filter_by_location(self, driver, jobs_page, filter_panel):
        jobs_page.open()
        filter_panel.apply("Location", "Pune")
        job_card_texts = jobs_page.get_job_card_texts()
        for text in job_card_texts:
            assert "Pune" in text, f"Expected 'Pune' in job location. Got: {text}"

    @allure.story("JB_004 - Filter by Experience shows jobs matching the experience band")
    @pytest.mark.high
    @pytest.mark.regression
    @pytest.mark.web
    def test_filter_by_experience(self, driver, jobs_page, filter_panel):
        jobs_page.open()
        filter_panel.apply("Experience", "3-7 years")
        job_card_texts = jobs_page.get_job_card_texts()
        for text in job_card_texts:
            assert any(exp in text for exp in ["3 years", "4 years", "5 years", "6 years", "7 years"]), \
                f"Expected experience in 3-7 years range. Got: {text}"

    @allure.story("JB_005 - Filter by Employment Type shows only full-time positions")
    @pytest.mark.high
    @pytest.mark.regression
    @pytest.mark.web
    def test_filter_by_employment_type(self, driver, jobs_page, filter_panel):
        jobs_page.open()
        filter_panel.apply("Employment Type", "Full Time, Permanent")
        job_card_texts = jobs_page.get_job_card_texts()
        for text in job_card_texts:
            assert "Full Time, Permanent" in text, f"Expected 'Full Time, Permanent'. Got: {text}"

    @allure.story("JB_006 - Filter by Salary range shows jobs within that CTC band")
    @pytest.mark.high
    @pytest.mark.regression
    @pytest.mark.web
    def test_filter_by_salary(self, driver, jobs_page, filter_panel):
        jobs_page.open()
        filter_panel.apply("Salary", "10-20 LPA")
        job_card_texts = jobs_page.get_job_card_texts()
        for text in job_card_texts:
            # Assert if text includes any salary indication within the range
            salary_matches = ["10 LPA", "15 LPA", "20 LPA"]
            assert any(salary in text for salary in salary_matches), \
                f"Expected salary in 10-20 LPA range. Got: {text}"

    @allure.story("JB_007 - Filter by Industry narrows job results")
    @pytest.mark.high
    @pytest.mark.regression
    @pytest.mark.web
    def test_filter_by_industry(self, driver, jobs_page, filter_panel):
        jobs_page.open()
        filter_panel.apply("Industry", "IT Services & Consulting")
        job_card_texts = jobs_page.get_job_card_texts()
        for text in job_card_texts:
            assert "IT Services & Consulting" in text, \
                f"Expected industry 'IT Services & Consulting'. Got: {text}"

    @allure.story("JB_009 - Company rating on job detail page matches rating")
    @pytest.mark.high
    @pytest.mark.regression
    @pytest.mark.web
    def test_company_rating_on_job_detail_page(self, driver, jobs_page, company_card):
        jobs_page.open()
        jobs_page.click_first_job()
        job_rating_text = jobs_page.get_page_text()
        company_card.click("Amazon")
        company_rating_text = company_card.get_all_card_texts()
        assert abs(float(job_rating_text) - float(company_rating_text)) <= 0.1, \
            f"Expected rating difference within ±0.1. Got job: {job_rating_text}, company: {company_rating_text}"

    @allure.story("JB_010 - Similar Jobs section shows related listings")
    @pytest.mark.medium
    @pytest.mark.regression
    @pytest.mark.web
    def test_similar_jobs_section(self, driver, jobs_page):
        jobs_page.open()
        jobs_page.click_first_job()
        similar_jobs_texts = jobs_page.get_job_card_texts()  # Assuming this returns similar jobs cards text
        assert len(similar_jobs_texts) >= 3, "Expected at least 3 similar jobs."
        # Further checks for relevance can be added based on known job details.
        pass