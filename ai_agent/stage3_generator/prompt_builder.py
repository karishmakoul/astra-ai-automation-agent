"""
Prompt Builder: constructs the system prompt and user message for Claude.

The system prompt is the most critical piece — it defines:
  1. Claude's identity and constraints
  2. The exact output format required
  3. The anti-hallucination rules
  4. The test writing conventions of this specific codebase
"""
from ai_agent.models import TestSpec
from ai_agent.stage2_context_retrieval.retriever import RetrievalResult


SYSTEM_PROMPT = """
You are a senior QA automation engineer working on a Playwright + Python test \
automation framework for AmbitionBox (https://www.ambitionbox.com).

Your task is to write pytest test functions for the given test cases.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANTI-HALLUCINATION RULES (CRITICAL)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. ALWAYS call list_page_methods() for every page/component you plan to use
   BEFORE writing any test code. Never assume a method exists.

2. ALWAYS call get_fixtures() before deciding which fixtures to use.
   Never invent fixture names.

3. If a method you want to use does not exist in list_page_methods() output,
   either use a different method that does exist, or call read_file() to
   check base_page.py for inherited methods.

4. If you cannot perform an action with available methods, add a comment:
   # TODO: add <method_name>(args) to <PageObject>

5. NEVER use page.locator(), page.goto(), or any raw Playwright API directly
   in tests. All browser interactions MUST go through page object methods.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CODEBASE CONVENTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Framework: pytest + Playwright (sync) + Allure reporting

File naming:  tests/ambitionbox/test_{page_name}.py
Class naming: Test{PageName} (e.g. TestSalariesPage)
Method naming: test_{what_is_being_tested} (snake_case, descriptive)

Required imports (always include these):
  import pytest
  import allure

Required decorators on every test class:
  @allure.feature("{Page Name}")

Required decorators on every test method:
  @allure.story("{TC_ID} - {title}")
  @pytest.mark.{priority}    # critical | high | medium | low
  @pytest.mark.regression    # or smoke if applicable
  @pytest.mark.web

Fixture pattern (from conftest.py):
  def test_something(self, driver, {page_fixture}, {component_fixtures}):
  # driver MUST always be the first fixture
  # page_fixture is the page object (e.g. companies_page, salaries_page)

Assertion style:
  Use plain Python assert with descriptive messages
  Example: assert "google" in url.lower(), f"Expected google in URL. Got: {url}"
  Do NOT use unittest-style assertEqual, assertTrue etc.

DO NOT assert exact counts or exact text values from live data.
The site has live user-contributed data that changes daily.
Always assert: existence, ranges, relative comparisons, pattern matches.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT (STRICT)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Output ONLY raw Python code. No markdown. No explanation. No code fences.
Start directly with: import pytest

If conflicts are detected in the context, output ONLY:
CONFLICT: <description of the conflict>
SOURCES: <file_a>, <file_b>
QUESTION: <what needs human clarification>
""".strip()


def build_user_message(spec: TestSpec, retrieval: RetrievalResult) -> str:
    """Build the user message combining TestSpec + retrieved context."""

    # ── Section 1: Test Specification ─────────────────────────────────────
    tc_lines = []
    for tc in spec.test_cases:
        tc_lines.append(f"""
  [{tc.id}] {tc.title}
  Priority: {tc.priority.value} | Type: {tc.type.value}
  Preconditions: {', '.join(tc.preconditions) or 'None'}
  Steps:
{chr(10).join(f'    {step}' for step in tc.steps)}
  Expected Result: {tc.expected_result}""")

    spec_section = f"""## TEST SPECIFICATION
Source: {spec.source.value} | ID: {spec.source_id}
Title: {spec.title}
Description: {spec.description}
Affected Pages: {', '.join(spec.affected_pages) or 'unknown'}
User Types: {', '.join(spec.user_types) or 'not specified'}

Acceptance Criteria:
{chr(10).join(f'  • {ac}' for ac in spec.acceptance_criteria) or '  (none specified)'}

Test Cases to Implement ({len(spec.test_cases)} total):
{''.join(tc_lines)}"""

    # ── Section 2: Retrieved Context ───────────────────────────────────────
    context_section = f"""## RETRIEVED CONTEXT (grounded in actual codebase)
{retrieval.context_for_prompt()}"""

    # ── Section 3: Task Instructions ──────────────────────────────────────
    pages_str = ", ".join(spec.affected_pages) or "the relevant page"
    task_section = f"""## YOUR TASK

1. Call get_fixtures() to know available fixtures.
2. Call list_page_methods() for each of these pages/components:
   {pages_str}, and any components used (filter_panel, search_bar, company_card).
3. For any method you are unsure about, call read_file() on the relevant file.
4. Write ONE complete pytest file with ALL {len(spec.test_cases)} test cases.
5. Follow EVERY convention rule from the system prompt exactly.
6. Output ONLY raw Python — no markdown, no explanation."""

    return "\n\n".join([spec_section, context_section, task_section])
