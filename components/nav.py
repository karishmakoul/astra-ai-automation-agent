import allure
from playwright.sync_api import Page


class LeftNav:
    """
    Reusable left-navigation component shared across every page.
    Instantiate with the current Playwright page object.
    """

    NAV_LINKS = {
        "home":               '[data-testid="nav-group-link-home"]',
        "companies":          '[data-testid="nav-group-link-companies"]',
        "reviews":            '[data-testid="nav-group-link-reviews"]',
        "salaries":           '[data-testid="nav-group-link-salaries"]',
        "interviews":         '[data-testid="nav-group-link-interview-questions"]',
        "jobs":               '[data-testid="nav-group-link-jobs"]',
    }

    TOOLS_TOGGLE   = '[data-testid="nav-group-toggle-tools"]'
    AWARDS_TOGGLE  = '[data-testid="nav-group-toggle-awards"]'
    TOOLS_ITEMS    = '[data-testid="nav-group-items-tools"] [data-testid="nav-menu-item"]'
    COMMUNITIES_TOGGLE = '[data-testid="left-nav-communities-toggle"]'

    def __init__(self, page: Page):
        self.page = page

    @allure.step("Navigate via left nav to: {section}")
    def go_to(self, section: str) -> str:
        """
        Click a top-level nav link by name.
        Returns the URL after navigation.
        section: 'home' | 'companies' | 'reviews' | 'salaries' | 'interviews' | 'jobs'
        """
        locator = self.NAV_LINKS.get(section.lower())
        if not locator:
            raise ValueError(f"Unknown nav section: '{section}'. Valid: {list(self.NAV_LINKS)}")
        # Dismiss any coachmark overlay that may block the click
        overlay_sel = '[data-testid*="coachmark-overlay"]'
        overlay = self.page.locator(overlay_sel).first
        if overlay.is_visible():
            overlay.click(force=True)
            try:
                self.page.locator(overlay_sel).wait_for(state="hidden", timeout=3000)
            except Exception:
                pass
        self.page.locator(locator).click()
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(800)
        return self.page.url

    @allure.step("Open Tools section in left nav")
    def open_tools(self):
        overlay_sel = '[data-testid="home-feed-tabs-coachmark-overlay"]'
        overlay = self.page.locator(overlay_sel).first
        if overlay.is_visible():
            overlay.click(force=True)
            try:
                self.page.locator(overlay_sel).wait_for(state="hidden", timeout=3000)
            except Exception:
                pass
        if self.page.locator(self.TOOLS_ITEMS).count() == 0:
            self.page.locator(self.TOOLS_TOGGLE).click()
            self.page.wait_for_timeout(400)

    TOOL_HREFS = {
        "Compare Companies":    "/compare",
        "Salary Calculator":    "/salaries/take-home-salary-calculator",
        "Are you paid fairly?": "/are-you-paid-fairly",
        "Evaluate Offer Letter":"/tools/offer-letter-comparison",
        "Gratuity Calculator":  "/tools/gratuity-calculator",
        "HRA Calculator":       "/tools/hra-calculator",
        "Salary Hike Calculator":"/tools/salary-hike-calculator",
    }

    @allure.step("Click tool: {tool_name}")
    def click_tool(self, tool_name: str) -> str:
        """Navigate directly to the tool URL — avoids submenu intercept issues."""
        path = self.TOOL_HREFS.get(tool_name)
        if not path:
            raise ValueError(f"Unknown tool: '{tool_name}'. Available: {list(self.TOOL_HREFS)}")
        self.page.goto(f"https://www.ambitionbox.com{path}", wait_until="domcontentloaded")
        self.page.wait_for_timeout(1500)
        return self.page.url

    def get_active_link_text(self) -> str:
        """Returns the text of whichever nav link is currently active."""
        for name, sel in self.NAV_LINKS.items():
            el = self.page.locator(sel)
            if el.count() and el.is_visible():
                classes = el.get_attribute("class") or ""
                parent_classes = el.evaluate("e => e.closest('[class]')?.className || ''")
                if "active" in classes or "active" in parent_classes or "selected" in classes:
                    return name
        return ""
