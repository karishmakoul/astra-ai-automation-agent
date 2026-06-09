"""
Azure DevOps Reader: fetches a work item by ID using the ADO REST API.
No official Python SDK needed — pure requests.
"""
import re
import requests
from base64 import b64encode

from ai_agent.config import AgentConfig
from ai_agent.models import TestSpec, InputSource
from ai_agent.stage1_ticket_parser.extractor import extract_test_spec


def _ado_auth_header() -> dict:
    token = b64encode(f":{AgentConfig.ADO_PAT}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def _strip_html(html: str) -> str:
    """Remove HTML tags from ADO description fields."""
    return re.sub(r"<[^>]+>", " ", html or "").strip()


def _build_raw_content(item: dict) -> str:
    fields = item.get("fields", {})
    parts = [
        f"Work Item: {item['id']}",
        f"Title: {fields.get('System.Title', '')}",
        f"Type: {fields.get('System.WorkItemType', '')}",
        f"Priority: {fields.get('Microsoft.VSTS.Common.Priority', '')}",
        f"State: {fields.get('System.State', '')}",
    ]

    desc = _strip_html(fields.get("System.Description", ""))
    if desc:
        parts.append(f"\nDescription:\n{desc}")

    ac = _strip_html(fields.get("Microsoft.VSTS.Common.AcceptanceCriteria", ""))
    if ac:
        parts.append(f"\nAcceptance Criteria:\n{ac}")

    repro = _strip_html(fields.get("Microsoft.VSTS.TCM.ReproSteps", ""))
    if repro:
        parts.append(f"\nSteps to Reproduce / Test Steps:\n{repro}")

    return "\n".join(parts)


def read_ado_ticket(ticket_id: str) -> TestSpec:
    """
    Fetch an Azure DevOps work item by ID and return a structured TestSpec.

    Args:
        ticket_id: Work item ID as string or "AB#123" format

    Returns:
        TestSpec with test cases extracted by Claude
    """
    if not AgentConfig.has_ado():
        raise EnvironmentError(
            "ADO credentials not configured.\n"
            "Set ADO_ORGANIZATION, ADO_PROJECT, ADO_PAT in ai_agent/.env"
        )

    # Strip "AB#" prefix if present
    numeric_id = ticket_id.replace("AB#", "").strip()

    url = (
        f"https://dev.azure.com/{AgentConfig.ADO_ORGANIZATION}/"
        f"{AgentConfig.ADO_PROJECT}/_apis/wit/workitems/{numeric_id}"
        f"?$expand=all&api-version=7.1"
    )

    response = requests.get(url, headers=_ado_auth_header(), timeout=15)
    response.raise_for_status()
    item = response.json()

    raw_content = _build_raw_content(item)

    return extract_test_spec(
        raw_content=raw_content,
        source=InputSource.ADO,
        source_id=ticket_id,
    )
