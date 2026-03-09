# Figma Plugin Specification: CD Agency

## Overview

A Figma plugin that connects text layers to the Content Design Agency, allowing designers to run agents directly on UI copy without leaving Figma.

## User Flow

### 1. Select & Launch
1. Designer selects a text layer in Figma
2. Right-click → Plugins → "CD Agency" (or keyboard shortcut)
3. Plugin panel opens with detected text

### 2. Agent Selection
- **Auto-suggest**: Based on the text context (button → CTA Optimizer, error state → Error Architect)
- **Manual pick**: Dropdown of all 15 agents
- **Quick actions**: "Review microcopy", "Check accessibility", "Optimize CTA"

### 3. Configuration
- **Preset**: Select design system (Material, Polaris, Atlassian, Apple HIG, Custom)
- **Additional context**: Optional fields for target audience, platform, tone
- **Scoring**: Toggle auto-scoring on/off

### 4. Results
- **Suggestions panel**: Agent output displayed alongside original
- **Inline comparison**: Before/after with diff highlighting
- **One-click apply**: Replace the text layer content with a suggestion
- **Scoring badge**: Readability grade, a11y pass/fail shown inline

### 5. History
- Recent runs saved per-file
- Pin favorite suggestions
- Export run history as CSV

## Architecture

```
┌─────────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Figma Plugin UI   │────→│  CD Agency API   │────→│  Claude API     │
│   (TypeScript)      │←────│  (Python/FastAPI) │←────│  (Anthropic)    │
└─────────────────────┘     └──────────────────┘     └─────────────────┘
```

### Plugin Side (TypeScript)
- Figma Plugin API for text layer access
- UI built with Figma's plugin UI framework
- Communicates with backend via HTTP POST
- Stores recent history in plugin data storage

### Backend (Python/FastAPI)
- Thin REST API wrapping the existing `runtime` package
- Endpoints:
  - `POST /api/run` — Run an agent on text
  - `POST /api/score` — Score text content
  - `GET /api/agents` — List available agents
  - `GET /api/presets` — List design system presets
- Auth: API key per user/team

### API Contract

```json
// POST /api/run
{
  "agent": "cta-optimization-specialist",
  "input": {
    "current_cta_text": "Submit",
    "ui_context": "Pricing page free trial button",
    "target_audience": "Engineering managers"
  },
  "preset": "material-design"
}

// Response
{
  "content": "...",
  "score": {
    "readability": { "grade": 4.2, "ease": 85 },
    "a11y": { "passed": true, "issues": 0 }
  },
  "model": "claude-sonnet-4-20250514",
  "tokens": { "input": 450, "output": 320 }
}
```

## UI Mockups

### Agent Picker Screen
```
┌─────────────────────────────────┐
│ CD Agency                    ✕  │
├─────────────────────────────────┤
│ Selected: "Submit"              │
│                                 │
│ Suggested: CTA Optimizer  [Run] │
│                                 │
│ ─ or pick an agent ──────────── │
│ ▸ Microcopy Review              │
│ ▸ Error Message Architect       │
│ ▸ Accessibility Auditor         │
│ ▸ Tone Calibrator               │
│ ▸ All Agents...                 │
│                                 │
│ Preset: [Material Design ▾]    │
└─────────────────────────────────┘
```

### Results Screen
```
┌─────────────────────────────────┐
│ CD Agency — CTA Optimizer    ✕  │
├─────────────────────────────────┤
│ Original: "Submit"              │
│                                 │
│ Suggestions:                    │
│ ┌─────────────────────────────┐ │
│ │ ★ "Start my free trial"    │ │
│ │   Ownership psychology      │ │
│ │            [Apply] [Copy]   │ │
│ ├─────────────────────────────┤ │
│ │   "Try free for 14 days"   │ │
│ │   Specificity               │ │
│ │            [Apply] [Copy]   │ │
│ └─────────────────────────────┘ │
│                                 │
│ Score: Grade 3 ✓ | A11y: Pass  │
│                                 │
│ [Run Another Agent]  [History]  │
└─────────────────────────────────┘
```

## Required Figma API Permissions
- `currentPage` — Read text layers
- `textNode.characters` — Read/write text content
- `pluginData` — Store run history
- `ui` — Plugin panel UI
- Network access for API calls

## Build Requirements
- TypeScript + Figma Plugin API
- Webpack for bundling
- Figma Plugin UI (HTML/CSS in iframe)
- Backend: FastAPI + existing `runtime` package
