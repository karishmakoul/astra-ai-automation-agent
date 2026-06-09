import pytest
import allure

@allure.feature("Reviews Page")
class TestReviewsPage:

    @allure.story("RV_001 - Overall rating displayed matches sum of category ratings")
    @pytest.mark.critical
    @pytest.mark.regression
    @pytest.mark.web
    def test_overall_rating_matches_category_average(self, driver, reviews_page):
        reviews_page.open("tcs")
        overall_rating = reviews_page.get_overall_rating()
        category_ratings = [
            reviews_page.get_category_rating("Job Security"),
            reviews_page.get_category_rating("Work-Life Balance"),
            reviews_page.get_category_rating("Culture")
            # Add more categories if needed
        ]
        average_category_rating = sum(category_ratings) / len(category_ratings)
        assert abs(overall_rating - average_category_rating) <= 0.1, \
            f"Expected overall rating to match average of categories: {average_category_rating}, but got: {overall_rating}"

    @allure.story("RV_002 - Filter by Department shows only reviews from that department")
    @pytest.mark.critical
    @pytest.mark.regression
    @pytest.mark.web
    def test_filter_by_department_shows_correct_reviews(self, driver, reviews_page):
        reviews_page.open("tcs")
        reviews_page.apply_filter("Department", "Engineering")
        # Pseudo-code, replace with actual method to get card details:
        department_reviews = reviews_page.get_review_departments()
        assert all(dept == "Engineering" for dept in department_reviews), \
            "Expected all reviews to be from 'Engineering' department"

    @allure.story("RV_003 - Filter by Designation shows only reviews from employees in that role")
    @pytest.mark.critical
    @pytest.mark.regression
    @pytest.mark.web
    def test_filter_by_designation_shows_correct_reviews(self, driver, reviews_page):
        reviews_page.open("tcs")
        reviews_page.apply_filter("Designation", "Software Engineer")
        # Pseudo-code, replace with actual method to read review designations:
        designations = reviews_page.get_review_designations()
        assert all("Software Engineer" in designation for designation in designations), \
            "Expected all reviews to be from 'Software Engineer' designation"

    @allure.story("RV_006 - Sort by Detailed shows reviews with more text content")
    @pytest.mark.medium
    @pytest.mark.regression
    @pytest.mark.web
    def test_sort_by_detailed_shows_longer_reviews(self, driver, reviews_page):
        reviews_page.open("tcs")
        initial_texts = reviews_page.get_review_texts(n=3)
        reviews_page.sort_by("Detailed")
        detailed_texts = reviews_page.get_review_texts(n=3)
        assert all(len(detailed) >= len(initial) for detailed, initial in zip(detailed_texts, initial_texts)), \
            "Expected 'Detailed' sorted reviews to be longer than 'Popular' sorted reviews"

    @allure.story("RV_008 - Category ratings in breakdown match individual review cards")
    @pytest.mark.high
    @pytest.mark.regression
    @pytest.mark.web
    def test_category_ratings_consistent_with_review_cards(self, driver, reviews_page):
        reviews_page.open("tcs")
        salary_category_rating = reviews_page.get_category_rating("Salary")
        # Pseudo-code, replace with actual method to get sub-rating from review:
        review_salary_ratings = reviews_page.get_review_salary_ratings()
        assert any(abs(salary_category_rating - review_rating) <= 0.1 for review_rating in review_salary_ratings), \
            "Expected salary ratings on review cards to match 'Salary' category rating"

    @allure.story("RV_012 - Clicking 'View all' on rating breakdown shows all categories")
    @pytest.mark.medium
    @pytest.mark.regression
    @pytest.mark.web
    def test_view_all_expands_rating_breakdown(self, driver, reviews_page):
        reviews_page.open("tcs")
        initial_visible_categories = reviews_page.get_visible_rating_categories()
        reviews_page.click_view_all_on_rating_breakdown()
        expanded_categories = reviews_page.get_visible_rating_categories()
        assert len(expanded_categories) > len(initial_visible_categories), \
            "Expected more categories to be visible after clicking 'View all'"

# Note: The pseudo-code comments indicate where additional methods are needed in the page object.