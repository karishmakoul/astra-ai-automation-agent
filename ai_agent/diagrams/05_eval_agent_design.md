# Stage 4 — Eval Agent: High-Level Design

## 1. Full Pipeline with Eval Gate

```mermaid
flowchart TD
    INPUT["📥 Input\nJira / ADO / Excel / Free-text"]

    S1["⚙️ STAGE 1 — PARSE\nparser_agent.py\n──────────────\nTestSpec\n(TC IDs · steps · expected results)"]

    S2["🔍 STAGE 2 — RAG RETRIEVE\nretriever.py\n──────────────\nRetrievalResult\n(code + tests + knowledge)"]

    CTX_CHECK{"🔎 Context Coverage\nChecker\n──────────────\nHow much does the\nRAG know about\nthis feature?"}

    HIGH["✅ HIGH\nFull page object\n+ similar tests\n+ business rules\nexist in RAG"]

    MED["⚠️ MEDIUM\nPage object exists\nbut some methods\nmissing OR no\nsimilar tests found"]

    LOW["❌ LOW / ZERO\nNo page object,\nno tests, no\nbusiness rules\nin RAG at all"]

    S3["✨ STAGE 3 — GENERATE\ngenerator_agent.py\n──────────────\nGPT-4o agentic loop\n(tool calls: list_page_methods,\nget_fixtures, read_file,\nsearch_context)"]

    SCAFFOLD["📝 Generate with\nDetailed TODO Scaffold\n──────────────\nPartial code +\nprecise TODOs:\n'Add method X to PageY\nat path Z'"]

    DISCOVERY["🧭 DISCOVERY MODE\ndiscovery_agent.py\n──────────────\nReport missing context\n+ structured questionnaire\nOR live site crawl\n→ auto-build page object\n→ update YAML knowledge\n→ re-index RAG\n→ then generate"]

    S4["🧪 STAGE 4 — EVAL\neval_agent.py\n──────────────\nRun 7 metrics\nacross 3 categories"]

    REPORT["📊 EvalReport\n──────────────\nOverall score\nPer-metric scores\nIssues found\nRecommendation"]

    EXCEL["📊 Excel Update\n──────────────\nPASS → Automated ✅\nFAIL → Automated (Failing) 🟡\nDISCOVERY → Needs Context 🔴"]

    DECISION{"Overall Score\n≥ threshold\n(0.70)?"}

    ACCEPT["✅ ACCEPT\nWrite final test file\nUpdate Excel → Automated"]

    REGEN["🔄 REGENERATE\nFeed EvalReport\nback to Stage 3\nas additional context\n(max 2 attempts)"]

    HUMAN["🙋 ESCALATE TO HUMAN\nScore too low after\n2 regen attempts\nFlag for manual review"]

    INPUT --> S1 --> S2 --> CTX_CHECK
    CTX_CHECK -->|High| HIGH --> S3
    CTX_CHECK -->|Medium| MED --> SCAFFOLD
    CTX_CHECK -->|Low/Zero| LOW --> DISCOVERY
    SCAFFOLD --> S3
    DISCOVERY --> S3
    S3 --> S4 --> REPORT --> DECISION
    DECISION -->|Yes| ACCEPT --> EXCEL
    DECISION -->|No| REGEN
    REGEN -->|Attempt 1 or 2| S3
    REGEN -->|Still failing| HUMAN --> EXCEL
    ACCEPT --> EXCEL

    classDef stage    fill:#1e2235,stroke:#7c83fd,color:#cdd6f4
    classDef decision fill:#1f2d3d,stroke:#8be9fd,color:#cdd6f4
    classDef good     fill:#1f3228,stroke:#50fa7b,color:#cdd6f4
    classDef warn     fill:#2d2a1f,stroke:#ffb86c,color:#cdd6f4
    classDef fail     fill:#3d1f1f,stroke:#ff5555,color:#cdd6f4
    classDef output   fill:#2a1f3d,stroke:#bd93f9,color:#cdd6f4

    class S1,S2,S3,S4 stage
    class CTX_CHECK,DECISION decision
    class HIGH,ACCEPT good
    class MED,SCAFFOLD,REGEN warn
    class LOW,DISCOVERY,HUMAN fail
    class REPORT,EXCEL output
```

---

## 2. Stage 4 Eval — 7 Metrics Across 3 Categories

