"""LangGraph-based agent runtime with tool calling and self-evaluation.

This module provides a graph-based agent execution flow that:
1. Retrieves relevant context from project memory
2. Generates content using the agent's system prompt + tools
3. Evaluates the output using linter, readability, and a11y tools
4. Re-generates if quality scores are below thresholds
5. Stores approved output in memory

Requires: pip install 'cd-agency[langgraph]'

Falls back gracefully — if langgraph/langchain-core are not installed,
the existing AgentRunner direct-call path is used instead.
"""

from __future__ import annotations

import json
import time
from typing import Any

from runtime.agent import Agent, AgentOutput
from runtime.model_providers import ModelRouter
from runtime.tools.base import Tool, ToolResult

# Quality thresholds for the evaluation loop
DEFAULT_READABILITY_THRESHOLD = 60.0  # Flesch Reading Ease
DEFAULT_MAX_CRITICAL_LINT_ISSUES = 0
DEFAULT_MAX_ITERATIONS = 3


# ---------------------------------------------------------------------------
# Agent state (works as plain dict — no TypedDict dependency required)
# ---------------------------------------------------------------------------

def _initial_state(
    agent_name: str,
    user_message: str,
    system_message: str,
    tools_available: list[str],
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
) -> dict[str, Any]:
    """Create the initial agent state dict."""
    return {
        "messages": [{"role": "user", "content": user_message}],
        "system_message": system_message,
        "agent_name": agent_name,
        "tools_available": tools_available,
        "current_output": "",
        "evaluation_scores": {},
        "iteration_count": 0,
        "max_iterations": max_iterations,
        "final_output": "",
        "memory_context": "",
        "total_input_tokens": 0,
        "total_output_tokens": 0,
    }


# ---------------------------------------------------------------------------
# ContentDesignGraph — builds and runs the LangGraph StateGraph
# ---------------------------------------------------------------------------

