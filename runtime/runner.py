"""Agent runner — executes agents via configurable LLM providers."""

from __future__ import annotations

import time
from typing import Any

from runtime.agent import Agent, AgentOutput
from runtime.config import Config
from runtime.providers import create_completion, create_completion_streaming


class AgentRunner:
    """Executes content design agents via any supported LLM provider."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config.from_env()

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
            ValueError: If required inputs are missing.
        """
        # Validate input
        errors = agent.validate_input(user_input)
        if errors:
            raise ValueError(f"Input validation failed: {'; '.join(errors)}")

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

        # Inject project memory if available
        from runtime.memory import ProjectMemory
        memory = ProjectMemory.load()
        memory_context = memory.get_context_for_agent(agent.name)
        if memory_context:
            system_message = f"{system_message}\n\n---\n\n{memory_context}"

        # Run preflight analysis and inject assumptions for missing context
        from runtime.preflight import run_preflight, build_assumption_block
        preflight = run_preflight(agent, user_input)
        assumption_block = build_assumption_block(preflight)
        if assumption_block:
            system_message = f"{system_message}\n\n---\n\n{assumption_block}"

        user_message = agent.build_user_message(user_input)

        # Resolve parameters
        resolved_model = model or self.config.model
        resolved_max_tokens = max_tokens or self.config.max_tokens
        resolved_temperature = temperature if temperature is not None else self.config.temperature

        if stream:
            output = self._run_streaming(
                agent, system_message, user_message,
                resolved_model, resolved_max_tokens, resolved_temperature,
            )
        else:
            output = self._run_sync(
                agent, system_message, user_message,
                resolved_model, resolved_max_tokens, resolved_temperature,
            )

        # Record content version for history tracking
        try:
            from runtime.versioning import ContentHistory
            history = ContentHistory.load()
            # Extract primary input text for the "before"
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

        return output

    def _run_sync(
        self,
        agent: Agent,
        system_message: str,
        user_message: str,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> AgentOutput:
        """Execute a synchronous (non-streaming) API call with retry."""
        last_error: Exception | None = None

        for attempt in range(self.config.max_retries):
            try:
                start = time.monotonic()
                result = create_completion(
                    provider_name=self.config.provider,
                    api_key=self.config.api_key,
                    model=model,
                    system=system_message,
                    messages=[{"role": "user", "content": user_message}],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    base_url=self.config.base_url or None,
                )
                elapsed_ms = (time.monotonic() - start) * 1000

                return AgentOutput(
                    content=result.content,
                    agent_name=agent.name,
                    model=model,
                    input_tokens=result.input_tokens,
                    output_tokens=result.output_tokens,
                    latency_ms=elapsed_ms,
                )
            except Exception as e:
                last_error = e
                # Don't retry on client errors (4xx) except rate limits (429)
                status_code = getattr(e, "status_code", None)
                if status_code and status_code != 429 and 400 <= status_code < 500:
                    raise
                # Exponential backoff for retryable errors
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)

        raise last_error  # type: ignore[misc]

    def _run_streaming(
        self,
        agent: Agent,
        system_message: str,
        user_message: str,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> AgentOutput:
        """Execute a streaming API call, collecting the full response."""
        start = time.monotonic()

        result = create_completion_streaming(
            provider_name=self.config.provider,
            api_key=self.config.api_key,
            model=model,
            system=system_message,
            messages=[{"role": "user", "content": user_message}],
            max_tokens=max_tokens,
            temperature=temperature,
            base_url=self.config.base_url or None,
        )

        elapsed_ms = (time.monotonic() - start) * 1000

        return AgentOutput(
            content=result.content,
            agent_name=agent.name,
            model=model,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            latency_ms=elapsed_ms,
        )

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

        from runtime.memory import ProjectMemory
        memory = ProjectMemory.load()
        memory_context = memory.get_context_for_agent(agent.name)
        if memory_context:
            system_message = f"{system_message}\n\n---\n\n{memory_context}"

        # Resolve parameters
        resolved_model = model or self.config.model
        resolved_max_tokens = max_tokens or self.config.max_tokens
        resolved_temperature = temperature if temperature is not None else self.config.temperature

        # Make multi-turn API call
        last_error: Exception | None = None
        for attempt in range(self.config.max_retries):
            try:
                start = time.monotonic()
                result = create_completion(
                    provider_name=self.config.provider,
                    api_key=self.config.api_key,
                    model=resolved_model,
                    system=system_message,
                    messages=messages,
                    max_tokens=resolved_max_tokens,
                    temperature=resolved_temperature,
                    base_url=self.config.base_url or None,
                )
                elapsed_ms = (time.monotonic() - start) * 1000

                output = AgentOutput(
                    content=result.content,
                    agent_name=agent.name,
                    model=resolved_model,
                    input_tokens=result.input_tokens,
                    output_tokens=result.output_tokens,
                    latency_ms=elapsed_ms,
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
            except Exception as e:
                last_error = e
                status_code = getattr(e, "status_code", None)
                if status_code and status_code != 429 and 400 <= status_code < 500:
                    raise
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)

        raise last_error  # type: ignore[misc]


def run_agent(
    agent: Agent,
    user_input: dict[str, Any],
    config: Config | None = None,
    **kwargs: Any,
) -> AgentOutput:
    """Convenience function to run an agent without creating a runner."""
    runner = AgentRunner(config)
    return runner.run(agent, user_input, **kwargs)
