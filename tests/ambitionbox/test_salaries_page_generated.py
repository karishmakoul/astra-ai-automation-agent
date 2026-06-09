import pytest
import allure

@allure.feature("Salaries Page")
class TestSalariesPage:

    @allure.story("SAL_001 - Searching by designation shows salary range for that role")
    @pytest.mark.critical
    @pytest.mark.regression
    @pytest.mark.web
    def test_searching_by_designation_shows_salary_range_for_that_role(self, driver, salaries_page):
        salaries_page.search_designation("Software Engineer")
        salary_ranges = salaries_page.get_salary_ranges()
        assert salary_ranges, "Expected salary ranges to be displayed for 'Software Engineer'."
        for salary in salary_ranges:
            assert "₹" in salary, f"Expected salary format '₹X–₹Y'. Got: {salary}"

    @allure.story("SAL_002 - Salary results filtered by experience show data within the experience band")
    @pytest.mark.critical
    @pytest.mark.regression
    @pytest.mark.web
    def test_salary_results_filtered_by_experience(self, driver, salaries_page, filter_panel):
        salaries_page.search_designation("Software Engineer")
        filter_panel.apply("Experience", "0-2 years")
        salary_texts = salaries_page.get_page_salary_text()
        assert "0-2 years" in salary_texts, "Expected all salary cards to show experience within 0-2 years."

    @allure.story("SAL_003 - Salary results filtered by location show data for that city only")
    @pytest.mark.high
    @pytest.mark.regression
    @pytest.mark.web
    def test_salary_results_filtered_by_location(self, driver, salaries_page, filter_panel):
        salaries_page.search_designation("Software Engineer")
        filter_panel.apply("Location", "Bangalore")
        salary_texts = salaries_page.get_page_salary_text()
        assert "Bangalore" in salary_texts, "Expected all salary cards to show Bangalore as the location."

    @allure.story("SAL_004 - Salary by company section shows correct salary range for each listed company")
    @pytest.mark.high
    @pytest.mark.regression
    @pytest.mark.web
    def test_salary_by_company_section(self, driver, salaries_page, company_card):
        # TODO: add method to locate 'Salaries by Company' section
        # TODO: add method to navigate to specific company page and verify salary range
        pass

    @allure.story("SAL_005 - Clicking a role in 'Salaries for Popular Roles' section shows salary details for that role")
    @pytest.mark.high
    @pytest.mark.regression
    @pytest.mark.web
    def test_clicking_role_in_popular_roles(self, driver, salaries_page):
        salaries_page.click_popular_role("Senior Software Engineer")
        page_text = salaries_page.get_page_salary_text()
        assert "Senior Software Engineer" in page_text, "Expected salary details for Senior Software Engineer role."

    @allure.story("SAL_006 - Department filter changes salary results to show only that department's roles")
    @pytest.mark.high
    @pytest.mark.regression
    @pytest.mark.web
    def test_department_filter_changes_salary_results(self, driver, salaries_page, filter_panel):
        salaries_page.select_department("Engineering - Software & QA")
        salary_texts = salaries_page.get_page_salary_text()
        assert "Engineering - Software & QA" in salary_texts, "Expected roles under Engineering - Software & QA."

    @allure.story("SAL_007 - Company-specific salary page shows correct designation-wise salary breakdown")
    @pytest.mark.critical
    @pytest.mark.regression
    @pytest.mark.web
    def test_company_specific_salary_breakdown(self, driver, salaries_page):
        salaries_page.open_company("tcs")
        salary_ranges = salaries_page.get_company_salary_text()
        assert "System Engineer" in salary_ranges, "Expected designation 'System Engineer' in TCS salary page."

    @allure.story("SAL_008 - In-hand salary calculator computes correct take-home based on entered CTC")
    @pytest.mark.high
    @pytest.mark.regression
    @pytest.mark.web
    def test_in_hand_salary_calculator(self, driver, salaries_page):
        result_text = salaries_page.calculate_salary("TCS", "Software Engineer", "10,00,000")
        assert "in-hand" in result_text, "Expected in-hand salary details after calculation."

    @allure.story("SAL_009 - Salary rating shown on company cards reflects the star rating from reviews page")
    @pytest.mark.high
    @pytest.mark.regression
    @pytest.mark.web
    def test_salary_rating_shown_on_company_cards(self, driver, salaries_page, company_card):
        # TODO: add method to get salary rating on company cards
        # TODO: add method to navigate to reviews page and verify rating
        pass

    @allure.story("SAL_010 - Login wall blocks exact salary figures — unlocking requires authentication")
    @pytest.mark.medium
    @pytest.mark.regression
    @pytest.mark.web
    def test_login_wall_blocks_exact_salary_figures(self, driver, salaries_page):
        salaries_page.assert_login_wall_shown()
        # TODO: add method to trigger login prompt and verify login requirement for details
        pass