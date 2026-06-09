"""
7 DeepEval GEval metrics for evaluating AI-generated pytest test code.

Each metric returns a MetricResult with a score (0–1), pass/fail, and reasoning.

Categories:
  Code Quality  (metrics 1-3) — structural correctness
  Spec Fidelity (metrics 4-5) — does it test what was asked?
  Flow Correct  (metrics 6-7) — is the sequence of steps right?
"""
from deepeval import evaluate
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

from ai_agent.stage4_eval.models import MetricResult
from ai_agent.stage4_eval.flow_extractor import extract_flows, extract_todo_count


# ── Shared LLM model for all GEval metrics ───────────────────────────────────
_EVAL_MODEL = "gpt-4o"


# ═════════════════════════════════════════════════════════════════════════════
# CATEGORY 1 — CODE QUALITY
# ═════════════════════════════════════════════════════════════════════════════

def metric_no_hallucinated_methods(
    generated_code: str,
    page_api_context: str,        # output of tool_list_page_methods() for each page
) -> MetricResult:
    """
    Metric 1: Every method called in the test code must exist in the
    page object API. Hallucinated method = instant fail.
    """
    metric = GEval(
        name="No Hallucinated Methods",
        model=_EVAL_MODEL,
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.CONTEXT,
        ],
        criteria="""
You are evaluating AI-generated pytest test code for method hallucination.

The CONTEXT contains the ONLY methods available on each page object and component.
The ACTUAL_OUTPUT is the generated Python test code.

Your task:
1. Find every method call in the test code (obj.method() pattern).
2. Check each method against the CONTEXT API list.
3. A method is HALLUCINATED if it appears in the test code but does NOT exist
   in the context API list for that object.
4. Ignore: assert, Python built-ins, pytest methods, fixture names.

Score:
  1.0  = zero hallucinated methods
  0.75 = 1 hallucinated method
  0.5  = 2 hallucinated methods
  0.0  = 3 or more hallucinated methods

In your reason, list each hallucinated method found (or confirm none found).
        """.strip(),
        threshold=0.75,
    )

    test_case = LLMTestCase(
        input="Verify generated test code uses only real page object methods",
        actual_output=generated_code,
        context=[page_api_context],
    )

    metric.measure(test_case)
    issues = []
    if metric.score < 1.0:
        issues.append(f"Hallucinated methods detected: {metric.reason}")

    return MetricResult(
        name="No Hallucinated Methods",
        score=round(metric.score, 3),
        passed=metric.is_successful(),
        reason=metric.reason or "",
        issues=issues,
    )


def metric_fixture_accuracy(
    generated_code: str,
    available_fixtures: str,      # output of tool_get_fixtures()
) -> MetricResult:
    """
    Metric 2: Every fixture name in test function signatures must exist
    in conftest.py. Invented fixtures cause import errors.
    """
    # Static check first — parse fixtures from generated code
    import ast, re
    static_issues = []
    fixture_lines = re.findall(r'def test_\w+\(self,(.*?)\):', generated_code)
    used_fixtures = set()
    for line in fixture_lines:
        for f in line.split(','):
            name = f.strip().split(':')[0].strip()
            if name:
                used_fixtures.add(name)

    known = set(
        line.strip().split('(')[0].strip()
        for line in available_fixtures.splitlines()
        if line.strip() and not line.strip().startswith('#')
    )

    invented = used_fixtures - known - {'self', 'request'}
    score = 1.0 if not invented else max(0.0, 1.0 - (len(invented) * 0.3))

    if invented:
        static_issues.append(f"Invented fixtures (not in conftest.py): {', '.join(invented)}")

    return MetricResult(
        name="Fixture Accuracy",
        score=round(score, 3),
        passed=score >= 0.9,
        reason=f"Used fixtures: {used_fixtures}. Known: {known}. Invented: {invented}",
        issues=static_issues,
    )


def metric_convention_adherence(
    generated_code: str,
    spec_title: str,
) -> MetricResult:
    """
    Metric 3: Check codebase conventions from SYSTEM_PROMPT are followed.
    Uses a mix of static checks + GEval.
    """
    issues = []
    score_parts = []

    # Static checks
    checks = [
        ("@allure.feature" in generated_code,        "@allure.feature decorator missing"),
        ("@allure.story"   in generated_code,        "@allure.story decorator missing on tests"),
        ("@pytest.mark."   in generated_code,        "@pytest.mark.{priority} missing"),
        ("import pytest"   in generated_code,        "import pytest missing"),
        ("import allure"   in generated_code,        "import allure missing"),
        ("page.locator("   not in generated_code,    "Raw page.locator() used — must go through page object"),
        ("page.goto("      not in generated_code,    "Raw page.goto() used — must go through page object"),
        (".assertEqual("   not in generated_code,    "unittest-style assertEqual used — use plain assert"),
        (".assertTrue("    not in generated_code,    "unittest-style assertTrue used — use plain assert"),
    ]

    for passed, msg in checks:
        score_parts.append(1.0 if passed else 0.0)
        if not passed:
            issues.append(msg)

    score = sum(score_parts) / len(score_parts)

    return MetricResult(
        name="Convention Adherence",
        score=round(score, 3),
        passed=score >= 0.80,
        reason=f"{int(score * len(checks))}/{len(checks)} conventions followed",
        issues=issues,
    )


