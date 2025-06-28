# Boss-Bot LangGraph Multi-Agent Architecture - Entity Relationship Diagram

This document contains the Mermaid Entity Relationship Diagram generated from the `spec.yml` file, visualizing the relationships between all entities in the Boss-Bot LangGraph multi-agent system.

## Entity Relationship Diagram

```mermaid
erDiagram
    WORKFLOW {
        string workflow_id PK
        string request_type
        string current_agent
        list previous_agents
        list processing_history
        list errors
    }

    USER_CONTEXT {
        string user_id PK
        string discord_guild_id
        dict preferences
        bool ai_opt_in
    }

    CONTENT_METADATA {
        string url PK
        string platform
        string content_type
        string title
        float duration
        string resolution
        list available_qualities
        float confidence_score
    }

    PROCESSING_OPTIONS {
        string processing_id PK
        string target_quality
        string target_format
        string target_platform
        string optimization_level
    }

    MAIN_SUPERVISOR {
        string supervisor_id PK
        string name
        string description
    }

    STRATEGY_SELECTOR {
        string selector_id PK
        string name
        string description
    }

    CONTENT_ANALYZER {
        string analyzer_id PK
        string name
        string description
    }

    SOCIAL_MEDIA_COORDINATOR {
        string coordinator_id PK
        string name
        string description
    }

    MEDIA_PROCESSING_COORDINATOR {
        string coordinator_id PK
        string name
        string description
    }

    QUEUE_OPTIMIZER {
        string optimizer_id PK
        string name
        string description
    }

    USER_INTERACTION_COORDINATOR {
        string coordinator_id PK
        string name
        string description
    }

    PLATFORM_SPECIALIST {
        string specialist_id PK
        string name
        string description
        string platform_type
    }

    VIDEO_PROCESSOR {
        string processor_id PK
        string name
        string description
    }

    IMAGE_PROCESSOR {
        string processor_id PK
        string name
        string description
    }

    QUALITY_OPTIMIZER {
        string optimizer_id PK
        string name
        string description
    }

    FALLBACK_HANDLER {
        string handler_id PK
        string name
        string description
    }

    DISCORD_RESPONDER {
        string responder_id PK
        string name
        string description
    }

    WORKFLOW_CONDITIONS {
        string condition_id PK
        string condition_name
        string logic_expression
    }

    CONFIGURATION {
        string config_id PK
        dict feature_flags
        dict integration_settings
        dict models_config
        dict performance_settings
        dict discord_config
        list supported_platforms
        dict media_processing_config
    }

    WORKFLOW_EDGES {
        string edge_id PK
        string from_agent
        string to_agent
        string condition_ref
    }

    %% Primary relationships
    WORKFLOW ||--|| USER_CONTEXT : has
    WORKFLOW ||--|| CONTENT_METADATA : contains
    WORKFLOW ||--|| PROCESSING_OPTIONS : defines
    WORKFLOW ||--o{ WORKFLOW_EDGES : follows

    %% Agent relationships - Main Supervisor orchestrates all
    MAIN_SUPERVISOR ||--o{ STRATEGY_SELECTOR : routes_to
    MAIN_SUPERVISOR ||--o{ CONTENT_ANALYZER : routes_to
    MAIN_SUPERVISOR ||--o{ SOCIAL_MEDIA_COORDINATOR : routes_to
    MAIN_SUPERVISOR ||--o{ MEDIA_PROCESSING_COORDINATOR : routes_to
    MAIN_SUPERVISOR ||--o{ QUEUE_OPTIMIZER : routes_to
    MAIN_SUPERVISOR ||--o{ USER_INTERACTION_COORDINATOR : routes_to

    %% Content Analysis Flow
    CONTENT_ANALYZER ||--o{ STRATEGY_SELECTOR : provides_analysis_to
    CONTENT_ANALYZER ||--o{ QUALITY_OPTIMIZER : informs

    %% Strategy Selection Flow
    STRATEGY_SELECTOR ||--o{ SOCIAL_MEDIA_COORDINATOR : selects_strategy_for
    STRATEGY_SELECTOR ||--o{ PLATFORM_SPECIALIST : directs_to

    %% Social Media Processing Chain
    SOCIAL_MEDIA_COORDINATOR ||--|| PLATFORM_SPECIALIST : coordinates
    PLATFORM_SPECIALIST ||--o{ MEDIA_PROCESSING_COORDINATOR : hands_off_to
    PLATFORM_SPECIALIST ||--o{ FALLBACK_HANDLER : fails_to

    %% Media Processing Chain
    MEDIA_PROCESSING_COORDINATOR ||--o{ VIDEO_PROCESSOR : delegates_to
    MEDIA_PROCESSING_COORDINATOR ||--o{ IMAGE_PROCESSOR : delegates_to
    VIDEO_PROCESSOR ||--|| QUALITY_OPTIMIZER : optimizes_with
    IMAGE_PROCESSOR ||--|| QUALITY_OPTIMIZER : optimizes_with

    %% Queue Management
    QUEUE_OPTIMIZER ||--o{ SOCIAL_MEDIA_COORDINATOR : optimizes_for
    QUEUE_OPTIMIZER ||--|| MAIN_SUPERVISOR : reports_to

    %% User Interaction Flow
    USER_INTERACTION_COORDINATOR ||--|| MAIN_SUPERVISOR : communicates_with
    USER_INTERACTION_COORDINATOR ||--|| DISCORD_RESPONDER : responds_via

    %% Quality and Response Chain
    QUALITY_OPTIMIZER ||--|| DISCORD_RESPONDER : finalizes_to
    QUALITY_OPTIMIZER ||--|| USER_INTERACTION_COORDINATOR : updates

    %% Error Handling
    FALLBACK_HANDLER ||--|| DISCORD_RESPONDER : recovers_to

    %% Swarm-style Dynamic Handoffs
    CONTENT_ANALYZER ||--o{ PLATFORM_SPECIALIST : requests_specialized_analysis
    STRATEGY_SELECTOR ||--|| USER_INTERACTION_COORDINATOR : requires_preferences
    MEDIA_PROCESSING_COORDINATOR ||--|| CONTENT_ANALYZER : requests_quality_assessment

    %% Configuration relationships
    CONFIGURATION ||--o{ WORKFLOW_CONDITIONS : defines
    CONFIGURATION ||--o{ MAIN_SUPERVISOR : configures
    WORKFLOW_EDGES ||--|| WORKFLOW_CONDITIONS : uses

    %% Content and Processing relationships
    CONTENT_METADATA ||--o{ PLATFORM_SPECIALIST : determines_platform_for
    PROCESSING_OPTIONS ||--|| QUALITY_OPTIMIZER : guides
    USER_CONTEXT ||--|| USER_INTERACTION_COORDINATOR : provides_context_to
```

