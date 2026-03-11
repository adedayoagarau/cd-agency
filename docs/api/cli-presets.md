# `presets` Command

> Stability: Stable

List available design system voice presets.

```bash
cd-agency presets
```

## Built-in Presets

| Preset | File | Source |
| --- | --- | --- |
| Apple HIG | `presets/apple-hig.yaml` | Apple Human Interface Guidelines |
| Atlassian Design | `presets/atlassian-design.yaml` | Atlassian Design System |
| Material Design | `presets/material-design.yaml` | Google Material Design 3 |
| Shopify Polaris | `presets/shopify-polaris.yaml` | Shopify Polaris |

## Usage with Voice Scoring

```bash
cd-agency score voice -i "Click here to see details" \
  --guide presets/material-design.yaml

# Rule-based (no API key needed)
cd-agency score voice -i "Click here to see details" \
  --guide presets/material-design.yaml --no-llm
```

## Preset File Format

Presets are YAML files with this structure:

```yaml
name: Material Design
tone_descriptors:
  - clear
  - concise
  - useful
  - friendly but not overly casual

do:
  - Use simple, direct language
  - Address the user as "you"
  - Use present tense
  - Use active voice

dont:
  - Use "please" excessively
  - Use ALL CAPS except for acronyms
  - Use technical jargon in user-facing copy

sample_content:
  - "Saved to your library"
  - "2 items selected"
  - "Can't load messages. Check your connection and try again."

character_limits:
  button: 25
  tooltip: 60
  snackbar: 80

terminology:
  sign_in: "Sign in"
  sign_out: "Sign out"
  select: "Select"
```

## Creating Custom Presets

Create a YAML file in `presets/` following the format above, then reference it:

```bash
cd-agency score voice -i "Your text" --guide presets/your-preset.yaml
```
