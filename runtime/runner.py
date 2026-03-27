"""Agent runner — executes agents via pluggable LLM providers."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from runtime.agent import Agent, AgentOutput
from runtime.config import Config
from runtime.model_providers import ModelRouter, ProviderResponse


class AgentRunner:
    """Executes content design agents via any supported LLM provider.

    Uses ModelRouter to dispatch to Anthropic, OpenAI, or OpenRouter
    based on the model string. Backward compatible — defaults to Anthropic.
    """

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config.from_env()
        self._router: ModelRouter | None = None

    @property
    def router(self) -> ModelRouter:
        """Lazy-initialize the model router."""
        if self._router is None:
            self._router = ModelRouter.from_config(self.config)
        return self._router

    def run(
        self,
        agent: Agent,
        user_input: dict[str, Any],
        *,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        stream: bool = False,
    ) -> AgentOutput:
        """Execute an agent with the given input.

        Model resolution order:
        1. Explicit `model` parameter
        2. Agent's `preferred_model` from YAML frontmatter
        3. Config default (from env/config file)

        Args:
            agent: The agent to execute.
            user_input: Dict of input fields matching the agent's input schema.
            model: Override the default model.
            max_tokens: Override the default max tokens.
            temperature: Override the default temperature.
            stream: If True, return a streaming response.

        Returns:
            AgentOutput with the agent's response and metadata.

        Raises:
            ValueError: If required inputs are missing or no provider available.
        """
        # Validate input
        errors = agent.validate_input(user_input)
        if errors:
            raise ValueError(f"Input validation failed: {'; '.join(errors)}")

        # Check if this agent should use LangGraph mode
        if agent.available_tools and not stream:
            output = self._try_langgraph_run(agent, user_input, model=model,
                                              max_tokens=max_tokens, temperature=temperature)
            if output is not None:
                return output

        # Build messages
        system_message = agent.build_system_message()

        # Inject product context if configured
        if self.config.product_context.is_configured():
            context_block = self.config.product_context.build_context_block()
            system_message = f"{system_message}\n\n---\n\n{context_block}"

        # Inject design system constraints if configured
        from runtime.design_system import load_design_system_from_config
        design_system = load_design_system_from_config()
        if design_system:
            ds_block = design_system.build_context_block()
            system_message = f"{system_message}\n\n---\n\n{ds_block}"

        # Inject brand DNA if available
        from runtime.brand_dna import load_brand_dna
        brand_dna = load_brand_dna()
        if not brand_dna.is_empty():
            brand_block = brand_dna.build_context_block()
            system_message = f"{system_message}\n\n---\n\n{brand_block}"

        # Inject memory context (session > project > workspace)
        from runtime.memory_hierarchy import MemoryHierarchy
        memory_hierarchy = MemoryHierarchy(project_dir=Path("."))
        primary_input = ""
        if agent.inputs:
            primary_input = str(user_input.get(agent.inputs[0].name, ""))
        memory_context = memory_hierarchy.get_context_for_agent(
            agent.name, query=primary_input
        )
        if memory_context:
            system_message = f"{system_message}\n\n---\n\n{memory_context}"

        # Run preflight analysis and inject assumptions for missing context
        from runtime.preflight import run_preflight, build_assumption_block
        preflight = run_preflight(agent, user_input)
        assumption_block = build_assumption_block(preflight)
        if assumption_block:
            system_message = f"{system_message}\n\n---\n\n{assumption_block}"

        user_message = agent.build_user_message(user_input)

        # Resolve parameters — model priority: explicit > agent preferred > config
        resolved_model = model or agent.preferred_model or self.config.model
        resolved_max_tokens = max_tokens or self.config.max_tokens
        resolved_temperature = temperature if temperature is not None else self.config.temperature

        messages = [{"role": "user", "content": user_message}]

        start = time.monotonic()
        provider, bare_model = self.router.resolve(resolved_model)

        if stream:
            response = provider.stream(
                model=bare_model,
                system=system_message,
                messages=messages,
                max_tokens=resolved_max_tokens,
                temperature=resolved_temperature,
            )
        else:
            response = provider.complete(
                model=bare_model,
                system=system_message,
                messages=messages,
                max_tokens=resolved_max_tokens,
                temperature=resolved_temperature,
                max_retries=self.config.max_retries,
            )

        elapsed_ms = (time.monotonic() - start) * 1000

        # Run post-hoc evaluation on the output content
        evaluation: dict[str, float] = {}
        composite_score = 0.0
        try:
            from runtime.langgraph_agent import run_posthoc_evaluation
            evaluation, composite_score = run_posthoc_evaluation(response.content)
        except Exception:
            pass

        # Determine pass/fail
        passed = True
        try:
            from runtime.quality_config import QualityConfig
            qc = QualityConfig()
            threshold = qc.get_threshold(agent.slug, "composite_score")
            passed = composite_score >= threshold
        except Exception:
            pass

        output = AgentOutput(
            content=response.content,
            agent_name=agent.name,
            model=resolved_model,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            latency_ms=elapsed_ms,
            raw_response=response.raw_response,
            evaluation=evaluation,
            composite_score=composite_score,
            passed=passed,
            iterations=1,
        )

        # Record content version for history tracking
        try:
            from runtime.versioning import ContentHistory
            history = ContentHistory.load()
            primary_input = ""
            if agent.inputs:
                primary_input = str(user_input.get(agent.inputs[0].name, ""))
            history.record(
                agent_name=agent.name,
                agent_slug=agent.slug,
                input_text=primary_input,
                output_text=output.content,
                input_fields={k: str(v) for k, v in user_input.items()},
                model=output.model,
                input_tokens=output.input_tokens,
                output_tokens=output.output_tokens,
                latency_ms=output.latency_ms,
            )
        except Exception:
            pass  # Versioning should never break agent execution

        # Record analytics
        try:
            from tools.analytics import Analytics
            analytics = Analytics.load()
            analytics.record_agent_run(
                agent_name=agent.name,
                input_tokens=output.input_tokens,
                output_tokens=output.output_tokens,
                latency_ms=output.latency_ms,
            )
        except Exception:
            pass  # Analytics should never break agent execution

        # Record evaluation history for the v2 history API
        try:
            from runtime.evaluation_history import EvaluationHistory
            eval_history = EvaluationHistory()
            eval_history.record(
                agent_slug=agent.slug,
                scores=evaluation,
                composite_score=composite_score,
                passed=passed,
                iteration_count=1,
            )
        except Exception:
            pass  # Evaluation history should never break agent execution

        # Persist to project memory for the v2 memory API
        try:
            from runtime.memory_hierarchy import MemoryHierarchy
            mem = MemoryHierarchy(project_dir=Path("."))
            primary_input_val = ""
            if agent.inputs:
                primary_input_val = str(user_input.get(agent.inputs[0].name, ""))
            mem.remember(
                key=f"agent-run:{agent.slug}:{int(time.time())}",
                value=f"Input: {primary_input_val[:200]}\nOutput: {output.content[:300]}",
                category="agent-run",
                source_agent=agent.name,
                visibility="project",
            )
        except Exception:
            pass  # Memory should never break agent execution

        return output

    def _try_langgraph_run(
        self,
        agent: Agent,
        user_input: dict[str, Any],
        *,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> AgentOutput | None:
        """Attempt to run the agent using the LangGraph pipeline.

        Returns None if langgraph is not installed, allowing fallback
        to the direct LLM call path.
        """
        try:
            from runtime.langgraph_agent import ContentDesignGraph, langgraph_available
        except ImportError:
            return None

        if not langgraph_available():
            return None

        from runtime.tools.registry import build_default_registry
        from runtime.memory import ProjectMemory

        tool_registry = build_default_registry()
        tools = tool_registry.get_tools_by_names(agent.available_tools)
        if not tools:
            return None

        memory = ProjectMemory.load()

        # Build system message with full context injection
        system_message = agent.build_system_message()

        if self.config.product_context.is_configured():
            context_block = self.config.product_context.build_context_block()
            system_message = f"{system_message}\n\n---\n\n{context_block}"

        from runtime.design_system import load_design_system_from_config
        design_system = load_design_system_from_config()
        if design_system:
            ds_block = design_system.build_context_block()
            system_message = f"{system_message}\n\n---\n\n{ds_block}"

        from runtime.brand_dna import load_brand_dna as _load_brand_dna
        brand_dna = _load_brand_dna()
        if not brand_dna.is_empty():
            brand_block = brand_dna.build_context_block()
            system_message = f"{system_message}\n\n---\n\n{brand_block}"

        from runtime.preflight import run_preflight, build_assumption_block
        preflight = run_preflight(agent, user_input)
        assumption_block = build_assumption_block(preflight)
        if assumption_block:
            system_message = f"{system_message}\n\n---\n\n{assumption_block}"

        resolved_model = model or agent.preferred_model or self.config.model
        resolved_max_tokens = max_tokens or self.config.max_tokens
        resolved_temperature = temperature if temperature is not None else self.config.temperature

        graph = ContentDesignGraph(
            agent=agent,
            tools=tools,
            model_router=self.router,
            memory=memory,
            model=resolved_model,
            max_tokens=resolved_max_tokens,
            temperature=resolved_temperature,
            max_retries=self.config.max_retries,
        )

        output = graph.run(user_input, system_message)

        # Record versioning and analytics
        try:
            from runtime.versioning import ContentHistory
            history = ContentHistory.load()
            primary_input = ""
            if agent.inputs:
                primary_input = str(user_input.get(agent.inputs[0].name, ""))
            history.record(
                agent_name=agent.name,
                agent_slug=agent.slug,
                input_text=primary_input,
                output_text=output.content,
                input_fields={k: str(v) for k, v in user_input.items()},
                model=output.model,
                input_tokens=output.input_tokens,
                output_tokens=output.output_tokens,
                latency_ms=output.latency_ms,
            )
        except Exception:
            pass

        try:
            from tools.analytics import Analytics
            analytics = Analytics.load()
            analytics.record_agent_run(
                agent_name=agent.name,
                input_tokens=output.input_tokens,
                output_tokens=output.output_tokens,
                latency_ms=output.latency_ms,
            )
        except Exception:
            pass

        # Persist to project memory for the v2 memory API
        try:
            from runtime.memory_hierarchy import MemoryHierarchy
            mem = MemoryHierarchy(project_dir=Path("."))
            primary_input_val = ""
            if agent.inputs:
                primary_input_val = str(user_input.get(agent.inputs[0].name, ""))
            mem.remember(
                key=f"agent-run:{agent.slug}:{int(time.time())}",
                value=f"Input: {primary_input_val[:200]}\nOutput: {output.content[:300]}",
                category="agent-run",
                source_agent=agent.name,
                visibility="project",
            )
        except Exception:
            pass  # Memory should never break agent execution

        return output

    def run_conversation(
        self,
        agent: Agent,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> AgentOutput:
        """Execute a multi-turn conversation with an agent.

        Args:
            agent: The agent to execute.
            messages: List of {"role": "user"|"assistant", "content": "..."} dicts.
            model: Override the default model.
            max_tokens: Override the default max tokens.
            temperature: Override the default temperature.

        Returns:
            AgentOutput with the agent's response and metadata.
        """
        # Build system message with full context injection
        system_message = agent.build_system_message()

        if self.config.product_context.is_configured():
            context_block = self.config.product_context.build_context_block()
            system_message = f"{system_message}\n\n---\n\n{context_block}"

        from runtime.design_system import load_design_system_from_config
        design_system = load_design_system_from_config()
        if design_system:
            ds_block = design_system.build_context_block()
            system_message = f"{system_message}\n\n---\n\n{ds_block}"

        from runtime.memory_hierarchy import MemoryHierarchy
        memory_hierarchy = MemoryHierarchy(project_dir=Path("."))
        conversation_query = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                conversation_query = str(msg.get("content", ""))
                break
        memory_context = memory_hierarchy.get_context_for_agent(
            agent.name, query=conversation_query
        )
        if memory_context:
            system_message = f"{system_message}\n\n---\n\n{memory_context}"

        # Resolve parameters
        resolved_model = model or agent.preferred_model or self.config.model
        resolved_max_tokens = max_tokens or self.config.max_tokens
        resolved_temperature = temperature if temperature is not None else self.config.temperature

        start = time.monotonic()
        provider, bare_model = self.router.resolve(resolved_model)

        response = provider.complete(
            model=bare_model,
            system=system_message,
            messages=messages,
            max_tokens=resolved_max_tokens,
            temperature=resolved_temperature,
            max_retries=self.config.max_retries,
        )

        elapsed_ms = (time.monotonic() - start) * 1000

        output = AgentOutput(
            content=response.content,
            agent_name=agent.name,
            model=resolved_model,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            latency_ms=elapsed_ms,
            raw_response=response.raw_response,
        )

        # Record analytics
        try:
            from tools.analytics import Analytics
            analytics = Analytics.load()
            analytics.record_agent_run(
                agent_name=agent.name,
                input_tokens=output.input_tokens,
                output_tokens=output.output_tokens,
                latency_ms=output.latency_ms,
            )
        except Exception:
            pass

        return output


def run_agent(
    agent: Agent,
    user_input: dict[str, Any],
    config: Config | None = None,
    **kwargs: Any,
) -> AgentOutput:
    """Convenience function to run an agent without creating a runner."""
    runner = AgentRunner(config)
    return runner.run(agent, user_input, **kwargs)
