---
allowed-tools:
  # Core development tools
  - Bash(uv add:*, uv remove:*, uv list:*, uv tree:*, uv check:*)
  - Bash(just check-*:*, just format:*, just fix:*, just ci:*)
  - Bash(git status:*, git diff:*, git log:*, git branch:*)

  # File operations
  - Read
  - Write
  - Edit
  - MultiEdit
  - Glob
  - Grep
  - LS

  # Project management
  - TodoWrite
  - TodoRead
  - Task

  # Documentation and research
  - langgraph-supervisor__*
  - langgraph-swarm__*
  - mcp__mcp-server-langgraph__*
  - mcp__mcp-server-langchain__*
  - mcp__mcp-server-trustcall__*
  - mcp__perplexity-ask__*
  - langgraph-docs-mcp__*
  - claude-code-docs-mcp__*
description: "Implements LangGraph multi-agent system for Boss-Bot using TDD approach with minimal code changes and extended thinking analysis"
---

# Implement Boss-Bot LangGraph Agent System

Think deeply about the implementation strategy, analyzing the current architecture, identifying integration points, and planning the most effective approach to enhance Boss-Bot with AI capabilities while maintaining backward compatibility. Consider the complexity of multi-agent coordination and the importance of gradual, tested rollout.

## Context & Project Status

You are implementing the LangGraph multi-agent system for Boss-Bot following the comprehensive plan in `ai_docs/plans/llm_agent/final_agent_plans/agent_implementation/projectplan.md`.

### Key Reference Files
@ai_docs/plans/llm_agent/final_agent_plans/agent_implementation/projectplan.md
@src/boss_bot/ai/agents/base_agent.py
@src/boss_bot/ai/agents/context.py
@src/boss_bot/core/downloads/strategies/base_strategy.py
@src/boss_bot/core/downloads/feature_flags.py

## Current Implementation Status Analysis

### Project Plan Progress
!`grep -A 20 "Implementation Log" ai_docs/plans/llm_agent/final_agent_plans/agent_implementation/projectplan.md`

### Current Dependencies Status
!`uv list | grep -E "(langgraph|langchain)" || echo "No LangGraph dependencies installed yet"`

### Phase Detection - Current AI Infrastructure
!`find src/boss_bot/ai -name "*.py" -type f | wc -l` files in AI directory

Existing AI structure:
!`ls -la src/boss_bot/ai/`

Agent implementations:
!`find src/boss_bot/ai/agents -name "*.py" -exec basename {} \; | grep -v __init__ || echo "Only base infrastructure exists"`

### Project Structure Overview
Use this command to get a comprehensive view of the project structure when needed:
!`tree -L 7 -I "*.pyc|__pycache__|.git|.pytest_cache|.ruff_cache|.mypy_cache|.coverage|htmlcov|.venv|.env|*.egg-info|build|dist|node_modules|.DS_Store|images" src tests`

### Strategy Pattern Integration Points
!`ls -la src/boss_bot/core/downloads/strategies/`

Current feature flags:
!`grep -E "(use_api|enabled)" src/boss_bot/core/downloads/feature_flags.py | head -5`

### Discord Integration Status
!`grep -n "class.*Cog" src/boss_bot/bot/cogs/downloads.py`

### Test Infrastructure
!`find tests -name "*ai*" -type d || echo "No AI test directory yet"`
!`find tests -name "*test_*agent*" -type f || echo "No agent tests yet"`

## Dynamic Phase Detection & Guidance

### Current Phase Analysis
Based on the status analysis above, determine the current implementation phase:

!`if [ -f "tests/test_ai/conftest.py" ]; then echo "Phase 2: Agent Implementation"; elif uv list | grep -q langgraph; then echo "Phase 1: Foundation Setup"; else echo "Phase 0: Dependencies & Setup"; fi`

### Phase-Specific Implementation Task
$ARGUMENTS

## Implementation Strategy (Adaptive Based on Phase)

### Phase 0: Dependencies & Setup
If no LangGraph dependencies are installed:
1. **Install Core Dependencies**:
```bash
# Core LangGraph Framework
uv add langgraph langgraph-sdk langchain-core

# Agent Coordination Patterns
uv add git+https://github.com/langchain-ai/langgraph-swarm-py
uv add git+https://github.com/langchain-ai/langgraph-supervisor-py

# Model Providers (start with OpenAI)
uv add langchain-openai

# State Management & Testing
uv add langgraph-checkpoint-sqlite
uv add --dev pytest-recording
```

2. **Verify Installation**: !`uv list | grep -E "(langgraph|langchain)"`

