"""Tests for base agent functionality."""

import pytest
from unittest.mock import AsyncMock, Mock
from pathlib import Path
from typing import Dict, Any

from boss_bot.ai.agents.base_agent import BaseAgent
from boss_bot.ai.agents.context import AgentContext, AgentRequest, AgentResponse, AgentContextManager


class TestAgentContext:
    """Test agent context data structure."""

    def test_agent_context_creation(self, fixture_agent_context):
        """Test AgentContext can be created with required fields."""
        context = AgentContext(**fixture_agent_context)

        assert context.request_id == "test-request-123"
        assert context.user_id == "test-user-456"
        assert context.guild_id == "test-guild-789"
        assert context.conversation_history == []
        assert context.metadata["platform"] == "discord"

    def test_agent_context_validation(self):
        """Test AgentContext validates required fields."""
        with pytest.raises(TypeError):
            AgentContext()  # Missing required fields

    def test_agent_context_optional_fields(self):
        """Test AgentContext works with minimal required fields."""
        context = AgentContext(
            request_id="test-123",
            user_id="user-456"
        )

        assert context.request_id == "test-123"
        assert context.user_id == "user-456"
        assert context.guild_id is None
        assert context.conversation_history == []


class TestAgentRequest:
    """Test agent request data structure."""

    def test_agent_request_creation(self, fixture_agent_context):
        """Test AgentRequest can be created with context and data."""
        context = AgentContext(**fixture_agent_context)
        request = AgentRequest(
            context=context,
            action="analyze_url",
            data={"url": "https://twitter.com/test"}
        )

        assert request.context == context
        assert request.action == "analyze_url"
        assert request.data["url"] == "https://twitter.com/test"

    def test_agent_request_validation(self):
        """Test AgentRequest validates required fields."""
        with pytest.raises(TypeError):
            AgentRequest()  # Missing required fields


class TestAgentResponse:
    """Test agent response data structure."""

    def test_agent_response_success(self):
        """Test successful AgentResponse creation."""
        response = AgentResponse(
            success=True,
            result="Analysis complete",
            confidence=0.95,
            reasoning="URL matches Twitter pattern",
            metadata={"platform": "twitter"}
        )

        assert response.success is True
        assert response.result == "Analysis complete"
        assert response.confidence == 0.95
        assert response.reasoning == "URL matches Twitter pattern"
        assert response.metadata["platform"] == "twitter"

    def test_agent_response_failure(self):
        """Test failed AgentResponse creation."""
        response = AgentResponse(
            success=False,
            error="Invalid URL format",
            confidence=0.0,
            reasoning="URL does not match any known patterns"
        )

        assert response.success is False
        assert response.error == "Invalid URL format"
        assert response.confidence == 0.0
        assert response.reasoning == "URL does not match any known patterns"


class ConcreteTestAgent(BaseAgent):
    """Concrete implementation of BaseAgent for testing."""

    async def _process_request(self, request: AgentRequest) -> AgentResponse:
        """Test implementation of process request."""
        return AgentResponse(
            success=True,
            result=f"Processed action: {request.action}",
            confidence=0.95,
            reasoning="Test agent processing"
        )


