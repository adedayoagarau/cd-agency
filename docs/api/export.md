# `tools.export` — Export Formats

> Stability: Stable

```python
from tools.export import ContentEntry, ExportFormat, export_entries
```

Multi-format content export for CMS integration and localization handoff.

## Enum: `ExportFormat`

```python
class ExportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"
    XLIFF = "xliff"
```

## Class: `ContentEntry`

A single piece of content for export.

```python
@dataclass
class ContentEntry:
    id: str
    source: str        # Original (before) text
    target: str        # Improved (after) text
    context: str = ""  # Context description
    agent: str = ""    # Agent that produced the output
    notes: str = ""    # Additional notes
```

### `entry.to_dict()`

- Returns: `dict` (only includes non-empty optional fields)

## `export_entries(entries, fmt)`

Export content entries in the specified format.

- `entries`: `list[ContentEntry]`
- `fmt`: `ExportFormat`
- Returns: `str`

```python
entries = [
    ContentEntry(id="btn-1", source="Click here", target="Learn more",
                 agent="microcopy-review-agent"),
    ContentEntry(id="err-1", source="Error occurred", target="Something went wrong. Try again.",
                 agent="error-message-architect"),
]

# JSON
print(export_entries(entries, ExportFormat.JSON))

# CSV
print(export_entries(entries, ExportFormat.CSV))

# XLIFF 1.2
print(export_entries(entries, ExportFormat.XLIFF))
```

## Format Details

### JSON

CMS-compatible JSON with version metadata:

```json
{
  "version": "1.0",
  "entries": [
    { "id": "btn-1", "source": "Click here", "target": "Learn more", "agent": "microcopy-review-agent" }
  ],
  "count": 1
}
```

### CSV

Spreadsheet-compatible with headers:

```
ID,Source (Before),Target (After),Context,Agent,Notes
```

### Markdown

Table format:

```markdown
| ID | Before | After | Context | Agent |
|-----|--------|-------|---------|-------|
```

### XLIFF 1.2

Industry-standard translation interchange format compatible with CAT tools
(memoQ, Trados, Memsource, etc.):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file source-language="en" target-language="en">
    <body>
      <trans-unit id="btn-1">
        <source>Click here</source>
        <target>Learn more</target>
      </trans-unit>
    </body>
  </file>
</xliff>
```

All special XML characters (`&`, `<`, `>`, `"`, `'`) are properly escaped.