class ContentDesignGraph:
    """Agentic content design pipeline using LangGraph.

    Nodes:
        retrieve_context → generate → evaluate → decide → (generate | finalize)
    """

    def __init__(
        self,
        agent: Agent,
        tools: list[Tool],
        model_router: ModelRouter,
        memory: Any,
        *,
        model: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        max_retries: int = 3,
        readability_threshold: float = DEFAULT_READABILITY_THRESHOLD,
        max_critical_lint: int = DEFAULT_MAX_CRITICAL_LINT_ISSUES,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
    ) -> None:
        self.agent = agent
        self.tools = {t.name: t for t in tools}
        self.model_router = model_router
        self.memory = memory
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.max_retries = max_retries
        self.readability_threshold = readability_threshold
        self.max_critical_lint = max_critical_lint
        self.max_iterations = max_iterations

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def _build_graph(self) -> Any:
        """Build the LangGraph StateGraph."""
        from langgraph.graph import StateGraph, END

        graph = StateGraph(dict)

        graph.add_node("retrieve_context", self._node_retrieve_context)
        graph.add_node("generate", self._node_generate)
        graph.add_node("evaluate", self._node_evaluate)
        graph.add_node("decide", self._node_decide)
        graph.add_node("finalize", self._node_finalize)

        graph.set_entry_point("retrieve_context")
        graph.add_edge("retrieve_context", "generate")
        graph.add_edge("generate", "evaluate")
        graph.add_edge("evaluate", "decide")
        graph.add_conditional_edges(
            "decide",
            self._should_regenerate,
            {"regenerate": "generate", "finalize": "finalize"},
        )
        graph.add_edge("finalize", END)

        return graph.compile()

    # ------------------------------------------------------------------
    # Nodes
    # ------------------------------------------------------------------

    def _node_retrieve_context(self, state: dict) -> dict:
        """Retrieve relevant context from project memory."""
        user_msg = state["messages"][0]["content"] if state["messages"] else ""

        context = ""
        if self.memory is not None:
            context = self.memory.get_context_for_agent(
                agent_name=state["agent_name"],
                query=user_msg,
            )

        return {"memory_context": context}

    def _node_generate(self, state: dict) -> dict:
        """Call the LLM with the agent system prompt, tools, and context."""
        system = state["system_message"]

        # Inject memory context
        if state.get("memory_context"):
            system = f"{system}\n\n---\n\n{state['memory_context']}"

        # On re-generation, inject evaluation feedback
        if state["iteration_count"] > 0 and state.get("evaluation_scores"):
            feedback = self._build_feedback(state["evaluation_scores"])
            state["messages"].append({
                "role": "user",
                "content": feedback,
            })

        state["iteration_count"] = state["iteration_count"] + 1

        # Resolve provider
        provider, bare_model = self.model_router.resolve(self.model)

        # Build tool schemas
        tool_schemas = [t.to_llm_tool_schema() for t in self.tools.values()]

        # Call LLM with tool use loop
        messages = list(state["messages"])
        content, tool_calls_made, input_tokens, output_tokens = self._llm_tool_loop(
            provider, bare_model, system, messages, tool_schemas,
        )

        state["total_input_tokens"] += input_tokens
        state["total_output_tokens"] += output_tokens

        # Append assistant response to conversation
        state["messages"].append({"role": "assistant", "content": content})

        return {"current_output": content, "messages": state["messages"]}

    def _node_evaluate(self, state: dict) -> dict:
        """Evaluate the current output using content tools."""
        output = state.get("current_output", "")
        scores: dict[str, Any] = {}

        # Run readability scoring
        if "score_readability" in self.tools:
            result = self.tools["score_readability"].execute(text=output)
            if result.success:
                scores["readability"] = result.data

        # Run linter
        if "run_linter" in self.tools:
            result = self.tools["run_linter"].execute(text=output, content_type="error")
            if result.success:
                scores["linter"] = result.data

        # Run accessibility check
        if "check_accessibility" in self.tools:
            result = self.tools["check_accessibility"].execute(text=output)
            if result.success:
                scores["accessibility"] = result.data

        # Run voice consistency check (rule-based, no LLM)
        if "check_voice_consistency" in self.tools:
            result = self.tools["check_voice_consistency"].execute(text=output)
            if result.success:
                scores["voice"] = result.data

        # Calculate composite score using agent-specific weights
        composite = self._calculate_composite_score(scores)
        scores["_composite"] = composite

        return {"evaluation_scores": scores}

    def _calculate_composite_score(self, scores: dict[str, Any]) -> float:
        """Calculate a weighted composite quality score (0–100)."""
        from runtime.evaluation_profiles import get_weights

        weights = get_weights(self.agent.slug)

        # Normalize raw scores to 0–100 scale
        normalized: dict[str, float] = {}

        readability = scores.get("readability", {})
        if readability:
            # Flesch Reading Ease is already 0–100 (roughly)
            normalized["readability"] = max(0, min(100, readability.get("flesch_reading_ease", 0)))

        linter = scores.get("linter", {})
        if "issues" in linter:
            # Fewer issues = higher score. 0 issues = 100, 10+ = 0
            issue_count = linter.get("issues_found", len(linter.get("issues", [])))
            normalized["linter"] = max(0, 100 - issue_count * 10)

        a11y = scores.get("accessibility", {})
        if "issues" in a11y:
            issue_count = len(a11y.get("issues", []))
            normalized["accessibility"] = max(0, 100 - issue_count * 15)

        voice = scores.get("voice", {})
        if voice:
            # Voice score is 1–10, scale to 0–100
            raw_score = voice.get("score", 5)
            normalized["voice"] = max(0, min(100, raw_score * 10))

        # Weighted average
        total_weight = 0.0
        composite = 0.0
        for metric, weight in weights.items():
            if metric in normalized:
                composite += normalized[metric] * weight
                total_weight += weight

        return round(composite / total_weight, 2) if total_weight > 0 else 0.0

    def _node_decide(self, state: dict) -> dict:
        """Decision node — routing happens via _should_regenerate."""
        return state

    def _node_finalize(self, state: dict) -> dict:
        """Store output in memory and return final result."""
        output = state.get("current_output", "")

        # Store in memory if available
        if self.memory is not None and output:
            try:
                self.memory.remember(
                    key=f"agent-output:{self.agent.slug}:{int(time.time())}",
                    value=output[:500],
                    category="pattern",
                    source_agent=self.agent.name,
                )
            except Exception:
                pass

        return {"final_output": output}

    # ------------------------------------------------------------------
    # Conditional edge
    # ------------------------------------------------------------------

    def _should_regenerate(self, state: dict) -> str:
        """Determine whether to regenerate or finalize."""
        if state["iteration_count"] >= state["max_iterations"]:
            self._record_evaluation(state)
            return "finalize"

        scores = state.get("evaluation_scores", {})

        # Check readability
        readability = scores.get("readability", {})
        ease = readability.get("flesch_reading_ease", 100)
        if ease < self.readability_threshold:
            return "regenerate"

        # Check linter — any error-severity issues trigger regeneration
        linter = scores.get("linter", {})
        issues = linter.get("issues", [])
        critical = [i for i in issues if i.get("severity") == "error"]
        if len(critical) > self.max_critical_lint:
            return "regenerate"

        # Check composite score against agent-specific threshold
        composite = scores.get("_composite", 100)
        from runtime.quality_config import QualityConfig
        config = QualityConfig()
        threshold = config.get_threshold(self.agent.slug, "composite_score")
        if composite < threshold:
            return "regenerate"

        self._record_evaluation(state)
        return "finalize"

    def _record_evaluation(self, state: dict) -> None:
        """Record the evaluation result in history (best-effort)."""
        try:
            from runtime.evaluation_history import EvaluationHistory

            scores = state.get("evaluation_scores", {})
            composite = scores.get("_composite", 0)
            from runtime.quality_config import QualityConfig
            config = QualityConfig()
            threshold = config.get_threshold(self.agent.slug, "composite_score")

            history = EvaluationHistory()
            history.record(
                agent_slug=self.agent.slug,
                scores={k: v for k, v in scores.items() if not k.startswith("_")},
                composite_score=composite,
                passed=composite >= threshold,
                iteration_count=state.get("iteration_count", 1),
            )
        except Exception:
            pass  # History should never break agent execution

    # ------------------------------------------------------------------
    # LLM tool-use loop
    # ------------------------------------------------------------------

    def _llm_tool_loop(
        self,
        provider: Any,
        model: str,
        system: str,
        messages: list[dict[str, str]],
        tool_schemas: list[dict],
        max_tool_rounds: int = 5,
    ) -> tuple[str, int, int, int]:
        """Call the LLM, handle tool calls, and return final content.

        Returns: (content, tool_calls_made, total_input_tokens, total_output_tokens)
        """
        total_input_tokens = 0
        total_output_tokens = 0
        tool_calls_made = 0

        for _ in range(max_tool_rounds):
            response = provider.complete(
                model=model,
                system=system,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                max_retries=self.max_retries,
            )

            total_input_tokens += response.input_tokens
            total_output_tokens += response.output_tokens

            raw = response.raw_response

            # Check for tool use in the response (Anthropic format)
            tool_use_blocks = []
            text_content = ""
            if raw and hasattr(raw, "content"):
                for block in raw.content:
                    if hasattr(block, "type"):
                        if block.type == "tool_use":
                            tool_use_blocks.append(block)
                        elif block.type == "text":
                            text_content += block.text

            if not tool_use_blocks:
                # No tool calls — return the text content
                return response.content or text_content, tool_calls_made, total_input_tokens, total_output_tokens

            # Execute tool calls
            # Build assistant message with tool use
            assistant_content = []
            for block in raw.content:
                if block.type == "text":
                    assistant_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })

            messages.append({"role": "assistant", "content": assistant_content})

            # Execute each tool and build tool result messages
            tool_results = []
            for block in tool_use_blocks:
                tool = self.tools.get(block.name)
                if tool:
                    result = tool.execute(**block.input)
                    tool_calls_made += 1
                else:
                    result = ToolResult(success=False, error=f"Unknown tool: {block.name}")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result.to_content_string(),
                })

            messages.append({"role": "user", "content": tool_results})

        # If we exhausted tool rounds, return whatever we have
        return text_content or response.content, tool_calls_made, total_input_tokens, total_output_tokens

    # ------------------------------------------------------------------
    # Feedback builder
    # ------------------------------------------------------------------

    def _build_feedback(self, scores: dict[str, Any]) -> str:
        """Build a feedback message from evaluation scores."""
        parts = [
            "Your previous output was evaluated and needs improvement. "
            "Please rewrite addressing these issues:\n"
        ]

        readability = scores.get("readability", {})
        if readability:
            ease = readability.get("flesch_reading_ease", 0)
            grade = readability.get("flesch_kincaid_grade", 0)
            if ease < self.readability_threshold:
                parts.append(
                    f"- Readability: Flesch ease is {ease} (target: >= {self.readability_threshold}), "
                    f"grade level is {grade}. Simplify sentences and use shorter words."
                )

        linter = scores.get("linter", {})
        issues = linter.get("issues", [])
        if issues:
            parts.append(f"- Linter found {len(issues)} issue(s):")
            for issue in issues[:5]:
                msg = issue.get("message", "")
                sug = issue.get("suggestion", "")
                parts.append(f"  - {msg}" + (f" → {sug}" if sug else ""))

        a11y = scores.get("accessibility", {})
        a11y_issues = a11y.get("issues", [])
        if a11y_issues:
            parts.append(f"- Accessibility: {len(a11y_issues)} issue(s):")
            for issue in a11y_issues[:3]:
                parts.append(f"  - [{issue.get('wcag_criterion', '')}] {issue.get('message', '')}")

        voice = scores.get("voice", {})
        if voice and voice.get("score", 10) < 7:
            parts.append(f"- Voice consistency: score {voice.get('score', 0)}/10.")
            deviations = voice.get("deviations", [])
            for dev in deviations[:3]:
                if isinstance(dev, dict):
                    parts.append(f"  - {dev.get('reason', '')}")

        composite = scores.get("_composite")
        if composite is not None:
            parts.append(f"\nComposite quality score: {composite:.0f}/100")

        parts.append("\nRewrite the content to fix these issues while maintaining the same meaning.")
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        user_input: dict[str, Any],
        system_message: str,
    ) -> AgentOutput:
        """Execute the LangGraph pipeline and return an AgentOutput.

        Args:
            user_input: Dict of input fields.
            system_message: Pre-built system message (with context injections).

        Returns:
            AgentOutput compatible with the existing runner interface.
        """
        user_message = self.agent.build_user_message(user_input)

        state = _initial_state(
            agent_name=self.agent.name,
            user_message=user_message,
            system_message=system_message,
            tools_available=list(self.tools.keys()),
            max_iterations=self.max_iterations,
        )

        start = time.monotonic()
        graph = self._build_graph()
        final_state = graph.invoke(state)
        elapsed_ms = (time.monotonic() - start) * 1000

        return AgentOutput(
            content=final_state.get("final_output", ""),
            agent_name=self.agent.name,
            model=self.model,
            input_tokens=final_state.get("total_input_tokens", 0),
            output_tokens=final_state.get("total_output_tokens", 0),
            latency_ms=elapsed_ms,
            raw_response=final_state.get("evaluation_scores"),
        )


# ---------------------------------------------------------------------------
# Availability check
# ---------------------------------------------------------------------------

def langgraph_available() -> bool:
    """Return True if langgraph and langchain-core are importable."""
    try:
        import langgraph  # noqa: F401
        return True
    except ImportError:
        return False
