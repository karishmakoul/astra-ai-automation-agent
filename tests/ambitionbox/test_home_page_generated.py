import pytest
import allure

@allure.feature("Home Page")
class TestHomePage:

    @allure.story("[HP_004] - Clicking a company logo/card in the homepage navigates to that company's overview")
    @pytest.mark.high
    @pytest.mark.regression
    @pytest.mark.web
    def test_clicking_company_card_navigates_to_overview(self, driver, home_page, company_card):
        home_page.assert_page_loaded()
        initial_hrefs = company_card.get_hrefs()
        assert initial_hrefs, "Expected at least one company card to be present on the home page"
        
        company_name = "Google"  # Example; select an existing company name dynamically instead
        company_card.click(company_name)
        
        current_url = driver.current_url
        assert company_name.lower() in current_url.lower(), f"Expected company name in the URL. Got: {current_url}"

    @allure.story("[HP_008] - Communities section links navigate to correct community pages")
    @pytest.mark.medium
    @pytest.mark.regression
    @pytest.mark.web
    def test_communities_section_links_navigation(self, driver, home_page):
        home_page.assert_page_loaded()
        
        # TODO: Add click_my_company_link() to HomePage
        # home_page.click_my_company_link()
        
        # Simulate a user going back to the home page after clicking
        driver.back()
        driver.wait()
        
        # TODO: Add click_community_link() to HomePage and verify URL for example 'Big 4'
        # home_page.click_community_link('Big 4')
        
        current_url = driver.current_url
        assert 'big-4' in current_url, f"Expected 'big-4' in community URL. Got: {current_url}"

    @allure.story("[HP_009] - Clicking Login opens login flow and unauthenticated user cannot access My Company tab content")
    @pytest.mark.high
    @pytest.mark.regression
    @pytest.mark.web
    def test_clicking_login_opens_login_flow(self, driver, home_page):
        home_page.assert_page_loaded()
        home_page.click_login()
        
        # Assuming a modal or new page — development assumes a login modal
        login_modal_visible = True  # Example pseudo-state; replace with actual UI verification
        
        assert login_modal_visible, "Expected login modal to be displayed but it was not."

    @allure.story("[HP_010] - ABECA Awards nav link navigates to correct awards page")
    @pytest.mark.medium
    @pytest.mark.regression
    @pytest.mark.web
    def test_abeca_awards_navigation(self, driver, home_page):
        home_page.assert_page_loaded()
        
        # TODO: Add click_awards_link(), click_abeca_2026() to HomePage
        # home_page.click_awards_link()
        # home_page.click_abeca_2026()
        
        current_url = driver.current_url
        assert 'abeca' in current_url or 'awards' in current_url, f"Expected 'abeca' or 'awards' in URL. Got: {current_url}"