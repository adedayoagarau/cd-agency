# Creating Custom Agents

> Stability: Stable

## Method 1: Interactive Wizard

```bash
cd-agency agent create
```

The wizard walks you through defining name, description, inputs, outputs, tags,
and the system prompt.

## Method 2: Manual File Creation

Create a `.md` file in the `content-design/` directory (or your configured
`agents_dir`):

```bash
touch content-design/my-custom-agent.md
```

Use the [Agent Format Specification](agent-format.md) to structure the file.

## Method 3: Import

```bash
cd-agency agent import path/to/agent.md
```

## Method 4: Programmatic

```python
from runtime.agent import Agent, AgentInput, OutputField
from runtime.registry import AgentRegistry
from pathlib import Path

# Create agent object
agent = Agent(
    name="My Custom Agent",
    description="Does something specific",
    tags=["custom"],
    inputs=[
        AgentInput(name="content", type="string", required=True,
                   description="Content to process"),
    ],
    outputs=[
        OutputField(name="result", type="string",
                    description="Processed content"),
    ],
    system_prompt="You are a content specialist that...",
    critical_rules="1. Always use active voice\n2. Keep it under 50 words",
)

# Register it
registry = AgentRegistry.from_directory(Path("content-design"))
registry.register(agent)

# Now it's available via registry.get("my-custom-agent")
```

## Tips for Good Agents

1. **Be specific.** Narrow agents outperform generalist ones.
2. **Include few-shot examples.** At least 2–3 input/output pairs.
3. **Define critical rules.** Hard constraints prevent off-brand output.
4. **Tag thoroughly.** Tags enable filtering and discovery.
5. **Set related agents.** This enables handoff in interactive mode.
6. **Test with scoring.** Run agent output through `score all` to verify quality.

## Testing Your Agent

```bash
# Check it loads
cd-agency agent list | grep my-custom

# View details
cd-agency agent info my-custom-agent

# Run it
cd-agency agent run my-custom-agent -i "test input"

# Score the output
cd-agency agent run my-custom-agent -i "test" | cd-agency score all
```
