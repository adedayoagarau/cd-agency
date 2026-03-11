"""Knowledge base loader — loads and resolves knowledge references for agents."""

from __future__ import annotations

import re
from pathlib import Path

import yaml


# Default knowledge directory relative to project root
DEFAULT_KNOWLEDGE_DIR = Path("knowledge")


def load_knowledge_file(filepath: Path) -> dict:
    """Load a single knowledge file and extract its metadata and content.

    Returns a dict with keys: title, domain, tags, sources, content.
    """
    text = filepath.read_text(encoding="utf-8")

    frontmatter, body = _parse_frontmatter(text)

    return {
        "title": frontmatter.get("title", filepath.stem),
        "domain": frontmatter.get("domain", ""),
        "tags": frontmatter.get("tags", []),
        "sources": frontmatter.get("sources", []),
        "content": body.strip(),
        "ref": _filepath_to_ref(filepath),
    }


def resolve_knowledge_refs(
    refs: list[str],
    knowledge_dir: Path | None = None,
) -> str:
    """Resolve a list of knowledge references to combined content.

    Each ref is a path relative to the knowledge directory, e.g.:
    - "foundations/plain-language"
    - "books/nicely-said"
    - "case-studies/slack-voice-and-errors"

    Returns a single string with all resolved knowledge content.
    """
    if not refs:
        return ""

    knowledge_dir = knowledge_dir or DEFAULT_KNOWLEDGE_DIR

    if not knowledge_dir.exists():
        return ""

    sections = []
    for ref in refs:
        filepath = knowledge_dir / f"{ref}.md"
        if not filepath.exists():
            continue

        try:
            data = load_knowledge_file(filepath)
            title = data["title"]
            content = data["content"]
            if content:
                sections.append(f"### {title}\n\n{content}")
        except Exception:
            # Skip files that fail to parse
            continue

    return "\n\n---\n\n".join(sections)


def list_knowledge_files(knowledge_dir: Path | None = None) -> list[dict]:
    """List all available knowledge files with metadata.

    Returns a list of dicts with keys: ref, title, domain, tags.
    """
    knowledge_dir = knowledge_dir or DEFAULT_KNOWLEDGE_DIR

    if not knowledge_dir.exists():
        return []

    files = []
    for filepath in sorted(knowledge_dir.rglob("*.md")):
        try:
            data = load_knowledge_file(filepath)
            files.append({
                "ref": data["ref"],
                "title": data["title"],
                "domain": data["domain"],
                "tags": data["tags"],
            })
        except Exception:
            continue

    return files


def search_knowledge(
    query: str,
    knowledge_dir: Path | None = None,
) -> list[dict]:
    """Search knowledge files by title, tags, and content.

    Returns matching knowledge file metadata sorted by relevance.
    """
    knowledge_dir = knowledge_dir or DEFAULT_KNOWLEDGE_DIR

    if not knowledge_dir.exists():
        return []

    query_lower = query.lower()
    results = []

    for filepath in sorted(knowledge_dir.rglob("*.md")):
        try:
            data = load_knowledge_file(filepath)
            score = 0

            # Title match
            if query_lower in data["title"].lower():
                score += 3

            # Tag match
            for tag in data["tags"]:
                if query_lower in tag.lower():
                    score += 2

            # Domain match
            if query_lower in data["domain"].lower():
                score += 2

            # Content match
            if query_lower in data["content"].lower():
                score += 1

            if score > 0:
                results.append({
                    "ref": data["ref"],
                    "title": data["title"],
                    "domain": data["domain"],
                    "tags": data["tags"],
                    "score": score,
                })
        except Exception:
            continue

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def _filepath_to_ref(filepath: Path) -> str:
    """Convert a filepath to a knowledge reference string.

    e.g. knowledge/foundations/plain-language.md -> foundations/plain-language
    """
    # Get the path relative to the knowledge dir
    parts = filepath.parts
    try:
        idx = parts.index("knowledge")
        relative_parts = parts[idx + 1:]
    except ValueError:
        relative_parts = parts[-2:]

    ref = "/".join(relative_parts)
    if ref.endswith(".md"):
        ref = ref[:-3]
    return ref


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and remaining body from markdown text."""
    pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)"
    match = re.match(pattern, text, re.DOTALL)

    if not match:
        return {}, text

    frontmatter_str = match.group(1)
    body = match.group(2)

    try:
        frontmatter = yaml.safe_load(frontmatter_str) or {}
    except yaml.YAMLError:
        frontmatter = {}

    return frontmatter, body
