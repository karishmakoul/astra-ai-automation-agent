"""
Extractor: takes raw ticket/description text and returns a structured TestSpec
via a single Claude API call with JSON output.

Used by: JiraReader, ADOReader, TextReader
Not used by: ExcelReader (data is already structured)
"""
import json
from openai import OpenAI

from ai_agent.config import AgentConfig
from ai_agent.models import TestSpec, TestCase, Priority, TestType, InputSource

SYSTEM_PROMPT = """
You are a senior QA analyst who extracts structured test specifications from
ticket descriptions or free-text requirements.

Your job:
1. Read the input carefully
2. Identify ALL testable behaviours — positive paths, negative paths, edge cases
3. Output ONLY valid JSON matching the schema below — no markdown, no explanation

Output schema:
{
  "title": "short title summarising what feature/flow is being tested",
  "description": "1-2 sentence summary of the feature",
  "acceptance_criteria": ["list of acceptance criteria as written in the ticket"],
  "affected_pages": ["snake_case page names e.g. home_page, companies_page, reviews_page"],
  "user_types": ["guest", "authenticated", "admin", "premium_user" — only include relevant ones],
  "test_cases": [
    {
      "id": "TC_001",
      "title": "clear, action-oriented title",
      "priority": "Critical|High|Medium|Low",
      "type": "Smoke|Regression|Sanity",
      "preconditions": ["list of preconditions"],
      "steps": ["numbered steps as strings"],
      "expected_result": "what should happen",
      "tags": ["optional tags"]
    }
  ]
}

Rules:
- priority=Critical for flows that block core user journeys
- priority=High for important but non-blocking flows
- Include at least one negative/error test case per feature
- affected_pages must use snake_case matching the codebase conventions
- Never invent requirements not stated in the input
- Generate between 3 and 15 test cases depending on feature complexity
""".strip()


def extract_test_spec(
    raw_content: str,
    source: InputSource,
    source_id: str,
) -> TestSpec:
    """
    Call Claude to extract a TestSpec from raw ticket/description text.
    Returns a fully validated TestSpec pydantic model.
    """
    AgentConfig.validate()

    client = OpenAI(api_key=AgentConfig.OPENAI_API_KEY)

    message = client.chat.completions.create(
        model=AgentConfig.OPENAI_MODEL,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Extract a structured test specification from the following:\n\n{raw_content}",
            },
        ],
        response_format={"type": "json_object"},
    )

    raw_json = message.choices[0].message.content.strip()

    # Strip markdown code fences if the model wrapped the JSON
    if raw_json.startswith("```"):
        raw_json = raw_json.split("```")[1]
        if raw_json.startswith("json"):
            raw_json = raw_json[4:]

    data = json.loads(raw_json)

    test_cases = [
        TestCase(
            id=tc.get("id", f"TC_{i+1:03d}"),
            title=tc.get("title", ""),
            priority=Priority(tc.get("priority", "High")),
            type=TestType(tc.get("type", "Regression")),
            preconditions=tc.get("preconditions", []),
            steps=tc.get("steps", []),
            expected_result=tc.get("expected_result", ""),
            tags=tc.get("tags", []),
        )
        for i, tc in enumerate(data.get("test_cases", []))
    ]

    return TestSpec(
        source=source,
        source_id=source_id,
        title=data.get("title", source_id),
        description=data.get("description", ""),
        acceptance_criteria=data.get("acceptance_criteria", []),
        affected_pages=data.get("affected_pages", []),
        user_types=data.get("user_types", []),
        test_cases=test_cases,
        raw_content=raw_content,
    )
