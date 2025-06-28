# Boss-Bot LangGraph Agent Interfaces & Communication Protocols

## Overview

This document defines the interfaces, data structures, and communication protocols for Boss-Bot's hybrid hierarchical-swarm LangGraph multi-agent architecture. The design ensures type safety, clear contracts between agents, and efficient inter-agent communication while maintaining compatibility with the existing strategy pattern.

## Core Data Structures

### 1. Agent Request/Response Protocol

```python
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid
from datetime import datetime

class RequestType(Enum):
    """Types of requests that can be processed by agents"""
    DOWNLOAD = "download"
    CONTENT_ANALYSIS = "content_analysis"
    MEDIA_PROCESSING = "media_processing"
    QUALITY_OPTIMIZATION = "quality_optimization"
    STRATEGY_SELECTION = "strategy_selection"
    QUEUE_OPTIMIZATION = "queue_optimization"
    USER_INTERACTION = "user_interaction"

class Priority(Enum):
    """Request priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

@dataclass
class UserContext:
    """User context information for personalized AI decisions"""
    user_id: str
    discord_guild_id: Optional[str] = None
    preferences: Dict[str, Any] = field(default_factory=dict)
    historical_downloads: List[str] = field(default_factory=list)
    quality_preferences: Dict[str, str] = field(default_factory=dict)
    platform_preferences: Dict[str, Any] = field(default_factory=dict)
    ai_opt_in: bool = True

@dataclass
class ContentMetadata:
    """Comprehensive content metadata from analysis"""
    url: str
    platform: str
    content_type: str  # video, image, audio, text
    title: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[float] = None  # seconds
    resolution: Optional[str] = None  # e.g., "1920x1080"
    file_size_estimate: Optional[int] = None  # bytes
    available_qualities: List[str] = field(default_factory=list)
    thumbnails: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    language: Optional[str] = None
    age_rating: Optional[str] = None
    confidence_score: float = 0.0  # 0.0 to 1.0

@dataclass
class ProcessingOptions:
    """Options for media processing operations"""
    target_quality: Optional[str] = None
    target_format: Optional[str] = None
    target_platform: Optional[str] = None  # discord, twitter, etc.
    crop_settings: Optional[Dict[str, Any]] = None
    filters: List[str] = field(default_factory=list)
    optimization_level: str = "balanced"  # fast, balanced, quality
    preserve_metadata: bool = True

@dataclass
class AgentRequest:
    """Standard request structure for all agent communications"""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request_type: RequestType = RequestType.DOWNLOAD
    priority: Priority = Priority.MEDIUM
    user_context: UserContext = field(default_factory=UserContext)
    content_metadata: Optional[ContentMetadata] = None
    processing_options: Optional[ProcessingOptions] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    timeout_seconds: int = 300
    requires_response: bool = True

class ResponseStatus(Enum):
    """Response status indicators"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    HANDOFF_REQUIRED = "handoff_required"

@dataclass
class AgentResponse:
    """Standard response structure for all agent communications"""
    request_id: str
    agent_id: str
    status: ResponseStatus
    data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    confidence_score: float = 1.0
    processing_time: float = 0.0
    next_agent_suggestion: Optional[str] = None
    handoff_context: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
```

### 2. Agent State Management

```python
@dataclass
class AgentState:
    """Shared state across agent workflows"""
    workflow_id: str
    current_agent: str
    previous_agents: List[str] = field(default_factory=list)
    shared_data: Dict[str, Any] = field(default_factory=dict)
    user_context: UserContext = field(default_factory=UserContext)
    content_metadata: Optional[ContentMetadata] = None
    processing_history: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

class StateManager:
    """Thread-safe state management for multi-agent workflows"""

    async def create_state(self, workflow_id: str, initial_context: UserContext) -> AgentState:
        """Create new workflow state"""

    async def update_state(self, workflow_id: str, updates: Dict[str, Any]) -> AgentState:
        """Update workflow state with new data"""

    async def get_state(self, workflow_id: str) -> Optional[AgentState]:
        """Retrieve current workflow state"""

    async def cleanup_state(self, workflow_id: str) -> None:
        """Clean up completed or expired workflow state"""

    async def record_agent_transition(self, workflow_id: str, from_agent: str, to_agent: str, context: Dict[str, Any]) -> None:
        """Record agent handoff for audit trail"""
```

## Agent Interface Definitions

### 1. Base Agent Interface