## Diagram Overview

### **Core Data Entities**
- **WORKFLOW**: Central orchestration entity that tracks the overall workflow state
- **USER_CONTEXT**: Discord user data, preferences, and AI opt-in status
- **CONTENT_METADATA**: Media content information including platform, type, and quality data
- **PROCESSING_OPTIONS**: Configuration for target quality, format, and optimization settings

### **Agent Hierarchy**
- **MAIN_SUPERVISOR**: Top-level orchestrator that routes requests to specialized teams
- **Coordinators**: Specialized coordinators for different domains (Social Media, Media Processing, Queue, User Interaction)
- **Specialists**: Platform-specific and processing-specific agents
- **Support Agents**: Quality optimization, error handling, and Discord response formatting

### **Configuration & Control**
- **WORKFLOW_CONDITIONS**: Defines routing logic and decision points
- **CONFIGURATION**: System-wide settings, feature flags, and integration points
- **WORKFLOW_EDGES**: Defines agent communication paths and handoff protocols

### **Relationship Types**

1. **Hierarchical Relationships** (`||--o{`): Main Supervisor routes to specialized agents
2. **One-to-One Coordination** (`||--||`): Direct agent-to-agent coordination
3. **Processing Chains**: Sequential handoffs through the workflow
4. **Swarm-style Handoffs**: Dynamic agent-to-agent communication based on runtime conditions
5. **Configuration Dependencies**: How settings and conditions control workflow behavior

### **Key Features Represented**

- **Hybrid Architecture**: Shows both hierarchical (supervisor-based) and swarm (peer-to-peer) patterns
- **Error Handling**: Fallback mechanisms and recovery paths
- **Dynamic Routing**: Conditional logic for intelligent agent selection
- **Integration Points**: How the system integrates with existing Boss-Bot components
- **State Management**: Shared state across all agents with proper data flow

This diagram serves as a comprehensive reference for understanding the data flow, agent relationships, and architectural patterns in the Boss-Bot LangGraph multi-agent system.
