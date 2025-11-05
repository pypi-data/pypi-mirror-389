"""
FreeplayAgent wrapper for LangGraph agents.

This module provides a wrapper around LangGraph agents using LangChain's official
RunnableBindingBase pattern to automatically inject Freeplay metadata into all
invocations via config_factories.
"""

import logging
from typing import Any, Callable, TypeVar

from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.runnables.base import RunnableBindingBase

logger = logging.getLogger(__name__)

# Type variables for generic typing
Input = TypeVar("Input")
Output = TypeVar("Output")


class FreeplayAgent(RunnableBindingBase[Input, Output]):
    """
    Wraps LangGraph agents using LangChain's official RunnableBindingBase pattern.

    This wrapper automatically injects Freeplay metadata into all invocation methods
    (invoke, ainvoke, stream, astream, batch, abatch, astream_events) via LangChain's
    config_factories mechanism. This follows LangChain's idiomatic approach for
    wrapping Runnables with configuration injection.

    All core invocation methods work directly without any special handling.
    For state management operations (get_state, update_state, etc.), use the
    unwrap() method to access CompiledStateGraph-specific methods.

    Args:
        agent: The underlying LangGraph agent (CompiledGraph or any Runnable)
        metadata_builder: Callable that builds Freeplay metadata dict when invoked
        fail_on_metadata_error: If True, raises exceptions when metadata building fails.
                               If False, logs warning and continues without metadata.

    Example:
        >>> agent = freeplay.create_agent(...)
        >>>
        >>> # Core invocation works directly
        >>> result = agent.invoke({"messages": [...]})
        >>>
        >>> # State management via unwrap()
        >>> config = {"configurable": {"thread_id": "thread-123"}}
        >>> state = agent.unwrap().get_state(config)
        >>> agent.unwrap().update_state(config, {"key": "value"})
    """

    def __init__(
        self,
        agent: Runnable[Input, Output],
        metadata_builder: Callable[[], dict[str, Any]],
        fail_on_metadata_error: bool = True,
    ):
        """
        Initialize the FreeplayAgent wrapper.

        Creates a config_factory that injects Freeplay metadata into all invocations.
        This factory is passed to RunnableBindingBase which handles calling it for
        all invocation methods automatically.
        """
        self._fail_on_metadata_error = fail_on_metadata_error

        def inject_freeplay_metadata(config: RunnableConfig) -> RunnableConfig:
            """
            Config factory that injects Freeplay metadata.

            This function is called by RunnableBindingBase for every invocation
            to merge Freeplay metadata into the config.

            Args:
                config: The current RunnableConfig (may be empty dict)

            Returns:
                New RunnableConfig with Freeplay metadata merged in

            Raises:
                Exception: If metadata building fails and fail_on_metadata_error is True
            """
            try:
                freeplay_metadata = metadata_builder()
            except Exception as e:
                if fail_on_metadata_error:
                    raise
                logger.warning(f"Failed to build Freeplay metadata: {e}", exc_info=True)
                return config
            else:
                existing_metadata = config.get("metadata", {})
                if not isinstance(existing_metadata, dict):
                    existing_metadata = {}

                return {
                    **config,
                    "metadata": {**existing_metadata, **freeplay_metadata},
                }

        # Initialize RunnableBindingBase with the agent and config factory
        super().__init__(
            bound=agent,
            config_factories=[inject_freeplay_metadata],
        )

    def unwrap(self) -> Runnable[Input, Output]:
        """
        Access the underlying agent for state management operations.

        Use this method to access CompiledStateGraph-specific methods that are
        not part of the core Runnable interface:

        State Management:
        - get_state(config, *, subgraphs=False) / aget_state(config, *, subgraphs=False)
        - update_state(config, values, as_node=None) / aupdate_state(config, values, as_node=None)
        - get_state_history(config, *, filter=None, before=None, limit=None)
        - aget_state_history(config, *, filter=None, before=None, limit=None)
        - bulk_update_state(config, updates) / abulk_update_state(config, updates)

        Multi-Agent Systems:
        - get_subgraphs(namespace=None, *, recurse=False) / aget_subgraphs(...)

        Cache Management:
        - clear_cache() / aclear_cache()

        Example:
            >>> agent = freeplay.create_agent(
            ...     prompt_name="assistant",
            ...     variables={"city": "SF"},
            ...     checkpointer=MemorySaver()  # Enable state persistence
            ... )
            >>>
            >>> # Core invocation works directly
            >>> result = agent.invoke(
            ...     {"messages": [HumanMessage(content="Hello")]},
            ...     config={"configurable": {"thread_id": "thread-123"}}
            ... )
            >>>
            >>> # State management via unwrap()
            >>> config = {"configurable": {"thread_id": "thread-123"}}
            >>> state = agent.unwrap().get_state(config)
            >>> print(f"Current messages: {state.values['messages']}")
            >>>
            >>> # Update state for human-in-the-loop workflows
            >>> agent.unwrap().update_state(
            ...     config,
            ...     {"approval": "granted"},
            ...     as_node="human"
            ... )

        For full type safety with state methods, use cast:
            >>> from typing import cast
            >>> from langgraph.graph.state import CompiledStateGraph
            >>> compiled = cast(CompiledStateGraph, agent.unwrap())
            >>> state = compiled.get_state(config)  # Full type hints

        Returns:
            The wrapped LangGraph agent (typically CompiledStateGraph)
        """
        return self.bound

    def __repr__(self) -> str:
        """String representation of the wrapper."""
        return f"FreeplayAgent(bound={self.bound!r})"
