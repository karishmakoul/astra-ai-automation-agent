"""
Parser Agent: routes the input to the correct reader and returns a TestSpec.
This is the single entry point for Stage 1.
"""
import json
import re
from pathlib import Path

from ai_agent.models import TestSpec


def _detect_ticket_source(ticket_id: str) -> str:
    """
    Auto-detect whether a ticket ID is Jira or ADO.
    - Jira format:  PROJ-123  or  ABC-4567
    - ADO format:   AB#123    or  123  (plain number)
    """
    if ticket_id.startswith("AB#") or ticket_id.isdigit():
        return "ado"
    if re.match(r"^[A-Z]+-\d+$", ticket_id):
        return "jira"
    return "jira"  # default


def parse(
    ticket_id:   str | None = None,
    excel_path:  str | None = None,
    sheet_name:  str | None = None,
    text:        str | None = None,
    source:      str | None = None,   # "jira" | "ado" — override auto-detect
    output_path: str | None = None,   # if set, save JSON to this file
) -> TestSpec:
    """
    Main entry point for Stage 1.
    Exactly one of ticket_id / excel_path / text must be provided.

    Args:
        ticket_id:   Jira or ADO ticket ID
        excel_path:  Path to Excel test case file
        sheet_name:  Specific sheet within the Excel file (optional)
        text:        Free-form description text
        source:      Force "jira" or "ado" (overrides auto-detect)
        output_path: Save the TestSpec JSON to this path

    Returns:
        TestSpec
    """
    inputs_provided = sum(
        x is not None for x in [ticket_id, excel_path, text]
    )
    if inputs_provided == 0:
        raise ValueError("Provide one of: --ticket, --excel, or --text")
    if inputs_provided > 1:
        raise ValueError("Provide only ONE of: --ticket, --excel, or --text")

    spec: TestSpec

    # ── Route to correct reader ─────────────────────────────────────────────
    if ticket_id:
        resolved_source = source or _detect_ticket_source(ticket_id)
        if resolved_source == "jira":
            from ai_agent.stage1_ticket_parser.readers.jira_reader import read_jira_ticket
            spec = read_jira_ticket(ticket_id)
        else:
            from ai_agent.stage1_ticket_parser.readers.ado_reader import read_ado_ticket
            spec = read_ado_ticket(ticket_id)

    elif excel_path:
        from ai_agent.stage1_ticket_parser.readers.excel_reader import read_excel
        spec = read_excel(excel_path, sheet_name=sheet_name)

    else:  # text
        from ai_agent.stage1_ticket_parser.readers.text_reader import read_text
        spec = read_text(text)

    # ── Optionally save output ──────────────────────────────────────────────
    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            spec.model_dump_json(indent=2, exclude={"raw_content"}),
            encoding="utf-8",
        )

    return spec