```mermaid
flowchart TD
    GEN["Generated Test File\ntest_*_generated.py"]

    subgraph CAT1["📦 CATEGORY 1 — Code Quality\n(Is the code structurally correct?)"]
        M1["Metric 1\n🔬 No Hallucinated Methods\n──────────────────────\nEvery method called must exist\nin list_page_methods() output.\nHallucinated call = fail.\n\nTool: GEval\nContext: page object API"]

        M2["Metric 2\n🔌 Fixture Accuracy\n──────────────────────\nEvery fixture in test signatures\nmust exist in conftest.py.\nInvented fixture = fail.\n\nTool: Static AST check\n+ GEval confirmation"]

        M3["Metric 3\n📐 Convention Adherence\n──────────────────────\nChecks: @allure decorators,\n@pytest.mark.{priority},\ndriver first fixture,\nno raw page.locator() calls,\nassert not assertEqual.\n\nTool: GEval\nContext: SYSTEM_PROMPT rules"]
    end

    subgraph CAT2["📋 CATEGORY 2 — Spec Fidelity\n(Does it test what was asked?)"]
        M4["Metric 4\n✅ Spec Coverage\n──────────────────────\nEvery TestCase in TestSpec\nmust have a test function.\nScore = covered / total.\n\nTool: GEval\nInput: TestSpec + generated code"]

        M5["Metric 5\n💪 Assertion Strength\n──────────────────────\nAssertions must verify\nspecific behaviour.\nFails for: assert True,\nassert text != '',\npass stubs, trivially weak.\n\nTool: GEval\nCriteria: assertion quality"]
    end

    subgraph CAT3["🗺️ CATEGORY 3 — Flow Correctness\n(Is the sequence of steps right?)"]
        M6["Metric 6\n🔄 Flow Order Validation\n──────────────────────\nExtract action sequence via AST.\nCompare to spec steps order.\nCheck: navigate → interact → assert.\nFlag reversed or missing steps.\n\nTool: AST extraction + GEval\nContext: spec steps + nav_flows.yaml"]

        M7["Metric 7\n📜 Business Rule Compliance\n──────────────────────\nChecks known rules e.g:\n• Login wall handled before salary\n• search() before filter()\n• overlay dismissed before nav\n• No exact value assertions\n  on live data\n\nTool: GEval\nContext: business_rules.yaml"]
    end

    SCORES["Weighted Score Aggregation\n──────────────────────\nCat 1 weight: 30%\nCat 2 weight: 40%\nCat 3 weight: 30%\n\nOverall = weighted average\nThreshold: 0.70 to ACCEPT"]

    GEN --> CAT1 & CAT2 & CAT3
    CAT1 --> SCORES
    CAT2 --> SCORES
    CAT3 --> SCORES

    classDef metric fill:#1e2235,stroke:#7c83fd,color:#cdd6f4,text-align:left
    classDef score  fill:#2a1f3d,stroke:#bd93f9,color:#cdd6f4

    class M1,M2,M3,M4,M5,M6,M7 metric
    class SCORES score
```

---

## 3. Discovery Mode — Zero Context Flow

