import pytest
import allure

@allure.feature("Interview Questions")
class TestInterviewQuestions:

    @allure.story("IQ_001 - Searching by company shows interview experiences for that company")
    @pytest.mark.critical
    @pytest.mark.regression
    @pytest.mark.web
    def test_search_company_interview_experiences(self, driver, interviews_page):
        interviews_page.open()
        interviews_page.search_company("Microsoft")
        page_text = interviews_page.get_page_text().lower()
        assert "microsoft" in page_text, "Expected 'Microsoft' interview experiences in search results."

    @allure.story("IQ_002 - Searching by job profile shows interview questions relevant to that role")
    @pytest.mark.critical
    @pytest.mark.regression
    @pytest.mark.web
    def test_search_job_profile_interview_questions(self, driver, interviews_page):
        interviews_page.open()
        interviews_page.search_company("Data Analyst")
        page_text = interviews_page.get_page_text().lower()
        assert "data analyst" in page_text, "Expected 'Data Analyst' interview questions in search results."

    @allure.story("IQ_003 - Interview experience card shows correct round type, difficulty and outcome")
    @pytest.mark.high
    @pytest.mark.regression
    @pytest.mark.web
    def test_interview_card_details(self, driver, interviews_page):
        interviews_page.open_company("tcs")
        first_card_text = interviews_page.get_first_card_text().lower()
        assert any(rt in first_card_text for rt in ["technical", "hr"]), "Expected interview round type in card."
        assert any(dl in first_card_text for dl in ["easy", "medium", "hard"]), "Expected difficulty level in card."
        assert any(oc in first_card_text for oc in ["selected", "rejected", "on hold"]), "Expected outcome in card."

    @allure.story("IQ_004 - Clicking an interview experience card opens the full interview story")
    @pytest.mark.critical
    @pytest.mark.regression
    @pytest.mark.web
    def test_full_interview_story_display(self, driver, interviews_page):
        interviews_page.open_company("some-company")
        interviews_page.click_first_card()
        detail_page_text = interviews_page.get_page_text()
        assert "rounds description" in detail_page_text, "Expected rounds description in full interview story."
        assert "questions asked" in detail_page_text, "Expected questions asked in full interview story."

    @allure.story("IQ_005 - Filter by difficulty 'Easy' shows only Easy-rated interview experiences")
    @pytest.mark.high
    @pytest.mark.regression
    @pytest.mark.web
    def test_filter_by_difficulty_easy(self, driver, interviews_page, filter_panel):
        interviews_page.open_company("tcs")
        filter_panel.apply_difficulty_filter("Easy")
        first_card_text = interviews_page.get_first_card_text().lower()
        assert "easy" in first_card_text, "Expected only 'Easy' difficulty interview experiences."

    @allure.story("IQ_006 - Filter by outcome 'Selected' shows only experiences where candidate was selected")
    @pytest.mark.high
    @pytest.mark.regression
    @pytest.mark.web
    def test_filter_by_outcome_selected(self, driver, interviews_page, filter_panel):
        interviews_page.open_company("tcs")
        filter_panel.apply_outcome_filter("Selected")
        first_card_text = interviews_page.get_first_card_text().lower()
        assert "selected" in first_card_text, "Expected only 'Selected' interview experiences."

    @allure.story("IQ_007 - Interview questions listed on a card are actual questions (not metadata)")
    @pytest.mark.high
    @pytest.mark.regression
    @pytest.mark.web
    def test_interview_questions_are_real(self, driver, interviews_page):
        interviews_page.open_company("some-company")
        interviews_page.click_first_card()
        detail_page_text = interviews_page.get_page_text()
        assert "explain the solid principles" in detail_page_text.lower(), "Expected real interview questions."

    @allure.story("IQ_008 - View Answers count on a question matches the number of answers shown when expanded")
    @pytest.mark.medium
    @pytest.mark.regression
    @pytest.mark.web
    def test_view_answers_count(self, driver, interviews_page):
        interviews_page.open_company("some-company")
        interviews_page.click_first_card()
        # TODO: add view_answers_count_check() to InterviewDetailPage

    @allure.story("IQ_009 - Interview preparation tips section is present on detail page")
    @pytest.mark.medium
    @pytest.mark.regression
    @pytest.mark.web
    def test_interview_preparation_tips_present(self, driver, interviews_page):
        interviews_page.open_company("some-company")
        interviews_page.click_first_card()
        detail_page_text = interviews_page.get_page_text()
        assert "interview preparation tips" in detail_page_text.lower(), "Expected preparation tips section."

    @allure.story("IQ_010 - Stats section shows correct counts (8L+ experiences, 1L+ companies, 25K+ profiles)")
    @pytest.mark.medium
    @pytest.mark.regression
    @pytest.mark.web
    def test_stats_section_correct_counts(self, driver, interviews_page):
        interviews_page.open()
        interviews_page.assert_platform_stats()

    @allure.story("IQ_011 - Popular role pills on interviews page navigate to correct role-specific interview page")
    @pytest.mark.high
    @pytest.mark.regression
    @pytest.mark.web
    def test_role_pills_navigation(self, driver, interviews_page):
        interviews_page.open()
        interviews_page.click_role_pill("Software Engineer")
        page_text = interviews_page.get_page_text().lower()
        assert "software engineer" in page_text, "Expected Software Engineer role-specific interview page."
        current_url = interviews_page.get_current_url()
        assert "software-engineer" in current_url, "Expected URL to contain 'software-engineer'."

# Note: If you need more method implementations to mirror test functionality,
# make sure the respective method exists in the InterviewPage component to avoid any execution errors.
# Any unavailable method should be marked as 'TODO' to add it to the respective page object/component.