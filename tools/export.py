"""Export agent and workflow outputs in multiple formats."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from enum import Enum


class ExportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"
    XLIFF = "xliff"


@dataclass
class ContentEntry:
    """A single piece of content for export."""

    id: str
    source: str
    target: str
    context: str = ""
    agent: str = ""
    notes: str = ""

    def to_dict(self) -> dict:
        d = {"id": self.id, "source": self.source, "target": self.target}
        if self.context:
            d["context"] = self.context
        if self.agent:
            d["agent"] = self.agent
        if self.notes:
            d["notes"] = self.notes
        return d


def export_entries(entries: list[ContentEntry], fmt: ExportFormat) -> str:
    """Export content entries in the specified format."""
    if fmt == ExportFormat.JSON:
        return _export_json(entries)
    elif fmt == ExportFormat.CSV:
        return _export_csv(entries)
    elif fmt == ExportFormat.MARKDOWN:
        return _export_markdown(entries)
    elif fmt == ExportFormat.XLIFF:
        return _export_xliff(entries)
    else:
        raise ValueError(f"Unsupported format: {fmt}")


def _export_json(entries: list[ContentEntry]) -> str:
    """Export as JSON (CMS-compatible)."""
    data = {
        "version": "1.0",
        "entries": [e.to_dict() for e in entries],
        "count": len(entries),
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


def _export_csv(entries: list[ContentEntry]) -> str:
    """Export as CSV (spreadsheet-compatible)."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Source (Before)", "Target (After)", "Context", "Agent", "Notes"])
    for e in entries:
        writer.writerow([e.id, e.source, e.target, e.context, e.agent, e.notes])
    return output.getvalue()


def _export_markdown(entries: list[ContentEntry]) -> str:
    """Export as Markdown table."""
    lines = ["# Content Export", ""]
    lines.append("| ID | Before | After | Context | Agent |")
    lines.append("|-----|--------|-------|---------|-------|")
    for e in entries:
        source = e.source.replace("|", "\\|")[:50]
        target = e.target.replace("|", "\\|")[:50]
        lines.append(f"| {e.id} | {source} | {target} | {e.context} | {e.agent} |")
    lines.append("")
    lines.append(f"*{len(entries)} entries exported*")
    return "\n".join(lines)


def _export_xliff(entries: list[ContentEntry]) -> str:
    """Export as XLIFF 1.2 (translation tool compatible)."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">',
        '  <file source-language="en" target-language="en" datatype="plaintext" original="cd-agency-export">',
        '    <body>',
    ]
    for e in entries:
        source_escaped = _xml_escape(e.source)
        target_escaped = _xml_escape(e.target)
        lines.append(f'      <trans-unit id="{_xml_escape(e.id)}">')
        lines.append(f'        <source>{source_escaped}</source>')
        lines.append(f'        <target>{target_escaped}</target>')
        if e.notes:
            lines.append(f'        <note>{_xml_escape(e.notes)}</note>')
        lines.append('      </trans-unit>')
    lines.append('    </body>')
    lines.append('  </file>')
    lines.append('</xliff>')
    return "\n".join(lines)


def _xml_escape(text: str) -> str:
    """Escape XML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )
