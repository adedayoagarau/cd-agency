# Voice Presets

> Stability: Stable

CD Agency ships with 4 design system voice presets for brand voice checking.

## Available Presets

### Material Design

Based on [Material Design 3](https://m3.material.io/foundations/content-design/overview) writing guidelines.

- **Tone:** Clear, concise, useful, friendly but not overly casual
- **Key rules:** Use "Sign in" (not "Log in"), use "Select" (not "Click"),
  no excessive "please", sentence case for UI elements
- **File:** `presets/material-design.yaml`

### Shopify Polaris

Based on the Shopify Polaris content guidelines.

- **File:** `presets/shopify-polaris.yaml`

### Atlassian Design

Based on the Atlassian Design System writing guidelines.

- **File:** `presets/atlassian-design.yaml`

### Apple HIG

Based on Apple Human Interface Guidelines.

- **File:** `presets/apple-hig.yaml`

## Usage

### CLI — With LLM (more accurate)

```bash
cd-agency score voice \
  -i "Click OK to continue" \
  --guide presets/material-design.yaml
```

### CLI — Without LLM (free, fast)

```bash
cd-agency score voice \
  -i "Click OK to continue" \
  --guide presets/material-design.yaml \
  --no-llm
```

### Python API

```python
from tools.voice_checker import VoiceChecker, VoiceProfile

profile = VoiceProfile.from_yaml("presets/material-design.yaml")
checker = VoiceChecker()

# LLM-based (requires API key)
result = checker.check("Click OK to continue", profile)

# Rule-based (no API key)
result = checker.check_without_llm("Click OK to continue", profile)

print(f"Score: {result.score}/10 ({result.label})")
```

## Preset File Format

```yaml
name: Design System Name

tone_descriptors:
  - descriptor1
  - descriptor2

do:
  - "Rule to follow"
  - "Another rule"

dont:
  - "Thing to avoid"
  - "Another thing"

sample_content:
  - "Example text that matches this voice"
  - "Another example"

character_limits:          # Optional
  button: 25
  tooltip: 60

terminology:               # Optional
  sign_in: "Sign in"
  sign_out: "Sign out"
```

## Creating Custom Presets

1. Create a YAML file following the format above.
2. Place it in `presets/` or any directory.
3. Reference it with `--guide path/to/preset.yaml`.

Only `name`, `tone_descriptors`, `do`, and `dont` are used by the voice
checker. `character_limits`, `terminology`, and `sample_content` provide
additional context for LLM-based checking.