### Phase 1: Foundation Enhancement
If dependencies exist but no agent implementations:
1. **Enhance BaseAgent with LangGraph Integration**
2. **Create Strategy Selector Agent**
3. **Set up comprehensive test infrastructure**
4. **Add feature flags for AI enhancement**

### Phase 2: Agent Implementation
If base infrastructure exists:
1. **Implement specialized agents** (Content Analyzer, Platform-specific agents)
2. **Create agent coordination workflows**
3. **Integrate with existing Discord/CLI systems**
4. **Comprehensive integration testing**

### Phase 3: Production Integration
If agents are implemented:
1. **Performance optimization and monitoring**
2. **Gradual rollout with feature flags**
3. **User acceptance testing**
4. **Documentation and training**

## TDD Implementation Approach

### Pre-Implementation Analysis
Think through these questions before starting:
- What specific capability are you implementing?
- How does it integrate with existing strategy pattern?
- What are the failure modes and fallback strategies?
- How will you test both AI and fallback behaviors?

### Red-Green-Refactor Cycle
1. **🔴 RED**: Write failing test for new capability
2. **🟢 GREEN**: Implement minimal code to pass test
3. **🔵 REFACTOR**: Enhance implementation with actual AI logic
4. **✅ VALIDATE**: Run full test suite and quality checks

## Core Implementation Principles

### 1. Architecture Integration Strategy
- **Enhance, Don't Replace**: Build upon existing Epic 5 strategy pattern
- **Backward Compatibility**: All existing functionality must continue working
- **Feature Flag Control**: Use environment variables for gradual AI rollout
- **Graceful Degradation**: AI failures fallback to existing CLI/API methods

### 2. Boss-Bot Integration Points
Based on current architecture analysis:

**Strategy Pattern Enhancement**:
- Extend `BaseDownloadStrategy.supports_url()` with AI confidence scoring
- Add AI-powered strategy selection while preserving existing fallbacks
- Integrate with feature flag system for controlled rollout

**Discord.py Integration**:
- Enhance existing `DownloadCog` with AI-powered commands
- Add natural language processing capabilities
- Maintain existing command compatibility

**Test Integration**:
- Follow existing pytest patterns with dpytest for Discord testing
- Use function-scoped fixtures for isolation
- Mock AI services for deterministic testing

### 3. Implementation Workflow Examples

#### Example 1: Enhancing BaseAgent with LangGraph
```python
# Current BaseAgent (exists) - reference @src/boss_bot/ai/agents/base_agent.py
# Enhancement needed: Add LangGraph create_react_agent integration

# 1. 🔴 RED: Write failing test first
def test_base_agent_creates_langgraph_react_agent():
    """Test BaseAgent can create LangGraph react agent."""
    from langgraph_swarm import create_react_agent

    agent = StrategySelector("test-agent", model=mock_model, system_prompt="test")
    react_agent = agent.create_react_agent()

    assert react_agent is not None
    assert hasattr(react_agent, 'invoke')  # LangGraph agent interface

# 2. 🟢 GREEN: Add method to BaseAgent
class BaseAgent:
    def create_react_agent(self):
        """Create LangGraph react agent with tools and handoffs."""
        from langgraph_swarm import create_react_agent, create_handoff_tool

        handoff_tools = [
            create_handoff_tool(agent_name=target.name)
            for target in self.handoff_targets
        ]

        return create_react_agent(
            model=self.model,
            tools=self.tools + handoff_tools,
            name=self.name,
            prompt=self.system_prompt
        )
```

#### Example 2: Strategy Selector with Fallback Pattern
```python
# Integration with existing strategy pattern
class StrategySelector(BaseAgent):
    async def select_strategy(self, url: str, user_context: dict) -> StrategyResult:
        """AI-enhanced strategy selection with fallback."""

        # Always get traditional fallback first
        from boss_bot.core.downloads.strategies import get_strategy_for_url
        fallback_strategy = get_strategy_for_url(url)

        # Check if AI enhancement is enabled
        if not self._should_use_ai_enhancement():
            return StrategyResult(
                strategy=fallback_strategy,
                confidence_score=0.7,  # Traditional method confidence
                fallback_strategy=fallback_strategy,
                reasoning="AI enhancement disabled, using traditional selection"
            )

        try:
            # AI-enhanced selection logic
            ai_result = await self._ai_select_strategy(url, user_context)
            ai_result.fallback_strategy = fallback_strategy
            return ai_result

        except Exception as e:
            logger.warning(f"AI strategy selection failed: {e}, using fallback")
            return StrategyResult(
                strategy=fallback_strategy,
                confidence_score=0.7,
                fallback_strategy=fallback_strategy,
                reasoning=f"AI selection failed: {e}, used fallback"
            )
```

