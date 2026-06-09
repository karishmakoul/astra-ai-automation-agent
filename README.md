# QA Automation Ecosystem

A full-stack QA automation ecosystem built in two parts:

1. **Playwright + Python Test Framework** — A production-grade, OOP-based automation framework tested against [AmbitionBox.com](https://www.ambitionbox.com)
2. **AI Automation Agent** — A RAG-powered agent that reads test tickets (Jira / ADO / Excel / free-text), understands your existing codebase, and generates grounded, hallucination-free pytest test scripts automatically

---

## Table of Contents

- [Project Structure](#project-structure)
- [Part 1 — Test Automation Framework](#part-1--test-automation-framework)
  - [Design Patterns](#design-patterns)
  - [Framework Core](#framework-core)
  - [Page Objects](#page-objects)
  - [Reusable Components](#reusable-components)
  - [Test Cases](#test-cases)
  - [Running Tests](#running-tests)
  - [Reporting](#reporting)
- [Part 2 — AI Automation Agent](#part-2--ai-automation-agent)
  - [How It Works](#how-it-works)
  - [Stage 1 — Parse](#stage-1--parse)
  - [Stage 2 — RAG Context Retrieval](#stage-2--rag-context-retrieval)
  - [Stage 3 — Generate](#stage-3--generate)
  - [Anti-Hallucination Strategy](#anti-hallucination-strategy)
  - [Excel Status Tracking](#excel-status-tracking)
  - [CLI Reference](#cli-reference)
- [Setup & Installation](#setup--installation)
- [Configuration](#configuration)
- [Architecture Diagrams](#architecture-diagrams)
- [Tech Stack](#tech-stack)

---

## Project Structure

```
Automation Agent/
│
├── core/                              # Framework core — shared infrastructure
│   ├── base_page.py                   # BasePage: 37 reusable browser interaction methods
│   ├── base_test.py                   # BaseTest class
│   └── driver/
│       ├── driver_factory.py          # Factory pattern — routes platform → driver class
│       ├── driver_manager.py          # Singleton — holds the active Playwright page
│       └── web_driver.py              # Playwright browser/context setup & teardown
│
├── pages/                             # Page Object Model layer
│   └── ambitionbox/
│       ├── home_page.py
│       ├── companies_page.py
│       ├── reviews_page.py
│       ├── salaries_page.py
│       ├── interviews_page.py
│       └── jobs_page.py
│
├── components/                        # Reusable UI components (shared across pages)
│   ├── nav.py                         # LeftNav — direct URL navigation
│   ├── search_bar.py                  # SearchBar
│   ├── filter_panel.py                # FilterPanel — Vue 2 chip + bottomSheet filters
│   └── company_card.py                # CompanyCard — card grid interactions
│
├── tests/
│   └── ambitionbox/
│       ├── test_home_page.py
│       ├── test_companies_page.py
│       ├── test_reviews_page.py
│       ├── test_jobs_page.py
│       ├── test_salaries_page_generated.py      # AI-generated
│       ├── test_reviews_page_generated.py       # AI-generated
│       ├── test_home_page_generated.py          # AI-generated
│       ├── test_jobs_page_generated.py          # AI-generated
│       └── test_interview_questions_generated.py # AI-generated
│
├── config/
│   ├── .env.local                     # Local browser/URL config
│   └── .env.staging                   # Staging overrides
│
├── conftest.py                        # All pytest fixtures (driver, page objects, components)
├── pytest.ini                         # Markers, reruns, Allure output path
├── AmbitionBox_Test_Cases.xlsx        # Test case tracker (71 test cases, 6 sheets)
│
├── ai_agent/                          # AI Automation Agent
│   ├── cli.py                         # CLI entry point — full pipeline orchestrator
│   ├── config.py                      # AgentConfig (OPENAI_API_KEY, model, integrations)
│   ├── models.py                      # Pydantic contracts: TestSpec, TestCase, enums
│   │
│   ├── stage1_ticket_parser/
│   │   ├── parser_agent.py            # Router — detects source and calls correct reader
│   │   ├── extractor.py               # GPT-4o call — raw text → structured TestSpec JSON
│   │   └── readers/
│   │       ├── excel_reader.py        # Excel reader + update_status_in_excel()
│   │       ├── jira_reader.py         # Jira REST API reader
│   │       ├── ado_reader.py          # Azure DevOps REST API reader
│   │       └── text_reader.py         # Free-text → extractor
│   │
│   ├── stage2_context_retrieval/
│   │   ├── chunker.py                 # AST-based method-level chunker → CodeChunk
│   │   ├── indexer.py                 # Embeds + stores chunks in ChromaDB (3 collections)
│   │   └── retriever.py              # Semantic search → RetrievalResult (4-phase)
│   │
│   ├── stage3_generator/
│   │   ├── generator_agent.py         # Agentic loop — GPT-4o with tool calling (max 10 rounds)
│   │   ├── prompt_builder.py          # Builds system + user prompt from spec + context
│   │   └── tools.py                   # 4 grounding tools: list_page_methods, get_fixtures,
│   │                                  #   read_file, search_context
│   │
│   ├── knowledge/
│   │   ├── business_rules.yaml        # Auth rules, filter behaviour, rating scales
│   │   ├── navigation_flows.yaml      # How each page is navigated, locators
│   │   └── user_types.yaml            # Guest, authenticated, premium user contexts
│   │
│   ├── vector_store/                  # ChromaDB persistent storage (auto-created)
│   └── diagrams/                      # Architecture diagrams (open in browser)
│       ├── 01_high_level_pipeline.html
│       ├── 02_low_level_sequence.html
│       ├── 03_file_dependency_map.html
│       └── 04_anti_hallucination_tool_loop.html
│
└── reports/
    ├── allure-results/                # Raw Allure data
    └── screenshots/                   # Auto-captured on test failure
```

---

## Part 1 — Test Automation Framework

### Design Patterns

| Pattern | Where Used | Purpose |
|---|---|---|
| **Factory** | `core/driver/driver_factory.py` | Routes `platform` string → correct driver class via a registry dict |
| **Singleton** | `core/driver/driver_manager.py` | Single shared Playwright `page` instance across the test session |
| **Page Object Model** | `pages/ambitionbox/` | Encapsulates all locators and interactions per page |
| **Component Object** | `components/` | Reusable UI widgets shared across multiple page tests |
| **Strategy** | `BasePage` wait methods | Pluggable wait strategies (visible, attached, stable) |

### Framework Core

**`core/base_page.py`** — Every page object inherits from this. Key methods:

```python
# Navigation
navigate(path)              # go to BASE_URL + path
get_current_url()

# Interactions
click(selector, label)
fill(selector, value, label)
press_key(selector, key)
hover(selector)

# Waits
wait_for_visible(selector)
wait_for_url_change(old_url)

# Assertions
assert_url_contains(partial_url)   # regex-based
assert_text_present(text)
assert_visible(selector)

# Helpers
dismiss_overlay()           # handles coachmark overlays
get_page_text()
scroll_to_bottom()
```

**`conftest.py`** — All fixtures in one place:

```python
@pytest.fixture() def driver()          # boots Playwright browser, tears down after test
@pytest.fixture() def pw_page(driver)   # raw Page object

# Page fixtures
@pytest.fixture() def home_page(pw_page)
@pytest.fixture() def companies_page(pw_page)
@pytest.fixture() def reviews_page(pw_page)
@pytest.fixture() def salaries_page(pw_page)
@pytest.fixture() def interviews_page(pw_page)
@pytest.fixture() def jobs_page(pw_page)

# Component fixtures (reusable across any page test)
@pytest.fixture() def left_nav(pw_page)
@pytest.fixture() def search_bar(pw_page)
@pytest.fixture() def filter_panel(pw_page)
@pytest.fixture() def company_card(pw_page)
```

### Page Objects

Each page object only contains locators and actions for that specific page:

```python
# Example — companies_page.py
class CompaniesPage(BasePage):
    URL_PATH   = "/list-of-companies"
    SEARCH_BAR = '[data-testid="CompaniesSearch"]'

    def open(self) -> "CompaniesPage"
    def search_company(company_name: str)
    def get_company_names() -> list[str]
    def click_company(company_name: str)
    def assert_page_loaded()
```

### Reusable Components

The component layer is the most critical reusability feature. Any page test can inject a component fixture without duplicating interaction logic.

**`components/filter_panel.py`** — The most complex component, handles Vue 2 reactive filter UI:
- Opens filters via data-testid chip buttons
- Clicks labels via `dispatchEvent(MouseEvent)` to trigger Vue reactivity
- Applies filters via `element.__vue__.handleClick()` (bypasses disabled-state checks)
- Sorts via URL params (`?sortBy=topPaying`) for reliability

**`components/nav.py`** — Direct `page.goto()` navigation to avoid submenu intercept failures

### Test Cases

71 functional test cases across 6 sheets in `AmbitionBox_Test_Cases.xlsx`:

| Sheet | Total | Automated ✅ | Failing ⚠️ |
|---|---|---|---|
| Home Page | 12 | 12 | 0 |
| Companies Page | 14 | 14 | 0 |
| Reviews Page | 10 | 10 | 0 |
| Salaries Page | 10 | 10 | 0 |
| Interview Questions | 11 | 11 | 0 |
| Jobs Page | 14 | 14 | 0 |
| **Total** | **71** | **71** | **0** |

### Running Tests

```bash
# Run all tests
pytest

# Run a specific page suite
pytest tests/ambitionbox/test_companies_page.py

# Run by priority marker
pytest -m critical
pytest -m "critical or high"

# Run by type
pytest -m regression
pytest -m smoke

# Run with visible browser (non-headless)
HEADLESS=false pytest

# Run and stop on first failure
pytest -x

# Run with parallelism (install pytest-xdist first)
pytest -n auto
```

### Reporting

Tests use **Allure** for rich HTML reporting with steps, screenshots, and history.

```bash
# Generate and open the Allure report
allure serve reports/allure-results

# Or generate a static report
allure generate reports/allure-results -o reports/allure-report --clean
open reports/allure-report/index.html
```

Screenshots are automatically captured on failure and attached to the Allure report. Saved to `reports/screenshots/`.

Tests auto-retry **2 times** on failure (configured in `pytest.ini` via `pytest-rerunfailures`).

---

## Part 2 — AI Automation Agent

The agent reads test tickets from any source, retrieves grounded context from your real codebase using RAG, then generates production-quality pytest test scripts — without hallucinating method names or fixture names that don't exist.

### How It Works

```
Input (Ticket / Excel / Text)
        ↓
 Stage 1 — PARSE      → TestSpec (Pydantic model)
        ↓
 Stage 2 — RETRIEVE   → RetrievalResult (real code + similar tests + business rules)
        ↓
 Stage 3 — GENERATE   → GPT-4o calls tools to verify real APIs, then writes tests
        ↓
 Output: test_*.py generated  +  Excel status updated to Automated
```

### Stage 1 — Parse

Converts any input source into a structured `TestSpec` Pydantic model.

| Input | Reader | Uses LLM? |
|---|---|---|
| Jira ticket ID (`PROJ-123`) | `jira_reader.py` → Jira REST API | ✅ Yes — `extractor.py` |
| ADO ticket ID (`AB#456`) | `ado_reader.py` → ADO REST API | ✅ Yes — `extractor.py` |
| Excel sheet | `excel_reader.py` → openpyxl | ❌ No — already structured |
| Free-text description | `text_reader.py` | ✅ Yes — `extractor.py` |

The `TestSpec` model carries: title, description, acceptance criteria, affected pages, user types, and a list of `TestCase` objects (each with ID, steps, priority, expected result).

### Stage 2 — RAG Context Retrieval

Before generating, the agent retrieves grounded context from your real codebase so the LLM cannot hallucinate.

**Index structure (ChromaDB — 3 collections):**

| Collection | Contains | Chunk type |
|---|---|---|
| `code_index` | Page objects, components, core base classes, conftest | Method-level (AST) |
| `test_index` | Existing test files | Method-level + staleness metadata |
| `know_index` | YAML knowledge files (business rules, navigation flows) | Key-value segments |

**Chunking strategy:** Python files are parsed with Python's `ast` module at method granularity. Each `CodeChunk` carries the method source, class context, signature, docstring, and file path — giving the LLM exactly what it needs to write correct calls.

**Retrieval is 4-phase:**
1. Page object methods matching the affected pages (most important — the API contract)
2. Similar existing test examples, classified as `verified` / `stale_candidate` / `unknown`
3. Business knowledge from YAML files
4. Conflict detection — if two retrieved chunks contradict each other, generation is aborted and a human-review flag is raised

**Build / refresh the index:**
```bash
python -m ai_agent.cli --index
```

### Stage 3 — Generate

An agentic loop powered by GPT-4o with function calling. The model **must** call tools to verify real method names before writing any test code.

**4 grounding tools (defined in `tools.py`):**

| Tool | What it does | Hallucination it prevents |
|---|---|---|
| `list_page_methods(page_name)` | AST-parses the page object file, returns all public method signatures + docstrings | Invented method names |
| `get_fixtures()` | AST-parses `conftest.py`, returns all `@pytest.fixture` names + args | Invented fixture names |
| `read_file(path)` | Returns raw file source | Wrong imports / locator assumptions |
| `search_context(query, n)` | Searches ChromaDB for additional context | Repeating already-retrieved info incorrectly |

The loop runs for up to **10 rounds**. After each tool call, results are fed back into the conversation. When `finish_reason == "stop"`, the raw code is extracted, syntax-checked via `ast.parse()`, and written to disk.

### Anti-Hallucination Strategy

Five layers working together:

1. **Folder conventions** — `_archive/`, `deprecated/`, `legacy/` folders are never indexed (SKIP_PATTERNS in `indexer.py`)
2. **Git recency** — `git log` last-modified dates are stored as metadata; old chunks get `stale_candidate` labels surfaced as warnings
3. **CI status** — test chunks carry pass/fail classification from `.pytest_cache`
4. **Conflict detection** — overlapping topics across chunks trigger a human-review abort before any generation happens
5. **Page object as API contract** — `list_page_methods()` is the ground truth; if a method doesn't exist there, the model adds a `# TODO: add <method>()` comment instead of inventing it

### Excel Status Tracking

After every successful generation run, the agent automatically updates the Excel test case tracker:

- Rows matching the generated TC IDs → **"Automated"** (green fill `#C6EFCE`)
- If `--dry-run` is used, the Excel file is **not** updated
- `update_status_in_excel()` in `excel_reader.py` handles the openpyxl write + styling

### CLI Reference

All commands run from the project root with the virtual environment active.

```
python -m ai_agent.cli [INPUT] [OPTIONS]
```

#### Flag Summary

| Flag | Type | Description |
|---|---|---|
| `--excel PATH` | input | Path to Excel test cases file |
| `--sheet NAME` | option | Sheet name within the Excel file |
| `--ticket ID` | input | Jira (`PROJ-123`) or ADO (`AB#456`) ticket ID |
| `--text "DESC"` | input | Free-text description of what to test |
| `--index` | action | Build / refresh the ChromaDB RAG index |
| `--search "QUERY"` | action | Search the RAG index (debug / explore) |
| `--api PAGE` | action | List all public methods for a page object |
| `--generate` | flag | Run full pipeline: parse → retrieve → generate |
| `--dry-run` | flag | With `--generate`: show code but skip writing to disk |
| `--retrieve` | flag | Parse + retrieve only (no code generation) |
| `--output PATH` | option | Save parsed TestSpec as JSON to this path |
| `--json` | flag | Print raw TestSpec JSON to stdout |
| `--source jira\|ado` | option | Force ticket source (overrides auto-detect) |

---

#### Step 0 — Build the RAG Index (run once, re-run after codebase changes)

```bash
python -m ai_agent.cli --index
```

What it does:
- Walks `pages/`, `components/`, `core/`, `tests/`, `conftest.py`
- Parses every `.py` file with Python's `ast` module at method-level granularity
- Embeds chunks locally using `sentence-transformers` (`all-MiniLM-L6-v2`)
- Stores ~350 chunks across 3 ChromaDB collections: `code_index`, `test_index`, `know_index`
- Skips `_archive/`, `deprecated/`, `.venv/`, `__pycache__` automatically

Expected output:
```
Building RAG index…
╭─────────────────────────────────────────╮
│ ✓ Index built successfully              │
│                                         │
│   Code chunks:      172                 │
│   Test chunks:       33                 │
│   Knowledge chunks: 144                 │
│   Total:            349                 │
╰─────────────────────────────────────────╯
```

---

#### Step 1 — Explore the Index (optional, for debugging)

**Search for relevant context:**
```bash
python -m ai_agent.cli --search "apply industry filter companies page"
python -m ai_agent.cli --search "login wall salary unlock"
python -m ai_agent.cli --search "Vue 2 filter bottomSheet apply button"
```

Expected output — ranked results with staleness warnings:
```
Top results for: 'apply industry filter companies page'

  1. components/filter_panel.py → FilterPanel → apply (score=0.821)
     def apply(filter_name: str, option: str): Open the filter section via top-bar chip…

  2. tests/ambitionbox/test_companies_page.py → TestCompaniesPage → test_industry_filter (score=0.743) ⚠ stale?
     filter_panel.apply("Industry", "Pharma")…
```

**List all methods for a page object:**
```bash
python -m ai_agent.cli --api companies_page
python -m ai_agent.cli --api filter_panel
python -m ai_agent.cli --api salaries_page
```

Expected output:
```
Available methods for: companies_page

  → CompaniesPage.open()
  → CompaniesPage.search_company(company_name)
  → CompaniesPage.get_company_names() -> list[str]
  → CompaniesPage.get_company_count() -> int
  → CompaniesPage.click_company(company_name)
  → CompaniesPage.assert_page_loaded()
  → CompaniesPage.assert_companies_listed(min_count=1)
```

---

#### Step 2 — Parse a Ticket / Excel / Text (Stage 1 only)

Use this to inspect the parsed `TestSpec` before generating — useful for verifying the agent understood the ticket correctly.

**From Excel:**
```bash
# Parse a specific sheet (only rows with status "To Be Automated")
python -m ai_agent.cli --excel AmbitionBox_Test_Cases.xlsx --sheet "Salaries Page"

# Parse all sheets combined
python -m ai_agent.cli --excel AmbitionBox_Test_Cases.xlsx

# Save parsed spec to JSON for inspection
python -m ai_agent.cli --excel AmbitionBox_Test_Cases.xlsx --sheet "Jobs Page" \
    --output outputs/jobs_spec.json
```

**From a Jira ticket:**
```bash
# Auto-detects Jira from ID format (PROJ-123)
python -m ai_agent.cli --ticket PROJ-123

# Force source if auto-detect is wrong
python -m ai_agent.cli --ticket PROJ-123 --source jira
```

**From an Azure DevOps ticket:**
```bash
# Auto-detects ADO from AB# prefix or plain number
python -m ai_agent.cli --ticket AB#456
python -m ai_agent.cli --ticket 789
```

**From free-text:**
```bash
python -m ai_agent.cli --text "Test that the industry filter on the Companies page
changes the list of companies shown. Verify that applying Pharma filter shows
different companies than the default list, and Clear All restores the defaults."
```

Expected output (Stage 1):
```
╭──────────────────────── Stage 1 — TestSpec ─────────────────────────╮
│ Companies Page — Filter Behaviour                                     │
│ Source: text | ID: text_input                                         │
╰──────────────────────────────────────────────────────────────────────╯

Acceptance Criteria:
  • Applying Pharma filter changes company list
  • Clear All restores the default state

                         3 Test Cases
  ID       Title                                    Priority   Type
 ─────────────────────────────────────────────────────────────────────
  TC_001   Industry filter changes companies shown  Critical   Regression
  TC_002   Clear All restores default companies     Critical   Regression
  TC_003   Empty results handled gracefully         High       Regression
```

---

#### Step 3 — Parse + Retrieve (Stages 1 & 2, no generation)

Useful to verify what context the agent will have before it writes code:

```bash
python -m ai_agent.cli --excel AmbitionBox_Test_Cases.xlsx --sheet "Reviews Page" --retrieve
python -m ai_agent.cli --text "Test salary unlock login wall" --retrieve
```

Expected output adds a retrieval summary below the TestSpec:
```
╭─────────────────────────────╮
│ Stage 2 — Retrieved Context │
╰─────────────────────────────╯

⚠ Staleness Warnings:
  tests/ambitionbox/test_reviews_page.py — last modified 999 days ago.
  Verify this test reflects the current application flow.

Page Object Methods: 8 chunks
  → pages/ambitionbox/reviews_page.py → ReviewsPage → get_overall_rating
  → pages/ambitionbox/reviews_page.py → ReviewsPage → apply_filter
  ...

Similar Test Examples: 5 chunks
  → tests/ambitionbox/test_reviews_page.py → TestReviewsPage → test_ai_summary (stale?)
  ...

Business Knowledge: 4 chunks
  → business_rules.ratings.scale
  → business_rules.data_quality.ci_vs_cd
```

---

#### Step 4 — Full Pipeline: Generate Test Code (Stages 1 + 2 + 3)

This is the main command. Runs all three stages and writes the output file.

**From Excel — all "To Be Automated" rows in a sheet:**
```bash
python -m ai_agent.cli --excel AmbitionBox_Test_Cases.xlsx --sheet "Salaries Page" --generate
python -m ai_agent.cli --excel AmbitionBox_Test_Cases.xlsx --sheet "Jobs Page" --generate
python -m ai_agent.cli --excel AmbitionBox_Test_Cases.xlsx --sheet "Reviews Page" --generate
python -m ai_agent.cli --excel AmbitionBox_Test_Cases.xlsx --sheet "Home Page" --generate
python -m ai_agent.cli --excel AmbitionBox_Test_Cases.xlsx --sheet "Interview Questions" --generate
python -m ai_agent.cli --excel AmbitionBox_Test_Cases.xlsx --sheet "Companies Page" --generate
```

**From a Jira ticket:**
```bash
python -m ai_agent.cli --ticket PROJ-123 --generate
```

**From free-text:**
```bash
python -m ai_agent.cli --text "Test that clicking a company card on the homepage
navigates to the company detail page showing Reviews, Salaries, and Interviews tabs." \
    --generate
```

Expected output (full pipeline):
```
╭──────────────────────── Stage 1 — TestSpec ──────────────────────────╮
│ Test cases from AmbitionBox_Test_Cases.xlsx — Salaries Page           │
╰──────────────────────────────────────────────────────────────────────╯
... (10 test cases listed)

╭─────────────────────────────╮
│ Stage 2 — Retrieved Context │
╰─────────────────────────────╯
... (retrieved chunks listed with staleness warnings)

╭──────────────────────────────────────╮
│ ✓ Stage 3 — Tests Generated          │
│ 5 tool calls | 11,654 tokens used    │
╰──────────────────────────────────────╯

Tool calls made:
  → get_fixtures({})
  → list_page_methods({'page_name': 'salaries_page'})
  → list_page_methods({'page_name': 'filter_panel'})
  → list_page_methods({'page_name': 'search_bar'})
  → list_page_methods({'page_name': 'company_card'})

Output file: tests/ambitionbox/test_salaries_page_generated.py

Generated code preview (first 50 lines):
   1 import pytest
   2 import allure
   3
   4 @allure.feature("Salaries Page")
   5 class TestSalariesPage:
   ...

✓ Excel updated: 10 test case(s) marked as Automated in 'AmbitionBox_Test_Cases.xlsx'
```

---

#### Dry Run — Preview Before Writing

Always use `--dry-run` first when testing a new sheet or ticket. Shows the generated code in the terminal but **does not** write the file or update Excel:

```bash
python -m ai_agent.cli --excel AmbitionBox_Test_Cases.xlsx --sheet "Companies Page" \
    --generate --dry-run

python -m ai_agent.cli --ticket PROJ-123 --generate --dry-run
python -m ai_agent.cli --text "Test login flow" --generate --dry-run
```

---

#### Real-World Scenarios

**"I just added a new page object — regenerate the index"**
```bash
python -m ai_agent.cli --index
```

**"I want to check what methods are available before writing tests"**
```bash
python -m ai_agent.cli --api reviews_page
python -m ai_agent.cli --api filter_panel
```

**"I have a Jira sprint — generate tests for all tickets"**
```bash
python -m ai_agent.cli --ticket QA-101 --generate
python -m ai_agent.cli --ticket QA-102 --generate
python -m ai_agent.cli --ticket QA-103 --generate
```

**"Preview what will be generated without committing anything"**
```bash
python -m ai_agent.cli --excel AmbitionBox_Test_Cases.xlsx \
    --sheet "Salaries Page" --generate --dry-run
```

**"Check for stale tests in the codebase"**
```bash
python -m ai_agent.cli --search "companies page filter" --retrieve
# Look for ⚠ stale? warnings in the output
```

**"Save the parsed spec as JSON to share with the team"**
```bash
python -m ai_agent.cli --excel AmbitionBox_Test_Cases.xlsx \
    --sheet "Reviews Page" --output outputs/reviews_spec.json --json
```

---

## Setup & Installation

### Prerequisites

- Python 3.11+
- [Allure CLI](https://allurereport.org/docs/install/) (for reports)
- An OpenAI API key (for the AI agent)

### 1. Clone & create virtual environment

```bash
git clone <repo-url>
cd "Automation Agent"
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 3. Configure the test framework

```bash
cp config/.env.local config/.env.local   # already present — edit if needed
```

```env
# config/.env.local
BASE_URL=https://www.ambitionbox.com
BROWSER=chromium
HEADLESS=false
PLATFORM=web
TIMEOUT=30000
SCREENSHOT_ON_FAILURE=true
```

### 4. Configure the AI agent

```bash
cp ai_agent/.env.example ai_agent/.env
# Edit ai_agent/.env and add your OpenAI key
```

```env
# ai_agent/.env
OPENAI_API_KEY=sk-...

# Optional overrides
# OPENAI_MODEL=gpt-4o

# Optional: Jira integration
# JIRA_SERVER=https://yourorg.atlassian.net
# JIRA_EMAIL=you@yourorg.com
# JIRA_API_TOKEN=...

# Optional: Azure DevOps integration
# ADO_ORGANIZATION=yourorg
# ADO_PROJECT=YourProject
# ADO_PAT=...
```

### 5. Build the RAG index (first time and after codebase changes)

```bash
python -m ai_agent.cli --index
```

This indexes ~350 chunks across your page objects, components, tests, and YAML knowledge files into a local ChromaDB vector store.

---

## Configuration

| File | Purpose |
|---|---|
| `config/.env.local` | Browser, URL, timeout, headless mode |
| `config/.env.staging` | Staging environment overrides |
| `pytest.ini` | Test discovery, markers, Allure path, auto-retry (2x) |
| `ai_agent/.env` | OpenAI API key, model, Jira/ADO credentials |
| `ai_agent/.env.example` | Template — copy to `.env` |

---

## Architecture Diagrams

Interactive HTML diagrams are in `ai_agent/diagrams/`. Open them in any browser:

| File | What it shows |
|---|---|
| `01_high_level_pipeline.html` | End-to-end 3-stage pipeline — inputs, components, outputs |
| `02_low_level_sequence.html` | Every function call across every file in chronological order |
| `03_file_dependency_map.html` | Which file imports which, data contracts between modules |
| `04_anti_hallucination_tool_loop.html` | Deep dive into the GPT-4o agentic tool loop in Stage 3 |

```bash
open ai_agent/diagrams/01_high_level_pipeline.html
```

---

## Tech Stack

### Test Framework

| Library | Version | Purpose |
|---|---|---|
| `playwright` | 1.60.0 | Browser automation (sync API) |
| `pytest` | 9.0.3 | Test runner |
| `pytest-playwright` | 0.8.0 | Playwright fixtures for pytest |
| `allure-pytest` | 2.16.0 | Rich HTML test reporting |
| `pytest-rerunfailures` | 16.3 | Auto-retry on flaky failures |
| `openpyxl` | 3.1.5 | Excel test case tracker read/write |

### AI Agent

| Library | Version | Purpose |
|---|---|---|
| `openai` | 2.41.0 | GPT-4o API (parse + generate) |
| `chromadb` | 1.5.9 | Local persistent vector store |
| `sentence-transformers` | 5.5.1 | Local embeddings (`all-MiniLM-L6-v2`, 384-dim) |
| `pydantic` | 2.13.4 | Data contracts between pipeline stages |
| `rich` | 15.0.0 | Beautiful CLI output |
| `pyyaml` | — | Knowledge base YAML parsing |

### Why local embeddings?

`sentence-transformers` runs completely offline — no API calls, no cost, no rate limits. The `all-MiniLM-L6-v2` model (384 dimensions) gives a strong balance between retrieval quality and speed for code search.

---

## Key Design Decisions

**Why sync Playwright instead of async?**
Sync API plays nicely with pytest without needing `asyncio` event loop management. Simpler fixtures, simpler debugging.

**Why method-level AST chunking instead of file-level?**
Retrieval precision. "How do I apply a filter?" should return exactly `FilterPanel.apply()`, not the entire 150-line file. Method-level chunks also carry class context and docstrings as metadata.

**Why ChromaDB instead of a hosted vector DB?**
Zero-infra, zero-cost, runs locally. The entire vector store is a folder (`ai_agent/vector_store/`). Perfect for a team's local dev machine or CI runner without external dependencies.

**Why tool calling instead of one-shot generation?**
One-shot generation produces plausible-looking but wrong code — invented method names, fixture names that don't exist. Tool calling forces the model to verify the actual API surface before writing a single line.

**Why OpenAI function calling format vs. Anthropic tool use?**
Same concept, different wire format. The agent was designed to be LLM-agnostic — only `generator_agent.py` and `extractor.py` contain provider-specific code.
