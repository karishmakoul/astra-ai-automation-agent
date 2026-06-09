"""
Indexer: walks the automation codebase, chunks Python files by method,
embeds with sentence-transformers, and persists to ChromaDB.

Collections:
  code_index  → page objects, components, core base classes, conftest
  test_index  → existing test files (with staleness metadata)
  know_index  → YAML knowledge files (business rules, navigation, user types)

Run:   python -m ai_agent.cli --index
Re-run to refresh after codebase changes.
"""
import subprocess
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from ai_agent.stage2_context_retrieval.chunker import chunk_python_file, CodeChunk

console = Console()

# ── Paths ──────────────────────────────────────────────────────────────────
PROJECT_ROOT   = Path(__file__).parent.parent.parent          # repo root
VECTOR_STORE   = Path(__file__).parent.parent / "vector_store"
KNOWLEDGE_DIR  = Path(__file__).parent.parent / "knowledge"

# ── Files/folders to index ─────────────────────────────────────────────────
INCLUDE_DIRS = [
    "pages",
    "components",
    "core",
    "tests",
    "conftest.py",
]

# ── Folders to NEVER index (stale/archived code) ──────────────────────────
SKIP_PATTERNS = [
    "_archive", "deprecated", "legacy", "archive",
    ".venv", "__pycache__", ".pytest_cache",
    "node_modules", ".git",
]

EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # 384-dim, fast, runs locally


def _should_skip(path: Path) -> bool:
    """Return True if this path should be excluded from indexing."""
    for part in path.parts:
        if any(skip in part.lower() for skip in SKIP_PATTERNS):
            return True
    # Skip files starting with underscore (archived by convention)
    if path.stem.startswith("_"):
        return True
    return False