```python
from abc import ABC, abstractmethod
from typing import AsyncGenerator

class BaseAgent(ABC):
    """Abstract base class for all LangGraph agents"""

    def __init__(self, agent_id: str, config: Dict[str, Any]):
        self.agent_id = agent_id
        self.config = config
        self.state_manager = StateManager()
        self.logger = self._setup_logging()

    @abstractmethod
    async def process_request(self, request: AgentRequest, state: AgentState) -> AgentResponse:
        """Process an incoming request and return response"""
        pass

    @abstractmethod
    async def can_handle_request(self, request: AgentRequest) -> bool:
        """Determine if this agent can handle the given request"""
        pass

    async def validate_request(self, request: AgentRequest) -> bool:
        """Validate request structure and requirements"""
        return True

    async def prepare_handoff(self, target_agent: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context for handoff to another agent"""
        return context

    async def health_check(self) -> Dict[str, Any]:
        """Return agent health status"""
        return {"status": "healthy", "agent_id": self.agent_id}

    def _setup_logging(self):
        """Set up agent-specific logging"""
        pass
```

### 2. Supervisor Agent Interface

```python
class SupervisorAgent(BaseAgent):
    """Base class for supervisor agents that coordinate other agents"""

    def __init__(self, agent_id: str, config: Dict[str, Any], child_agents: List[BaseAgent]):
        super().__init__(agent_id, config)
        self.child_agents = {agent.agent_id: agent for agent in child_agents}
        self.routing_rules = self._load_routing_rules()

    @abstractmethod
    async def route_request(self, request: AgentRequest, state: AgentState) -> str:
        """Determine which child agent should handle the request"""
        pass

    async def coordinate_agents(self, request: AgentRequest, state: AgentState) -> AgentResponse:
        """Coordinate multiple agents for complex workflows"""
        pass

    async def handle_agent_failure(self, failed_agent: str, request: AgentRequest, state: AgentState) -> AgentResponse:
        """Handle failure from child agent"""
        pass

    def _load_routing_rules(self) -> Dict[str, Any]:
        """Load routing rules for request distribution"""
        return {}
```

### 3. Specialized Agent Interfaces

```python
class ContentAnalysisAgent(BaseAgent):
    """Agent for analyzing content before processing"""

    async def analyze_url(self, url: str, user_context: UserContext) -> ContentMetadata:
        """Analyze URL and extract comprehensive metadata"""
        pass

    async def assess_quality_options(self, metadata: ContentMetadata) -> List[str]:
        """Assess available quality options and recommend best choices"""
        pass

    async def detect_content_issues(self, metadata: ContentMetadata) -> List[str]:
        """Detect potential issues with content (age rating, size, etc.)"""
        pass

class StrategySelectionAgent(BaseAgent):
    """Agent for intelligent download strategy selection"""

    async def select_optimal_strategy(self, url: str, user_context: UserContext, content_metadata: ContentMetadata) -> str:
        """Select the best download strategy based on analysis"""
        pass

    async def evaluate_strategy_confidence(self, strategy: str, context: Dict[str, Any]) -> float:
        """Evaluate confidence in strategy selection"""
        pass

    async def suggest_fallback_strategies(self, primary_strategy: str) -> List[str]:
        """Suggest fallback strategies if primary fails"""
        pass

class MediaProcessingAgent(BaseAgent):
    """Agent for media processing operations"""

    async def process_media(self, file_path: str, processing_options: ProcessingOptions) -> str:
        """Process media file according to specified options"""
        pass

    async def optimize_for_platform(self, file_path: str, target_platform: str) -> str:
        """Optimize media for specific platform requirements"""
        pass

    async def extract_thumbnails(self, file_path: str, count: int = 3) -> List[str]:
        """Extract thumbnail images from video content"""
        pass

class QueueOptimizationAgent(BaseAgent):
    """Agent for intelligent queue management"""

    async def prioritize_queue_items(self, queue_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Reorder queue items for optimal processing"""
        pass

    async def predict_processing_time(self, item: Dict[str, Any]) -> float:
        """Predict how long an item will take to process"""
        pass

    async def optimize_batch_processing(self, queue_items: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Group items for efficient batch processing"""
        pass
```

## Communication Protocols

### 1. Inter-Agent Message Protocol

```python
class MessageType(Enum):
    """Types of inter-agent messages"""
    REQUEST = "request"
    RESPONSE = "response"
    HANDOFF = "handoff"
    STATUS_UPDATE = "status_update"
    ERROR_NOTIFICATION = "error_notification"
    HEALTH_CHECK = "health_check"

@dataclass
class AgentMessage:
    """Message structure for inter-agent communication"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MessageType = MessageType.REQUEST
    sender_id: str = ""
    recipient_id: str = ""
    workflow_id: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    requires_ack: bool = True
    timeout_seconds: int = 30

class MessageBus:
    """Event-driven message bus for agent communication"""

    async def send_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Send message to target agent"""
        pass

    async def broadcast_message(self, message: AgentMessage, recipients: List[str]) -> List[AgentMessage]:
        """Broadcast message to multiple agents"""
        pass

    async def subscribe_to_messages(self, agent_id: str, message_types: List[MessageType]) -> AsyncGenerator[AgentMessage, None]:
        """Subscribe to specific message types"""
        pass

    async def acknowledge_message(self, message_id: str, response_data: Dict[str, Any]) -> None:
        """Acknowledge received message"""
        pass
```