# ═════════════════════════════════════════════════════════════════════════════
# CATEGORY 2 — SPEC FIDELITY
# ═════════════════════════════════════════════════════════════════════════════

def metric_spec_coverage(
    generated_code: str,
    spec_summary: str,            # formatted list of TC IDs + titles from TestSpec
    total_tc_count: int,
) -> MetricResult:
    """
    Metric 4: Every test case in the spec must have a corresponding
    test function that asserts the expected result.
    """
    metric = GEval(
        name="Spec Coverage",
        model=_EVAL_MODEL,
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.EXPECTED_OUTPUT,
        ],
        criteria="""
You are evaluating whether AI-generated pytest code covers all required test cases.

The INPUT lists the required test cases (TC IDs and titles).
The ACTUAL_OUTPUT is the generated Python test code.
The EXPECTED_OUTPUT is the total number of test cases that should be implemented.

Your task:
1. For each TC ID in INPUT, find a corresponding test function in ACTUAL_OUTPUT.
2. A test is COVERED if:
   - A test function exists for that TC
   - The function body is NOT just `pass` or an empty stub
   - The function contains at least one assertion (assert statement)
3. A test is NOT COVERED if: no function found, or body is pass-only.

Score = covered_count / total_count

In your reason: list which TCs are covered and which are missing/stubbed.
        """.strip(),
        threshold=0.80,
    )

    test_case = LLMTestCase(
        input=spec_summary,
        actual_output=generated_code,
        expected_output=str(total_tc_count),
    )

    metric.measure(test_case)
    issues = []
    if metric.score < 1.0:
        issues.append(f"Spec coverage gap: {metric.reason}")

    return MetricResult(
        name="Spec Coverage",
        score=round(metric.score, 3),
        passed=metric.is_successful(),
        reason=metric.reason or "",
        issues=issues,
    )


def metric_assertion_strength(generated_code: str) -> MetricResult:
    """
    Metric 5: Assertions must verify specific behaviour.
    Trivially weak assertions (assert True, assert x, pass stubs) are penalised.
    """
    metric = GEval(
        name="Assertion Strength",
        model=_EVAL_MODEL,
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
        ],
        criteria="""
You are evaluating the quality of assertions in AI-generated pytest test code.

For each test function in ACTUAL_OUTPUT, evaluate its assertions:

STRONG assertion (score contribution 1.0):
  - Checks specific content: assert "google" in url.lower()
  - Checks ranges: assert 1.0 <= rating <= 5.0
  - Checks meaningful existence: assert len(results) > 0
  - Checks relative comparison: assert filtered != default
  - Checks pattern: assert re.search(r'\\d+', text)

WEAK assertion (score contribution 0.0):
  - assert True
  - assert x  (bare variable with no comparison)
  - assert page_text  (truthy check only)
  - assert result != ""  (trivially true)
  - pass  (no assertion at all)
  - assert result is not None  (with no further check)

Score = strong_assertion_count / total_assertion_count
If no assertions exist: score = 0.0

List each weak assertion and which test it appears in.
        """.strip(),
        threshold=0.70,
    )

    test_case = LLMTestCase(
        input="Evaluate assertion quality in the generated test code",
        actual_output=generated_code,
    )

    metric.measure(test_case)
    issues = []
    if metric.score < 1.0:
        issues.append(f"Weak assertions found: {metric.reason}")

    return MetricResult(
        name="Assertion Strength",
        score=round(metric.score, 3),
        passed=metric.is_successful(),
        reason=metric.reason or "",
        issues=issues,
    )


# ═════════════════════════════════════════════════════════════════════════════
# CATEGORY 3 — FLOW CORRECTNESS
# ═════════════════════════════════════════════════════════════════════════════

