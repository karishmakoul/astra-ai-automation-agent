"""
Jira Reader: fetches a Jira issue and converts it to a TestSpec.
Supports both Jira Cloud (atlassian.net) and Jira Server.
"""
from ai_agent.config import AgentConfig
from ai_agent.models import TestSpec, InputSource
from ai_agent.stage1_ticket_parser.extractor import extract_test_spec


def _build_raw_content(issue) -> str:
    """Flatten a Jira issue object into readable text for the extractor."""
    fields = issue.fields
    parts = [
        f"Ticket: {issue.key}",
        f"Summary: {fields.summary}",
        f"Type: {fields.issuetype.name}",
        f"Priority: {getattr(fields.priority, 'name', 'Unknown')}",
        f"Status: {fields.status.name}",
    ]

    if fields.description:
        # Jira description can be plain text or Atlassian Document Format (ADF)
        desc = fields.description
        if isinstance(desc, dict):
            # ADF — extract plain text from content blocks
            desc = _extract_adf_text(desc)
        parts.append(f"\nDescription:\n{desc}")

    # Custom field: Acceptance Criteria (common field names vary by project)
    for field_name in ["customfield_10016", "customfield_10014", "acceptance_criteria"]:
        val = getattr(fields, field_name, None)
        if val:
            parts.append(f"\nAcceptance Criteria:\n{val}")
            break

    # Comments (first 3 — often contain clarifications)
    try:
        comments = issue.fields.comment.comments[:3]
        if comments:
            parts.append("\nComments:")
            for c in comments:
                parts.append(f"  - {c.author.displayName}: {c.body[:300]}")
    except Exception:
        pass

    return "\n".join(parts)


def _extract_adf_text(adf: dict, depth: int = 0) -> str:
    """Recursively extract plain text from Atlassian Document Format JSON."""
    if depth > 10:
        return ""
    text_parts = []
    if adf.get("type") == "text":
        text_parts.append(adf.get("text", ""))
    for child in adf.get("content", []):
        text_parts.append(_extract_adf_text(child, depth + 1))
    return " ".join(t for t in text_parts if t)


def read_jira_ticket(ticket_id: str) -> TestSpec:
    """
    Fetch a Jira ticket by ID and return a structured TestSpec.

    Args:
        ticket_id: Jira issue key e.g. "PROJ-123"

    Returns:
        TestSpec with test cases extracted by Claude
    """
    if not AgentConfig.has_jira():
        raise EnvironmentError(
            "Jira credentials not configured.\n"
            "Set JIRA_SERVER, JIRA_EMAIL, JIRA_API_TOKEN in ai_agent/.env"
        )

    try:
        from jira import JIRA
    except ImportError:
        raise ImportError("Install jira: pip install jira")

    client = JIRA(
        server=AgentConfig.JIRA_SERVER,
        basic_auth=(AgentConfig.JIRA_EMAIL, AgentConfig.JIRA_API_TOKEN),
    )

    issue = client.issue(ticket_id)
    raw_content = _build_raw_content(issue)

    return extract_test_spec(
        raw_content=raw_content,
        source=InputSource.JIRA,
        source_id=ticket_id,
    )
