# CD Agency Figma Plugin

A Figma plugin that connects text layers to the Content Design Agency, allowing designers to run agents directly on UI copy without leaving Figma.

## Features

- **Select & Run**: Select any text layer, pick an agent, get improved copy
- **Auto-suggest**: Plugin suggests the best agent based on your text content (e.g., error text triggers Error Message Architect)
- **15 Specialized Agents**: Microcopy Review, CTA Optimizer, Error Architect, Accessibility Auditor, Tone Evaluator, and more
- **Design System Presets**: Apply Material Design, Polaris, Atlassian, or Apple HIG voice guidelines
- **One-click Apply**: Replace text layer content with improved copy directly in Figma
- **Scoring**: See readability grade and a11y compliance inline on results
- **History**: Recent runs saved locally with CSV export
- **Additional Context**: Provide target audience, UI context, and tone hints for better results

## Prerequisites

You need the CD Agency API backend running. See `api/` in the project root.

```bash
# Start the API server
cd /path/to/cd-agency
pip install fastapi uvicorn
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

The API exposes these endpoints used by the plugin:

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/agents/{slug}/run` | POST | Run an agent on input text |
| `/api/v1/score/all` | POST | Score text (readability, lint, a11y) |
| `/api/v1/agents` | GET | List available agents |
| `/api/v1/presets` | GET | List design system presets |

## Build & Install

```bash
cd figma-plugin
npm install
npm run build
```

This compiles TypeScript and bundles everything into `dist/`:
- `dist/code.js` -- Main thread (Figma sandbox)
- `dist/ui.html` -- UI thread (iframe with embedded JS/CSS)

### Import into Figma

1. Open Figma Desktop
2. Go to **Plugins > Development > Import plugin from manifest...**
3. Select `figma-plugin/manifest.json`
4. The plugin appears under **Plugins > Development > CD Agency**

## Configure API URL

On first launch the plugin shows a setup screen:

1. Enter the **API Base URL** (default: `http://localhost:8000`)
2. Optionally enter an **API Key** if your backend requires authentication
3. Click **Connect**

You can change these later via the settings icon in the header.

Settings are stored in the iframe's `localStorage` and persist across sessions.

## Usage

1. **Select** a text layer in your Figma design
2. **Launch** the plugin (right-click > Plugins > CD Agency)
3. The plugin shows your selected text and suggests relevant agents
4. **Pick an agent** from the dropdown or click a quick-action pill
5. Optionally select a **design system preset** (Material, Polaris, Atlassian, Apple HIG)
6. Optionally expand **Additional Context** to provide audience, UI context, or tone
7. Click **Run Agent**
8. Review the **suggestions** with rationale
9. Click **Apply** to update the Figma text layer, or **Copy** to clipboard
10. Check the **score badges** for readability grade and a11y pass/fail
11. Click **Run Another** to try a different agent, or view **History**

## Development

```bash
npm run watch    # Build in dev mode + watch for changes
npm run dev      # Same as watch
npm run build    # Production build
```

The project uses:
- **TypeScript** for type safety
- **Webpack** with two entry points (code.ts for Figma sandbox, ui.ts for iframe)
- **html-webpack-plugin** to bundle ui.html with injected JS
- **@figma/plugin-typings** for Figma Plugin API types

### File Structure

```
figma-plugin/
  manifest.json       Figma plugin manifest
  package.json        Node dependencies and scripts
  tsconfig.json       TypeScript configuration
  webpack.config.js   Webpack multi-config (code + UI)
  src/
    code.ts           Main thread - Figma API access, text layer read/write
    ui.ts             UI thread - rendering, API calls, state management
    ui.html           HTML template with embedded CSS
  dist/               Build output (generated)
    code.js
    ui.html
```

### Architecture

```
+---------------------+     +------------------+     +-----------------+
|  Figma Plugin UI    |---->|  CD Agency API   |---->|  Claude API     |
|  (TypeScript/HTML)  |<----|  (Python/FastAPI) |<----|  (Anthropic)    |
+---------------------+     +------------------+     +-----------------+
```

- **code.ts** runs in Figma's sandbox with access to the Figma Plugin API (reading/writing text nodes)
- **ui.ts** runs in an iframe, handles rendering and HTTP calls to the backend
- Communication between code.ts and ui.ts uses `postMessage`

## Plugin Screens

### Setup
- First-launch configuration for API URL and optional API key
- Clean centered layout with the CD Agency branding

### Agent Picker (main screen)
- Shows detected text from the selected layer with layer context
- Quick-action pills with auto-suggested agents based on text content
- Full agent dropdown (all 15 agents)
- Design system preset selector
- Collapsible additional context fields (audience, UI context, tone)
- Auto-score toggle

### Loading
- Spinner with agent name and progress message
- Displayed while the API call is in flight

### Results
- Before/after comparison (original text shown with strikethrough)
- Multiple suggestion cards with rationale text
- Recommended suggestion highlighted in green
- Apply and Copy buttons per suggestion
- Score badges (readability grade, a11y pass/fail)
- Collapsible full agent response text
- Navigation to run another agent or view history

### History
- List of recent runs with agent name, original text preview, and time
- Click to view past results
- Clear all and Export CSV buttons

### Settings
- Edit API URL and API key
- Accessible via gear icon from the picker screen