def metric_flow_order_validation(
    generated_code: str,
    spec_steps_summary: str,       # ordered steps from TestSpec
    navigation_flows_context: str, # relevant section from navigation_flows.yaml
) -> MetricResult:
    """
    Metric 6: The sequence of actions in each test must follow the correct order:
    navigate → interact → assert. Validated against spec steps and known flows.
    """
    # Extract flows with static AST analysis first
    flows = extract_flows(generated_code)
    static_issues = []
    for flow in flows:
        static_issues.extend(flow.issues)

    # Build a summary for GEval
    flow_summary = "\n".join(
        f"  {f.function_name}: {f.action_summary() or '(empty)'}"
        for f in flows
    )

    metric = GEval(
        name="Flow Order Validation",
        model=_EVAL_MODEL,
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.CONTEXT,
        ],
        criteria="""
You are evaluating whether AI-generated test code follows the correct action flow.

The INPUT contains the REQUIRED steps from the test specification (in order).
The ACTUAL_OUTPUT contains the extracted action sequence from the generated code.
The CONTEXT contains known valid flow patterns from the navigation knowledge base.

Evaluate each test function:

1. ORDER RULE: Actions must follow: navigate/open → interact/search → assert
   - open() or navigate() MUST come before any interaction
   - Assertions MUST come after interactions
   - Penalty for: assertion before navigation, interaction before open()

2. SPEC MAPPING: Each spec step should have a corresponding code action.
   - "Navigate to salaries page" → salaries_page.open()
   - "Apply experience filter" → filter_panel.apply(...)
   - "Verify salary ranges shown" → assert / get_salary_ranges()
   Penalty for: spec steps with no code equivalent

3. PATTERN MATCH: The sequence should match a known valid flow from CONTEXT
   or at minimum not match any invalid_pattern.

Score:
  1.0 = perfect order, all spec steps covered, matches known valid flow
  0.75 = minor ordering issue OR 1 spec step missing
  0.5  = clear ordering violation OR multiple steps missing
  0.0  = completely wrong order or empty tests

List specific ordering violations by test function name.
        """.strip(),
        threshold=0.70,
    )

    test_case = LLMTestCase(
        input=spec_steps_summary,
        actual_output=flow_summary,
        context=[navigation_flows_context],
    )

    metric.measure(test_case)

    all_issues = static_issues.copy()
    if metric.score < 1.0:
        all_issues.append(f"Flow order issue: {metric.reason}")

    # Blend static + LLM scores
    static_score = 1.0 - (min(len(static_issues), 3) * 0.2)
    blended = round((metric.score * 0.7 + static_score * 0.3), 3)

    return MetricResult(
        name="Flow Order Validation",
        score=blended,
        passed=blended >= 0.70,
        reason=metric.reason or "",
        issues=all_issues,
    )


def metric_business_rule_compliance(
    generated_code: str,
    business_rules_context: str,   # relevant section from business_rules.yaml
    affected_pages: list[str],
) -> MetricResult:
    """
    Metric 7: The generated test must comply with known business rules
    (login walls, filter pre-conditions, data format expectations, etc.)
    """
    metric = GEval(
        name="Business Rule Compliance",
        model=_EVAL_MODEL,
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.CONTEXT,
        ],
        criteria="""
You are evaluating whether AI-generated test code complies with known business rules.

The CONTEXT contains the business rules for this application.
The ACTUAL_OUTPUT is the generated Python test code.
The INPUT lists the affected pages being tested.

Check each rule in CONTEXT against the generated code:

KEY RULES TO ENFORCE:
1. LOGIN WALL: If tests access salary figures, review writing, or job applications,
   they must either handle the login wall OR explicitly assert that the login
   modal appears. Penalty if salary/review data is accessed without login handling.

2. FILTER ORDER: On companies/jobs pages, search or open() must come before
   filter_panel.apply(). Never filter on an empty page.

3. LIVE DATA: Tests must NOT assert exact counts or exact text from live data.
   Bad: assert rating == 3.3
   Good: assert 1.0 <= rating <= 5.0

4. OVERLAY: On the home page, dismiss_overlay() should be called before
   any navigation interaction.

5. SALARY FORMAT: Salary assertions should check for ₹ and /yr patterns,
   not exact values.

Score:
  1.0 = all applicable rules followed
  0.75 = 1 rule violated
  0.5  = 2 rules violated
  0.0  = 3+ rules violated

For each violation: state the rule, the test function, and the problematic line.
        """.strip(),
        threshold=0.75,
    )

    test_case = LLMTestCase(
        input=f"Affected pages: {', '.join(affected_pages)}",
        actual_output=generated_code,
        context=[business_rules_context],
    )

    metric.measure(test_case)
    issues = []
    if metric.score < 1.0:
        issues.append(f"Business rule violation: {metric.reason}")

    return MetricResult(
        name="Business Rule Compliance",
        score=round(metric.score, 3),
        passed=metric.is_successful(),
        reason=metric.reason or "",
        issues=issues,
    )
