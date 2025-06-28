"""LangGraph workflow for multi-agent download coordination."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, TypedDict

from boss_bot.ai.agents.context import AgentContext, AgentRequest

if TYPE_CHECKING:
    from boss_bot.ai.agents.base_agent import BaseAgent
    from boss_bot.ai.agents.content_analyzer import ContentAnalyzer
    from boss_bot.ai.agents.strategy_selector import StrategySelector
    from boss_bot.core.downloads.strategies.base_strategy import BaseDownloadStrategy

logger = logging.getLogger(__name__)


class WorkflowState(TypedDict):
    """State structure for the download workflow."""

    # Input data
    url: str  # Required, no default
    user_context: dict[str, Any]  # Could default to {}
    request_id: str  # Could default to "" or generate UUID

    # Agent results
    strategy_selection: dict[str, Any] | None
    content_analysis: dict[str, Any] | None
    download_result: dict[str, Any] | None

    # Workflow control
    current_step: Literal["start", "strategy_selection", "content_analysis", "download", "complete", "error"]
    error_message: str | None
    retry_count: int  # Default: 0
    max_retries: int  # Default: 3


@dataclass
class DownloadWorkflowConfig:
    """Configuration for the download workflow."""

    max_retries: int = 3
    timeout_seconds: int = 300
    enable_content_analysis: bool = True
    enable_ai_strategy_selection: bool = True
    fallback_to_traditional: bool = True


class DownloadWorkflow:
    """LangGraph workflow for coordinating multi-agent downloads.

    This workflow orchestrates the download process by coordinating
    between different agents:
    1. StrategySelector - Determines the best download strategy
    2. ContentAnalyzer - Analyzes content before download
    3. Download execution - Performs the actual download

    The workflow uses LangGraph's state machine pattern for
    robust error handling and agent coordination.
    """

    def __init__(
        self,
        strategy_selector: StrategySelector | None = None,
        content_analyzer: ContentAnalyzer | None = None,
        config: DownloadWorkflowConfig | None = None,
    ):
        """Initialize the download workflow.

        Args:
            strategy_selector: AI agent for strategy selection
            content_analyzer: AI agent for content analysis
            config: Workflow configuration options
        """
        self.strategy_selector = strategy_selector
        self.content_analyzer = content_analyzer
        self.config = config or DownloadWorkflowConfig()

        # Available strategies (populated by initialize_strategies)
        self._strategies: dict[str, BaseDownloadStrategy] = {}

        logger.info(f"Initialized DownloadWorkflow with config: {self.config}")

    def initialize_strategies(self, strategies: dict[str, BaseDownloadStrategy]) -> None:
        """Initialize available download strategies.

        Args:
            strategies: Dictionary mapping platform names to strategy instances
        """
        self._strategies = strategies
        logger.info(f"Initialized workflow with {len(strategies)} strategies")

    async def run_workflow(
        self,
        url: str,
        user_context: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """Run the complete download workflow.

        Args:
            url: URL to download
            user_context: Optional user context and preferences
            request_id: Optional request identifier

        Returns:
            Dictionary containing workflow results
        """
        if not request_id:
            import uuid

            request_id = str(uuid.uuid4())

        # Initialize workflow state
        state: WorkflowState = {
            "url": url,
            "user_context": user_context or {},
            "request_id": request_id,
            "strategy_selection": None,
            "content_analysis": None,
            "download_result": None,
            "current_step": "start",
            "error_message": None,
            "retry_count": 0,
            "max_retries": self.config.max_retries,
        }

        logger.info(f"Starting download workflow for URL: {url} (request_id: {request_id})")

        try:
            # Create LangGraph workflow if available
            if self._has_langgraph():
                return await self._run_langgraph_workflow(state)
            else:
                return await self._run_simple_workflow(state)

        except Exception as e:
            logger.error(f"Workflow failed for {url}: {e}", exc_info=True)
            state["current_step"] = "error"
            state["error_message"] = str(e)
            return self._create_error_result(state, str(e))

    def _has_langgraph(self) -> bool:
        """Check if LangGraph is available for workflow execution."""
        try:
            import langgraph

            return True
        except ImportError:
            return False

    async def _run_langgraph_workflow(self, state: WorkflowState) -> dict[str, Any]:
        """Run workflow using LangGraph state machine."""
        try:
            from langgraph.graph import END, StateGraph

            # Create workflow graph
            workflow = StateGraph(WorkflowState)

            # Add workflow nodes (node names must not conflict with state keys)
            workflow.add_node("select_strategy", self._strategy_selection_node)
            workflow.add_node("analyze_content", self._content_analysis_node)
            workflow.add_node("execute_download", self._download_node)
            workflow.add_node("handle_error", self._error_handler_node)

            # Define workflow edges
            workflow.set_entry_point("select_strategy")

            # Strategy selection routing
            workflow.add_conditional_edges(
                "select_strategy",
                self._route_after_strategy_selection,
                {
                    "content_analysis": "analyze_content",
                    "download": "execute_download",
                    "error": "handle_error",
                },
            )

            # Content analysis routing
            workflow.add_conditional_edges(
                "analyze_content",
                self._route_after_content_analysis,
                {
                    "download": "execute_download",
                    "error": "handle_error",
                },
            )

            # Download routing
            workflow.add_conditional_edges(
                "execute_download",
                self._route_after_download,
                {
                    "complete": END,
                    "retry": "select_strategy",
                    "error": "handle_error",
                },
            )

            # Error handler always ends
            workflow.add_edge("handle_error", END)

            # Compile and run workflow
            app = workflow.compile()

            logger.info("Running LangGraph workflow")
            result = await app.ainvoke(state)

            # Check if workflow ended with an error
            if result.get("error_message"):
                return self._create_error_result(result, result["error_message"])
            else:
                # Update state to complete for successful workflow
                result["current_step"] = "complete"
                return self._create_success_result(result)

        except Exception as e:
            logger.error(f"LangGraph workflow failed: {e}", exc_info=True)
            return await self._run_simple_workflow(state)

    async def _run_simple_workflow(self, state: WorkflowState) -> dict[str, Any]:
        """Run simplified workflow without LangGraph."""
        logger.info("Running simplified workflow (LangGraph not available)")

        try:
            # Step 1: Strategy Selection
            state["current_step"] = "strategy_selection"
            await self._strategy_selection_node(state)

            if state["error_message"]:
                return self._create_error_result(state, state["error_message"])

            # Step 2: Content Analysis (if enabled)
            if self.config.enable_content_analysis and self.content_analyzer:
                state["current_step"] = "content_analysis"
                await self._content_analysis_node(state)

                if state["error_message"]:
                    logger.warning(f"Content analysis failed, continuing: {state['error_message']}")

            # Step 3: Download
            state["current_step"] = "download"
            await self._download_node(state)

            if state["error_message"]:
                return self._create_error_result(state, state["error_message"])

            state["current_step"] = "complete"
            return self._create_success_result(state)

        except Exception as e:
            logger.error(f"Simple workflow failed: {e}", exc_info=True)
            return self._create_error_result(state, str(e))

    async def _strategy_selection_node(self, state: WorkflowState) -> WorkflowState:
        """Workflow node for strategy selection."""
        try:
            if self.strategy_selector and self.config.enable_ai_strategy_selection:
                # Use AI strategy selector
                context = AgentContext(
                    request_id=state["request_id"],
                    user_id=state["user_context"].get("user_id", "unknown"),
                    guild_id=state["user_context"].get("guild_id"),
                    metadata=state["user_context"],
                )

                request = AgentRequest(
                    context=context,
                    action="select_strategy",
                    data={"url": state["url"], "strategies": list(self._strategies.keys())},
                )

                response = await self.strategy_selector.process_request(request)

                if response.success:
                    state["strategy_selection"] = {
                        "selected_strategy": response.result,
                        "confidence": response.confidence,
                        "reasoning": response.reasoning,
                        "ai_enhanced": True,
                    }
                else:
                    logger.warning(f"AI strategy selection failed: {response.error}")
                    # Fall back to traditional selection
                    await self._traditional_strategy_selection(state)
            else:
                # Use traditional strategy selection
                await self._traditional_strategy_selection(state)

        except Exception as e:
            logger.error(f"Strategy selection failed: {e}", exc_info=True)
            state["error_message"] = f"Strategy selection failed: {e}"

        return state

    async def _traditional_strategy_selection(self, state: WorkflowState) -> None:
        """Traditional strategy selection based on URL patterns."""
        url = state["url"]

        # Check if any strategies are available
        if not self._strategies:
            state["error_message"] = f"No strategy found for URL: {url}"
            return

        # Simple URL-based strategy selection
        selected_strategy = None
        for strategy_name, strategy in self._strategies.items():
            if strategy.supports_url(url):
                selected_strategy = strategy_name
                break

        if selected_strategy:
            state["strategy_selection"] = {
                "selected_strategy": selected_strategy,
                "confidence": 0.8,  # Default confidence for traditional selection
                "reasoning": f"URL pattern matches {selected_strategy} strategy",
                "ai_enhanced": False,
            }
        else:
            state["error_message"] = f"No strategy found for URL: {url}"

    async def _content_analysis_node(self, state: WorkflowState) -> WorkflowState:
        """Workflow node for content analysis."""
        try:
            if not self.content_analyzer:
                logger.info("Content analyzer not available, skipping content analysis")
                return state

            context = AgentContext(
                request_id=state["request_id"],
                user_id=state["user_context"].get("user_id", "unknown"),
                guild_id=state["user_context"].get("guild_id"),
                metadata=state["user_context"],
            )

            request = AgentRequest(
                context=context,
                action="analyze_content",
                data={"url": state["url"]},
            )

            response = await self.content_analyzer.process_request(request)

            if response.success:
                state["content_analysis"] = {
                    "analysis": response.result,
                    "confidence": response.confidence,
                    "reasoning": response.reasoning,
                    "metadata": response.metadata,
                }
            else:
                logger.warning(f"Content analysis failed: {response.error}")
                # Continue without content analysis

        except Exception as e:
            logger.error(f"Content analysis failed: {e}", exc_info=True)
            # Content analysis failure is not critical, continue workflow

        return state

    async def _download_node(self, state: WorkflowState) -> WorkflowState:
        """Workflow node for download execution."""
        try:
            strategy_info = state.get("strategy_selection")
            if not strategy_info:
                state["error_message"] = "No strategy selected for download"
                return state

            strategy_name = strategy_info["selected_strategy"]
            strategy = self._strategies.get(strategy_name)

            if not strategy:
                state["error_message"] = f"Strategy '{strategy_name}' not available"
                return state

            logger.info(f"Executing download with {strategy_name} strategy")

            # Perform download
            download_result = await strategy.download(state["url"])

            state["download_result"] = {
                "success": True,
                "metadata": download_result,
                "strategy_used": strategy_name,
                "content_analysis": state.get("content_analysis"),
            }

        except Exception as e:
            logger.error(f"Download failed: {e}", exc_info=True)
            state["error_message"] = f"Download failed: {e}"

        return state

    async def _error_handler_node(self, state: WorkflowState) -> WorkflowState:
        """Workflow node for error handling."""
        error_msg = state.get("error_message", "Unknown error")
        logger.error(f"Workflow error: {error_msg}")

        # Could implement retry logic here
        state["current_step"] = "error"
        return state

    def _route_after_strategy_selection(self, state: WorkflowState) -> str:
        """Route after strategy selection."""
        if state.get("error_message"):
            return "error"
        elif self.config.enable_content_analysis and self.content_analyzer:
            return "content_analysis"
        else:
            return "download"

    def _route_after_content_analysis(self, state: WorkflowState) -> str:
        """Route after content analysis."""
        if state.get("error_message"):
            return "error"
        else:
            return "download"

    def _route_after_download(self, state: WorkflowState) -> str:
        """Route after download."""
        if state.get("error_message"):
            # Check if we should retry
            if state["retry_count"] < state["max_retries"]:
                state["retry_count"] += 1
                state["error_message"] = None  # Reset error for retry
                logger.info(f"Retrying download (attempt {state['retry_count']})")
                return "retry"
            else:
                return "error"
        else:
            return "complete"

    def _create_success_result(self, state: WorkflowState) -> dict[str, Any]:
        """Create success result from workflow state."""
        return {
            "success": True,
            "request_id": state["request_id"],
            "url": state["url"],
            "strategy_selection": state.get("strategy_selection"),
            "content_analysis": state.get("content_analysis"),
            "download_result": state.get("download_result"),
            "workflow_steps": state["current_step"],
        }

    def _create_error_result(self, state: WorkflowState, error: str) -> dict[str, Any]:
        """Create error result from workflow state."""
        return {
            "success": False,
            "request_id": state["request_id"],
            "url": state["url"],
            "error": error,
            "strategy_selection": state.get("strategy_selection"),
            "content_analysis": state.get("content_analysis"),
            "workflow_steps": state["current_step"],
            "retry_count": state.get("retry_count", 0),
        }


def create_download_workflow_graph():
    """Create and return the compiled LangGraph workflow for LangGraph Cloud.

    This function creates a standalone instance of the DownloadWorkflow
    and returns the compiled graph for deployment to LangGraph Cloud.
    """
    from langgraph.graph import END, StateGraph

    # Create workflow graph
    workflow = StateGraph(WorkflowState)

    # For LangGraph Cloud, we need simple node functions
    # These will be basic implementations that can work without the full class context
    async def strategy_selection_node(state: WorkflowState) -> WorkflowState:
        """Simple strategy selection for LangGraph Cloud."""
        # Basic URL-based strategy selection
        url = state["url"]

        # Simple pattern matching for common platforms
        if "youtube.com" in url or "youtu.be" in url:
            selected_strategy = "youtube"
        elif "reddit.com" in url:
            selected_strategy = "reddit"
        elif "twitter.com" in url or "x.com" in url:
            selected_strategy = "twitter"
        elif "instagram.com" in url:
            selected_strategy = "instagram"
        else:
            selected_strategy = "generic"

        state["strategy_selection"] = {
            "selected_strategy": selected_strategy,
            "confidence": 0.8,
            "reasoning": f"URL pattern matches {selected_strategy} platform",
            "ai_enhanced": False,
        }
        return state

    async def content_analysis_node(state: WorkflowState) -> WorkflowState:
        """Simple content analysis for LangGraph Cloud."""
        # Basic content analysis based on URL
        url = state["url"]

        # Get platform from strategy selection, with fallback
        strategy_selection = state.get("strategy_selection", {})
        platform = strategy_selection.get("selected_strategy", "unknown") if strategy_selection else "unknown"

        state["content_analysis"] = {
            "analysis": {"platform": platform},
            "confidence": 0.7,
            "reasoning": "Basic platform-based analysis",
            "metadata": {"url": url},
        }
        return state

    async def download_execution_node(state: WorkflowState) -> WorkflowState:
        """Download execution node for LangGraph Cloud."""
        # Simulate download result
        strategy_info = state.get("strategy_selection", {})
        strategy_name = strategy_info.get("selected_strategy", "unknown")

        state["download_result"] = {
            "success": True,
            "metadata": {"strategy": strategy_name, "url": state["url"]},
            "strategy_used": strategy_name,
            "content_analysis": state.get("content_analysis"),
        }
        return state

    async def error_handler_node(state: WorkflowState) -> WorkflowState:
        """Error handling node for LangGraph Cloud."""
        state["current_step"] = "error"
        return state

    def route_after_strategy_selection(state: WorkflowState) -> str:
        """Route after strategy selection."""
        if state.get("error_message"):
            return "error"
        return "content_analysis"

    def route_after_content_analysis(state: WorkflowState) -> str:
        """Route after content analysis."""
        if state.get("error_message"):
            return "error"
        return "download"

    def route_after_download(state: WorkflowState) -> str:
        """Route after download."""
        if state.get("error_message"):
            return "error"
        return "complete"

    # Add workflow nodes
    workflow.add_node("select_strategy", strategy_selection_node)
    workflow.add_node("analyze_content", content_analysis_node)
    workflow.add_node("execute_download", download_execution_node)
    workflow.add_node("handle_error", error_handler_node)

    # Define workflow edges
    workflow.set_entry_point("select_strategy")

    # Strategy selection routing
    workflow.add_conditional_edges(
        "select_strategy",
        route_after_strategy_selection,
        {
            "content_analysis": "analyze_content",
            "error": "handle_error",
        },
    )

    # Content analysis routing
    workflow.add_conditional_edges(
        "analyze_content",
        route_after_content_analysis,
        {
            "download": "execute_download",
            "error": "handle_error",
        },
    )

    # Download routing
    workflow.add_conditional_edges(
        "execute_download",
        route_after_download,
        {
            "complete": END,
            "error": "handle_error",
        },
    )

    # Error handler always ends
    workflow.add_edge("handle_error", END)

    # Compile and return the graph
    return workflow.compile()


# Export the graph for LangGraph Cloud
graph = create_download_workflow_graph()
