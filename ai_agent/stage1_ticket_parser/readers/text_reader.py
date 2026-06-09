"""
Text Reader: accepts free-form text or description and extracts a TestSpec via Claude.
This is the simplest reader — just pass text straight to the extractor.
"""
from ai_agent.models import TestSpec, InputSource
from ai_agent.stage1_ticket_parser.extractor import extract_test_spec


def read_text(description: str) -> TestSpec:
    """
    Extract a TestSpec from a free-text description.

    Args:
        description: Plain text requirement or feature description

    Returns:
        TestSpec with test cases extracted by Claude
    """
    if not description or not description.strip():
        raise ValueError("Description cannot be empty.")

    return extract_test_spec(
        raw_content=description.strip(),
        source=InputSource.TEXT,
        source_id="text_input",
    )
