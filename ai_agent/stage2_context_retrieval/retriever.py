"""
Retriever: queries ChromaDB collections and returns context chunks
grounded in the actual codebase for use by the generator agent.

Design:
  - Always fetches page object for the affected page first (API contract)
  - Then fetches similar test examples (patterns to follow)
  - Then fetches relevant knowledge (business rules)
  - Detects and surfaces contradictions instead of silently picking one
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

VECTOR_STORE   = Path(__file__).parent.parent / "vector_store"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


@dataclass
class RetrievedChunk:
    text:       str
    chunk_id:   str
    metadata:   dict
    score:      float       # cosine distance (lower = more similar)
    collection: str         # "code" | "test" | "knowledge"

    @property
    def is_stale(self) -> bool:
        return self.metadata.get("staleness") == "stale_candidate"

    @property
    def file(self) -> str:
        return self.metadata.get("file", "")

    @property
    def class_name(self) -> str:
        return self.metadata.get("class_name", "")

    @property
    def method_name(self) -> str:
        return self.metadata.get("method_name", "")

    def short_label(self) -> str:
        parts = [self.file]
        if self.class_name:  parts.append(self.class_name)
        if self.method_name: parts.append(self.method_name)
        return " → ".join(parts)


@dataclass
class RetrievalResult:
    page_object_methods: list[RetrievedChunk]   = field(default_factory=list)
    similar_tests:       list[RetrievedChunk]   = field(default_factory=list)
    knowledge:           list[RetrievedChunk]   = field(default_factory=list)
    conflicts:           list[dict]             = field(default_factory=list)
    stale_warnings:      list[str]              = field(default_factory=list)

    def all_chunks(self) -> list[RetrievedChunk]:
        return self.page_object_methods + self.similar_tests + self.knowledge

    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0

    def context_for_prompt(self) -> str:
        """Format all retrieved chunks into a single context string for the LLM."""
        parts = []

        if self.page_object_methods:
            parts.append("## AVAILABLE PAGE OBJECT METHODS (use ONLY these):")
            for c in self.page_object_methods:
                parts.append(f"\n### {c.short_label()}\n```python\n{c.text}\n```")

        if self.similar_tests:
            parts.append("\n## EXISTING TEST EXAMPLES (follow these patterns):")
            for c in self.similar_tests:
                stale = " ⚠️ POTENTIALLY STALE" if c.is_stale else ""
                parts.append(f"\n### {c.short_label()}{stale}\n```python\n{c.text}\n```")

        if self.knowledge:
            parts.append("\n## BUSINESS RULES & KNOWLEDGE:")
            for c in self.knowledge:
                parts.append(f"\n{c.text}")

        if self.conflicts:
            parts.append("\n## ⚠️ CONFLICTS DETECTED — DO NOT GENERATE, REPORT THESE:")
            for conflict in self.conflicts:
                parts.append(
                    f"\n- Topic: {conflict['topic']}\n"
                    f"  Version A: {conflict['source_a']}\n"
                    f"  Version B: {conflict['source_b']}\n"
                    f"  Difference: {conflict['difference']}"
                )

        if self.stale_warnings:
            parts.append("\n## ⚠️ STALENESS WARNINGS:")
            for w in self.stale_warnings:
                parts.append(f"  - {w}")

        return "\n".join(parts)


class Retriever:

    def __init__(self):
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        self.client = chromadb.PersistentClient(
            path=str(VECTOR_STORE),
            settings=Settings(anonymized_telemetry=False),
        )
        self.code_col = self.client.get_collection("code_index")
        self.test_col = self.client.get_collection("test_index")
        self.know_col = self.client.get_collection("know_index")

    # ── Main entry point ────────────────────────────────────────────────────

    def retrieve(
        self,
        query:          str,
        affected_pages: list[str],
        n_code:         int = 8,
        n_tests:        int = 5,
        n_knowledge:    int = 4,
    ) -> RetrievalResult:
        """
        Retrieve all relevant context for generating tests.

        Args:
            query:          Feature description (e.g. "salary filter by experience")
            affected_pages: Page names from TestSpec (e.g. ["salaries_page"])
            n_code:         Max code chunks to retrieve
            n_tests:        Max test example chunks to retrieve
            n_knowledge:    Max knowledge chunks to retrieve

        Returns:
            RetrievalResult with page objects, test examples, and knowledge
        """
        result = RetrievalResult()
        query_vec = self._embed(query)

        # ── Phase 1: Page object methods (API contract) ────────────────────
        result.page_object_methods = self._get_page_object_methods(
            affected_pages, query_vec, n_code
        )

        # ── Phase 2: Similar test examples ────────────────────────────────
        raw_tests = self._query_collection(
            self.test_col, query_vec, n_results=n_tests * 2
        )
        # Separate verified from stale
        verified = [c for c in raw_tests if not c.is_stale]
        stale    = [c for c in raw_tests if c.is_stale]

        result.similar_tests = verified[:n_tests]

        # Warn about stale but still include if we have too few verified
        if len(verified) < 2 and stale:
            extra = stale[: n_tests - len(verified)]
            result.similar_tests += extra
            for s in extra:
                result.stale_warnings.append(
                    f"{s.file} — last modified {s.metadata.get('last_modified', '?')} "
                    f"({s.metadata.get('days_old', '?')} days ago). "
                    f"Verify this test reflects the current application flow."
                )

        # ── Phase 3: Business knowledge ────────────────────────────────────
        result.knowledge = self._query_collection(
            self.know_col, query_vec, n_results=n_knowledge
        )

        # ── Phase 4: Conflict detection ────────────────────────────────────
        result.conflicts = self._detect_conflicts(
            result.similar_tests, affected_pages
        )

        return result

    def get_page_object_api(self, page_name: str) -> list[str]:
        """
        Return all method signatures for a given page object.
        Used by the generator to validate that it only calls real methods.
        """
        results = self.code_col.get(
            where={"$and": [
                {"chunk_type": "page_object"},
                {"file": {"$contains": page_name}},
            ]},
            include=["metadatas"],
        )
        sigs = []
        for meta in results.get("metadatas", []):
            sig = meta.get("signature", "")
            if sig and not sig.startswith("class "):
                sigs.append(sig)
        return sorted(set(sigs))

    def search(self, query: str, n: int = 10) -> list[RetrievedChunk]:
        """Free-text search across all collections. Used for CLI --search."""
        vec = self._embed(query)
        all_chunks = []
        for col, name in [(self.code_col, "code"), (self.test_col, "test"), (self.know_col, "knowledge")]:
            try:
                chunks = self._query_collection(col, vec, n_results=n // 3 + 1)
                for c in chunks:
                    c.collection = name
                all_chunks.extend(chunks)
            except Exception:
                pass
        # Sort by score (lower = better match)
        all_chunks.sort(key=lambda c: c.score)
        return all_chunks[:n]

    # ── Internal helpers ────────────────────────────────────────────────────

    def _embed(self, text: str) -> list[float]:
        return self.model.encode(text).tolist()

    def _query_collection(
        self,
        collection,
        query_vec: list[float],
        n_results: int = 5,
        where: dict | None = None,
    ) -> list[RetrievedChunk]:
        """Query a ChromaDB collection and return RetrievedChunk objects."""
        kwargs: dict[str, Any] = {
            "query_embeddings": [query_vec],
            "n_results":        min(n_results, collection.count() or 1),
            "include":          ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        try:
            res = collection.query(**kwargs)
        except Exception:
            return []

        chunks = []
        for doc, meta, dist in zip(
            res["documents"][0],
            res["metadatas"][0],
            res["distances"][0],
        ):
            chunks.append(RetrievedChunk(
                text=doc,
                chunk_id=res.get("ids", [[]])[0][len(chunks)] if res.get("ids") else "",
                metadata=meta,
                score=dist,
                collection="",
            ))
        return chunks

    def _get_page_object_methods(
        self,
        affected_pages: list[str],
        query_vec: list[float],
        n: int,
    ) -> list[RetrievedChunk]:
        """
        Retrieve page object methods for the affected pages.
        First tries exact file match, then falls back to semantic search.
        """
        chunks = []

        # Try exact page-name match in file metadata
        for page in affected_pages:
            normalized = page.lower().replace(" ", "_")
            try:
                exact = self.code_col.get(
                    where={"$and": [
                        {"chunk_type": "page_object"},
                        {"file": {"$contains": normalized}},
                    ]},
                    include=["documents", "metadatas"],
                )
                for doc, meta in zip(
                    exact.get("documents", []),
                    exact.get("metadatas", []),
                ):
                    chunks.append(RetrievedChunk(
                        text=doc, chunk_id="",
                        metadata=meta, score=0.0,
                        collection="code",
                    ))
            except Exception:
                pass

        # Supplement with semantic search if needed
        if len(chunks) < n:
            semantic = self._query_collection(
                self.code_col, query_vec,
                n_results=n - len(chunks),
                where={"chunk_type": {"$in": ["page_object", "component"]}},
            )
            # Avoid duplicates
            existing_ids = {c.text[:100] for c in chunks}
            for c in semantic:
                if c.text[:100] not in existing_ids:
                    c.collection = "code"
                    chunks.append(c)

        return chunks[:n]

    def _detect_conflicts(
        self,
        test_chunks: list[RetrievedChunk],
        affected_pages: list[str],
    ) -> list[dict]:
        """
        Detect when two test chunks describe the same scenario differently.
        Simple heuristic: same page + similar text but different method calls.
        """
        conflicts = []

        # Group by page name
        by_page: dict[str, list[RetrievedChunk]] = {}
        for chunk in test_chunks:
            for page in affected_pages:
                if page in chunk.file.lower():
                    by_page.setdefault(page, []).append(chunk)

        for page, page_chunks in by_page.items():
            if len(page_chunks) < 2:
                continue
            # Check for method name mismatches between chunks
            seen_methods: dict[str, str] = {}  # action → source
            import re
            for chunk in page_chunks:
                methods = re.findall(r'(\w+_page|filter_panel|search_bar)\.\w+\(', chunk.text)
                for method_call in methods:
                    obj, _, meth = method_call.partition(".")
                    key = f"{page}:{obj}"
                    if key in seen_methods and seen_methods[key] != meth:
                        conflicts.append({
                            "topic":      f"{page} — {obj} usage",
                            "source_a":   seen_methods[key + "_src"],
                            "source_b":   chunk.file,
                            "difference": f"'{seen_methods[key]}' vs '{meth}'",
                        })
                    else:
                        seen_methods[key]        = meth
                        seen_methods[key + "_src"] = chunk.file

        return conflicts