```mermaid
flowchart TD
    UNKNOWN["Agent receives request for\nan unknown page / feature\ne.g. Community → My Company"]

    INTROSPECT["🔎 Context Coverage Check\n──────────────────────\nSearch RAG for page name\nSearch RAG for feature keywords\nCheck pages/ folder for page object\nCheck knowledge/ YAML files"]

    MISSING["📋 Discovery Report\n──────────────────────\n□ No page object found\n□ No navigation flow found\n□ No business rules found\n□ No similar tests found"]

    CHOICE{"Discovery\nStrategy?"}

    QUESTIONNAIRE["📝 Questionnaire Mode\n──────────────────────\nAgent outputs structured Q&A:\n\nNAVIGATION:\n  Q1. URL path?\n  Q2. Entry point from homepage?\n\nINTERACTIONS:\n  Q3. What filters/tabs exist?\n  Q4. Login required?\n\nBUSINESS RULES:\n  Q5. What = success for this page?\n  Q6. Known flaky elements?"]

    CRAWL["🌐 Auto-Crawl Mode\n(discovery_agent.py)\n──────────────────────\n1. Playwright navigates to URL\n2. Extract all interactive elements\n   (buttons, links, inputs, tabs)\n3. Record URL changes on click\n4. Extract visible text labels\n5. Feed DOM snapshot to GPT-4o"]

    USER_ANSWERS["👤 User provides answers\nto questionnaire"]

    GPT_INFER["🤖 GPT-4o infers structure\nfrom DOM snapshot\n──────────────────────\n'This looks like a feed page\nwith category tabs and\na post card component'"]

    BUILD_CONTEXT["🏗️ Build New Context\n──────────────────────\nGenerate page object skeleton:\n  pages/ambitionbox/community_page.py\n\nUpdate YAML knowledge:\n  navigation_flows.yaml → community_page\n  business_rules.yaml → community rules\n  (marked: INFERRED — needs human verify)\n\nRe-index RAG:\n  python -m ai_agent.cli --index"]

    CONFIDENCE{"Confidence in\ninferred context?\n(GPT-4o self-scores)"}

    GENERATE["✨ Proceed to Stage 3\nGenerate tests with\nnewly built context"]

    HUMAN_REVIEW["🙋 Flag for Human Review\n──────────────────────\nOutput discovery report\n+ inferred page object\n+ questions needing answers\nbefore generation is safe"]

    UNKNOWN --> INTROSPECT --> MISSING --> CHOICE
    CHOICE -->|User available| QUESTIONNAIRE
    CHOICE -->|Auto mode| CRAWL
    QUESTIONNAIRE --> USER_ANSWERS --> BUILD_CONTEXT
    CRAWL --> GPT_INFER --> BUILD_CONTEXT
    BUILD_CONTEXT --> CONFIDENCE
    CONFIDENCE -->|High ≥ 0.75| GENERATE
    CONFIDENCE -->|Low < 0.75| HUMAN_REVIEW

    classDef action  fill:#1e2235,stroke:#7c83fd,color:#cdd6f4
    classDef decision fill:#1f2d3d,stroke:#8be9fd,color:#cdd6f4
    classDef good    fill:#1f3228,stroke:#50fa7b,color:#cdd6f4
    classDef warn    fill:#2d2a1f,stroke:#ffb86c,color:#cdd6f4
    classDef fail    fill:#3d1f1f,stroke:#ff5555,color:#cdd6f4

    class INTROSPECT,MISSING,QUESTIONNAIRE,CRAWL,USER_ANSWERS,GPT_INFER,BUILD_CONTEXT action
    class CHOICE,CONFIDENCE decision
    class GENERATE good
    class HUMAN_REVIEW fail
    class UNKNOWN warn
```

---

## 4. Flow Validation — Metric 6 Deep Dive

```mermaid
flowchart LR
    subgraph INPUTS["Inputs"]
        CODE["Generated test code\n(Python source)"]
        SPEC["TestSpec\n(ordered steps from ticket)"]
        YAML["navigation_flows.yaml\n(known valid flows\n+ invalid patterns)"]
    end

    subgraph EXTRACT["Step 1 — Extract"]
        AST_PARSE["AST Parser\n──────────────\nWalk FunctionDef nodes\nExtract method calls\nin order of appearance\n\nOutput:\n[open(), search_designation(),\n apply_filter(), get_salary_ranges()]"]

        SPEC_PARSE["Spec Step Parser\n──────────────\nMap natural language steps\nto action categories:\n'Navigate to page' → navigate\n'Apply filter' → interact\n'Verify results' → assert"]

        YAML_PARSE["Flow Rule Loader\n──────────────\nLoad valid_flows[]\nLoad invalid_patterns[]\nLoad business pre-conditions"]
    end

    subgraph JUDGE["Step 2 — Judge (GEval)"]
        RULE1["Rule 1: Order Check\n──────────────\nnavigation must come first\ninteractions before assertions\nno assertion as first step"]

        RULE2["Rule 2: Spec Mapping\n──────────────\nEach spec step must map\nto ≥1 code action\nNo spec step left uncovered"]

        RULE3["Rule 3: Pattern Match\n──────────────\nCode sequence must match\na known valid_flow pattern\nOR not match any\ninvalid_pattern"]

        RULE4["Rule 4: Pre-condition Check\n──────────────\nBusiness pre-conditions met\ne.g. login handled before\naccessing salary data"]
    end

    SCORE["Flow Score\n0.0 – 1.0"]

    CODE --> AST_PARSE
    SPEC --> SPEC_PARSE
    YAML --> YAML_PARSE
    AST_PARSE & SPEC_PARSE & YAML_PARSE --> RULE1 & RULE2 & RULE3 & RULE4
    RULE1 & RULE2 & RULE3 & RULE4 --> SCORE

    classDef input  fill:#2d2620,stroke:#ffb86c,color:#cdd6f4
    classDef proc   fill:#1e2235,stroke:#7c83fd,color:#cdd6f4
    classDef judge  fill:#2a1f3d,stroke:#bd93f9,color:#cdd6f4
    classDef output fill:#1f3228,stroke:#50fa7b,color:#cdd6f4

    class CODE,SPEC,YAML input
    class AST_PARSE,SPEC_PARSE,YAML_PARSE proc
    class RULE1,RULE2,RULE3,RULE4 judge
    class SCORE output
```

