"""
Context Coverage Checker: runs BEFORE Stage 3 generation.

Inspects the RetrievalResult and the codebase to decide whether
the agent has enough context to generate reliable tests.

Returns a ContextCoverage object with level HIGH / MEDIUM / LOW
so the caller can route to: normal generate / scaffold / discovery mode.
"""
from pathlib import Path

from ai_agent.stage2_context_retrieval.retriever import RetrievalResult
from ai_agent.stage4_eval.models import ContextCoverage, CoverageLevel

PROJECT_ROOT = Path(__file__).parent.parent.parent


def check_coverage(
    affected_pages: list[str],
    retrieval: RetrievalResult,
) -> ContextCoverage:
    """
    Inspect retrieval quality and codebase presence for the affected pages.

    Scoring:
      +2  page object file found on disk
      +1  per page object method chunk retrieved  (max +3)
      +1  per verified similar test chunk         (max +2)
      +1  per knowledge chunk retrieved           (max +2)
      ─────────────────────────────────────────────────────
      Max  9   HIGH   >= 6
           MEDIUM 3-5
           LOW    < 3
    """
    score    = 0
    missing  = []
    details  = []

    # ── Check page object files on disk ──────────────────────────────────────
    for page in affected_pages:
        name = page.lower().replace(" ", "_")
        candidates = [
            PROJECT_ROOT / "pages" / "ambitionbox" / f"{name}.py",
            PROJECT_ROOT / "components" / f"{name}.py",
        ]
        found = any(c.exists() for c in candidates)
        if found:
            score += 2
            details.append(f"✅ Page object found: {name}.py")
        else:
            missing.append(f"No page object found for '{page}' — "
                           f"expected at pages/ambitionbox/{name}.py")
            details.append(f"❌ Page object missing: {name}.py")

    # ── Page object method chunks retrieved ───────────────────────────────────
    method_count = min(len(retrieval.page_object_methods), 3)
    score += method_count
    if method_count == 0:
        missing.append("No page object method chunks retrieved from RAG")
    else:
        details.append(f"✅ {len(retrieval.page_object_methods)} method chunks retrieved")

    # ── Similar test chunks (non-stale) ───────────────────────────────────────
    verified_tests = [c for c in retrieval.similar_tests if not c.is_stale]
    test_count = min(len(verified_tests), 2)
    score += test_count
    if test_count == 0:
        missing.append("No verified similar test examples found — "
                       "agent has no style reference")
        details.append("⚠️  No verified test examples (all stale or none)")
    else:
        details.append(f"✅ {len(verified_tests)} verified test examples retrieved")

    # ── Business knowledge chunks ─────────────────────────────────────────────
    know_count = min(len(retrieval.knowledge), 2)
    score += know_count
    if know_count == 0:
        missing.append("No business rules or navigation flows found in knowledge base")
        details.append("⚠️  No knowledge chunks retrieved")
    else:
        details.append(f"✅ {len(retrieval.knowledge)} knowledge chunks retrieved")

    # ── Derive level ──────────────────────────────────────────────────────────
    if score >= 6:
        level = CoverageLevel.HIGH
    elif score >= 3:
        level = CoverageLevel.MEDIUM
    else:
        level = CoverageLevel.LOW

    return ContextCoverage(
        level=level,
        page_object_found=(score >= 2),
        similar_tests=len(verified_tests),
        knowledge_chunks=len(retrieval.knowledge),
        missing=missing,
        detail="\n".join(details) + f"\n\nTotal coverage score: {score}/9",
    )