### 2. Handoff Protocol

```python
class HandoffType(Enum):
    """Types of agent handoffs"""
    SEQUENTIAL = "sequential"  # Pass to next agent in sequence
    SPECIALIZED = "specialized"  # Hand off to specialist agent
    PARALLEL = "parallel"  # Split work across multiple agents
    ESCALATION = "escalation"  # Escalate to supervisor

@dataclass
class HandoffRequest:
    """Request for agent handoff"""
    handoff_type: HandoffType
    source_agent: str
    target_agent: str
    workflow_id: str
    context: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    priority: Priority = Priority.MEDIUM

class HandoffCoordinator:
    """Coordinates agent handoffs and workflow continuity"""

    async def request_handoff(self, handoff_request: HandoffRequest) -> bool:
        """Request handoff to another agent"""
        pass

    async def validate_handoff(self, handoff_request: HandoffRequest) -> bool:
        """Validate that handoff is appropriate and possible"""
        pass

    async def execute_handoff(self, handoff_request: HandoffRequest) -> AgentResponse:
        """Execute the agent handoff"""
        pass

    async def rollback_handoff(self, workflow_id: str, target_state: str) -> bool:
        """Rollback failed handoff to previous state"""
        pass
```

### 3. Error Handling Protocol

```python
class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AgentError:
    """Standardized error structure"""
    error_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    workflow_id: str = ""
    error_type: str = ""
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    message: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

class ErrorHandler:
    """Centralized error handling for agent workflows"""

    async def handle_agent_error(self, error: AgentError) -> AgentResponse:
        """Handle error from agent and determine recovery strategy"""
        pass

    async def escalate_error(self, error: AgentError) -> None:
        """Escalate error to supervisor or human operator"""
        pass

    async def attempt_recovery(self, error: AgentError, workflow_id: str) -> bool:
        """Attempt automatic recovery from error"""
        pass

    async def fallback_to_traditional(self, request: AgentRequest) -> AgentResponse:
        """Fallback to traditional (non-AI) processing"""
        pass
```

## Specialized Team Interfaces

### 1. Social Media Management Team

```python
class SocialMediaCoordinator(SupervisorAgent):
    """Coordinates social media download and analysis operations"""

    async def analyze_social_content(self, url: str, user_context: UserContext) -> ContentMetadata:
        """Comprehensive social media content analysis"""
        pass

    async def select_download_strategy(self, url: str, analysis: ContentMetadata) -> str:
        """Select optimal download strategy for social media content"""
        pass

    async def optimize_for_sharing(self, content: str, target_platforms: List[str]) -> Dict[str, str]:
        """Optimize content for sharing on different platforms"""
        pass

class PlatformSpecialistAgent(BaseAgent):
    """Base class for platform-specific agents (Twitter, Reddit, etc.)"""

    @property
    @abstractmethod
    def supported_platforms(self) -> List[str]:
        """List of platforms this agent supports"""
        pass

    @abstractmethod
    async def extract_platform_metadata(self, url: str) -> Dict[str, Any]:
        """Extract platform-specific metadata"""
        pass

    @abstractmethod
    async def download_content(self, url: str, quality_settings: Dict[str, Any]) -> str:
        """Download content using platform-specific methods"""
        pass
```

### 2. Media Processing Team

```python
class MediaProcessingCoordinator(SupervisorAgent):
    """Coordinates media processing operations"""

    async def create_processing_plan(self, media_file: str, target_specs: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive processing plan for media"""
        pass

    async def execute_processing_pipeline(self, plan: Dict[str, Any]) -> List[str]:
        """Execute multi-step processing pipeline"""
        pass

    async def quality_assessment(self, original: str, processed: str) -> Dict[str, Any]:
        """Assess quality of processed media"""
        pass

class VideoProcessingAgent(BaseAgent):
    """Specialized agent for video processing"""

    async def transcode_video(self, input_path: str, target_format: str, quality: str) -> str:
        """Transcode video to target format and quality"""
        pass

    async def extract_audio(self, video_path: str) -> str:
        """Extract audio track from video"""
        pass

    async def generate_preview(self, video_path: str, duration: int = 10) -> str:
        """Generate preview clip from video"""
        pass

class ImageProcessingAgent(BaseAgent):
    """Specialized agent for image processing"""

    async def resize_image(self, image_path: str, target_size: tuple) -> str:
        """Resize image to target dimensions"""
        pass

    async def optimize_image(self, image_path: str, target_platform: str) -> str:
        """Optimize image for specific platform"""
        pass

    async def extract_text(self, image_path: str) -> str:
        """Extract text from image using OCR"""
        pass
```

