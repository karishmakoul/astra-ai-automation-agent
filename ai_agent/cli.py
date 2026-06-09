"""
CLI entry point for the AI Automation Agent.

Usage examples:

  Stage 1 — Parse a ticket / Excel / text:
    python -m ai_agent.cli --ticket PROJ-123
    python -m ai_agent.cli --excel AmbitionBox_Test_Cases.xlsx --sheet "Companies Page"
    python -m ai_agent.cli --text "Test that the industry filter changes visible companies"

  Stage 2 — Build / refresh the RAG index:
    python -m ai_agent.cli --index

  Stage 2 — Test retrieval:
    python -m ai_agent.cli --search "apply industry filter companies page"
    python -m ai_agent.cli --api companies_page

  Stage 3 — Generate test code:
    python -m ai_agent.cli --excel AmbitionBox_Test_Cases.xlsx --sheet "Salaries Page" --generate
    python -m ai_agent.cli --text "Test salary filter by experience" --generate
    python -m ai_agent.cli --excel AmbitionBox_Test_Cases.xlsx --sheet "Salaries Page" --generate --dry-run
"""
import argparse
import sys

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich import box

console = Console()


# ── Formatters ──────────────────────────────────────────────────────────────

def _print_spec(spec) -> None:
    console.print(Panel.fit(
        f"[bold cyan]{spec.title}[/bold cyan]\n"
        f"[dim]Source: {spec.source.value} | ID: {spec.source_id}[/dim]",
        title="[bold]Stage 1 — TestSpec[/bold]",
        border_style="cyan",
    ))
    if spec.description:
        console.print(f"\n[bold]Description:[/bold] {spec.description}")
    if spec.acceptance_criteria:
        console.print("\n[bold]Acceptance Criteria:[/bold]")
        for ac in spec.acceptance_criteria:
            console.print(f"  • {ac}")
    if spec.affected_pages:
        console.print(f"\n[bold]Affected Pages:[/bold] {', '.join(spec.affected_pages)}")
    if spec.user_types:
        console.print(f"[bold]User Types:[/bold]  {', '.join(spec.user_types)}")
    if spec.test_cases:
        table = Table(box=box.SIMPLE_HEAD, header_style="bold magenta",
                      title=f"\n[bold]{len(spec.test_cases)} Test Cases[/bold]")
        table.add_column("ID",       style="cyan",   width=8)
        table.add_column("Title",    style="white",  width=50)
        table.add_column("Priority", style="yellow", width=10)
        table.add_column("Type",     style="green",  width=12)
        priority_color = {"Critical": "bold red", "High": "yellow",
                          "Medium": "green", "Low": "dim"}
        for tc in spec.test_cases:
            color = priority_color.get(tc.priority.value, "white")
            table.add_row(tc.id, tc.title[:48],
                          f"[{color}]{tc.priority.value}[/{color}]", tc.type.value)
        console.print(table)


def _print_retrieval(result) -> None:
    console.print(Panel.fit(
        "[bold green]Stage 2 — Retrieved Context[/bold green]",
        border_style="green",
    ))
    if result.conflicts:
        console.print("\n[bold red]⚠ CONFLICTS DETECTED — human review needed:[/bold red]")
        for c in result.conflicts:
            console.print(f"  Topic: {c['topic']}")
            console.print(f"    A: {c['source_a']}")
            console.print(f"    B: {c['source_b']}")
    if result.stale_warnings:
        console.print("\n[bold yellow]⚠ Staleness Warnings:[/bold yellow]")
        for w in result.stale_warnings:
            console.print(f"  {w}")
    if result.page_object_methods:
        console.print(f"\n[bold]Page Object Methods:[/bold] {len(result.page_object_methods)} chunks")
        for c in result.page_object_methods[:4]:
            console.print(f"  [cyan]→[/cyan] {c.short_label()}")
    if result.similar_tests:
        console.print(f"\n[bold]Similar Test Examples:[/bold] {len(result.similar_tests)} chunks")
        for c in result.similar_tests:
            stale = " [yellow](stale?)[/yellow]" if c.is_stale else ""
            console.print(f"  [cyan]→[/cyan] {c.short_label()}{stale}")
    if result.knowledge:
        console.print(f"\n[bold]Business Knowledge:[/bold] {len(result.knowledge)} chunks")
        for c in result.knowledge:
            console.print(f"  [cyan]→[/cyan] {c.metadata.get('topic', c.file)}")


