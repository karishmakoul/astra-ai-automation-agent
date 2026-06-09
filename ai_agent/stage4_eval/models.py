"""
Eval Agent data models.

EvalReport      — top-level report for one generated test file
MetricResult    — score + reasoning for one metric
TestCaseResult  — per-test-function verdict
ContextCoverage — pre-generation coverage check result
"""
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class CoverageLevel(str, Enum):
    HIGH   = "high"     # full page object + similar tests + business rules
    MEDIUM = "medium"   # page object exists but gaps (missing methods / no tests)
    LOW    = "low"      # no page object, no tests, minimal knowledge


class Recommendation(str, Enum):
    ACCEPT     = "accept"      # score >= threshold
    REGENERATE = "regenerate"  # score in mid-band, retry with eval feedback
    ESCALATE   = "escalate"    # score too low after retries


@dataclass
class MetricResult:
    name:    str
    score:   float          # 0.0 – 1.0
    passed:  bool           # score >= metric threshold
    reason:  str = ""       # GPT-4o explanation
    issues:  list[str] = field(default_factory=list)

    def short(self) -> str:
        icon = "✅" if self.passed else "❌"
        return f"{icon} {self.name:<35} {self.score:.2f}"


@dataclass
class TestCaseResult:
    tc_id:    str           # SAL_001
    function: str           # test_searching_by_designation_shows_salary_range
    covered:  bool          # corresponding function found in generated file
    issues:   list[str] = field(default_factory=list)


@dataclass
class EvalReport:
    filepath:       str                          # tests/ambitionbox/test_*.py
    generated_at:   datetime = field(default_factory=datetime.utcnow)

    # ── Per-metric scores ───────────────────────────────────────────────────
    metrics:        list[MetricResult] = field(default_factory=list)

    # ── Per-test-case coverage ──────────────────────────────────────────────
    test_case_results: list[TestCaseResult] = field(default_factory=list)

    # ── Aggregated ─────────────────────────────────────────────────────────
    overall_score:  float = 0.0
    passed:         bool  = False
    recommendation: Recommendation = Recommendation.ESCALATE
    issues:         list[str] = field(default_factory=list)
    tokens_used:    int   = 0

    # ── Threshold config ────────────────────────────────────────────────────
    ACCEPT_THRESHOLD:     float = 0.70
    REGENERATE_THRESHOLD: float = 0.50

    def compute(self) -> "EvalReport":
        """Calculate overall_score, passed, recommendation from metric results."""
        WEIGHTS = {
            "No Hallucinated Methods":   0.15,
            "Fixture Accuracy":          0.10,
            "Convention Adherence":      0.05,
            "Spec Coverage":             0.25,
            "Assertion Strength":        0.15,
            "Flow Order Validation":     0.15,
            "Business Rule Compliance":  0.15,
        }
        weighted_sum = 0.0
        weight_total = 0.0
        for m in self.metrics:
            w = WEIGHTS.get(m.name, 0.10)
            weighted_sum += m.score * w
            weight_total += w

        self.overall_score = round(weighted_sum / weight_total if weight_total else 0.0, 3)
        self.passed        = self.overall_score >= self.ACCEPT_THRESHOLD

        if self.overall_score >= self.ACCEPT_THRESHOLD:
            self.recommendation = Recommendation.ACCEPT
        elif self.overall_score >= self.REGENERATE_THRESHOLD:
            self.recommendation = Recommendation.REGENERATE
        else:
            self.recommendation = Recommendation.ESCALATE

        # Collect all issues across metrics
        for m in self.metrics:
            self.issues.extend(m.issues)

        return self


@dataclass
class ContextCoverage:
    level:              CoverageLevel
    page_object_found:  bool  = False
    similar_tests:      int   = 0
    knowledge_chunks:   int   = 0
    missing:            list[str] = field(default_factory=list)
    detail:             str   = ""