### 4. Error Handling & Fallback Pattern
```python
async def ai_enhanced_method(self, *args, **kwargs):
    """Standard AI enhancement pattern with fallback."""

    # Fast path: if AI disabled, use traditional method
    if not self.settings.ai_enhanced_enabled:
        return await self._traditional_method(*args, **kwargs)

    try:
        # AI implementation with timeout
        result = await asyncio.wait_for(
            self._ai_implementation(*args, **kwargs),
            timeout=self.settings.ai_timeout_seconds or 30
        )
        return result

    except asyncio.TimeoutError:
        logger.warning("AI processing timeout, using fallback")
        return await self._traditional_method(*args, **kwargs)

    except Exception as e:
        logger.error(f"AI processing failed: {e}", exc_info=True)
        return await self._traditional_method(*args, **kwargs)
```

## Task Management & Progress Tracking

### Current Todo Status
!`TodoRead || echo "No current todos - will create task list"`

### Update Implementation Progress
```markdown
# Update the project plan progress tracking:
- Use TodoWrite to manage specific implementation tasks
- Update ai_docs/plans/llm_agent/final_agent_plans/agent_implementation/projectplan.md
- Track completion of each component
```

## Quality Assurance Pipeline

### Pre-Implementation Validation
!`just check-type | tail -3` (current type check status)
!`just check-test --collect-only | grep "collected" || echo "Test collection check"`

### Implementation Quality Gates
1. **🧪 Test First**: Write test, watch it fail (Red)
2. **⚡ Minimal Implementation**: Pass the test (Green)
3. **🔨 Refactor**: Improve with actual AI logic (Refactor)
4. **✅ Validate**: Run quality checks

### Post-Implementation Checks
```bash
# Comprehensive validation before marking complete
just check-test "tests/test_ai/"        # AI-specific tests
just check-test "tests/test_bot/"        # Integration tests
just check-type                          # Type safety
just format                              # Code formatting
just check-code                          # Linting
just ci                                  # Full pipeline
```

## Troubleshooting & Common Issues

### Dependency Conflicts
If LangGraph installation fails:
!`uv tree | grep -E "(langgraph|langchain)" | head -10`

### Integration Problems
Check current strategy pattern status:
!`python -c "from boss_bot.core.downloads.strategies import get_strategy_for_url; print('Strategy pattern working')" 2>/dev/null || echo "Strategy import issue"`

### Test Infrastructure Issues
Verify existing test patterns:
!`find tests -name "conftest.py" | head -3`
!`grep -r "fixture_.*_test" tests/conftest.py | head -2 || echo "Check fixture naming"`

## Enhanced Help Resources

### LangGraph Patterns & Documentation
- **LangGraph Core**: Use `mcp__mcp-server-langgraph__*` for framework docs
- **Swarm Coordination**: Use `langgraph-swarm__*` for multi-agent patterns
- **Supervisor Patterns**: Use `langgraph-supervisor__*` for hierarchical agents
- **Documentation**: Use `langgraph-docs-mcp__*` for official guides

### Architecture Questions
- **Boss-Bot Patterns**: Reference existing @files loaded in context
- **Strategy Integration**: Analyze current `BaseDownloadStrategy` implementations
- **Testing Patterns**: Follow existing dpytest and pytest-asyncio patterns
- **Real-time Research**: Use `mcp__perplexity-ask__*` for latest patterns

## Implementation Readiness Checklist

### ✅ Before You Start
- [ ] Current phase identified via dynamic detection
- [ ] Relevant files loaded into context (@file references)
- [ ] Dependencies status verified
- [ ] Integration points analyzed
- [ ] Test infrastructure understood

### ✅ During Implementation
- [ ] TDD cycle followed (Red-Green-Refactor)
- [ ] Backward compatibility maintained
- [ ] Feature flags implemented
- [ ] Error handling with fallbacks
- [ ] Performance considerations addressed

### ✅ Before Completion
- [ ] All tests passing (`just check-test`)
- [ ] Type safety verified (`just check-type`)
- [ ] Code formatted (`just format`)
- [ ] Integration tests passed
- [ ] TodoWrite updated with progress
- [ ] Documentation updated

Think through the architecture implications, consider the integration complexity, and plan each change carefully. Boss-Bot's existing architecture is excellent - your job is to enhance it intelligently with AI capabilities while maintaining its reliability and user experience.

## Next Steps Based on Phase

The command has now provided comprehensive context about the current state. Proceed with the phase-appropriate implementation, following TDD principles and maintaining the high quality standards Boss-Bot users expect.
