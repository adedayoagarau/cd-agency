# VS Code Extension Specification: CD Agency

## Overview

A VS Code extension that provides inline content design assistance — lint UI strings as you type, run agents on selected text, and show content quality scores in the editor.

## Features

### 1. Inline Content Lint (Squiggly Lines)

Automatically detects UI strings in code files and shows lint warnings:

```tsx
// Yellow squiggly under "Click here" — suggests "View details" instead
<Button>Click here to see pricing</Button>
//       ~~~~~~~~~~~~~~~~~~~~~~~~~~
//       ⚠ [cd-agency] Avoid "click here" — describe the destination
//       Suggestion: "View pricing details"
```

**Detection heuristics:**
- JSX/TSX: Text inside component tags (`<Button>`, `<Text>`, `<p>`, etc.)
- JSON: Values in locale/translation files
- Markdown: Headings and body text
- YAML: String values in workflow definitions

### 2. Command Palette Actions

Available via `Cmd+Shift+P`:

- **CD Agency: Run Agent on Selection** — Select text → pick agent → see results in side panel
- **CD Agency: Score Selection** — Show readability + a11y + lint scores for selected text
- **CD Agency: Quick Fix** — Auto-apply suggested fixes for lint warnings
- **CD Agency: Switch Preset** — Change active design system preset
- **CD Agency: Check File** — Run full content audit on current file

### 3. Sidebar Panel

Persistent panel showing scores for the active file:

```
┌─────────────────────────┐
│ CD Agency               │
├─────────────────────────┤
│ File: LoginForm.tsx      │
│                          │
│ Content Quality          │
│ ████████░░ 7.5/10       │
│                          │
│ Readability: Grade 4 ✓  │
│ A11y: Pass (0 issues)   │
│ Lint: 2 warnings        │
│                          │
│ ─ Issues ─────────────── │
│ L12: Passive voice       │
│ L28: Button text > 25ch │
│                          │
│ Preset: Material Design  │
│ [Run Full Audit]         │
└─────────────────────────┘
```

### 4. Hover Information

Hover over detected UI strings to see:
- Character count vs. recommended limit
- Readability grade for the sentence
- Quick agent suggestions

### 5. CodeLens

Above detected UI strings:
```tsx
// 📝 Grade 3 | 14 chars | Run: Microcopy Review
<Button>Start free trial</Button>
```

## Architecture

```
┌─────────────────────────┐
│  VS Code Extension      │
│  (TypeScript)           │
├─────────────────────────┤
│  Content Detection      │  ← Finds UI strings in code
│  Inline Diagnostics     │  ← Shows lint warnings
│  Sidebar WebView        │  ← Scoring panel
│  Command Handlers       │  ← Palette actions
├─────────────────────────┤
│  cd-agency CLI bridge   │  ← Calls CLI subprocess
└─────┬───────────────────┘
      │
      ▼
┌─────────────────────────┐
│  cd-agency CLI          │
│  (Python)               │
│  score / agent run      │
└─────────────────────────┘
```

The extension shells out to the `cd-agency` CLI (already installed via pip) rather than embedding Python. This keeps the extension lightweight and reuses the full runtime.

## Configuration (settings.json)

```json
{
  "cdAgency.preset": "material-design",
  "cdAgency.autoLint": true,
  "cdAgency.lintOnSave": true,
  "cdAgency.showCodeLens": true,
  "cdAgency.targetReadingGrade": 8,
  "cdAgency.filePatterns": [
    "**/*.tsx",
    "**/*.jsx",
    "**/locales/**/*.json"
  ],
  "cdAgency.characterLimits": {
    "button": 25,
    "tooltip": 60,
    "notification": 120
  },
  "cdAgency.cliPath": "cd-agency"
}
```

## Extension Manifest (package.json)

```json
{
  "name": "cd-agency-vscode",
  "displayName": "CD Agency — Content Design",
  "description": "AI-powered content design lint, scoring, and agent assistance",
  "categories": ["Linters", "Other"],
  "activationEvents": [
    "onLanguage:typescriptreact",
    "onLanguage:javascriptreact",
    "onLanguage:json",
    "onLanguage:markdown"
  ],
  "contributes": {
    "commands": [
      { "command": "cdAgency.runAgent", "title": "CD Agency: Run Agent on Selection" },
      { "command": "cdAgency.scoreSelection", "title": "CD Agency: Score Selection" },
      { "command": "cdAgency.checkFile", "title": "CD Agency: Check File" },
      { "command": "cdAgency.switchPreset", "title": "CD Agency: Switch Preset" }
    ],
    "views": {
      "explorer": [
        { "id": "cdAgencyPanel", "name": "CD Agency" }
      ]
    }
  }
}
```

## Build Requirements

- TypeScript
- VS Code Extension API (`vscode` module)
- WebView for sidebar panel
- Child process for CLI invocation
- Language Server Protocol (LSP) for inline diagnostics