def _print_generation(result) -> None:
    if result.is_conflict():
        console.print(Panel.fit(
            "[bold red]⚠ CONFLICTS — Generation Stopped[/bold red]",
            border_style="red",
        ))
        for c in result.conflicts:
            console.print(f"  [red]•[/red] {c}")
        console.print("\n[dim]Resolve conflicts before generating.[/dim]")
        return

    if not result.success:
        console.print(Panel.fit(
            f"[bold red]✗ Generation Failed[/bold red]\n{result.error}",
            border_style="red",
        ))
        return

    console.print(Panel.fit(
        f"[bold green]✓ Stage 3 — Tests Generated[/bold green]\n"
        f"[dim]{len(result.tool_calls_made)} tool calls | "
        f"{result.tokens_used:,} tokens used[/dim]",
        border_style="green",
    ))

    if result.tool_calls_made:
        console.print("\n[bold]Tool calls made:[/bold]")
        for call in result.tool_calls_made:
            console.print(f"  [cyan]→[/cyan] {call[:80]}")

    if result.warnings:
        console.print("\n[bold yellow]⚠ Warnings:[/bold yellow]")
        for w in result.warnings:
            console.print(f"  {w[:100]}")

    if result.filepath:
        console.print(f"\n[bold]Output file:[/bold] [green]{result.filepath}[/green]")

    if result.code:
        console.print("\n[bold]Generated code preview (first 50 lines):[/bold]")
        preview = "\n".join(result.code.splitlines()[:50])
        console.print(Syntax(preview, "python", theme="monokai", line_numbers=True))


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="AI Automation Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Stage 1: input modes
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("--ticket",  metavar="ID")
    input_group.add_argument("--excel",   metavar="PATH")
    input_group.add_argument("--text",    metavar="DESC")

    # Stage 2: index / search
    input_group.add_argument("--index",  action="store_true")
    input_group.add_argument("--search", metavar="QUERY")
    input_group.add_argument("--api",    metavar="PAGE")

    # Shared options
    parser.add_argument("--source",   choices=["jira", "ado"])
    parser.add_argument("--sheet",    metavar="NAME")
    parser.add_argument("--output",   metavar="PATH")
    parser.add_argument("--json",     action="store_true")

    # Stage 2+3 flags
    parser.add_argument("--retrieve", action="store_true",
                        help="After parsing, also run retrieval")
    parser.add_argument("--generate", action="store_true",
                        help="Parse → retrieve → generate test code (full pipeline)")
    parser.add_argument("--dry-run",  action="store_true",
                        help="With --generate: show code but don't write to disk")

    args = parser.parse_args()

    if not any([args.ticket, args.excel, args.text,
                args.index, args.search, args.api]):
        parser.print_help()
        sys.exit(1)

    try:
        # ── Stage 2: --index ───────────────────────────────────────────────
        if args.index:
            from ai_agent.stage2_context_retrieval.indexer import Indexer
            console.print("[bold cyan]Building RAG index…[/bold cyan]")
            indexer = Indexer()
            counts  = indexer.index_all()
            stats   = indexer.stats()
            console.print(Panel.fit(
                f"[green]✓ Index built successfully[/green]\n\n"
                f"  Code chunks:      [cyan]{counts['code']}[/cyan]\n"
                f"  Test chunks:      [cyan]{counts['test']}[/cyan]\n"
                f"  Knowledge chunks: [cyan]{counts['knowledge']}[/cyan]\n"
                f"  [bold]Total:            {stats['total']}[/bold]",
                title="Stage 2 — Index Complete", border_style="green",
            ))
            return

        # ── Stage 2: --search ──────────────────────────────────────────────
        if args.search:
            from ai_agent.stage2_context_retrieval.retriever import Retriever
            with console.status("[bold cyan]Searching…[/bold cyan]", spinner="dots"):
                retriever = Retriever()
                results   = retriever.search(args.search, n=8)
            console.print(f"\n[bold]Top results for:[/bold] '{args.search}'\n")
            for i, chunk in enumerate(results, 1):
                stale = " [yellow]⚠ stale?[/yellow]" if chunk.is_stale else ""
                console.print(
                    f"  [cyan]{i}.[/cyan] {chunk.short_label()} "
                    f"[dim](score={chunk.score:.3f})[/dim]{stale}"
                )
                console.print(f"     [dim]{chunk.text[:120].strip()}…[/dim]\n")
            return

        # ── Stage 2: --api ─────────────────────────────────────────────────
        if args.api:
            from ai_agent.stage2_context_retrieval.retriever import Retriever
            with console.status("[bold cyan]Loading API…[/bold cyan]", spinner="dots"):
                retriever = Retriever()
                methods   = retriever.get_page_object_api(args.api)
            console.print(f"\n[bold]Available methods for:[/bold] {args.api}\n")
            for m in methods:
                console.print(f"  [cyan]→[/cyan] {m}")
            return

        # ── Stage 1: parse ─────────────────────────────────────────────────
        from ai_agent.stage1_ticket_parser.parser_agent import parse
        with console.status("[bold cyan]Parsing input…[/bold cyan]", spinner="dots"):
            spec = parse(
                ticket_id=args.ticket,
                excel_path=args.excel,
                sheet_name=args.sheet,
                text=args.text,
                source=args.source,
                output_path=args.output,
            )

        if args.json:
            print(spec.model_dump_json(indent=2, exclude={"raw_content"}))
            return

        _print_spec(spec)
        if args.output:
            console.print(f"\n[green]✓ Saved to:[/green] {args.output}")

        # Stop here if no further stages requested
        if not args.retrieve and not args.generate:
            return

        # ── Stage 2: retrieve ──────────────────────────────────────────────
        from ai_agent.stage2_context_retrieval.retriever import Retriever
        with console.status("[bold cyan]Retrieving context from RAG…[/bold cyan]",
                            spinner="dots"):
            retriever = Retriever()
            retrieval = retriever.retrieve(
                query=spec.title + " " + spec.description,
                affected_pages=spec.affected_pages,
            )

        if args.retrieve and not args.generate:
            _print_retrieval(retrieval)
            return

        # Show retrieval summary even when generating
        _print_retrieval(retrieval)

        # ── Stage 3: generate ──────────────────────────────────────────────
        if args.generate:
            from ai_agent.stage3_generator.generator_agent import GeneratorAgent
            dry_run = getattr(args, "dry_run", False)

            with console.status(
                "[bold cyan]Generating tests with GPT-4o…[/bold cyan]",
                spinner="dots",
            ):
                agent  = GeneratorAgent()
                result = agent.generate(spec, retrieval, dry_run=dry_run)

            _print_generation(result)

            # ── Update Excel status after successful generation ─────────────
            if result.success and args.excel and not dry_run:
                from ai_agent.stage1_ticket_parser.readers.excel_reader import (
                    update_status_in_excel,
                )
                tc_ids  = [tc.id for tc in spec.test_cases]
                updated = update_status_in_excel(
                    file_path=args.excel,
                    sheet_name=args.sheet,
                    tc_ids=tc_ids,
                    new_status="Automated",
                )
                console.print(
                    f"\n[bold green]✓ Excel updated:[/bold green] "
                    f"{updated} test case(s) marked as [green]Automated[/green] "
                    f"in '{args.excel}'"
                )

    except EnvironmentError as e:
        console.print(f"[bold red]Config error:[/bold red] {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        console.print(f"[bold red]File not found:[/bold red] {e}")
        sys.exit(1)
    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise


if __name__ == "__main__":
    main()
