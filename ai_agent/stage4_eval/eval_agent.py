"""
Eval Agent: orchestrates all 7 metrics against a generated test file.

Flow:
  1. Load generated test file source
  2. Build context strings (page API, fixtures, business rules, nav flows)
  3. Run all 7 metrics (concurrently where possible)
  4. Aggregate into EvalReport
  5. Update Excel status (PASS → Automated, FAIL → Automated Failing)
"""
import yaml
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from ai_agent.models import TestSpec
from ai_agent.stage3_generator.tools import (
    tool_list_page_methods, tool_get_fixtures, tool_read_file
)
from ai_agent.stage4_eval.models import EvalReport, MetricResult, TestCaseResult
from ai_agent.stage4_eval.metrics import (
    metric_no_hallucinated_methods,
    metric_fixture_accuracy,
    metric_convention_adherence,
    metric_spec_coverage,
    metric_assertion_strength,
    metric_flow_order_validation,
    metric_business_rule_compliance,
)
from ai_agent.stage4_eval.flow_extractor import extract_todo_count

console = Console()

PROJECT_ROOT  = Path(__file__).parent.parent.parent
KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"


class EvalAgent:

    def evaluate(
        self,
        filepath: str,
        spec: TestSpec,
        excel_path: str | None = None,
        sheet_name: str | None = None,
    ) -> EvalReport:
        """
        Run all 7 metrics against the generated test file.

        Args:
            filepath:   Relative path to generated test file (from project root)
            spec:       The TestSpec the file was generated from
            excel_path: If provided, update Excel status after evaluation
            sheet_name: Sheet to update in Excel
        """
        report = EvalReport(filepath=filepath)

        # ── Load generated code ───────────────────────────────────────────────
        full_path = PROJECT_ROOT / filepath
        if not full_path.exists():
            report.issues.append(f"Generated file not found: {filepath}")
            return report

        generated_code = full_path.read_text(encoding="utf-8")
        todo_count     = extract_todo_count(generated_code)

        if todo_count > 0:
            report.issues.append(
                f"{todo_count} TODO stub(s) found — some methods need implementing"
            )

        # ── Build context strings ─────────────────────────────────────────────
        page_api_context      = self._build_page_api_context(spec.affected_pages)
        available_fixtures    = tool_get_fixtures()
        business_rules_ctx    = self._load_knowledge("business_rules.yaml")
        navigation_flows_ctx  = self._load_knowledge("navigation_flows.yaml")
        spec_summary          = self._build_spec_summary(spec)
        spec_steps_summary    = self._build_steps_summary(spec)

        # ── Run metrics (Cat 1 + Cat 2 static run in parallel, Cat 3 after) ───
        console.print("\n[bold cyan]Running evaluation metrics…[/bold cyan]")

        results: list[MetricResult] = []

        # Metrics 1-3 and 4-5 can run concurrently (independent)
        def run_m1(): return metric_no_hallucinated_methods(generated_code, page_api_context)
        def run_m2(): return metric_fixture_accuracy(generated_code, available_fixtures)
        def run_m3(): return metric_convention_adherence(generated_code, spec.title)
        def run_m4(): return metric_spec_coverage(generated_code, spec_summary, len(spec.test_cases))
        def run_m5(): return metric_assertion_strength(generated_code)

        with ThreadPoolExecutor(max_workers=5) as ex:
            futures = {
                ex.submit(run_m1): "M1",
                ex.submit(run_m2): "M2",
                ex.submit(run_m3): "M3",
                ex.submit(run_m4): "M4",
                ex.submit(run_m5): "M5",
            }
            for future in as_completed(futures):
                label = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    icon = "✅" if result.passed else "❌"
                    console.print(f"  {icon} {result.name:<35} [cyan]{result.score:.2f}[/cyan]")
                except Exception as e:
                    console.print(f"  ⚠️  {label} failed: {e}")

        # Metrics 6 & 7 (Flow + Business Rules) — sequential, heavier
        try:
            m6 = metric_flow_order_validation(
                generated_code, spec_steps_summary, navigation_flows_ctx
            )
            results.append(m6)
            icon = "✅" if m6.passed else "❌"
            console.print(f"  {icon} {m6.name:<35} [cyan]{m6.score:.2f}[/cyan]")
        except Exception as e:
            console.print(f"  ⚠️  Flow Order Validation failed: {e}")

        try:
            m7 = metric_business_rule_compliance(
                generated_code, business_rules_ctx, spec.affected_pages
            )
            results.append(m7)
            icon = "✅" if m7.passed else "❌"
            console.print(f"  {icon} {m7.name:<35} [cyan]{m7.score:.2f}[/cyan]")
        except Exception as e:
            console.print(f"  ⚠️  Business Rule Compliance failed: {e}")

        # ── Assemble report ───────────────────────────────────────────────────
        report.metrics = results
        report.compute()

        # ── Update Excel if provided ──────────────────────────────────────────
        if excel_path and spec.test_cases:
            self._update_excel(report, spec, excel_path, sheet_name)

        return report

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _build_page_api_context(self, affected_pages: list[str]) -> str:
        parts = []
        for page in affected_pages:
            parts.append(tool_list_page_methods(page))
        # Also include base_page inherited methods
        parts.append(tool_read_file("core/base_page.py")[:2000])
        return "\n\n".join(parts)

    def _load_knowledge(self, filename: str) -> str:
        path = KNOWLEDGE_DIR / filename
        if not path.exists():
            return f"(knowledge file {filename} not found)"
        return path.read_text(encoding="utf-8")[:3000]

    def _build_spec_summary(self, spec: TestSpec) -> str:
        lines = [f"Test Specification: {spec.title}", ""]
        for tc in spec.test_cases:
            lines.append(f"  [{tc.id}] {tc.title}")
            lines.append(f"  Expected: {tc.expected_result}")
        return "\n".join(lines)

    def _build_steps_summary(self, spec: TestSpec) -> str:
        lines = [f"Required test flows for: {spec.title}", ""]
        for tc in spec.test_cases:
            lines.append(f"[{tc.id}] {tc.title}")
            for i, step in enumerate(tc.steps, 1):
                lines.append(f"  Step {i}: {step}")
            lines.append(f"  Expected: {tc.expected_result}")
            lines.append("")
        return "\n".join(lines)

    def _update_excel(
        self,
        report: EvalReport,
        spec: TestSpec,
        excel_path: str,
        sheet_name: str | None,
    ):
        from ai_agent.stage1_ticket_parser.readers.excel_reader import update_status_in_excel
        tc_ids = [tc.id for tc in spec.test_cases]

        if report.passed:
            n = update_status_in_excel(excel_path, sheet_name, tc_ids, "Automated")
            console.print(f"\n[green]✓ Excel:[/green] {n} rows → [green]Automated[/green]")
        else:
            n = update_status_in_excel(excel_path, sheet_name, tc_ids, "Automated (Failing)")
            console.print(f"\n[yellow]⚠ Excel:[/yellow] {n} rows → [yellow]Automated (Failing)[/yellow]")
