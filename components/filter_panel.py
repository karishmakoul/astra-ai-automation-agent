import allure
from playwright.sync_api import Page


class FilterPanel:
    """
    Reusable filter panel for Companies and Jobs pages.
    Uses JS-based interaction to handle the Vue-rendered filter sheet.
    Flow: All Filters → JS click filter section tab → JS click checkbox → JS click Apply.
    """

    ALL_FILTERS_BTN = '[data-testid="allFilters-desktop"]'
    SHEET           = "#bottomSheet"

    SORT_URL_PARAMS = {
        "Top Paying": "topPaying",
        "Popular":    "popular",
        "Latest":     "latest",
        "Relevance":  "relevance",
    }

    def __init__(self, page: Page):
        self.page = page

    def _open_filter_section(self, filter_name: str):
        """
        Click the TOP-BAR filter chip button to open the sheet AND activate
        that filter's section directly (more reliable than All Filters → tab click).
        """
        self.page.locator(f'button[data-testid="filterChip-{filter_name}"]').click()
        self.page.wait_for_timeout(1500)

    def _click_option(self, option_text: str) -> bool:
        """
        Click a label by its `for` attribute ID (most reliable) rather than by text.
        When the filter chip is clicked, an inline label matching the checkbox may appear
        OUTSIDE the bottomSheet — using querySelector('label[for=...]') finds that
        visible one, not the hidden one inside the filter content area.
        """
        clicked = self.page.evaluate("""(text) => {
            // First try: find by specific for-attribute constructed from value
            // The checkbox value pattern is: {section}_{value} (e.g. industries_pharma, locations_bengaluru)

            // Second try: find label visible to the user (parent container is visible)
            const labels = [...document.querySelectorAll('label')];
            const match = labels.find(l =>
                l.innerText.trim().toLowerCase().includes(text.toLowerCase()) &&
                window.getComputedStyle(l).display !== 'none' &&
                window.getComputedStyle(l.parentElement || l).display !== 'none'
            );
            if (match) {
                match.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                return {clicked: true, for: match.getAttribute('for'), text: match.innerText.trim().substring(0,30)};
            }
            return false;
        }""", option_text)
        self.page.wait_for_timeout(400)
        return bool(clicked)

    def _apply(self):
        """
        Call Vue's handleClick() on the Apply button — the only reliable
        way to trigger the filter application in this Vue 2 app.
        """
        self.page.evaluate("""() => {
            const btn = document.querySelector('#bottomSheet button[title="Apply"]');
            if (btn?.__vue__) {
                btn.__vue__.handleClick();
            } else if (btn) {
                btn.click();
            }
        }""")
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(4000)

    def _clear_all(self):
        self.page.evaluate("""() => {
            const btn = [...document.querySelectorAll('#bottomSheet button')]
                .find(b => b.innerText.trim() === 'Clear All');
            if (btn) btn.click();
        }""")
        self.page.wait_for_timeout(500)

    # ── Public API ────────────────────────────────────────────────

    @allure.step("Apply filter '{filter_name}' = '{option}'")
    def apply(self, filter_name: str, option: str):
        """Open the filter section via top-bar chip, select option, apply."""
        self._open_filter_section(filter_name)
        clicked = self._click_option(option)
        if not clicked:
            raise AssertionError(f"Filter option '{option}' not found in '{filter_name}' filter")
        self._apply()

    @allure.step("Clear all filters")
    def clear_all(self):
        self.page.locator(self.ALL_FILTERS_BTN).click()
        self.page.wait_for_timeout(800)
        # Click Clear All via Vue's handleClick
        self.page.evaluate("""() => {
            const btns = [...document.querySelectorAll('#bottomSheet button')];
            const clearBtn = btns.find(b => b.innerText.trim() === 'Clear All');
            if (clearBtn?.__vue__) clearBtn.__vue__.handleClick();
            else if (clearBtn) clearBtn.click();
        }""")
        self.page.wait_for_timeout(500)
        self._apply()

    @allure.step("Sort by: '{sort_option}'")
    def sort_by(self, sort_option: str):
        """Apply sort via URL param — most reliable approach for this site."""
        param = self.SORT_URL_PARAMS.get(sort_option, sort_option.lower().replace(" ", ""))
        base_url = self.page.url.split("?")[0]
        self.page.goto(f"{base_url}?sortBy={param}", wait_until="domcontentloaded")
        self.page.wait_for_timeout(2000)

    def get_checked_options(self) -> list[str]:
        """Return currently checked filter values."""
        return self.page.evaluate("""() =>
            [...document.querySelectorAll('#bottomSheet input[type="checkbox"]:checked')]
            .map(c => c.value)
        """)