---

## 5. EvalReport — Output Format

```mermaid
flowchart TD
    REPORT["📊 EvalReport\ntest_salaries_page_generated.py"]

    subgraph SUMMARY["Summary"]
        S1["Overall Score: 0.81 / 1.00\nStatus: ✅ PASS  threshold=0.70\nTests in file: 10\nTool calls made: 5\nTokens used: 11,654"]
    end

    subgraph METRICS["Per-Metric Breakdown"]
        M1["Metric 1 · No Hallucinated Methods  1.00 ✅"]
        M2["Metric 2 · Fixture Accuracy         1.00 ✅"]
        M3["Metric 3 · Convention Adherence     0.88 ✅"]
        M4["Metric 4 · Spec Coverage            0.90 ✅  9/10 TCs covered"]
        M5["Metric 5 · Assertion Strength       0.75 ✅"]
        M6["Metric 6 · Flow Order Validation    0.80 ✅"]
        M7["Metric 7 · Business Rule Compliance 0.67 ⚠️  login wall not handled in SAL_010"]
    end

    subgraph ISSUES["Issues Found"]
        I1["⚠️ SAL_004: test body is a pass stub — TODO not yet implemented"]
        I2["⚠️ SAL_010: salary unlock test accesses data without handling login wall"]
        I3["ℹ️ SAL_007: assertion 'assert salary_ranges' could be stronger"]
    end

    subgraph ACTION["Recommendation"]
        A1["ACCEPT with minor fixes\n──────────────────\nAuto-fix: SAL_007 assertion strengthened\nNeeds human: SAL_004 TODO, SAL_010 login flow\nExcel: 8 → Automated ✅  2 → Automated Failing 🟡"]
    end

    REPORT --> SUMMARY & METRICS & ISSUES & ACTION

    classDef section fill:#1e2235,stroke:#7c83fd,color:#cdd6f4
    classDef good    fill:#1f3228,stroke:#50fa7b,color:#cdd6f4
    classDef warn    fill:#2d2a1f,stroke:#ffb86c,color:#cdd6f4

    class SUMMARY,METRICS,ISSUES section
    class ACTION good
```

---

## 6. Files to Build

```
ai_agent/
├── stage4_eval/
│   ├── __init__.py
│   ├── models.py              # EvalReport, MetricResult, FailureCategory dataclasses
│   ├── metrics.py             # 7 GEval metric definitions (DeepEval)
│   ├── flow_extractor.py      # AST-based action sequence extractor (Metric 6)
│   ├── eval_agent.py          # Orchestrator — runs all 7 metrics → EvalReport
│   └── context_checker.py     # Pre-generation: High / Medium / Low coverage check
│
├── stage5_discovery/          # (future)
│   ├── __init__.py
│   ├── discovery_agent.py     # Crawl unknown page → infer page object structure
│   └── knowledge_builder.py   # Auto-update navigation_flows.yaml + business_rules.yaml
│
└── cli.py                     # +--eval flag  +--eval after --generate
```

---

## 7. Metric Weights & Scoring

| Category | Metric | Weight | Fail if |
|---|---|---|---|
| Code Quality | No Hallucinated Methods | 15% | Any invented method |
| Code Quality | Fixture Accuracy | 10% | Any invented fixture |
| Code Quality | Convention Adherence | 5% | < 3 conventions missed |
| Spec Fidelity | Spec Coverage | 25% | < 80% test cases covered |
| Spec Fidelity | Assertion Strength | 15% | > 2 trivially weak assertions |
| Flow Correctness | Flow Order Validation | 15% | navigate/interact/assert out of order |
| Flow Correctness | Business Rule Compliance | 15% | Any known rule violated |

**Overall threshold to ACCEPT: 0.70**  
**Auto-regenerate if: 0.50 – 0.69** (max 2 attempts)  
**Escalate to human if: < 0.50**