## Integration with Existing Systems

### 1. Strategy Pattern Integration

```python
class AIEnhancedStrategy(BaseDownloadStrategy):
    """Enhanced strategy that integrates with agent system"""

    def __init__(self, platform: str, agent_coordinator: SocialMediaCoordinator):
        super().__init__(platform)
        self.agent_coordinator = agent_coordinator

    async def ai_enhanced_download(self, url: str, user_context: UserContext) -> AgentResponse:
        """Download using AI-enhanced workflow"""

        # Create agent request
        request = AgentRequest(
            request_type=RequestType.DOWNLOAD,
            user_context=user_context,
            payload={"url": url}
        )

        # Process through agent coordinator
        return await self.agent_coordinator.process_request(request, AgentState())

    async def traditional_fallback(self, url: str, **kwargs) -> str:
        """Fallback to traditional download method"""
        return await super().download(url, **kwargs)
```

### 2. Discord Bot Integration

```python
class AIEnhancedDiscordCog(commands.Cog):
    """Discord cog with AI agent integration"""

    def __init__(self, bot, agent_coordinator: MainSupervisor):
        self.bot = bot
        self.agent_coordinator = agent_coordinator

    @commands.command(name="smart-download")
    async def smart_download(self, ctx: commands.Context, url: str, *, options: str = ""):
        """AI-enhanced download command"""

        # Build user context from Discord interaction
        user_context = UserContext(
            user_id=str(ctx.author.id),
            discord_guild_id=str(ctx.guild.id) if ctx.guild else None,
            preferences=await self._load_user_preferences(ctx.author.id)
        )

        # Create and process agent request
        request = AgentRequest(
            request_type=RequestType.DOWNLOAD,
            user_context=user_context,
            payload={"url": url, "discord_context": ctx}
        )

        # Process through main supervisor
        response = await self.agent_coordinator.process_request(request, AgentState())

        # Handle response appropriately
        await self._handle_agent_response(ctx, response)
```

## Performance and Monitoring

### 1. Performance Metrics

```python
@dataclass
class PerformanceMetrics:
    """Performance metrics for agent operations"""
    agent_id: str
    operation_type: str
    start_time: datetime
    end_time: datetime
    success: bool
    input_size: Optional[int] = None
    output_size: Optional[int] = None
    memory_usage: Optional[int] = None
    cpu_usage: Optional[float] = None
    confidence_score: Optional[float] = None

class MetricsCollector:
    """Collects and aggregates performance metrics"""

    async def record_operation(self, metrics: PerformanceMetrics) -> None:
        """Record operation metrics"""
        pass

    async def get_agent_performance(self, agent_id: str, time_window: int = 3600) -> Dict[str, Any]:
        """Get performance summary for agent"""
        pass

    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics"""
        pass
```

### 2. Circuit Breaker Pattern

```python
class CircuitBreaker:
    """Circuit breaker for agent failure protection"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    async def call_agent(self, agent: BaseAgent, request: AgentRequest, state: AgentState) -> AgentResponse:
        """Call agent with circuit breaker protection"""

        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half-open"
            else:
                return AgentResponse(
                    request_id=request.request_id,
                    agent_id=agent.agent_id,
                    status=ResponseStatus.FAILURE,
                    error_message="Agent circuit breaker is open"
                )

        try:
            response = await agent.process_request(request, state)
            if response.status == ResponseStatus.SUCCESS:
                self._on_success()
            else:
                self._on_failure()
            return response

        except Exception as e:
            self._on_failure()
            return AgentResponse(
                request_id=request.request_id,
                agent_id=agent.agent_id,
                status=ResponseStatus.FAILURE,
                error_message=str(e)
            )

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        return (datetime.utcnow() - self.last_failure_time).seconds > self.recovery_timeout

    def _on_success(self) -> None:
        """Reset circuit breaker on successful operation"""
        self.failure_count = 0
        self.state = "closed"

    def _on_failure(self) -> None:
        """Handle failure and update circuit breaker state"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
```

This comprehensive interface design provides a robust foundation for implementing the LangGraph multi-agent architecture while maintaining type safety, clear communication protocols, and integration with Boss-Bot's existing systems. The design emphasizes reliability, observability, and graceful degradation to ensure excellent user experience even during AI system failures.
