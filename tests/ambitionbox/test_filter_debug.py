import pytest


def test_filter_inline(driver, companies_page, company_card):
    """Direct click via label ID - this WORKS."""
    page = companies_page.page
    default_hrefs = set(company_card.get_hrefs())

    page.locator('button[data-testid="filterChip-Industry"]').click()
    page.wait_for_timeout(1500)

    result = page.evaluate("""() => {
        const label = document.querySelector('label[for="industries_pharma"]');
        if (label) {
            label.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
            return {method: 'id', id: label.getAttribute('for'), checked: document.querySelector('#bottomSheet input[value="pharma"]')?.checked};
        }
        return {method: 'id', found: false};
    }""")
    print(f"\nResult: {result}")
    page.wait_for_timeout(400)

    page.evaluate("""() => {
        const btn = document.querySelector('#bottomSheet button[title="Apply"]');
        if (btn?.__vue__) btn.__vue__.handleClick();
    }""")
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(4000)

    filtered_hrefs = set(company_card.get_hrefs())
    print(f"CHANGED: {default_hrefs != filtered_hrefs}, first filtered: {list(filtered_hrefs)[0]}")
    assert default_hrefs != filtered_hrefs


def test_filter_text_search(driver, companies_page, company_card):
    """Text search click - does this FAIL?"""
    page = companies_page.page
    default_hrefs = set(company_card.get_hrefs())

    page.locator('button[data-testid="filterChip-Industry"]').click()
    page.wait_for_timeout(1500)

    result = page.evaluate("""() => {
        const labels = [...document.querySelectorAll('#bottomSheet label')];
        const match = labels.find(l => l.innerText.trim().toLowerCase().includes('pharma'));
        if (match) {
            match.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
            return {method: 'text', for: match.getAttribute('for'), text: match.innerText.trim(), checked: document.querySelector('#bottomSheet input[value="pharma"]')?.checked};
        }
        return {method: 'text', found: false};
    }""")
    print(f"\nResult: {result}")
    page.wait_for_timeout(400)

    page.evaluate("""() => {
        const btn = document.querySelector('#bottomSheet button[title="Apply"]');
        if (btn?.__vue__) btn.__vue__.handleClick();
    }""")
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(4000)

    filtered_hrefs = set(company_card.get_hrefs())
    print(f"CHANGED: {default_hrefs != filtered_hrefs}, first filtered: {list(filtered_hrefs)[0]}")
    assert default_hrefs != filtered_hrefs
