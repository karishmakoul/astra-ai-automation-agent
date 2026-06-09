from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Priority(str, Enum):
    CRITICAL = "Critical"
    HIGH     = "High"
    MEDIUM   = "Medium"
    LOW      = "Low"


class TestType(str, Enum):
    SMOKE      = "Smoke"
    REGRESSION = "Regression"
    SANITY     = "Sanity"


class InputSource(str, Enum):
    JIRA  = "jira"
    ADO   = "ado"
    EXCEL = "excel"
    TEXT  = "text"


class TestCase(BaseModel):
    id:              str
    title:           str
    priority:        Priority        = Priority.HIGH
    type:            TestType        = TestType.REGRESSION
    preconditions:   list[str]       = Field(default_factory=list)
    steps:           list[str]       = Field(default_factory=list)
    expected_result: str             = ""
    tags:            list[str]       = Field(default_factory=list)


class TestSpec(BaseModel):
    """
    Normalised output of Stage 1.
    Every downstream stage works against this model — not raw ticket text.
    """
    source:               InputSource
    source_id:            str                      # ticket ID, file path, or "text"
    title:                str
    description:          str                      = ""
    acceptance_criteria:  list[str]                = Field(default_factory=list)
    affected_pages:       list[str]                = Field(default_factory=list)
    user_types:           list[str]                = Field(default_factory=list)
    test_cases:           list[TestCase]           = Field(default_factory=list)
    raw_content:          str                      = ""   # original text for audit
    created_at:           datetime                 = Field(default_factory=datetime.utcnow)

    def summary(self) -> str:
        return (
            f"Source : {self.source.value} | ID: {self.source_id}\n"
            f"Title  : {self.title}\n"
            f"Pages  : {', '.join(self.affected_pages) or 'unknown'}\n"
            f"Users  : {', '.join(self.user_types) or 'unknown'}\n"
            f"TCs    : {len(self.test_cases)}"
        )
