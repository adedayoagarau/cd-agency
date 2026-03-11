# `interactive` Command

> Stability: Stable

Guided interactive session — pick an agent, provide input, and see results.

```bash
cd-agency interactive
```

## How It Works

1. **Choose a task category:**

```
What are you working on?
   1. Writing or reviewing microcopy (buttons, labels, tooltips)
   2. Creating or improving CTAs
   3. Writing error messages
   4. Designing onboarding flows
   5. Checking accessibility
   6. Adjusting tone and voice
   7. Writing for mobile
   8. Designing empty states
   9. Writing notifications
  10. General content design help
```

2. **Provide inputs** for the selected agent (required and optional fields).

3. **View the agent's output** with token usage and latency.

4. **Optional: Score the output** — run readability, lint, and a11y checks
   on the agent's response.

5. **Optional: Hand off** to a related agent for further refinement.

## Requirements

- `ANTHROPIC_API_KEY` must be set (agents require API access).
- Terminal must support interactive input (not suitable for pipes or CI).
