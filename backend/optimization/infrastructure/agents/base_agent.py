"""BaseAgent ABC implementing the Template Method pattern.

All optimization and interview agents inherit from this class.
The ``run()`` method defines the skeleton algorithm:
    1. ``prepare(state)``      — build the LLM prompt from current state
    2. ``execute(prompt)``     — call the LLM (or vector store)
    3. ``parse_output(raw)``   — validate and structure the raw output

Cross-cutting concerns handled here:
    - Structured logging at each phase (prepare / execute / parse)
    - Token-usage tracking from LLM response metadata
    - Error wrapping with agent-specific context
    - LLM provider selection via the Strategy pattern
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

from langchain_openai import ChatOpenAI
from pydantic.types import SecretStr

from config import get_settings
from shared.domain.exceptions import AgentExecutionError


class BaseAgent(ABC):
    """Abstract base agent with Template Method lifecycle.

    Subclasses override ``prepare``, ``execute``, and ``parse_output``
    to define agent-specific behaviour while inheriting the common
    workflow skeleton, logging, and error handling.
    """

    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)

    # ----------------------------------------------------------
    # Template method
    # ----------------------------------------------------------

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """Orchestrate prepare → execute → parse_output.

        Args:
            state: Current LangGraph state (``OptimizationState``
                or ``InterviewState``).

        Returns:
            Partial state update dictionary.

        Raises:
            AgentExecutionError: If any phase fails.
        """
        agent_name = self.__class__.__name__
        self._logger.info("Agent %s starting — prepare phase", agent_name)

        try:
            # Phase 1: Prepare
            prompt = self.prepare(state)
            self._logger.debug(
                "Agent %s prompt built (%d chars)",
                agent_name,
                len(prompt),
            )

            # Phase 2: Execute
            self._logger.info("Agent %s — execute phase", agent_name)
            raw_output = self.execute(prompt)
            self._logger.debug(
                "Agent %s raw output (%d chars)",
                agent_name,
                len(raw_output),
            )

            # Phase 3: Parse
            self._logger.info("Agent %s — parse phase", agent_name)
            result = self.parse_output(raw_output)
            self._logger.info("Agent %s completed successfully", agent_name)

            return result

        except AgentExecutionError:
            # Already wrapped — re-raise without double-wrapping
            raise
        except Exception as exc:
            self._logger.error("Agent %s failed: %s", agent_name, str(exc))
            raise AgentExecutionError(
                agent_name=agent_name,
                message=str(exc),
            ) from exc

    # ----------------------------------------------------------
    # Abstract methods (subclasses MUST implement)
    # ----------------------------------------------------------

    @abstractmethod
    def prepare(self, state: dict[str, Any]) -> str:
        """Build the prompt (or query) from current state.

        Args:
            state: Current pipeline state.

        Returns:
            Prompt string for LLM or query for vector store.
        """
        ...

    @abstractmethod
    def execute(self, prompt: str) -> str:
        """Execute the LLM call or vector search.

        Args:
            prompt: Prepared prompt or query string.

        Returns:
            Raw output string from the provider.
        """
        ...

    @abstractmethod
    def parse_output(self, raw_output: str) -> dict[str, Any]:
        """Parse and validate raw output into a partial state update.

        Args:
            raw_output: Raw string returned by ``execute``.

        Returns:
            Dictionary of state fields to update.
        """
        ...

    # ----------------------------------------------------------
    # LLM provider selection (Strategy pattern)
    # ----------------------------------------------------------

    def _get_model(
        self,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.0,
    ) -> ChatOpenAI:
        """Create an LLM chat-model instance.

        The provider is selected based on ``Settings.llm_provider``:
        ``"openai"`` (default) or ``"deepseek"``.

        Args:
            model_name: Model identifier
                (e.g. ``"gpt-4o"``, ``"gpt-4o-mini"``).
            temperature: Sampling temperature
                (``0.0`` = deterministic).

        Returns:
            Configured ``ChatOpenAI`` instance.
        """
        settings = get_settings()

        if settings.llm_provider == "deepseek":
            return ChatOpenAI(
                model="deepseek-chat",
                temperature=temperature,
                api_key=SecretStr(settings.deepseek_api_key),
                base_url="https://api.deepseek.com",
                max_retries=2,
                timeout=30.0,
            )

        # Default: OpenAI
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=SecretStr(settings.openai_api_key),
            max_retries=2,
            timeout=30.0,
        )

    # ----------------------------------------------------------
    # Token tracking
    # ----------------------------------------------------------

    def _track_tokens(
        self,
        response_metadata: dict[str, Any],
        agent_name: str,
    ) -> int:
        """Extract token count from LLM response metadata.

        Args:
            response_metadata: Metadata dict from a LangChain
                ``AIMessage``.
            agent_name: Agent name for structured logging.

        Returns:
            Total tokens consumed by this call.
        """
        token_usage: dict[str, int] = response_metadata.get("token_usage", {})
        total: int = token_usage.get("total_tokens", 0)
        self._logger.info(
            "Agent %s token usage: prompt=%d, completion=%d, total=%d",
            agent_name,
            token_usage.get("prompt_tokens", 0),
            token_usage.get("completion_tokens", 0),
            total,
        )
        return total