class TestBaseAgent:
    """Test base agent functionality."""

    def test_base_agent_creation(self, fixture_mock_llm_model):
        """Test BaseAgent can be created with required parameters."""
        agent = ConcreteTestAgent(
            name="test_agent",
            model=fixture_mock_llm_model,
            system_prompt="You are a test agent"
        )

        assert agent.name == "test_agent"
        assert agent.model == fixture_mock_llm_model
        assert agent.system_prompt == "You are a test agent"
        assert agent.tools == []
        assert agent.handoff_targets == []

    def test_base_agent_abstract_methods(self, fixture_mock_llm_model):
        """Test BaseAgent is abstract and requires implementation."""
        # BaseAgent should be abstract - this will be implemented by concrete agents
        agent = ConcreteTestAgent(
            name="test_agent",
            model=fixture_mock_llm_model,
            system_prompt="Test prompt"
        )

        # Should have abstract methods that need implementation
        assert hasattr(agent, 'process_request')
        assert hasattr(agent, 'validate_request')

    @pytest.mark.asyncio
    async def test_base_agent_process_request_interface(self, fixture_mock_llm_model, fixture_agent_context):
        """Test BaseAgent process_request interface."""
        agent = ConcreteTestAgent(
            name="test_agent",
            model=fixture_mock_llm_model,
            system_prompt="Test prompt"
        )

        context = AgentContext(**fixture_agent_context)
        request = AgentRequest(
            context=context,
            action="test_action",
            data={"test": "data"}
        )

        # BaseAgent should define the interface and concrete implementation should work
        response = await agent.process_request(request)
        assert isinstance(response, AgentResponse)
        assert response.success is True
        assert "test_action" in response.result

    def test_base_agent_add_tool(self, fixture_mock_llm_model):
        """Test adding tools to agent."""
        agent = ConcreteTestAgent(
            name="test_agent",
            model=fixture_mock_llm_model,
            system_prompt="Test prompt"
        )

        mock_tool = Mock()
        mock_tool.name = "test_tool"

        agent.add_tool(mock_tool)

        assert len(agent.tools) == 1
        assert agent.tools[0] == mock_tool

    def test_base_agent_add_handoff_target(self, fixture_mock_llm_model):
        """Test adding handoff targets to agent."""
        agent = ConcreteTestAgent(
            name="test_agent",
            model=fixture_mock_llm_model,
            system_prompt="Test prompt"
        )

        target_agent = Mock()
        target_agent.name = "target_agent"

        agent.add_handoff_target(target_agent)

        assert len(agent.handoff_targets) == 1
        assert agent.handoff_targets[0] == target_agent

    @pytest.mark.asyncio
    async def test_base_agent_langgraph_integration(self, fixture_mock_llm_model):
        """Test BaseAgent can create LangGraph react agent."""
        agent = ConcreteTestAgent(
            name="test_agent",
            model=fixture_mock_llm_model,
            system_prompt="You are a test agent with tools"
        )

        # Add some mock tools
        mock_tool1 = Mock()
        mock_tool1.name = "search_tool"
        mock_tool2 = Mock()
        mock_tool2.name = "download_tool"

        agent.add_tool(mock_tool1)
        agent.add_tool(mock_tool2)

        # Test LangGraph react agent creation
        react_agent = agent.create_react_agent()

        assert react_agent is not None
        assert hasattr(react_agent, 'invoke')  # LangGraph agent interface
        assert hasattr(react_agent, 'name')

    @pytest.mark.asyncio
    async def test_base_agent_langgraph_with_handoffs(self, fixture_mock_llm_model):
        """Test BaseAgent creates handoff tools for LangGraph coordination."""
        agent1 = ConcreteTestAgent(
            name="strategy_selector",
            model=fixture_mock_llm_model,
            system_prompt="You select download strategies"
        )

        agent2 = ConcreteTestAgent(
            name="content_analyzer",
            model=fixture_mock_llm_model,
            system_prompt="You analyze content"
        )

        # Set up handoff relationship
        agent1.add_handoff_target(agent2)

        # Create react agent with handoffs
        react_agent = agent1.create_react_agent()

        assert react_agent is not None
        # Should have handoff tools for coordination
        assert agent1.handoff_targets == [agent2]


class TestAgentContextManager:
    """Test agent context management."""

    def test_context_manager_creation(self):
        """Test AgentContextManager can be created."""
        manager = AgentContextManager()

        assert manager is not None
        assert hasattr(manager, 'create_context')
        assert hasattr(manager, 'get_context')
        assert hasattr(manager, 'update_context')

    def test_context_manager_create_context(self, fixture_agent_context):
        """Test context manager can create new contexts."""
        manager = AgentContextManager()

        context = manager.create_context(**fixture_agent_context)

        assert isinstance(context, AgentContext)
        assert context.request_id == "test-request-123"

    def test_context_manager_store_and_retrieve(self, fixture_agent_context):
        """Test context manager can store and retrieve contexts."""
        manager = AgentContextManager()

        # Create and store context
        context = manager.create_context(**fixture_agent_context)
        manager.store_context(context)

        # Retrieve context
        retrieved = manager.get_context(context.request_id)

        assert retrieved is not None
        assert retrieved.request_id == context.request_id
        assert retrieved.user_id == context.user_id
