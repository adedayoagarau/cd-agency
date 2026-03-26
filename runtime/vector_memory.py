"""Vector-based semantic memory using ChromaDB and sentence-transformers.

Provides semantic search over project memory so agents retrieve context
by meaning rather than keyword matching. Runs entirely offline — no API
keys needed. ChromaDB persists vectors to disk; sentence-transformers
encodes on CPU.

Dependencies (optional — install via ``pip install cd-agency[vectors]``):
  - chromadb>=0.4.18
  - sentence-transformers>=2.2.2
"""

from __future__ import annotations

import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from runtime.memory import MEMORY_DIR, MemoryEntry

VECTOR_DIR = "vectors"
COLLECTION_NAME = "memory"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


class VectorMemory:
    """Semantic memory store backed by ChromaDB with sentence-transformer embeddings."""

    def __init__(self, project_dir: Path | None = None) -> None:
        import chromadb

        self.project_dir = project_dir or Path(".")
        self._vector_path = self.project_dir / MEMORY_DIR / VECTOR_DIR
        self._vector_path.mkdir(parents=True, exist_ok=True)

        self._client = chromadb.PersistentClient(path=str(self._vector_path))
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        self._model: Any = None  # lazy-loaded SentenceTransformer

    def _get_model(self) -> Any:
        """Lazy-load the sentence-transformer model on first use.

        Raises ``RuntimeError`` if the model cannot be loaded (e.g. it
        has not been downloaded and there is no internet access).
        """
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            try:
                self._model = SentenceTransformer(EMBEDDING_MODEL)
            except Exception as exc:
                raise RuntimeError(
                    f"Could not load embedding model '{EMBEDDING_MODEL}'. "
                    f"Ensure you have internet access for the initial download "
                    f"(~80 MB, one-time only): {exc}"
                ) from exc
            # Validate that the model can actually encode
            try:
                self._model.encode("test", convert_to_numpy=True)
            except Exception as exc:
                self._model = None
                raise RuntimeError(
                    f"Embedding model '{EMBEDDING_MODEL}' loaded but cannot "
                    f"encode text: {exc}"
                ) from exc
        return self._model

    def _encode(self, text: str) -> list[float]:
        """Encode a single text string into an embedding vector."""
        model = self._get_model()
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def remember(
        self,
        key: str,
        value: str,
        category: str = "decision",
        source_agent: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Store a memory entry with its embedding in ChromaDB.

        Uses ``key`` as the document ID so repeated calls upsert.
        """
        embedding = self._encode(value)
        ts = time.time()

        store_metadata: dict[str, Any] = {
            "key": key,
            "category": category,
            "source_agent": source_agent,
            "timestamp": ts,
        }
        if metadata:
            # Flatten user metadata — ChromaDB metadata values must be
            # str | int | float | bool, so we stringify complex values.
            for k, v in metadata.items():
                if isinstance(v, (str, int, float, bool)):
                    store_metadata[f"meta_{k}"] = v
                else:
                    store_metadata[f"meta_{k}"] = str(v)

        self._collection.upsert(
            ids=[key],
            documents=[value],
            embeddings=[embedding],
            metadatas=[store_metadata],
        )

    def semantic_search(self, query: str, n_results: int = 5) -> list[MemoryEntry]:
        """Return the most semantically similar memory entries for *query*."""
        if self._collection.count() == 0:
            return []

        embedding = self._encode(query)
        # Don't request more results than exist
        actual_n = min(n_results, self._collection.count())
        results = self._collection.query(
            query_embeddings=[embedding],
            n_results=actual_n,
            include=["documents", "metadatas", "distances"],
        )

        return self._results_to_entries(results)

    def recall(self, key: str) -> MemoryEntry | None:
        """Exact key lookup — no embedding needed."""
        results = self._collection.get(ids=[key], include=["documents", "metadatas"])
        if not results["ids"]:
            return None
        return self._single_result_to_entry(
            id_=results["ids"][0],
            document=results["documents"][0],  # type: ignore[index]
            metadata=results["metadatas"][0],  # type: ignore[index]
        )

    def recall_by_category(self, category: str) -> list[MemoryEntry]:
        """Filter entries by category metadata."""
        results = self._collection.get(
            where={"category": category},
            include=["documents", "metadatas"],
        )
        entries = []
        for i, id_ in enumerate(results["ids"]):
            entries.append(
                self._single_result_to_entry(
                    id_=id_,
                    document=results["documents"][i],  # type: ignore[index]
                    metadata=results["metadatas"][i],  # type: ignore[index]
                )
            )
        return entries

    def forget(self, key: str) -> bool:
        """Remove an entry by key. Returns True if it existed."""
        existing = self._collection.get(ids=[key])
        if not existing["ids"]:
            return False
        self._collection.delete(ids=[key])
        return True

    def get_context_for_agent(
        self,
        agent_name: str = "",
        query: str = "",
        n_results: int = 5,
    ) -> str:
        """Build a context string from semantically relevant memories.

        When *query* is provided, returns the top results ranked by
        semantic similarity. Falls back to returning all entries when
        no query is given (matches the old category-dump behaviour).
        """
        if self._collection.count() == 0:
            return ""

        if query:
            entries = self.semantic_search(query, n_results=n_results)
        else:
            # No query — return everything (backward compat)
            all_results = self._collection.get(include=["documents", "metadatas"])
            entries = []
            for i, id_ in enumerate(all_results["ids"]):
                entries.append(
                    self._single_result_to_entry(
                        id_=id_,
                        document=all_results["documents"][i],  # type: ignore[index]
                        metadata=all_results["metadatas"][i],  # type: ignore[index]
                    )
                )

        if not entries:
            return ""

        parts = ["## Project Memory (Semantic)\n"]
        for entry in entries:
            label = entry.category.title() if entry.category else "General"
            parts.append(f"- **[{label}] {entry.key}**: {entry.value}")

        return "\n".join(parts)

    def count(self) -> int:
        """Return the number of stored entries."""
        return self._collection.count()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _single_result_to_entry(
        id_: str,
        document: str,
        metadata: dict[str, Any],
    ) -> MemoryEntry:
        user_meta: dict[str, Any] = {}
        for k, v in metadata.items():
            if k.startswith("meta_"):
                user_meta[k[5:]] = v

        return MemoryEntry(
            key=metadata.get("key", id_),
            value=document,
            category=metadata.get("category", ""),
            source_agent=metadata.get("source_agent", ""),
            timestamp=metadata.get("timestamp", 0.0),
            metadata=user_meta,
        )

    @staticmethod
    def _results_to_entries(results: dict[str, Any]) -> list[MemoryEntry]:
        """Convert ChromaDB query results dict into MemoryEntry list."""
        entries: list[MemoryEntry] = []
        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        for i, id_ in enumerate(ids):
            doc = documents[i] if i < len(documents) else ""
            meta = metadatas[i] if i < len(metadatas) else {}
            entries.append(
                VectorMemory._single_result_to_entry(
                    id_=id_, document=doc, metadata=meta
                )
            )
        return entries


def migrate_json_to_vectors(project_dir: Path | None = None) -> int:
    """Import entries from the legacy JSON memory file into ChromaDB.

    Returns the number of entries migrated. Idempotent — existing keys
    are upserted.
    """
    import json

    project_dir = project_dir or Path(".")
    json_path = project_dir / MEMORY_DIR / "memory.json"

    if not json_path.exists():
        return 0

    data = json.loads(json_path.read_text(encoding="utf-8"))
    raw_entries = data.get("entries", {})
    if not raw_entries:
        return 0

    vector_memory = VectorMemory(project_dir)
    count = 0
    for key, entry_data in raw_entries.items():
        vector_memory.remember(
            key=entry_data.get("key", key),
            value=entry_data.get("value", ""),
            category=entry_data.get("category", "decision"),
            source_agent=entry_data.get("source_agent", ""),
            metadata=entry_data.get("metadata", {}),
        )
        count += 1

    return count
