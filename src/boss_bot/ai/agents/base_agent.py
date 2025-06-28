"""Base agent class for LangGraph multi-agent architecture."""

from __future__ import annotations

import abc
import logging
import time
from typing import TYPE_CHECKING, Any, List, Optional

from boss_bot.ai.agents.context import AgentContext, AgentRequest, AgentResponse

if TYPE_CHECKING:
    from langchain_core.language_models import BaseLanguageModel
    from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)


class BaseAgent(abc.ABC):
    """Abstract base class for all agents in the LangGraph system.

    This class provides the foundation for all agents, including:
    - Model management and interaction
    - Tool management and execution
    - Agent handoff protocols
    - Context and state management
    - Error handling and logging
    """

    def __init__(
        self,
        name: str,
        model: BaseLanguageModel,
        system_prompt: str,
        tools: list[BaseTool] | None = None,
        handoff_targets: list[BaseAgent] | None = None,
    ):
        """Initialize the base agent.

        Args:
            name: Agent name for identification and logging
            model: Language model instance for AI processing
            system_prompt: System prompt defining agent behavior
            tools: Optional list of tools available to the agent
            handoff_targets: Optional list of agents this agent can handoff to
        """
        self.name = name
        self.model = model
        self.system_prompt = system_prompt
        self.tools: list[BaseTool] = tools or []
        self.handoff_targets: list[BaseAgent] = handoff_targets or []

        # Performance tracking
        self._request_count = 0
        self._total_processing_time = 0.0

        logger.info(f"Initialized agent '{name}' with {len(self.tools)} tools")

    def add_tool(self, tool: BaseTool) -> None:
        """Add a tool to the agent's toolkit.

        Args:
            tool: Tool to add to the agent
        """
        self.tools.append(tool)
        logger.debug(f"Added tool '{tool.name}' to agent '{self.name}'")

    def add_handoff_target(self, agent: BaseAgent) -> None:
        """Add a handoff target agent.

        Args:
            agent: Agent that this agent can handoff requests to
        """
        self.handoff_targets.append(agent)
        logger.debug(f"Added handoff target '{agent.name}' to agent '{self.name}'")

    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """Process an agent request.

        This is the main entry point for agent processing. It handles
        validation, timing, error handling, and delegates to the
        abstract _process_request method for actual implementation.

        Args:
            request: AgentRequest containing context and action data

        Returns:
            AgentResponse with processing results
        """
        start_time = time.time()
        self._request_count += 1

        try:
            # Validate request
            if not self.validate_request(request):
                return AgentResponse(
                    success=False,
                    error=f"Invalid request for agent '{self.name}'",
                    confidence=0.0,
                    reasoning="Request validation failed",
                )

            logger.info(f"Agent '{self.name}' processing action '{request.action}'")

            # Delegate to implementation
            response = await self._process_request(request)

            # Add processing time
            processing_time = (time.time() - start_time) * 1000
            response.processing_time_ms = processing_time
            self._total_processing_time += processing_time

            logger.info(
                f"Agent '{self.name}' completed action '{request.action}' "
                f"in {processing_time:.2f}ms (success: {response.success})"
            )

            return response

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"Agent '{self.name}' failed processing: {e}", exc_info=True)

            return AgentResponse(
                success=False,
                error=f"Processing failed: {e!s}",
                confidence=0.0,
                reasoning=f"Exception occurred during processing: {type(e).__name__}",
                processing_time_ms=processing_time,
            )

    @abc.abstractmethod
    async def _process_request(self, request: AgentRequest) -> AgentResponse:
        """Process the actual request (implementation required).

        This method must be implemented by concrete agent classes
        to provide the specific functionality of the agent.

        Args:
            request: AgentRequest to process

        Returns:
            AgentResponse with processing results
        """
        pass

    def validate_request(self, request: AgentRequest) -> bool:
        """Validate an incoming request.

        Base implementation performs basic validation. Concrete agents
        can override to add specific validation logic.

        Args:
            request: AgentRequest to validate

        Returns:
            True if request is valid, False otherwise
        """
        if not isinstance(request, AgentRequest):
            return False

        if not request.context or not request.action:
            return False

        if not isinstance(request.context, AgentContext):
            return False

        return True

    def can_handle_action(self, action: str) -> bool:
        """Check if this agent can handle a specific action.

        Base implementation returns True for all actions. Concrete agents
        should override to specify which actions they support.

        Args:
            action: Action name to check

        Returns:
            True if action is supported, False otherwise
        """
        return True

    def create_react_agent(self):
        """Create LangGraph react agent with tools and handoff capabilities.

        Integrates the BaseAgent with LangGraph's react agent pattern,
        enabling tool usage and multi-agent handoff coordination.

        Returns:
            LangGraph react agent instance
        """
        try:
            from langgraph_swarm import create_handoff_tool, create_react_agent
        except ImportError:
            logger.warning("langgraph_swarm not available, creating basic agent")
            # Fallback implementation for when langgraph_swarm is not available
            from types import SimpleNamespace

            agent = SimpleNamespace()
            agent.invoke = lambda x: {"messages": [{"role": "assistant", "content": "Basic agent response"}]}
            agent.name = self.name
            return agent

        # Create handoff tools for agent coordination
        handoff_tools = []
        for target in self.handoff_targets:
            try:
                handoff_tool = create_handoff_tool(agent_name=target.name)
                handoff_tools.append(handoff_tool)
                logger.debug(f"Created handoff tool for agent '{target.name}'")
            except Exception as e:
                logger.warning(f"Failed to create handoff tool for {target.name}: {e}")

        # Combine agent tools with handoff tools
        all_tools = self.tools + handoff_tools

        try:
            # Create the react agent with LangGraph
            react_agent = create_react_agent(
                model=self.model, tools=all_tools, name=self.name, prompt=self.system_prompt
            )

            logger.info(f"Created LangGraph react agent '{self.name}' with {len(all_tools)} tools")
            return react_agent

        except Exception as e:
            logger.error(f"Failed to create react agent: {e}", exc_info=True)
            # Return fallback agent
            from types import SimpleNamespace

            agent = SimpleNamespace()
            agent.invoke = lambda x: {
                "messages": [{"role": "assistant", "content": f"Agent {self.name} fallback response"}]
            }
            agent.name = self.name
            return agent

    def get_handoff_target(self, target_name: str) -> BaseAgent | None:
        """Get a handoff target agent by name.

        Args:
            target_name: Name of the target agent

        Returns:
            Target agent if found, None otherwise
        """
        for agent in self.handoff_targets:
            if agent.name == target_name:
                return agent
        return None

    @property
    def performance_metrics(self) -> dict[str, Any]:
        """Get performance metrics for this agent.

        Returns:
            Dictionary with performance metrics
        """
        avg_processing_time = self._total_processing_time / self._request_count if self._request_count > 0 else 0.0

        return {
            "name": self.name,
            "request_count": self._request_count,
            "total_processing_time_ms": self._total_processing_time,
            "average_processing_time_ms": avg_processing_time,
            "tool_count": len(self.tools),
            "handoff_target_count": len(self.handoff_targets),
        }

    def __repr__(self) -> str:
        """String representation of the agent."""
        return (
            f"{self.__class__.__name__}("
            f"name='{self.name}', "
            f"tools={len(self.tools)}, "
            f"handoff_targets={len(self.handoff_targets)}"
            f")"
        )