def _git_last_modified(filepath: Path) -> str:
    """Return ISO date string of when this file was last committed."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ci", str(filepath)],
            capture_output=True, text=True, cwd=PROJECT_ROOT,
        )
        date_str = result.stdout.strip()
        return date_str[:10] if date_str else "unknown"
    except Exception:
        return "unknown"


def _days_since(date_str: str) -> int:
    """Return number of days since a YYYY-MM-DD date string."""
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return (datetime.utcnow() - d).days
    except Exception:
        return 999


def _ci_status_for_test(filepath: Path) -> str:
    """
    Approximate CI status from pytest cache.
    Returns 'passing', 'failing', or 'unknown'.
    In a real project, replace this with a CI API call.
    """
    cache = PROJECT_ROOT / ".pytest_cache" / "v" / "cache" / "lastfailed"
    if not cache.exists():
        return "unknown"
    try:
        import json
        failed = json.loads(cache.read_text())
        rel = str(filepath.relative_to(PROJECT_ROOT))
        # If any test in this file appears in lastfailed → flag as failing
        if any(rel in k for k in failed):
            return "failing"
        return "passing"
    except Exception:
        return "unknown"


class Indexer:

    def __init__(self):
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        VECTOR_STORE.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(VECTOR_STORE),
            settings=Settings(anonymized_telemetry=False),
        )

        # Two collections: code + tests are separated so retrieval can filter
        self.code_col = self.client.get_or_create_collection(
            name="code_index",
            metadata={"description": "Page objects, components, base classes"},
        )
        self.test_col = self.client.get_or_create_collection(
            name="test_index",
            metadata={"description": "Existing test files with staleness metadata"},
        )
        self.know_col = self.client.get_or_create_collection(
            name="know_index",
            metadata={"description": "YAML knowledge files: business rules, flows, users"},
        )

    # ── Public API ─────────────────────────────────────────────────────────

    def index_all(self) -> dict[str, int]:
        """Index the full codebase. Returns count of chunks per collection."""
        counts = {"code": 0, "test": 0, "knowledge": 0}

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:

            # ── 1. Python source files ─────────────────────────────────────
            py_files = self._collect_python_files()
            task = progress.add_task("Indexing Python files…", total=len(py_files))

            for filepath in py_files:
                is_test = "tests/" in str(filepath).replace("\\", "/")
                col     = self.test_col if is_test else self.code_col
                chunks  = chunk_python_file(filepath, PROJECT_ROOT)
                if chunks:
                    self._upsert_chunks(col, chunks, filepath, is_test)
                    if is_test:
                        counts["test"] += len(chunks)
                    else:
                        counts["code"] += len(chunks)
                progress.advance(task)

            # ── 2. Knowledge YAML files ────────────────────────────────────
            yaml_files = list(KNOWLEDGE_DIR.glob("*.yaml")) + list(KNOWLEDGE_DIR.glob("*.yml"))
            if yaml_files:
                ktask = progress.add_task("Indexing knowledge files…", total=len(yaml_files))
                for kfile in yaml_files:
                    n = self._index_knowledge_file(kfile)
                    counts["knowledge"] += n
                    progress.advance(ktask)

        return counts

    def index_file(self, filepath: Path) -> int:
        """Index or re-index a single file. Returns chunk count."""
        is_test = "tests/" in str(filepath).replace("\\", "/")
        col     = self.test_col if is_test else self.code_col
        chunks  = chunk_python_file(filepath, PROJECT_ROOT)
        if chunks:
            self._upsert_chunks(col, chunks, filepath, is_test)
        return len(chunks)

    def stats(self) -> dict[str, Any]:
        """Return collection sizes."""
        return {
            "code_chunks":      self.code_col.count(),
            "test_chunks":      self.test_col.count(),
            "knowledge_chunks": self.know_col.count(),
            "total":            (
                self.code_col.count()
                + self.test_col.count()
                + self.know_col.count()
            ),
        }

    # ── Internal helpers ────────────────────────────────────────────────────

    def _collect_python_files(self) -> list[Path]:
        files: list[Path] = []
        for entry in INCLUDE_DIRS:
            target = PROJECT_ROOT / entry
            if target.is_file() and target.suffix == ".py":
                if not _should_skip(target):
                    files.append(target)
            elif target.is_dir():
                for py in target.rglob("*.py"):
                    if not _should_skip(py):
                        files.append(py)
        return sorted(set(files))

    def _upsert_chunks(
        self,
        collection,
        chunks: list[CodeChunk],
        filepath: Path,
        is_test: bool,
    ):
        last_modified = _git_last_modified(filepath)
        days_old      = _days_since(last_modified)
        ci_status     = _ci_status_for_test(filepath) if is_test else "n/a"

        # Staleness heuristic: tests not touched in 18+ months are flagged
        staleness = (
            "stale_candidate" if (is_test and days_old > 548)
            else "verified" if (ci_status == "passing")
            else "unknown"
        )

        ids        = []
        documents  = []
        embeddings = []
        metadatas  = []

        for chunk in chunks:
            ids.append(chunk.chunk_id)
            documents.append(chunk.text[:2000])  # ChromaDB document limit
            metadatas.append({
                **chunk.metadata,
                "last_modified":  last_modified,
                "days_old":       days_old,
                "ci_status":      ci_status,
                "staleness":      staleness,
            })

        # Batch embed
        raw_embeddings = self.model.encode(documents, show_progress_bar=False)
        embeddings     = [e.tolist() for e in raw_embeddings]

        collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def _index_knowledge_file(self, filepath: Path) -> int:
        """Parse a YAML knowledge file into flat key-value chunks and index them."""
        try:
            data = yaml.safe_load(filepath.read_text(encoding="utf-8"))
        except Exception:
            return 0

        if not isinstance(data, dict):
            return 0

        chunks = _flatten_yaml(data, filepath.stem)
        if not chunks:
            return 0

        ids        = [f"{filepath.stem}::{i}" for i in range(len(chunks))]
        documents  = [c["text"] for c in chunks]
        metadatas  = [
            {
                "file":       str(filepath.name),
                "chunk_type": "knowledge",
                "topic":      c.get("topic", filepath.stem),
                "staleness":  "verified",
            }
            for c in chunks
        ]

        raw_emb   = self.model.encode(documents, show_progress_bar=False)
        embeddings = [e.tolist() for e in raw_emb]

        self.know_col.upsert(ids=ids, documents=documents,
                             embeddings=embeddings, metadatas=metadatas)
        return len(chunks)


def _flatten_yaml(data: dict, topic: str, prefix: str = "") -> list[dict]:
    """Recursively flatten a YAML dict into text chunks."""
    chunks = []

    def _recurse(obj, path: str):
        if isinstance(obj, dict):
            # Emit a chunk for this dict node
            text = f"[{topic}] {path}:\n"
            text += "\n".join(
                f"  {k}: {v}"
                for k, v in obj.items()
                if not isinstance(v, (dict, list))
            )
            if text.strip():
                chunks.append({"text": text.strip(), "topic": path or topic})
            for k, v in obj.items():
                _recurse(v, f"{path}.{k}" if path else k)
        elif isinstance(obj, list):
            text = f"[{topic}] {path}:\n" + "\n".join(f"  - {item}" for item in obj)
            chunks.append({"text": text.strip(), "topic": path or topic})
        else:
            text = f"[{topic}] {path}: {obj}"
            chunks.append({"text": text.strip(), "topic": path or topic})

    _recurse(data, prefix)
    return [c for c in chunks if len(c["text"]) > 10]
