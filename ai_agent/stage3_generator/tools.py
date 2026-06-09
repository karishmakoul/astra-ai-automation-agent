"""
Tool definitions and implementations for the Generator Agent.

Claude calls these tools during generation to ground itself in real code.
Each tool prevents a specific category of hallucination:

  read_file           → prevents wrong method signatures
  list_page_methods   → prevents calling non-existent methods
  get_fixtures        → prevents using wrong fixture names
  search_context      → prevents repeating retrieval inside the agent
"""
import ast
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent

# ── Tool schemas (sent to Claude's API) ─────────────────────────────────────

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Read the full contents of a file in the automation project. "
                "Use this to verify exact method signatures, locators, or imports "
                "before referencing them in generated test code."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": (
                            "Relative path from project root. "
                            "Examples: 'pages/ambitionbox/companies_page.py', "
                            "'components/filter_panel.py', 'conftest.py'"
                        ),
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_page_methods",
            "description": (
                "List all public methods and their signatures for a page object or component. "
                "ALWAYS call this before writing test code that interacts with a page. "
                "Never call a method that is not in this list."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "page_name": {
                        "type": "string",
                        "description": (
                            "Name of the page object or component. "
                            "Examples: 'companies_page', 'filter_panel', "
                            "'home_page', 'search_bar', 'company_card'"
                        ),
                    }
                },
                "required": ["page_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_fixtures",
            "description": (
                "Return all pytest fixtures available in conftest.py. "
                "Use this to know which fixtures to declare in test function signatures. "
                "Never invent fixture names."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_context",
            "description": (
                "Search the RAG index for additional context. "
                "Use when you need an example of how a specific action is performed "
                "that is not covered by the already-retrieved context."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What you are looking for. Be specific.",
                    },
                    "n": {
                        "type": "integer",
                        "description": "Number of results to return (default 3, max 6).",
                        "default": 3,
                    },
                },
                "required": ["query"],
            },
        },
    },
]


# ── Tool implementations ─────────────────────────────────────────────────────

def _find_file(page_name: str) -> Path | None:
    """Locate a page object or component file by name."""
    name = page_name.lower().replace(" ", "_")
    candidates = [
        PROJECT_ROOT / "pages" / "ambitionbox" / f"{name}.py",
        PROJECT_ROOT / "components" / f"{name}.py",
        PROJECT_ROOT / "core" / f"{name}.py",
    ]
    for c in candidates:
        if c.exists():
            return c
    # Fuzzy: search recursively
    for f in PROJECT_ROOT.rglob(f"*{name}*.py"):
        if ".venv" not in str(f) and "__pycache__" not in str(f):
            return f
    return None


def tool_read_file(path: str) -> str:
    """Read a file from the project. Returns content or error message."""
    full = PROJECT_ROOT / path
    if not full.exists():
        return f"ERROR: File not found: {path}"
    if not full.suffix == ".py":
        return f"ERROR: Only .py files are readable. Got: {path}"
    content = full.read_text(encoding="utf-8")
    return f"# === {path} ===\n{content}"


def tool_list_page_methods(page_name: str) -> str:
    """Parse a page object file and return all public method signatures."""
    filepath = _find_file(page_name)
    if not filepath:
        return f"ERROR: No file found for page '{page_name}'. Check the page name."

    source = filepath.read_text(encoding="utf-8")
    rel    = str(filepath.relative_to(PROJECT_ROOT))

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return f"ERROR: Could not parse {rel}: {e}"

    results = [f"# File: {rel}"]
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            results.append(f"\nclass {node.name}:")
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if item.name.startswith("_"):
                        continue  # skip private methods
                    # Build signature
                    args = [a.arg for a in item.args.args if a.arg != "self"]
                    defaults = item.args.defaults
                    n_defaults = len(defaults)
                    n_args     = len(args)
                    sig_parts  = []
                    for i, arg in enumerate(args):
                        di = i - (n_args - n_defaults)
                        if di >= 0:
                            try:
                                default_val = ast.unparse(defaults[di])
                            except Exception:
                                default_val = "..."
                            sig_parts.append(f"{arg}={default_val}")
                        else:
                            sig_parts.append(arg)
                    sig = f"  def {item.name}({', '.join(sig_parts)})"
                    # Return type hint
                    if item.returns:
                        try:
                            sig += f" -> {ast.unparse(item.returns)}"
                        except Exception:
                            pass
                    # Docstring
                    doc = ast.get_docstring(item)
                    if doc:
                        sig += f"\n      # {doc.split(chr(10))[0][:80]}"
                    results.append(sig)

    return "\n".join(results)


def tool_get_fixtures() -> str:
    """Parse conftest.py and return all fixture names and their descriptions."""
    conftest = PROJECT_ROOT / "conftest.py"
    if not conftest.exists():
        return "ERROR: conftest.py not found."

    source = conftest.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return "ERROR: Could not parse conftest.py"

    results = ["# Available pytest fixtures (from conftest.py):", ""]
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Check if decorated with @pytest.fixture
            def _is_fixture_decorator(d):
                # Unwrap calls like @pytest.fixture() or @pytest.fixture(autouse=True)
                target = d.func if isinstance(d, ast.Call) else d
                return (
                    (isinstance(target, ast.Name) and target.id == "fixture")
                    or (isinstance(target, ast.Attribute) and target.attr == "fixture")
                )

            is_fixture = any(_is_fixture_decorator(d) for d in node.decorator_list)
            if is_fixture:
                doc = ast.get_docstring(node) or ""
                args = [a.arg for a in node.args.args]
                results.append(f"  {node.name}({', '.join(args)})")
                if doc:
                    results.append(f"      # {doc.split(chr(10))[0][:80]}")

    return "\n".join(results)


def tool_search_context(query: str, n: int = 3) -> str:
    """Search the RAG index for additional context."""
    try:
        from ai_agent.stage2_context_retrieval.retriever import Retriever
        retriever = Retriever()
        results   = retriever.search(query, n=min(n, 6))
        if not results:
            return "No results found."
        parts = []
        for i, chunk in enumerate(results, 1):
            parts.append(f"--- Result {i}: {chunk.short_label()} ---")
            parts.append(chunk.text[:600])
        return "\n\n".join(parts)
    except Exception as e:
        return f"Search error: {e}"


def dispatch_tool(name: str, inputs: dict) -> str:
    """Route a tool call from Claude to the correct implementation."""
    if name == "read_file":
        return tool_read_file(inputs["path"])
    elif name == "list_page_methods":
        return tool_list_page_methods(inputs["page_name"])
    elif name == "get_fixtures":
        return tool_get_fixtures()
    elif name == "search_context":
        return tool_search_context(inputs["query"], inputs.get("n", 3))
    else:
        return f"ERROR: Unknown tool '{name}'"
