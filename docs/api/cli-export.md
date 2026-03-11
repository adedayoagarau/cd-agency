# `export` Command

> Stability: Stable

Export content in various formats for CMS integration, localization handoff, or
documentation.

```bash
cd-agency export [OPTIONS]
```

## Options

| Option | Short | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `--input` | `-i` | string | | Original (before) text **(required)** |
| `--output` | `-o` | string | | Improved (after) text **(required)** |
| `--id` | | string | `"1"` | Content entry ID |
| `--context` | | string | `""` | Context description |
| `--agent` | | string | `""` | Agent that produced the output |
| `--format` | `-f` | choice | `json` | Export format |

## Formats

### JSON

```bash
cd-agency export -i "Click here" -o "Learn more" --format json
```

```json
{
  "version": "1.0",
  "entries": [
    { "id": "1", "source": "Click here", "target": "Learn more" }
  ],
  "count": 1
}
```

### CSV

```bash
cd-agency export -i "Click here" -o "Learn more" --format csv
```

```csv
ID,Source (Before),Target (After),Context,Agent,Notes
1,Click here,Learn more,,,
```

### Markdown

```bash
cd-agency export -i "Click here" -o "Learn more" --format markdown
```

```markdown
# Content Export

| ID | Before | After | Context | Agent |
|-----|--------|-------|---------|-------|
| 1 | Click here | Learn more | | |

*1 entries exported*
```

### XLIFF 1.2

Industry-standard translation interchange format.

```bash
cd-agency export -i "Click here" -o "Learn more" --format xliff
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file source-language="en" target-language="en" datatype="plaintext"
        original="cd-agency-export">
    <body>
      <trans-unit id="1">
        <source>Click here</source>
        <target>Learn more</target>
      </trans-unit>
    </body>
  </file>
</xliff>
```
