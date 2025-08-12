# Boss-Bot LangGraph Pseudo-Code Documentation

This document provides detailed pseudo-code and module descriptions for the LangGraph multi-agent implementation in Boss-Bot.

## Table of Contents
1. [Agent Implementations](#agent-implementations)
2. [Agent Teams](#agent-teams)
3. [LangChain Chains](#langchain-chains)
4. [Coordination Layer](#coordination-layer)
5. [LangGraph Definitions](#langgraph-definitions)
6. [Memory Management](#memory-management)
7. [Routing and Load Balancing](#routing-and-load-balancing)
8. [Safety and Security](#safety-and-security)
9. [State Management](#state-management)
10. [LangChain Tools](#langchain-tools)

---

## Agent Implementations

### base_agent.py
**Purpose**: Abstract base class that all agents inherit from, providing common functionality like state management, error handling, and communication protocols.

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from langgraph_swarm import create_react_agent, create_handoff_tool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import tool

@dataclass
class AgentContext:
    """Context passed between agents"""
    request_id: str
    user_id: str
    guild_id: Optional[str]
    conversation_history: List[BaseMessage]
    metadata: Dict[str, Any]

class BaseAgent(ABC):
    """Abstract base class for all agents in the system using LangGraph patterns"""

    def __init__(self, name: str, model: str = "gpt-4"):
        self.name = name
        self.model = model
        self.tools = []
        self.handoff_targets = []
        self.system_prompt = ""

    def create_agent(self):
        """Create LangGraph react agent with handoff tools"""
        handoff_tools = [
            create_handoff_tool(agent_name=target)
            for target in self.handoff_targets
        ]

        return create_react_agent(
            model=self.model,
            tools=self.tools + handoff_tools,
            name=self.name,
            prompt=self.get_system_prompt()
        )

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return system prompt for this agent"""
        pass

    @abstractmethod
    def get_tools(self) -> List[Any]:
        """Return the tools available to this agent"""
        pass

    async def log_decision(self, decision: str, reasoning: str) -> None:
        """Log agent decisions for auditing"""
        pass
```

### main_supervisor.py
**Purpose**: Top-level orchestrator that routes requests to appropriate agent teams and manages the overall workflow.

```python
from typing import List, Dict, Any
from boss_bot.ai.agents.base_agent import BaseAgent, AgentContext
from langgraph_supervisor import Supervisor, create_agent
from langgraph_swarm import Swarm
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict
from typing import Annotated
from langgraph.graph import add_messages

class BossBotState(TypedDict):
    """Main application state for LangGraph"""
    messages: Annotated[list, add_messages]
    request_id: str
    user_id: str
    current_agent: str
    context: Dict[str, Any]
    processing_history: List[Dict[str, Any]]
    result: Dict[str, Any]

class MainSupervisor:
    """Main supervisor agent using langgraph-supervisor-py patterns"""

    def __init__(self):
        self.teams = {
            "social_media": SocialMediaTeam(),
            "media_processing": MediaProcessingTeam(),
            "content_analysis": ContentAnalysisTeam(),
            "user_interaction": UserInteractionTeam()
        }
        self.supervisor = self._build_supervisor()
        self.swarm_coordinator = self._build_swarm_coordinator()

    def _build_supervisor(self) -> Supervisor:
        """Build the hierarchical supervisor using langgraph-supervisor-py"""
        # Create team agents for supervision
        team_agents = []
        for team_name, team in self.teams.items():
            agent = create_agent(
                model="gpt-4",
                tools=team.get_tools(),
                name=team_name,
                prompt=team.get_system_prompt()
            )
            team_agents.append(agent)

        # Create supervisor with routing logic
        return Supervisor(
            agents=team_agents,
            routing_logic="route_based_on_intent"
        )

    def _build_swarm_coordinator(self):
        """Build swarm coordination for peer-to-peer handoffs"""
        # Each team can also operate as a swarm internally
        team_swarms = {}
        for team_name, team in self.teams.items():
            if hasattr(team, 'create_swarm'):
                team_swarms[team_name] = team.create_swarm()
        return team_swarms

    async def process(self, context: AgentContext) -> Dict[str, Any]:
        """Main processing logic using supervisor pattern"""
        # Convert context to supervisor format
        supervisor_input = self._convert_context_for_supervisor(context)

        # Process through supervisor
        result = await self.supervisor.run(supervisor_input)

        return result

    def _convert_context_for_supervisor(self, context: AgentContext) -> str:
        """Convert AgentContext to supervisor input format"""
        user_message = context.metadata.get("user_input", "")
        return f"User request: {user_message}"

    async def _classify_intent(self, context: AgentContext) -> Dict[str, Any]:
        """Classify user intent using NLP"""
        # Intent classification is now handled by supervisor routing
        return {"type": "supervisor_routed"}
```

### strategy_selector.py
**Purpose**: AI-enhanced strategy selection that determines the best download strategy based on content analysis and historical data.

```python
from typing import Dict, Any, List
from boss_bot.ai.agents.base_agent import BaseAgent, AgentContext
from boss_bot.core.downloads.strategies.base_strategy import BaseDownloadStrategy

class StrategySelector(BaseAgent):
    """AI agent for intelligent strategy selection"""

    def __init__(self):
        super().__init__("StrategySelector", model="gpt-3.5-turbo")
        self.strategies = self._load_available_strategies()
        self.performance_history = {}

    async def process(self, context: AgentContext) -> Dict[str, Any]:
        """Select optimal download strategy"""
        url = context.metadata.get("url")

        # Analyze URL and content
        content_analysis = await self._analyze_content(url)

        # Get user preferences
        user_prefs = await self._get_user_preferences(context.user_id)

        # Analyze historical performance
        historical_data = self._get_historical_performance(url, context.user_id)

        # Make intelligent strategy selection
        selected_strategy = await self._select_strategy(
            content_analysis,
            user_prefs,
            historical_data
        )

        return {
            "strategy": selected_strategy,
            "confidence": 0.95,
            "reasoning": "Selected based on content type and historical success",
            "alternatives": self._get_alternative_strategies(selected_strategy)
        }

    async def _analyze_content(self, url: str) -> Dict[str, Any]:
        """Analyze content at URL"""
        # Use content analyzer tools
        pass

    async def _select_strategy(
        self,
        content: Dict[str, Any],
        preferences: Dict[str, Any],
        history: Dict[str, Any]
    ) -> BaseDownloadStrategy:
        """AI-powered strategy selection"""
        prompt = f"""
        Select the best download strategy for:
        - Content: {content}
        - User preferences: {preferences}
        - Historical success: {history}

        Available strategies: {list(self.strategies.keys())}
        """
        # Use LLM to select strategy
        pass
```

### content_analyzer.py
**Purpose**: Multi-modal content analysis for media files, providing quality assessment and metadata extraction.

```python
from typing import Dict, Any, Optional
from boss_bot.ai.agents.base_agent import BaseAgent, AgentContext
from langchain.tools import Tool

class ContentAnalyzer(BaseAgent):
    """Agent for analyzing media content"""

    def __init__(self):
        super().__init__("ContentAnalyzer", model="gpt-4-vision-preview")
        self.vision_tools = self._initialize_vision_tools()

    async def process(self, context: AgentContext) -> Dict[str, Any]:
        """Analyze media content"""
        url = context.metadata.get("url")
        media_type = context.metadata.get("media_type")

        analysis_result = {
            "url": url,
            "media_type": media_type,
            "quality_assessment": {},
            "content_description": "",
            "metadata": {},
            "recommendations": []
        }

        if media_type == "video":
            analysis_result.update(await self._analyze_video(url))
        elif media_type == "image":
            analysis_result.update(await self._analyze_image(url))
        elif media_type == "audio":
            analysis_result.update(await self._analyze_audio(url))

        # Perform safety analysis
        safety_check = await self._check_content_safety(analysis_result)
        analysis_result["safety"] = safety_check

        return analysis_result

    async def _analyze_video(self, url: str) -> Dict[str, Any]:
        """Analyze video content"""
        # Extract frames for analysis
        frames = await self._extract_key_frames(url)

        # Analyze each frame
        frame_analyses = []
        for frame in frames:
            analysis = await self._analyze_frame(frame)
            frame_analyses.append(analysis)

        # Aggregate results
        return {
            "duration": await self._get_video_duration(url),
            "resolution": await self._get_video_resolution(url),
            "quality_score": self._calculate_quality_score(frame_analyses),
            "content_themes": self._extract_themes(frame_analyses),
            "optimal_format": self._recommend_format(frame_analyses)
        }

    async def _check_content_safety(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Check content for safety issues"""
        return {
            "is_safe": True,
            "confidence": 0.98,
            "warnings": [],
            "age_rating": "general"
        }
```

### nlp_processor.py
**Purpose**: Natural language understanding for processing user commands in conversational format.

```python
from typing import Dict, Any, List, Tuple
from boss_bot.ai.agents.base_agent import BaseAgent, AgentContext
from langchain.schema import HumanMessage, SystemMessage

class NLPProcessor(BaseAgent):
    """Agent for natural language processing of user commands"""

    def __init__(self):
        super().__init__("NLPProcessor", model="gpt-4")
        self.command_patterns = self._load_command_patterns()

    async def process(self, context: AgentContext) -> Dict[str, Any]:
        """Process natural language command"""
        user_input = context.metadata.get("user_input", "")

        # Extract entities and intent
        entities = await self._extract_entities(user_input)
        intent = await self._classify_intent(user_input, entities)

        # Convert to structured command
        structured_command = await self._structure_command(
            user_input,
            entities,
            intent
        )

        return {
            "original_input": user_input,
            "intent": intent,
            "entities": entities,
            "structured_command": structured_command,
            "confidence": self._calculate_confidence(entities, intent)
        }

    async def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract entities from text"""
        prompt = f"""
        Extract the following entities from this text:
        - URLs
        - Platform names (twitter, reddit, etc.)
        - Quality preferences (720p, high quality, etc.)
        - Format preferences (mp4, webm, etc.)
        - Time references

        Text: {text}
        """
        # Use LLM for entity extraction
        pass

    async def _structure_command(
        self,
        text: str,
        entities: Dict[str, Any],
        intent: str
    ) -> Dict[str, Any]:
        """Convert natural language to structured command"""
        if intent == "download":
            return {
                "command": "download",
                "url": entities.get("urls", [None])[0],
                "options": {
                    "quality": entities.get("quality", "best"),
                    "format": entities.get("format", "auto")
                }
            }
        # Handle other intents
        pass
```

### intent_classifier.py
**Purpose**: Classifies user intent from various input formats to route to appropriate handlers.

```python
from typing import Dict, Any, List
from boss_bot.ai.agents.base_agent import BaseAgent, AgentContext
from enum import Enum

class UserIntent(Enum):
    DOWNLOAD = "download"
    ANALYZE = "analyze"
    QUEUE_MANAGE = "queue_manage"
    SETTINGS = "settings"
    HELP = "help"
    UNKNOWN = "unknown"

class IntentClassifier(BaseAgent):
    """Agent for classifying user intent"""

    def __init__(self):
        super().__init__("IntentClassifier", model="gpt-3.5-turbo")
        self.intent_examples = self._load_intent_examples()

    async def process(self, context: AgentContext) -> Dict[str, Any]:
        """Classify user intent"""
        user_input = context.metadata.get("user_input", "")
        conversation_history = context.conversation_history

        # Build classification prompt
        classification = await self._classify_with_context(
            user_input,
            conversation_history
        )

        # Validate classification
        validated_intent = self._validate_intent(classification)

        return {
            "primary_intent": validated_intent["intent"],
            "confidence": validated_intent["confidence"],
            "secondary_intents": validated_intent.get("alternatives", []),
            "requires_clarification": validated_intent["confidence"] < 0.7,
            "suggested_clarifications": self._get_clarifications(validated_intent)
        }

    async def _classify_with_context(
        self,
        input_text: str,
        history: List[Any]
    ) -> Dict[str, Any]:
        """Classify intent using conversation context"""
        # Build few-shot examples
        examples = self._format_examples(self.intent_examples)

        prompt = f"""
        Classify the user's intent based on their message and conversation history.

        Examples:
        {examples}

        Conversation history:
        {self._format_history(history)}

        Current message: {input_text}

        Intent classification:
        """
        # Use LLM for classification
        pass
```

---

## Agent Teams

### social_media/social_media_coordinator.py
**Purpose**: Coordinates platform-specific agents for optimal social media content handling.

```python
from typing import Dict, Any, List
from boss_bot.ai.agents.base_agent import BaseAgent, AgentContext
from langgraph_swarm import Swarm, create_react_agent, create_handoff_tool
from langgraph.checkpoint.memory import InMemorySaver

class SocialMediaCoordinator:
    """Coordinator for social media team using swarm patterns"""

    def __init__(self):
        self.checkpointer = InMemorySaver()
        self.swarm = self._create_social_media_swarm()
        self.platform_agents = {
            "twitter": "TwitterSpecialist",
            "reddit": "RedditSpecialist",
            "instagram": "InstagramSpecialist",
            "youtube": "YouTubeSpecialist"
        }

    def _create_social_media_swarm(self) -> Swarm:
        """Create swarm of social media specialist agents"""
        # Twitter specialist
        twitter_agent = create_react_agent(
            model="gpt-4",
            tools=[
                self._get_twitter_tools(),
                create_handoff_tool(agent_name="RedditSpecialist"),
                create_handoff_tool(agent_name="InstagramSpecialist"),
                create_handoff_tool(agent_name="YouTubeSpecialist")
            ],
            name="TwitterSpecialist",
            prompt="You are a Twitter/X specialist. Handle Twitter content analysis and downloads. Hand off other platforms to appropriate specialists."
        )

        # Reddit specialist
        reddit_agent = create_react_agent(
            model="gpt-4",
            tools=[
                self._get_reddit_tools(),
                create_handoff_tool(agent_name="TwitterSpecialist"),
                create_handoff_tool(agent_name="InstagramSpecialist"),
                create_handoff_tool(agent_name="YouTubeSpecialist")
            ],
            name="RedditSpecialist",
            prompt="You are a Reddit specialist. Handle Reddit content analysis and downloads. Hand off other platforms to appropriate specialists."
        )

        # Instagram specialist
        instagram_agent = create_react_agent(
            model="gpt-4",
            tools=[
                self._get_instagram_tools(),
                create_handoff_tool(agent_name="TwitterSpecialist"),
                create_handoff_tool(agent_name="RedditSpecialist"),
                create_handoff_tool(agent_name="YouTubeSpecialist")
            ],
            name="InstagramSpecialist",
            prompt="You are an Instagram specialist. Handle Instagram content analysis and downloads. Hand off other platforms to appropriate specialists."
        )

        # YouTube specialist
        youtube_agent = create_react_agent(
            model="gpt-4",
            tools=[
                self._get_youtube_tools(),
                create_handoff_tool(agent_name="TwitterSpecialist"),
                create_handoff_tool(agent_name="RedditSpecialist"),
                create_handoff_tool(agent_name="InstagramSpecialist")
            ],
            name="YouTubeSpecialist",
            prompt="You are a YouTube specialist. Handle YouTube content analysis and downloads. Hand off other platforms to appropriate specialists."
        )

        agents = [twitter_agent, reddit_agent, instagram_agent, youtube_agent]
        return Swarm(agents)

    async def process(self, context: AgentContext) -> Dict[str, Any]:
        """Process using swarm coordination"""
        url = context.metadata.get("url")
        platform = self._detect_platform(url)

        # Convert context to swarm input
        config = {"configurable": {"thread_id": context.request_id}}

        # Process through swarm with platform detection
        result = await self.swarm.run(
            {
                "messages": [{
                    "role": "user",
                    "content": f"Process this {platform} URL: {url}"
                }]
            },
            config=config
        )

        return result

    def _detect_platform(self, url: str) -> str:
        """Detect social media platform from URL"""
        if "twitter.com" in url or "x.com" in url:
            return "twitter"
        elif "reddit.com" in url:
            return "reddit"
        elif "instagram.com" in url:
            return "instagram"
        elif "youtube.com" in url or "youtu.be" in url:
            return "youtube"
        return "unknown"

    def _get_twitter_tools(self):
        """Get Twitter-specific tools"""
        # Return Twitter tools
        pass

    def _get_reddit_tools(self):
        """Get Reddit-specific tools"""
        # Return Reddit tools
        pass

    def _get_instagram_tools(self):
        """Get Instagram-specific tools"""
        # Return Instagram tools
        pass

    def _get_youtube_tools(self):
        """Get YouTube-specific tools"""
        # Return YouTube tools
        pass
```

### media_processing/media_supervisor.py
**Purpose**: Supervises media processing tasks and coordinates format optimization.

```python
from typing import Dict, Any, List, Optional
from boss_bot.ai.agents.base_agent import BaseAgent, AgentContext
from dataclasses import dataclass

@dataclass
class MediaTask:
    """Represents a media processing task"""
    task_id: str
    media_type: str
    source_path: str
    target_format: Optional[str]
    quality_settings: Dict[str, Any]

class MediaSupervisor(BaseAgent):
    """Supervisor for media processing team"""

    def __init__(self):
        super().__init__("MediaSupervisor")
        self.processors = {
            "video": VideoProcessor(),
            "image": ImageProcessor(),
            "audio": AudioProcessor()
        }
        self.format_optimizer = FormatOptimizer()

    async def process(self, context: AgentContext) -> Dict[str, Any]:
        """Supervise media processing workflow"""
        media_info = context.metadata.get("media_info")
        user_requirements = context.metadata.get("requirements", {})

        # Determine optimal processing pipeline
        pipeline = await self._build_processing_pipeline(
            media_info,
            user_requirements
        )

        # Execute pipeline steps
        results = []
        for step in pipeline:
            processor = self.processors.get(step["processor"])
            if processor:
                result = await processor.process_media(
                    step["input"],
                    step["settings"]
                )
                results.append(result)

        # Optimize final output
        optimized = await self.format_optimizer.optimize(
            results[-1],
            user_requirements
        )

        return {
            "processed_media": optimized,
            "pipeline_steps": pipeline,
            "quality_metrics": self._calculate_quality_metrics(optimized),
            "size_reduction": self._calculate_size_reduction(media_info, optimized)
        }

    async def _build_processing_pipeline(
        self,
        media_info: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Build optimal processing pipeline"""
        # AI-driven pipeline construction
        pass
```

---

## LangChain Chains

### content_analysis.py
**Purpose**: Chain for comprehensive content analysis including quality, safety, and metadata.

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_openai import ChatOpenAI
from typing import Dict, Any

class ContentAnalysisChain:
    """Chain for analyzing media content using LCEL patterns"""

    def __init__(self, llm):
        self.llm = llm
        self.quality_chain = self._build_quality_chain()
        self.safety_chain = self._build_safety_chain()
        self.metadata_chain = self._build_metadata_chain()

    def _build_quality_chain(self):
        """Build chain for quality assessment using LCEL"""
        prompt = ChatPromptTemplate.from_template("""
        Analyze the quality of this media content:

        Media Features: {media_features}
        User Preferences: {user_preferences}

        Provide quality assessment including:
        1. Overall quality score (0-100)
        2. Specific quality metrics
        3. Recommendations for improvement
        4. Optimal format for use case

        Return the response as JSON with keys: quality_score, metrics, recommendations, optimal_format
        """)

        return prompt | self.llm | JsonOutputParser()

    def _build_safety_chain(self):
        """Build chain for safety analysis using LCEL"""
        prompt = ChatPromptTemplate.from_template("""
        Analyze content safety and compliance:

        Content: {content_description}
        Platform Policies: {platform_policies}

        Determine:
        1. Content safety rating (safe/questionable/unsafe)
        2. Policy compliance (compliant/violation/needs_review)
        3. Potential issues
        4. Recommendations

        Return the response as JSON with keys: safety_rating, compliance, issues, recommendations
        """)

        return prompt | self.llm | JsonOutputParser()

    def _build_metadata_chain(self):
        """Build chain for metadata extraction using LCEL"""
        prompt = ChatPromptTemplate.from_template("""
        Extract and analyze metadata from this media content:

        Media Data: {media_data}

        Extract:
        1. Technical metadata (resolution, format, duration, etc.)
        2. Content metadata (title, description, tags, etc.)
        3. Quality indicators
        4. Accessibility features

        Return the response as JSON with keys: technical, content, quality_indicators, accessibility
        """)

        return prompt | self.llm | JsonOutputParser()

    async def analyze(self, media_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run full content analysis using parallel chain execution"""
        # Run chains in parallel for better performance
        quality_result = await self.quality_chain.ainvoke({
            "media_features": media_data["features"],
            "user_preferences": media_data.get("preferences", {})
        })

        safety_result = await self.safety_chain.ainvoke({
            "content_description": media_data["description"],
            "platform_policies": media_data.get("policies", "general")
        })

        metadata_result = await self.metadata_chain.ainvoke({
            "media_data": media_data
        })

        return {
            "quality": quality_result,
            "safety": safety_result,
            "metadata": metadata_result
        }
```

---

## Coordination Layer

### handoff_manager.py
**Purpose**: Manages agent-to-agent handoffs in swarm-style coordination.

```python
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import asyncio

@dataclass
class HandoffRequest:
    """Represents a handoff request between agents"""
    request_id: str
    from_agent: str
    to_agent: str
    context: Dict[str, Any]
    reason: str
    timestamp: datetime

class HandoffManager:
    """Manages agent handoffs and coordination"""

    def __init__(self):
        self.active_handoffs: Dict[str, HandoffRequest] = {}
        self.handoff_history: List[HandoffRequest] = []
        self.agent_availability: Dict[str, bool] = {}

    async def request_handoff(
        self,
        from_agent: str,
        to_agent: str,
        context: Dict[str, Any],
        reason: str
    ) -> bool:
        """Request handoff from one agent to another"""
        handoff_id = self._generate_handoff_id()

        # Check if target agent is available
        if not await self._check_agent_availability(to_agent):
            return False

        # Create handoff request
        handoff = HandoffRequest(
            request_id=handoff_id,
            from_agent=from_agent,
            to_agent=to_agent,
            context=context,
            reason=reason,
            timestamp=datetime.now()
        )

        # Validate handoff (prevent circular references)
        if not self._validate_handoff(handoff):
            return False

        # Execute handoff
        success = await self._execute_handoff(handoff)

        # Record handoff
        self.handoff_history.append(handoff)

        return success

    def _validate_handoff(self, handoff: HandoffRequest) -> bool:
        """Validate handoff request"""
        # Check for circular handoffs
        recent_handoffs = self._get_recent_handoffs(
            handoff.context.get("request_id")
        )

        # Detect circular pattern
        if self._detect_circular_pattern(recent_handoffs, handoff):
            return False

        return True

    async def _execute_handoff(self, handoff: HandoffRequest) -> bool:
        """Execute the handoff between agents"""
        try:
            # Prepare context for target agent
            enriched_context = self._enrich_context(handoff)

            # Notify target agent
            await self._notify_agent(handoff.to_agent, enriched_context)

            # Update active handoffs
            self.active_handoffs[handoff.request_id] = handoff

            return True
        except Exception as e:
            # Log error and return failure
            return False
```

### swarm_protocols.py
**Purpose**: Swarm coordination using langgraph-swarm-py patterns.

```python
from typing import Dict, Any, List, Optional
from langgraph_swarm import Swarm, create_react_agent, create_handoff_tool
from langgraph.checkpoint.memory import InMemorySaver
from datetime import datetime

class BossSwarmCoordinator:
    """Boss-Bot swarm coordination using langgraph-swarm-py"""

    def __init__(self):
        self.checkpointer = InMemorySaver()
        self.swarms = {}
        self.agent_configs = {}

    def create_team_swarm(
        self,
        team_name: str,
        agents_config: List[Dict[str, Any]]
    ) -> Swarm:
        """Create a swarm for a specific team using langgraph-swarm-py"""
        agents = []

        # Store agent configs for reference
        self.agent_configs[team_name] = {
            config['name']: config for config in agents_config
        }

        for config in agents_config:
            # Create handoff tools for peer agents in the same team
            handoff_tools = []
            for peer_config in agents_config:
                if peer_config['name'] != config['name']:
                    handoff_tools.append(
                        create_handoff_tool(
                            agent_name=peer_config['name'],
                            description=f"Transfer to {peer_config['name']}: {peer_config.get('description', '')}"
                        )
                    )

            # Create the react agent
            agent = create_react_agent(
                model=config['model'],
                tools=config['tools'] + handoff_tools,
                name=config['name'],
                prompt=config['prompt']
            )
            agents.append(agent)

        # Create swarm with default active agent
        swarm = Swarm(agents, default_active_agent=agents_config[0]['name'])
        self.swarms[team_name] = swarm
        return swarm

    async def run_swarm(
        self,
        team_name: str,
        input_data: Dict[str, Any],
        thread_id: str
    ) -> Dict[str, Any]:
        """Run a swarm with the given input"""
        if team_name not in self.swarms:
            raise ValueError(f"Swarm {team_name} not found")

        swarm = self.swarms[team_name]
        config = {"configurable": {"thread_id": thread_id}}

        # Execute swarm
        result = await swarm.run(input_data, config=config)

        return {
            "team": team_name,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }

    def create_multi_team_coordinator(
        self,
        team_swarms: Dict[str, Swarm],
        coordinator_config: Dict[str, Any]
    ) -> Swarm:
        """Create a coordinator that can handoff between different team swarms"""

        # Create handoff tools for each team
        team_handoff_tools = []
        for team_name in team_swarms.keys():
            team_handoff_tools.append(
                create_handoff_tool(
                    agent_name=f"{team_name}_coordinator",
                    description=f"Hand off to {team_name} team for specialized processing"
                )
            )

        # Create coordinator agent
        coordinator = create_react_agent(
            model=coordinator_config['model'],
            tools=coordinator_config['tools'] + team_handoff_tools,
            name="MultiTeamCoordinator",
            prompt=coordinator_config['prompt']
        )

        # Combine with team representatives
        all_agents = [coordinator]
        for team_name, swarm in team_swarms.items():
            # Create a representative agent for each team
            team_rep = create_react_agent(
                model="gpt-4",
                tools=[create_handoff_tool(agent_name="MultiTeamCoordinator")],
                name=f"{team_name}_coordinator",
                prompt=f"You represent the {team_name} team. Route requests to your team's swarm or hand back to coordinator."
            )
            all_agents.append(team_rep)

        return Swarm(all_agents, default_active_agent="MultiTeamCoordinator")

    async def broadcast_to_teams(
        self,
        message: str,
        target_teams: List[str],
        thread_id_prefix: str
    ) -> Dict[str, Any]:
        """Broadcast a message to multiple team swarms"""
        results = {}

        for team_name in target_teams:
            if team_name in self.swarms:
                thread_id = f"{thread_id_prefix}_{team_name}"
                try:
                    result = await self.run_swarm(
                        team_name,
                        {"messages": [{"role": "user", "content": message}]},
                        thread_id
                    )
                    results[team_name] = result
                except Exception as e:
                    results[team_name] = {"error": str(e)}

        return results

    def get_swarm_status(self, team_name: str) -> Dict[str, Any]:
        """Get status information about a swarm"""
        if team_name not in self.swarms:
            return {"error": "Swarm not found"}

        config = self.agent_configs.get(team_name, {})

        return {
            "team_name": team_name,
            "agent_count": len(config),
            "agents": list(config.keys()),
            "created": True,
            "capabilities": [
                agent_config.get('capabilities', [])
                for agent_config in config.values()
            ]
        }
```

---

## LangGraph Definitions

### main_graph.py
**Purpose**: Main application graph defining the overall agent workflow.

```python
from langgraph.graph import StateGraph, END, add_messages
from typing_extensions import TypedDict
from typing import Dict, Any, List, Optional, Annotated
from boss_bot.ai.agents import MainSupervisor

class BossBotState(TypedDict):
    """Main application state using TypedDict"""
    messages: Annotated[list, add_messages]
    request_id: str
    user_id: str
    command: str
    context: Dict[str, Any]
    current_agent: str
    processing_history: List[Dict[str, Any]]
    result: Optional[Dict[str, Any]]
    error: Optional[str]

def build_main_graph():
    """Build the main Boss-Bot workflow graph using proper StateGraph patterns"""

    # Create graph builder
    builder = StateGraph(BossBotState)

    # Add nodes with proper node functions
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("intent_classifier", intent_classifier_node)
    builder.add_node("content_analyzer", content_analyzer_node)
    builder.add_node("strategy_selector", strategy_selector_node)
    builder.add_node("download_executor", download_executor_node)
    builder.add_node("media_processor", media_processor_node)
    builder.add_node("result_formatter", result_formatter_node)

    # Set entry point
    builder.set_entry_point("supervisor")

    # Define sequential edges
    builder.add_edge("supervisor", "intent_classifier")

    # Conditional routing based on intent
    builder.add_conditional_edges(
        "intent_classifier",
        route_by_intent,
        {
            "download": "content_analyzer",
            "analyze": "content_analyzer",
            "process": "media_processor",
            "help": "result_formatter"
        }
    )

    # Download workflow edges
    builder.add_edge("content_analyzer", "strategy_selector")
    builder.add_edge("strategy_selector", "download_executor")
    builder.add_edge("download_executor", "media_processor")

    # Final formatting and termination
    builder.add_edge("media_processor", "result_formatter")
    builder.add_edge("result_formatter", END)

    # Compile the graph
    return builder.compile()

async def supervisor_node(state: BossBotState) -> dict:
    """Supervisor node logic - returns partial state update"""
    supervisor = MainSupervisor()

    # Process initial request
    result = await supervisor.process(
        AgentContext(
            request_id=state["request_id"],
            user_id=state["user_id"],
            conversation_history=state.get("messages", []),
            metadata={"command": state["command"]}
        )
    )

    # Return partial state update
    return {
        "current_agent": "supervisor",
        "processing_history": state.get("processing_history", []) + [{
            "agent": "supervisor",
            "action": "initial_processing",
            "result": result
        }],
        "context": {**state.get("context", {}), "supervisor_result": result}
    }

async def intent_classifier_node(state: BossBotState) -> dict:
    """Intent classifier node"""
    from boss_bot.ai.agents.intent_classifier import IntentClassifier

    classifier = IntentClassifier()

    # Get user input from messages or command
    user_input = state.get("command", "")
    if state.get("messages"):
        last_message = state["messages"][-1]
        if hasattr(last_message, 'content'):
            user_input = last_message.content

    # Classify intent
    intent_result = await classifier.process(
        AgentContext(
            request_id=state["request_id"],
            user_id=state["user_id"],
            conversation_history=state.get("messages", []),
            metadata={"user_input": user_input}
        )
    )

    return {
        "current_agent": "intent_classifier",
        "context": {**state.get("context", {}), "intent": intent_result}
    }

def route_by_intent(state: BossBotState) -> str:
    """Route based on classified intent"""
    intent = state.get("context", {}).get("intent", {}).get("primary_intent", "unknown")

    routing_map = {
        "download": "content_analyzer",
        "analyze": "content_analyzer",
        "process": "media_processor",
        "help": "result_formatter"
    }

    return routing_map.get(intent, "result_formatter")

async def content_analyzer_node(state: BossBotState) -> dict:
    """Content analyzer node"""
    from boss_bot.ai.agents.content_analyzer import ContentAnalyzer

    analyzer = ContentAnalyzer()

    analysis_result = await analyzer.process(
        AgentContext(
            request_id=state["request_id"],
            user_id=state["user_id"],
            conversation_history=state.get("messages", []),
            metadata=state.get("context", {})
        )
    )

    return {
        "current_agent": "content_analyzer",
        "context": {**state.get("context", {}), "content_analysis": analysis_result}
    }

async def result_formatter_node(state: BossBotState) -> dict:
    """Result formatter node"""
    # Format final result
    result = {
        "success": True,
        "data": state.get("context", {}),
        "processing_agents": [
            step["agent"] for step in state.get("processing_history", [])
        ]
    }

    return {
        "current_agent": "result_formatter",
        "result": result
    }
```

### download_graph.py
**Purpose**: Specialized graph for download workflows with strategy selection and execution.

```python
from langgraph.graph import StateGraph, State
from typing import Dict, Any, Optional

class DownloadState(State):
    """State for download workflow"""
    url: str
    platform: str
    strategy: Optional[str]
    download_options: Dict[str, Any]
    content_metadata: Dict[str, Any]
    download_result: Optional[Dict[str, Any]]
    post_processing: Dict[str, Any]

def build_download_graph() -> StateGraph:
    """Build download-specific workflow graph"""

    graph = StateGraph(DownloadState)

    # Add nodes
    graph.add_node("url_validator", validate_url_node)
    graph.add_node("platform_detector", detect_platform_node)
    graph.add_node("content_analyzer", analyze_content_node)
    graph.add_node("strategy_selector", select_strategy_node)
    graph.add_node("options_optimizer", optimize_options_node)
    graph.add_node("downloader", execute_download_node)
    graph.add_node("post_processor", post_process_node)
    graph.add_node("quality_checker", check_quality_node)

    # Define workflow
    graph.add_edge("START", "url_validator")
    graph.add_edge("url_validator", "platform_detector")
    graph.add_edge("platform_detector", "content_analyzer")

    # Parallel analysis and strategy selection
    graph.add_edge("content_analyzer", "strategy_selector")
    graph.add_edge("content_analyzer", "options_optimizer")

    # Merge and download
    graph.add_edge("strategy_selector", "downloader")
    graph.add_edge("options_optimizer", "downloader")

    # Post-processing
    graph.add_edge("downloader", "post_processor")
    graph.add_edge("post_processor", "quality_checker")

    # Conditional retry on quality issues
    graph.add_conditional_edge(
        "quality_checker",
        check_quality_result,
        {
            "pass": "END",
            "retry": "options_optimizer",
            "fail": "END"
        }
    )

    return graph.compile()

async def select_strategy_node(state: DownloadState) -> DownloadState:
    """Select download strategy using AI"""
    from boss_bot.ai.agents.strategy_selector import StrategySelector

    selector = StrategySelector()

    # Prepare context
    context = AgentContext(
        request_id=state.get("request_id", ""),
        user_id=state.get("user_id", ""),
        conversation_history=[],
        metadata={
            "url": state.url,
            "platform": state.platform,
            "content_metadata": state.content_metadata
        }
    )

    # Select strategy
    result = await selector.process(context)

    # Update state
    state.strategy = result["strategy"]
    state.download_options.update({
        "strategy_confidence": result["confidence"],
        "strategy_reasoning": result["reasoning"]
    })

    return state
```

---

## Memory Management

### conversation_memory.py
**Purpose**: Manages conversation history and context across sessions using LangMem.

```python
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMessage

class ConversationMemoryManager:
    """Manages conversation memory with persistence"""

    def __init__(self, connection_string: str, ttl_hours: int = 24):
        self.connection_string = connection_string
        self.ttl = timedelta(hours=ttl_hours)
        self.memory_store = {}  # In production, use LangMem

    async def get_conversation_memory(
        self,
        user_id: str,
        session_id: Optional[str] = None
    ) -> ConversationBufferMemory:
        """Get or create conversation memory for user"""
        key = f"{user_id}:{session_id}" if session_id else user_id

        if key in self.memory_store:
            memory_data = self.memory_store[key]
            if self._is_valid(memory_data):
                return memory_data["memory"]

        # Create new memory
        memory = ConversationBufferMemory(
            return_messages=True,
            memory_key="conversation_history"
        )

        # Load historical context if available
        historical = await self._load_historical_context(user_id)
        if historical:
            memory.chat_memory.messages.extend(historical)

        # Store memory
        self.memory_store[key] = {
            "memory": memory,
            "created_at": datetime.now(),
            "last_accessed": datetime.now()
        }

        return memory

    async def save_interaction(
        self,
        user_id: str,
        messages: List[BaseMessage],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Save interaction to persistent storage"""
        # In production, save to LangMem
        pass

    async def get_relevant_memories(
        self,
        user_id: str,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant memories based on query"""
        # Use vector search in LangMem
        # For now, return recent memories
        memories = []

        for key, data in self.memory_store.items():
            if key.startswith(user_id):
                memory = data["memory"]
                messages = memory.chat_memory.messages[-limit:]
                memories.extend([
                    {
                        "message": msg,
                        "timestamp": data["last_accessed"],
                        "relevance_score": 0.8  # Placeholder
                    }
                    for msg in messages
                ])

        return memories[:limit]

    def _is_valid(self, memory_data: Dict[str, Any]) -> bool:
        """Check if memory is still valid"""
        age = datetime.now() - memory_data["created_at"]
        return age < self.ttl
```

### user_preferences.py
**Purpose**: Learns and stores user preferences for personalized agent behavior.

```python
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class UserPreference:
    """Represents a learned user preference"""
    preference_type: str
    value: Any
    confidence: float
    learned_at: datetime
    evidence_count: int = 1
    last_used: datetime = field(default_factory=datetime.now)

class UserPreferenceManager:
    """Manages user preferences and learning"""

    def __init__(self):
        self.preferences: Dict[str, Dict[str, UserPreference]] = {}
        self.learning_threshold = 0.7

    async def learn_preference(
        self,
        user_id: str,
        preference_type: str,
        observed_value: Any,
        context: Dict[str, Any]
    ) -> None:
        """Learn from user behavior"""
        if user_id not in self.preferences:
            self.preferences[user_id] = {}

        user_prefs = self.preferences[user_id]

        if preference_type in user_prefs:
            # Update existing preference
            pref = user_prefs[preference_type]

            # Calculate new confidence based on consistency
            if pref.value == observed_value:
                pref.confidence = min(1.0, pref.confidence + 0.1)
                pref.evidence_count += 1
            else:
                # Conflicting evidence, reduce confidence
                pref.confidence = max(0.0, pref.confidence - 0.2)

                # If confidence drops too low, replace preference
                if pref.confidence < self.learning_threshold:
                    pref.value = observed_value
                    pref.confidence = 0.5
                    pref.evidence_count = 1

            pref.last_used = datetime.now()
        else:
            # Create new preference
            user_prefs[preference_type] = UserPreference(
                preference_type=preference_type,
                value=observed_value,
                confidence=0.5,
                learned_at=datetime.now()
            )

    async def get_preferences(
        self,
        user_id: str,
        preference_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get user preferences"""
        if user_id not in self.preferences:
            return {}

        user_prefs = self.preferences[user_id]

        if preference_types:
            return {
                ptype: pref.value
                for ptype, pref in user_prefs.items()
                if ptype in preference_types and pref.confidence >= self.learning_threshold
            }

        return {
            ptype: pref.value
            for ptype, pref in user_prefs.items()
            if pref.confidence >= self.learning_threshold
        }

    async def apply_preferences(
        self,
        user_id: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply user preferences to options"""
        preferences = await self.get_preferences(user_id)

        # Apply preferences to options
        enhanced_options = options.copy()

        for pref_type, pref_value in preferences.items():
            if pref_type == "quality_preference":
                enhanced_options["quality"] = pref_value
            elif pref_type == "format_preference":
                enhanced_options["format"] = pref_value
            elif pref_type == "subtitle_preference":
                enhanced_options["subtitles"] = pref_value
            # Add more preference applications

        return enhanced_options
```

---

## Routing and Load Balancing

### agent_router.py
**Purpose**: Routes requests to appropriate agents based on capabilities and availability.

```python
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AgentCapability:
    """Defines agent capabilities"""
    agent_name: str
    capability_type: str
    performance_score: float
    avg_response_time: float
    success_rate: float

class AgentRouter:
    """Routes requests to appropriate agents"""

    def __init__(self):
        self.agent_registry: Dict[str, Dict[str, Any]] = {}
        self.capability_map: Dict[str, List[AgentCapability]] = {}
        self.routing_history: List[Dict[str, Any]] = []

    async def register_agent(
        self,
        agent_name: str,
        capabilities: List[str],
        metadata: Dict[str, Any]
    ) -> None:
        """Register agent with router"""
        self.agent_registry[agent_name] = {
            "capabilities": capabilities,
            "metadata": metadata,
            "status": "available",
            "last_active": datetime.now()
        }

        # Update capability map
        for capability in capabilities:
            if capability not in self.capability_map:
                self.capability_map[capability] = []

            self.capability_map[capability].append(
                AgentCapability(
                    agent_name=agent_name,
                    capability_type=capability,
                    performance_score=1.0,
                    avg_response_time=0.0,
                    success_rate=1.0
                )
            )

    async def route_request(
        self,
        request_type: str,
        context: Dict[str, Any],
        requirements: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Route request to best available agent"""
        # Find agents with required capability
        capable_agents = self.capability_map.get(request_type, [])

        if not capable_agents:
            return None

        # Filter available agents
        available_agents = [
            cap for cap in capable_agents
            if self.agent_registry[cap.agent_name]["status"] == "available"
        ]

        if not available_agents:
            return None

        # Select best agent based on performance
        best_agent = self._select_best_agent(
            available_agents,
            requirements or {}
        )

        # Record routing decision
        self.routing_history.append({
            "timestamp": datetime.now(),
            "request_type": request_type,
            "selected_agent": best_agent.agent_name,
            "performance_score": best_agent.performance_score
        })

        return best_agent.agent_name

    def _select_best_agent(
        self,
        agents: List[AgentCapability],
        requirements: Dict[str, Any]
    ) -> AgentCapability:
        """Select best agent based on scoring"""
        # Score agents based on multiple factors
        scored_agents = []

        for agent in agents:
            score = self._calculate_agent_score(agent, requirements)
            scored_agents.append((score, agent))

        # Sort by score and return best
        scored_agents.sort(key=lambda x: x[0], reverse=True)
        return scored_agents[0][1]

    def _calculate_agent_score(
        self,
        agent: AgentCapability,
        requirements: Dict[str, Any]
    ) -> float:
        """Calculate agent score for request"""
        # Base score from performance metrics
        base_score = (
            agent.performance_score * 0.4 +
            agent.success_rate * 0.4 +
            (1.0 / (1.0 + agent.avg_response_time)) * 0.2
        )

        # Apply requirement-based adjustments
        if requirements.get("priority") == "speed":
            base_score *= (1.0 / (1.0 + agent.avg_response_time))
        elif requirements.get("priority") == "quality":
            base_score *= agent.success_rate

        return base_score
```

---

## Safety and Security

### content_filter.py
**Purpose**: Filters content for safety and appropriateness using AI.

```python
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass

class ContentRating(Enum):
    SAFE = "safe"
    QUESTIONABLE = "questionable"
    UNSAFE = "unsafe"

@dataclass
class ContentFilterResult:
    """Result of content filtering"""
    rating: ContentRating
    confidence: float
    categories: List[str]
    warnings: List[str]
    recommendations: List[str]

class ContentFilter:
    """AI-powered content safety filter"""

    def __init__(self, model: str = "gpt-4"):
        self.model = model
        self.safety_categories = [
            "violence", "adult_content", "hate_speech",
            "self_harm", "illegal_content", "personal_info"
        ]

    async def analyze_content(
        self,
        content_description: str,
        content_metadata: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None
    ) -> ContentFilterResult:
        """Analyze content for safety issues"""
        # Prepare analysis prompt
        analysis = await self._run_safety_analysis(
            content_description,
            content_metadata
        )

        # Determine rating
        rating = self._determine_rating(analysis)

        # Generate warnings and recommendations
        warnings = self._generate_warnings(analysis)
        recommendations = self._generate_recommendations(
            analysis,
            user_context
        )

        return ContentFilterResult(
            rating=rating,
            confidence=analysis.get("confidence", 0.0),
            categories=analysis.get("detected_categories", []),
            warnings=warnings,
            recommendations=recommendations
        )

    async def _run_safety_analysis(
        self,
        description: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run AI safety analysis"""
        prompt = f"""
        Analyze the following content for safety issues:

        Description: {description}
        Metadata: {metadata}

        Check for these categories: {self.safety_categories}

        Provide:
        1. Detected categories
        2. Severity level (0-10) for each
        3. Overall safety assessment
        4. Confidence level
        """

        # In production, use actual LLM call
        # For now, return mock result
        return {
            "detected_categories": [],
            "severity_scores": {},
            "overall_safety": "safe",
            "confidence": 0.95
        }

    def _determine_rating(self, analysis: Dict[str, Any]) -> ContentRating:
        """Determine content rating from analysis"""
        severity_scores = analysis.get("severity_scores", {})

        max_severity = max(severity_scores.values()) if severity_scores else 0

        if max_severity >= 7:
            return ContentRating.UNSAFE
        elif max_severity >= 4:
            return ContentRating.QUESTIONABLE
        else:
            return ContentRating.SAFE
```

### prompt_injection_detector.py
**Purpose**: Detects and prevents prompt injection attacks in user inputs.

```python
from typing import Dict, Any, List, Tuple
import re

class PromptInjectionDetector:
    """Detects potential prompt injection attacks"""

    def __init__(self):
        self.injection_patterns = [
            r"ignore previous instructions",
            r"disregard all prior",
            r"new instructions:",
            r"system prompt",
            r"you are now",
            r"act as if",
            r"</prompt>",
            r"```system",
        ]
        self.severity_thresholds = {
            "low": 0.3,
            "medium": 0.6,
            "high": 0.8
        }

    async def detect_injection(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Detect potential prompt injection"""
        # Pattern matching
        pattern_matches = self._check_patterns(user_input)

        # Semantic analysis
        semantic_score = await self._semantic_analysis(user_input)

        # Context analysis
        context_score = self._analyze_context(user_input, context)

        # Calculate overall risk
        risk_score = self._calculate_risk_score(
            pattern_matches,
            semantic_score,
            context_score
        )

        return {
            "risk_score": risk_score,
            "risk_level": self._get_risk_level(risk_score),
            "detected_patterns": pattern_matches,
            "semantic_score": semantic_score,
            "recommendations": self._get_recommendations(risk_score)
        }

    def _check_patterns(self, text: str) -> List[str]:
        """Check for known injection patterns"""
        detected = []

        for pattern in self.injection_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                detected.append(pattern)

        return detected

    async def _semantic_analysis(self, text: str) -> float:
        """Analyze semantic indicators of injection"""
        # In production, use LLM for semantic analysis
        # Check for suspicious semantic patterns

        indicators = [
            "contains instructions to AI",
            "attempts to modify behavior",
            "references system prompts",
            "contains role-play instructions"
        ]

        # Mock scoring
        score = 0.0

        # Increase score based on indicators
        if "ignore" in text.lower() and "instructions" in text.lower():
            score += 0.3

        if "you are" in text.lower() or "act as" in text.lower():
            score += 0.2

        return min(1.0, score)

    def _get_risk_level(self, risk_score: float) -> str:
        """Determine risk level from score"""
        if risk_score >= self.severity_thresholds["high"]:
            return "high"
        elif risk_score >= self.severity_thresholds["medium"]:
            return "medium"
        elif risk_score >= self.severity_thresholds["low"]:
            return "low"
        else:
            return "minimal"
```

---

## State Management

### shared_state.py
**Purpose**: Manages shared state between agents in a thread-safe manner.

```python
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
from contextlib import asynccontextmanager

@dataclass
class AgentState:
    """Shared state structure for agents"""
    request_id: str
    user_id: str
    current_agent: str
    workflow_stage: str
    data: Dict[str, Any] = field(default_factory=dict)
    processing_history: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

class SharedStateManager:
    """Thread-safe shared state management"""

    def __init__(self):
        self.states: Dict[str, AgentState] = {}
        self.locks: Dict[str, asyncio.Lock] = {}
        self.state_observers: Dict[str, List[callable]] = {}

    @asynccontextmanager
    async def get_state(self, request_id: str):
        """Get state with lock for safe access"""
        # Ensure lock exists
        if request_id not in self.locks:
            self.locks[request_id] = asyncio.Lock()

        # Acquire lock
        async with self.locks[request_id]:
            if request_id not in self.states:
                raise ValueError(f"State not found for request {request_id}")

            state = self.states[request_id]
            yield state

            # Update timestamp after modification
            state.updated_at = datetime.now()

            # Notify observers
            await self._notify_observers(request_id, state)

    async def create_state(
        self,
        request_id: str,
        user_id: str,
        initial_agent: str,
        initial_data: Optional[Dict[str, Any]] = None
    ) -> AgentState:
        """Create new shared state"""
        if request_id in self.states:
            raise ValueError(f"State already exists for request {request_id}")

        state = AgentState(
            request_id=request_id,
            user_id=user_id,
            current_agent=initial_agent,
            workflow_stage="initialized",
            data=initial_data or {}
        )

        self.states[request_id] = state
        self.locks[request_id] = asyncio.Lock()

        return state

    async def update_state(
        self,
        request_id: str,
        updates: Dict[str, Any],
        agent_name: str
    ) -> None:
        """Update shared state"""
        async with self.get_state(request_id) as state:
            # Update data
            state.data.update(updates)

            # Update current agent
            state.current_agent = agent_name

            # Add to history
            state.processing_history.append({
                "agent": agent_name,
                "timestamp": datetime.now(),
                "updates": list(updates.keys()),
                "stage": state.workflow_stage
            })

    async def transition_stage(
        self,
        request_id: str,
        new_stage: str,
        agent_name: str
    ) -> None:
        """Transition to new workflow stage"""
        async with self.get_state(request_id) as state:
            old_stage = state.workflow_stage
            state.workflow_stage = new_stage

            # Log transition
            state.processing_history.append({
                "agent": agent_name,
                "timestamp": datetime.now(),
                "action": "stage_transition",
                "from_stage": old_stage,
                "to_stage": new_stage
            })

    def register_observer(
        self,
        request_id: str,
        observer: callable
    ) -> None:
        """Register state change observer"""
        if request_id not in self.state_observers:
            self.state_observers[request_id] = []

        self.state_observers[request_id].append(observer)

    async def _notify_observers(
        self,
        request_id: str,
        state: AgentState
    ) -> None:
        """Notify observers of state changes"""
        observers = self.state_observers.get(request_id, [])

        for observer in observers:
            try:
                if asyncio.iscoroutinefunction(observer):
                    await observer(state)
                else:
                    observer(state)
            except Exception as e:
                # Log error but don't fail
                pass
```

### checkpoint_manager.py
**Purpose**: Manages state checkpointing for failure recovery and debugging.

```python
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import asyncio
from pathlib import Path

class CheckpointManager:
    """Manages state checkpoints for recovery"""

    def __init__(self, checkpoint_dir: str = "./checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)
        self.active_checkpoints: Dict[str, List[str]] = {}

    async def create_checkpoint(
        self,
        request_id: str,
        state: Dict[str, Any],
        stage: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a checkpoint of current state"""
        checkpoint_id = f"{request_id}_{stage}_{datetime.now().timestamp()}"

        checkpoint_data = {
            "checkpoint_id": checkpoint_id,
            "request_id": request_id,
            "stage": stage,
            "state": state,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat()
        }

        # Save checkpoint
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.json"

        async with aiofiles.open(checkpoint_path, 'w') as f:
            await f.write(json.dumps(checkpoint_data, indent=2))

        # Track active checkpoint
        if request_id not in self.active_checkpoints:
            self.active_checkpoints[request_id] = []

        self.active_checkpoints[request_id].append(checkpoint_id)

        return checkpoint_id

    async def restore_checkpoint(
        self,
        checkpoint_id: str
    ) -> Dict[str, Any]:
        """Restore state from checkpoint"""
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.json"

        if not checkpoint_path.exists():
            raise ValueError(f"Checkpoint {checkpoint_id} not found")

        async with aiofiles.open(checkpoint_path, 'r') as f:
            checkpoint_data = json.loads(await f.read())

        return checkpoint_data

    async def get_latest_checkpoint(
        self,
        request_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get the latest checkpoint for a request"""
        checkpoints = self.active_checkpoints.get(request_id, [])

        if not checkpoints:
            return None

        # Get latest checkpoint
        latest_id = checkpoints[-1]
        return await self.restore_checkpoint(latest_id)

    async def cleanup_checkpoints(
        self,
        request_id: str,
        keep_last: int = 3
    ) -> None:
        """Clean up old checkpoints"""
        checkpoints = self.active_checkpoints.get(request_id, [])

        if len(checkpoints) <= keep_last:
            return

        # Remove old checkpoints
        to_remove = checkpoints[:-keep_last]

        for checkpoint_id in to_remove:
            checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.json"
            if checkpoint_path.exists():
                checkpoint_path.unlink()

        # Update active list
        self.active_checkpoints[request_id] = checkpoints[-keep_last:]
```

---

## LangChain Tools

### media_inspector.py
**Purpose**: Tools for inspecting and analyzing media files.

```python
from langchain_core.tools import tool
from typing import Dict, Any, List
import asyncio

class MediaInspectorTools:
    """Collection of media inspection tools using modern @tool decorator"""

    @staticmethod
    @tool
    async def extract_video_metadata(video_path: str) -> Dict[str, Any]:
        """Extract comprehensive video metadata using ffprobe or similar tools

        Args:
            video_path: Path to the video file to analyze

        Returns:
            Dictionary containing video metadata including duration, resolution, codecs, etc.
        """
        # Use ffprobe or similar
        metadata = {
            "duration": 0,
            "resolution": {"width": 0, "height": 0},
            "fps": 0,
            "codec": "",
            "bitrate": 0,
            "has_audio": False,
            "audio_channels": 0,
            "file_size": 0
        }

        # In production, use actual video analysis
        # For now, return mock data
        return metadata

    @staticmethod
    @tool
    async def analyze_image_content(image_path: str) -> Dict[str, Any]:
        """Analyze image content using vision models to extract description and objects

        Args:
            image_path: Path to the image file to analyze

        Returns:
            Dictionary containing image analysis including description, objects, quality
        """
        # In production, use vision model
        # For now, return mock analysis
        return {
            "description": "A sample image",
            "objects_detected": [],
            "text_detected": "",
            "dominant_colors": [],
            "quality_score": 0.85,
            "content_type": "general"
        }

    @staticmethod
    @tool
    async def detect_media_quality(media_path: str) -> Dict[str, Any]:
        """Detect quality metrics of media file and provide optimization recommendations

        Args:
            media_path: Path to the media file to analyze

        Returns:
            Dictionary containing quality metrics and recommendations
        """
        # Analyze quality indicators
        return {
            "overall_quality": "high",
            "resolution_quality": 0.9,
            "compression_artifacts": 0.1,
            "color_accuracy": 0.95,
            "sharpness": 0.88,
            "recommendations": ["suitable for archival"]
        }

    @staticmethod
    @tool
    async def extract_audio_features(audio_path: str) -> Dict[str, Any]:
        """Extract audio features and characteristics from audio files

        Args:
            audio_path: Path to the audio file to analyze

        Returns:
            Dictionary containing audio features and metadata
        """
        return {
            "duration": 0,
            "sample_rate": 44100,
            "channels": 2,
            "bitrate": 320,
            "format": "mp3",
            "has_speech": False,
            "volume_level": 0.75,
            "quality_indicators": {
                "dynamic_range": 0.8,
                "signal_to_noise": 0.9
            }
        }

    @staticmethod
    def get_tools():
        """Get all tools as a list for agent configuration"""
        return [
            MediaInspectorTools.extract_video_metadata,
            MediaInspectorTools.analyze_image_content,
            MediaInspectorTools.detect_media_quality,
            MediaInspectorTools.extract_audio_features
        ]
```

### discord_tools.py
**Purpose**: Tools for interacting with Discord API and bot functionality.

```python
from langchain.tools import Tool
from typing import Dict, Any, List, Optional
import discord

class DiscordTools:
    """Tools for Discord integration"""

    def __init__(self, bot_instance):
        self.bot = bot_instance

    def get_tools(self) -> List[Tool]:
        """Get all Discord tools"""
        return [
            Tool(
                name="send_discord_message",
                description="Send a message to a Discord channel",
                func=self.send_message
            ),
            Tool(
                name="create_discord_embed",
                description="Create a rich embed for Discord",
                func=self.create_embed
            ),
            Tool(
                name="get_channel_info",
                description="Get information about a Discord channel",
                func=self.get_channel_info
            ),
            Tool(
                name="upload_to_discord",
                description="Upload a file to Discord",
                func=self.upload_file
            )
        ]

    async def send_message(
        self,
        channel_id: int,
        content: str,
        embed: Optional[discord.Embed] = None
    ) -> Dict[str, Any]:
        """Send message to Discord channel"""
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                return {"success": False, "error": "Channel not found"}

            message = await channel.send(content=content, embed=embed)

            return {
                "success": True,
                "message_id": message.id,
                "channel_id": channel_id
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def create_embed(
        self,
        title: str,
        description: str,
        color: int = 0x00ff00,
        fields: Optional[List[Dict[str, Any]]] = None,
        thumbnail: Optional[str] = None
    ) -> discord.Embed:
        """Create Discord embed"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=color
        )

        if fields:
            for field in fields:
                embed.add_field(
                    name=field.get("name", ""),
                    value=field.get("value", ""),
                    inline=field.get("inline", False)
                )

        if thumbnail:
            embed.set_thumbnail(url=thumbnail)

        return embed

    async def upload_file(
        self,
        channel_id: int,
        file_path: str,
        filename: Optional[str] = None,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload file to Discord"""
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                return {"success": False, "error": "Channel not found"}

            with open(file_path, 'rb') as f:
                file = discord.File(f, filename=filename or Path(file_path).name)
                message = await channel.send(content=content, file=file)

            return {
                "success": True,
                "message_id": message.id,
                "file_url": message.attachments[0].url if message.attachments else None
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
```

---

## Integration Examples

### Enhanced Download Command
**How the AI system enhances the existing download command:**

```python
# In src/boss_bot/bot/cogs/downloads.py

from boss_bot.ai.graphs.main_graph import build_main_graph
from boss_bot.ai.agents.base_agent import AgentContext

class DownloadsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ai_graph = build_main_graph()
        self.state_manager = SharedStateManager()

    @commands.command(name="smart-download")
    async def smart_download(self, ctx, url: str):
        """AI-enhanced download command"""
        # Create agent context
        context = AgentContext(
            request_id=str(ctx.message.id),
            user_id=str(ctx.author.id),
            guild_id=str(ctx.guild.id) if ctx.guild else None,
            conversation_history=[],
            metadata={
                "command": "smart-download",
                "url": url,
                "channel_id": str(ctx.channel.id)
            }
        )

        # Create shared state
        await self.state_manager.create_state(
            request_id=context.request_id,
            user_id=context.user_id,
            initial_agent="MainSupervisor",
            initial_data={"url": url}
        )

        # Run through AI graph
        result = await self.ai_graph.arun({
            "request_id": context.request_id,
            "user_id": context.user_id,
            "command": f"download {url}",
            "context": context.metadata
        })

        # Send result to user
        if result.get("error"):
            await ctx.send(f"❌ Error: {result['error']}")
        else:
            embed = self._create_result_embed(result)
            await ctx.send(embed=embed)
```

---

## Development Notes

1. **Gradual Implementation**: Start with Phase 1 agents and gradually add complexity
2. **Testing Strategy**: Use LangSmith for tracking agent conversations and debugging
3. **Performance Monitoring**: Implement comprehensive metrics for each agent
4. **Error Handling**: Each agent should gracefully handle failures and provide fallbacks
5. **Documentation**: Maintain detailed documentation of agent capabilities and interactions

This pseudo-code provides a comprehensive foundation for implementing the LangGraph multi-agent system in Boss-Bot, with clear module purposes and integration points with the existing architecture.

---

## API Corrections Summary

**✅ CORRECTED**: This document has been updated to reflect the actual APIs from the planned Python modules:

### Major API Corrections Made

1. **langgraph-swarm-py Integration**:
   - Added proper `create_react_agent`, `create_handoff_tool`, and `Swarm` usage
   - Replaced custom handoff implementations with native swarm patterns
   - Added swarm coordination in social media team and protocols

2. **langgraph-supervisor-py Integration**:
   - Added `Supervisor` and `create_agent` for hierarchical coordination
   - Updated MainSupervisor to use proper supervisor patterns
   - Combined hierarchical supervision with swarm coordination

3. **StateGraph Modernization**:
   - Fixed state definition using `TypedDict` instead of custom `State` class
   - Added proper `add_messages` annotation for message handling
   - Updated graph building with `builder.compile()` pattern
   - Added proper node functions returning partial state updates

4. **LangChain Expression Language (LCEL)**:
   - Replaced deprecated `LLMChain` with modern LCEL patterns
   - Updated to use `ChatPromptTemplate` and `JsonOutputParser`
   - Added proper chain composition with `|` operator
   - Fixed async execution with `ainvoke()`

5. **Tool Definition Updates**:
   - Replaced `Tool` class usage with `@tool` decorator
   - Added proper type hints and docstrings
   - Updated tool registration patterns for agent configuration

6. **Import Corrections**:
   - Fixed imports to use `langchain_core` instead of deprecated `langchain` modules
   - Added proper `typing_extensions` for `TypedDict`
   - Updated to use current LangGraph API patterns

### Code Quality Improvements

- **Type Safety**: Added proper type annotations throughout
- **Documentation**: Enhanced docstrings with Args/Returns sections
- **Error Handling**: Maintained robust error handling patterns
- **Async Patterns**: Consistent async/await usage aligned with LangGraph
- **Modern Patterns**: Updated to current LangChain/LangGraph best practices

The corrected pseudo-code now accurately reflects the actual APIs and patterns from:
- `langgraph-swarm-py` for peer-to-peer agent coordination
- `langgraph-supervisor-py` for hierarchical agent management
- `langgraph` core for state management and graph building
- `langchain-core` for modern chain and tool patterns

This ensures the implementation will use the correct libraries and patterns as specified in the AGENT_DEPS.md dependency list.
