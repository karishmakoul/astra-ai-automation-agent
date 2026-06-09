"""
Flow Extractor: parses generated test code with AST and extracts the
ordered sequence of method calls inside each test function.

Used by Metric 6 (Flow Order Validation) to compare the generated
action sequence against the spec steps and navigation_flows.yaml rules.
"""
import ast
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ActionCall:
    """One method call extracted from a test function."""
    obj:    str   # page/component object name (e.g. salaries_page, filter_panel)
    method: str   # method name (e.g. search_designation)
    line:   int   # source line number
    category: str = ""  # navigation | interaction | assertion | unknown

    def full(self) -> str:
        return f"{self.obj}.{self.method}()"


@dataclass
class TestFlow:
    """Ordered action sequence for one test function."""
    function_name: str
    actions:  list[ActionCall] = field(default_factory=list)
    has_navigation: bool = False
    has_interaction: bool = False
    has_assertion: bool = False
    issues: list[str] = field(default_factory=list)

    def action_summary(self) -> str:
        return " → ".join(a.full() for a in self.actions)


# ── Categorisation rules ─────────────────────────────────────────────────────

_NAVIGATION_METHODS = {
    "open", "navigate", "go_to", "goto", "visit",
    "go_to_reviews", "go_to_salaries", "go_to_jobs",
    "go_to_interviews", "go_to_companies",
}

_ASSERTION_METHODS = {
    "assert", "assert_page_loaded", "assert_text_present",
    "assert_url_contains", "assert_visible", "assert_companies_listed",
    "assert_platform_stats", "assert_write_review_visible",
    "assert_gender_ratings_differ", "assert_nav_links_visible",
    "assert_login_button_visible",
}

_ASSERTION_PREFIXES = ("assert_", "verify_", "check_")

_PLAIN_ASSERT_NODES = (ast.Assert,)


def _categorise(method: str) -> str:
    m = method.lower()
    if m in _NAVIGATION_METHODS or m == "open":
        return "navigation"
    if m in _ASSERTION_METHODS or m.startswith(_ASSERTION_PREFIXES):
        return "assertion"
    # get_* / count_* = read — treat as neutral interaction
    if m.startswith("get_") or m.startswith("count_") or m.startswith("is_"):
        return "read"
    return "interaction"


# ── AST walking ──────────────────────────────────────────────────────────────

class _FlowVisitor(ast.NodeVisitor):
    """Walk a test function body and collect ordered ActionCall objects."""

    def __init__(self):
        self.actions: list[ActionCall] = []

    def visit_Expr(self, node):
        """Capture method calls like salaries_page.open()"""
        if isinstance(node.value, ast.Call):
            self._handle_call(node.value)
        self.generic_visit(node)

    def visit_Assign(self, node):
        """Capture assignments like result = salaries_page.get_salary_ranges()"""
        if isinstance(node.value, ast.Call):
            self._handle_call(node.value)
        self.generic_visit(node)

    def visit_Assert(self, node):
        """Capture plain `assert` statements."""
        self.actions.append(ActionCall(
            obj="assert", method="assert", line=node.lineno,
            category="assertion",
        ))
        self.generic_visit(node)

    def _handle_call(self, call: ast.Call):
        if isinstance(call.func, ast.Attribute):
            if isinstance(call.func.value, ast.Name):
                obj    = call.func.value.id
                method = call.func.attr
                self.actions.append(ActionCall(
                    obj=obj, method=method,
                    line=getattr(call, "lineno", 0),
                    category=_categorise(method),
                ))


def extract_flows(source: str) -> list[TestFlow]:
    """
    Parse a generated test file source and return one TestFlow per test function.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return []

    flows: list[TestFlow] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if not node.name.startswith("test_"):
            continue

        visitor = _FlowVisitor()
        for child in node.body:
            visitor.visit(child)

        flow = TestFlow(function_name=node.name, actions=visitor.actions)

        # Classify what's present
        categories = {a.category for a in flow.actions}
        flow.has_navigation  = "navigation" in categories
        flow.has_interaction = "interaction" in categories or "read" in categories
        flow.has_assertion   = "assertion" in categories

        # Detect ordering issues
        if flow.actions:
            first_cat = flow.actions[0].category
            if first_cat == "assertion":
                flow.issues.append(
                    f"{node.name}: first action is an assertion — navigation missing"
                )
            if first_cat == "interaction":
                flow.issues.append(
                    f"{node.name}: first action is an interaction — open()/navigate() missing"
                )

        # Check assertion exists
        if not flow.has_assertion:
            flow.issues.append(
                f"{node.name}: no assertion found — test may not verify anything"
            )

        # Check for pass stubs
        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            flow.issues.append(f"{node.name}: body is a pass stub — not implemented")
        if all(isinstance(s, (ast.Pass, ast.Expr)) and
               (isinstance(s, ast.Pass) or (
                   isinstance(s.value, ast.Constant) and isinstance(s.value.value, str)
               )) for s in node.body):
            if not flow.has_assertion and not flow.has_navigation:
                flow.issues.append(f"{node.name}: test body appears empty or stub-only")

        flows.append(flow)

    return flows


def extract_todo_count(source: str) -> int:
    """Count # TODO lines in the source."""
    return sum(1 for line in source.splitlines() if "# TODO" in line)


def extract_method_calls(source: str) -> list[str]:
    """Return a flat list of all obj.method() strings called in the file."""
    calls = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return calls

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name):
                    calls.append(f"{node.func.value.id}.{node.func.attr}")
    return calls
