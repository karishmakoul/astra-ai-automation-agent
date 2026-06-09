"""
Chunker: splits Python source files into method-level chunks using Python's AST.

Why method-level chunking?
  - Each chunk maps to one callable unit the LLM can use
  - Retrieval is precise — "how to apply a filter" → retrieves exactly FilterPanel.apply()
  - Metadata (class, method, signature) prevents hallucinated method names

Each chunk contains:
  - The full source of one method/function
  - Its class context (class name + docstring)
  - Metadata: file, class, method name, signature, chunk type
"""
import ast
import textwrap
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CodeChunk:
    """One semantic unit extracted from a Python file."""
    text:       str                    # the actual source text fed to the embedder
    chunk_id:   str                    # unique ID: file_path::ClassName::method_name
    metadata:   dict = field(default_factory=dict)

    def display(self) -> str:
        return f"[{self.metadata.get('chunk_type','?')}] {self.chunk_id}"


def _get_source_segment(source_lines: list[str], node: ast.AST) -> str:
    """Extract raw source lines for an AST node."""
    start = node.lineno - 1
    end   = node.end_lineno
    return textwrap.dedent("\n".join(source_lines[start:end]))


def _get_docstring(node: ast.AST) -> str:
    """Safely extract docstring from a class or function node."""
    try:
        return ast.get_docstring(node) or ""
    except Exception:
        return ""


def _method_signature(func_node: ast.FunctionDef) -> str:
    """Build a human-readable signature string from an AST FunctionDef."""
    args = []
    fn_args = func_node.args

    # positional args
    num_defaults = len(fn_args.defaults)
    num_args     = len(fn_args.args)
    for i, arg in enumerate(fn_args.args):
        default_offset = i - (num_args - num_defaults)
        if default_offset >= 0:
            default_node = fn_args.defaults[default_offset]
            try:
                default_val = ast.unparse(default_node)
            except Exception:
                default_val = "..."
            args.append(f"{arg.arg}={default_val}")
        else:
            args.append(arg.arg)

    # *args
    if fn_args.vararg:
        args.append(f"*{fn_args.vararg.arg}")

    # **kwargs
    if fn_args.kwarg:
        args.append(f"**{fn_args.kwarg.arg}")

    return f"{func_node.name}({', '.join(args)})"


def chunk_python_file(
    filepath: Path,
    project_root: Path,
) -> list[CodeChunk]:
    """
    Parse a Python file and return one CodeChunk per method/function.
    Also emits one class-level chunk per class (for class docstring context).
    """
    source = filepath.read_text(encoding="utf-8")
    source_lines = source.splitlines()
    rel_path = str(filepath.relative_to(project_root))

    try:
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError:
        return []

    chunks: list[CodeChunk] = []

    # ── Module-level functions (e.g. standalone helpers) ───────────────────
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.FunctionDef)
            and not isinstance(getattr(node, "_parent", None), ast.ClassDef)
        ):
            # set parent refs
            pass

    # Set parent on every node (ast doesn't do this by default)
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child._parent = node  # type: ignore[attr-defined]

    for node in ast.walk(tree):

        # ── Class-level chunk ──────────────────────────────────────────────
        if isinstance(node, ast.ClassDef):
            class_doc   = _get_docstring(node)
            class_chunk = _get_source_segment(source_lines, node)
            chunk_id    = f"{rel_path}::{node.name}"

            chunks.append(CodeChunk(
                text=(
                    f"# File: {rel_path}\n"
                    f"class {node.name}:\n"
                    f'    """{class_doc}"""\n\n'
                    f"{class_chunk[:600]}"   # truncate very long class bodies
                ),
                chunk_id=chunk_id,
                metadata={
                    "file":        rel_path,
                    "class_name":  node.name,
                    "method_name": "",
                    "chunk_type":  _classify_file(rel_path),
                    "docstring":   class_doc[:200],
                    "signature":   f"class {node.name}",
                },
            ))

        # ── Method-level chunk ─────────────────────────────────────────────
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            parent = getattr(node, "_parent", None)
            class_name = parent.name if isinstance(parent, ast.ClassDef) else ""
            method_src  = _get_source_segment(source_lines, node)
            signature   = _method_signature(node)
            doc         = _get_docstring(node)

            # Build context-rich text for the embedder
            text_parts = [f"# File: {rel_path}"]
            if class_name:
                class_doc = _get_docstring(parent) if isinstance(parent, ast.ClassDef) else ""
                text_parts.append(f"# Class: {class_name} — {class_doc[:120]}")
            text_parts.append(f"\ndef {signature}:")
            if doc:
                text_parts.append(f'    """{doc}"""')
            text_parts.append(method_src)

            chunk_id = (
                f"{rel_path}::{class_name}::{node.name}"
                if class_name
                else f"{rel_path}::{node.name}"
            )

            chunks.append(CodeChunk(
                text="\n".join(text_parts),
                chunk_id=chunk_id,
                metadata={
                    "file":        rel_path,
                    "class_name":  class_name,
                    "method_name": node.name,
                    "signature":   signature,
                    "chunk_type":  _classify_file(rel_path),
                    "docstring":   doc[:200],
                },
            ))

    return chunks


def _classify_file(rel_path: str) -> str:
    """Tag a file as page_object | component | test | base | conftest | knowledge."""
    p = rel_path.lower()
    if "pages/"      in p: return "page_object"
    if "components/" in p: return "component"
    if "tests/"      in p: return "test"
    if "core/"       in p: return "base"
    if "conftest"    in p: return "conftest"
    return "other"
