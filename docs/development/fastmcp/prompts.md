# Prompts

Prompts in FastMCP are templates that help structure conversations with language models. They allow you to create reusable message templates with parameters, making it easy to generate consistent, well-formatted prompts for various tasks.

## Overview

Prompts are functions that return structured messages for language model conversations. They can:

- Accept parameters to customize the generated messages
- Return single messages or conversation threads
- Include various content types (text, images, resources)
- Be used by MCP clients to enhance AI interactions

## Basic Prompts

### Simple String Prompt

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Prompt Server")

@mcp.prompt()
def greeting_prompt() -> str:
    """Generate a friendly greeting."""
    return "Hello! I'm ready to help you with any questions you might have."

@mcp.prompt()
def analysis_prompt() -> str:
    """Prompt for data analysis tasks."""
    return "Please analyze the following data and provide insights, trends, and recommendations."
```

### Parameterized Prompts

```python
@mcp.prompt()
def topic_prompt(topic: str, context: str = "") -> str:
    """Generate a prompt for discussing a specific topic."""
    prompt = f"Let's discuss {topic}."
    if context:
        prompt += f" Here's some relevant context: {context}"
    return prompt

@mcp.prompt()
def writing_prompt(
    style: str,
    audience: str,
    length: int = 500
) -> str:
    """Generate a writing prompt with specific requirements."""
    return f"""
    Please write content in a {style} style for {audience}.
    Target length: approximately {length} words.
    Focus on clarity, engagement, and appropriateness for the target audience.
    """
```

## Message Objects

### Using Message Classes

```python
from mcp.server.fastmcp.prompts import UserMessage, AssistantMessage

@mcp.prompt()
def conversation_starter() -> list[UserMessage]:
    """Create a conversation starter."""
    return [
        UserMessage("Hi! I'd like to brainstorm some ideas."),
        UserMessage("What's the best way to approach creative problem solving?")
    ]

@mcp.prompt()
def example_conversation() -> list[UserMessage | AssistantMessage]:
    """Show an example conversation flow."""
    return [
        UserMessage("What are the benefits of renewable energy?"),
        AssistantMessage("Renewable energy offers several key benefits: environmental sustainability, energy independence, cost savings over time, and job creation in green industries."),
        UserMessage("Can you elaborate on the environmental benefits?")
    ]
```

### Mixed Content Types

```python
from mcp.types import TextContent, EmbeddedResource

@mcp.prompt()
def analysis_with_data(dataset_name: str) -> list[dict]:
    """Create prompt with embedded resource data."""
    return [
        {
            "role": "user",
            "content": TextContent(
                type="text",
                text="Please analyze the following dataset and provide insights:"
            )
        },
        {
            "role": "user",
            "content": EmbeddedResource(
                type="resource",
                resource={"uri": f"data://{dataset_name}", "text": "Dataset content here"}
            )
        }
    ]
```

## Parameter Validation

### Type Hints and Defaults

```python
from typing import Literal
from pydantic import Field

@mcp.prompt()
def code_review_prompt(
    language: Literal["python", "javascript", "java", "go"],
    focus: str = Field(description="What aspect to focus on (e.g., performance, security)"),
    severity: Literal["low", "medium", "high"] = "medium"
) -> str:
    """Generate a code review prompt."""
    return f"""
    Please review this {language} code with a focus on {focus}.
    Review severity level: {severity}

    Look for:
    - Code quality and best practices
    - Potential bugs or issues
    - Performance considerations
    - Security vulnerabilities

    Provide specific, actionable feedback.
    """

@mcp.prompt()
def learning_prompt(
    subject: str = Field(description="Subject to learn about"),
    level: Literal["beginner", "intermediate", "advanced"] = "beginner",
    format: Literal["tutorial", "quiz", "exercise"] = "tutorial"
) -> str:
    """Generate personalized learning content."""
    return f"""
    Create a {format} for learning {subject} at {level} level.

    Requirements:
    - Match the learner's {level} skill level
    - Use clear, engaging explanations
    - Include practical examples
    - Provide progression steps
    """
```

### Complex Validation

```python
from typing import Annotated
from pydantic import Field

@mcp.prompt()
def article_prompt(
    title: Annotated[str, Field(min_length=5, max_length=100)],
    keywords: Annotated[list[str], Field(min_length=1, max_length=10)],
    word_count: Annotated[int, Field(ge=100, le=5000)],
    tone: Literal["formal", "casual", "academic", "creative"] = "casual"
) -> str:
    """Generate an article writing prompt with validation."""
    keywords_str = ", ".join(keywords)

    return f"""
    Write an article titled "{title}" with the following specifications:

    - Word count: {word_count} words
    - Tone: {tone}
    - Keywords to include: {keywords_str}
    - Structure: Introduction, main content, conclusion
    - Include relevant examples and evidence
    """
```

## Async Prompts

Prompts can be async for dynamic content generation:

```python
import httpx
from datetime import datetime

@mcp.prompt()
async def news_prompt(topic: str) -> str:
    """Generate a prompt with current news context."""
    async with httpx.AsyncClient() as client:
        # Fetch recent news (example)
        response = await client.get(f"https://api.news.com/search?q={topic}")
        news_data = response.json()

    context = f"Recent news about {topic}:\n"
    for article in news_data.get("articles", [])[:3]:
        context += f"- {article['title']}\n"

    return f"""
    {context}

    Based on this recent news context, please provide analysis and insights about {topic}.
    Consider current trends, implications, and potential future developments.
    """

@mcp.prompt()
async def personalized_prompt(user_id: str) -> str:
    """Generate personalized prompt based on user data."""
    # Fetch user preferences (example)
    user_data = await get_user_preferences(user_id)

    interests = ", ".join(user_data.get("interests", []))
    experience_level = user_data.get("experience_level", "beginner")

    return f"""
    Welcome back! Based on your interests in {interests} and your {experience_level}
    experience level, I'm ready to provide tailored assistance.

    What would you like to explore today?
    """

async def get_user_preferences(user_id: str) -> dict:
    """Mock function to fetch user preferences."""
    return {
        "interests": ["technology", "science", "programming"],
        "experience_level": "intermediate"
    }
```

## Prompt Templates

### Research Templates

```python
@mcp.prompt()
def research_prompt(
    topic: str,
    research_type: Literal["academic", "market", "technical"] = "academic",
    depth: Literal["overview", "detailed", "comprehensive"] = "overview"
) -> list[UserMessage]:
    """Generate research-focused prompts."""

    base_prompt = f"I need to research {topic}."

    if research_type == "academic":
        methodology = "peer-reviewed sources, academic papers, and scholarly articles"
    elif research_type == "market":
        methodology = "market reports, industry analysis, and business data"
    else:  # technical
        methodology = "technical documentation, specifications, and expert resources"

    depth_instructions = {
        "overview": "Provide a high-level summary with key points",
        "detailed": "Include detailed analysis with supporting evidence",
        "comprehensive": "Provide exhaustive coverage with multiple perspectives"
    }

    return [
        UserMessage(base_prompt),
        UserMessage(f"Focus on {methodology}."),
        UserMessage(depth_instructions[depth] + "."),
        UserMessage("Structure the research with clear sections and cite sources.")
    ]

@mcp.prompt()
def problem_solving_prompt(
    problem: str,
    domain: str,
    constraints: list[str] = [],
    approach: Literal["analytical", "creative", "systematic"] = "analytical"
) -> str:
    """Generate problem-solving prompts."""

    constraints_text = ""
    if constraints:
        constraints_text = f"\nConstraints to consider: {', '.join(constraints)}"

    approach_instructions = {
        "analytical": "Break down the problem systematically and use logical reasoning",
        "creative": "Think outside the box and consider unconventional solutions",
        "systematic": "Follow a structured methodology and evaluate all options"
    }

    return f"""
    Problem to solve: {problem}
    Domain: {domain}{constraints_text}

    Approach: {approach_instructions[approach]}

    Please:
    1. Analyze the problem clearly
    2. Identify key factors and variables
    3. Generate potential solutions
    4. Evaluate pros and cons
    5. Recommend the best approach
    """
```

### Content Generation Templates

```python
@mcp.prompt()
def content_brief_prompt(
    content_type: Literal["blog", "email", "social", "documentation"],
    target_audience: str,
    key_message: str,
    call_to_action: str = ""
) -> str:
    """Generate content creation briefs."""

    format_guidelines = {
        "blog": "engaging introduction, structured body with headers, conclusion",
        "email": "clear subject line, personal greeting, concise message, strong CTA",
        "social": "attention-grabbing hook, concise message, relevant hashtags",
        "documentation": "clear structure, step-by-step instructions, examples"
    }

    cta_text = f"\nCall to action: {call_to_action}" if call_to_action else ""

    return f"""
    Create {content_type} content with the following specifications:

    Target audience: {target_audience}
    Key message: {key_message}{cta_text}

    Format requirements: {format_guidelines[content_type]}

    Ensure the content is:
    - Relevant and valuable to the target audience
    - Clear and easy to understand
    - Engaging and actionable
    - Appropriate for the {content_type} format
    """

@mcp.prompt()
def educational_content_prompt(
    subject: str,
    learning_objective: str,
    student_level: Literal["elementary", "middle", "high", "college", "adult"],
    format: Literal["lesson", "quiz", "exercise", "project"] = "lesson"
) -> list[UserMessage]:
    """Generate educational content prompts."""

    level_adaptations = {
        "elementary": "simple vocabulary, visual examples, short attention spans",
        "middle": "age-appropriate complexity, interactive elements, peer learning",
        "high": "critical thinking, real-world applications, independent work",
        "college": "advanced concepts, research skills, analytical thinking",
        "adult": "practical applications, professional relevance, flexible pacing"
    }

    return [
        UserMessage(f"Create a {format} for teaching {subject}."),
        UserMessage(f"Learning objective: {learning_objective}"),
        UserMessage(f"Student level: {student_level}"),
        UserMessage(f"Adapt content for: {level_adaptations[student_level]}"),
        UserMessage("Include assessment methods and follow-up activities.")
    ]
```

## Dynamic Prompts

### Context-Aware Prompts

```python
from datetime import datetime, date

@mcp.prompt()
def daily_briefing_prompt(
    focus_areas: list[str],
    include_weather: bool = True,
    include_calendar: bool = True
) -> str:
    """Generate personalized daily briefing prompt."""

    today = date.today().strftime("%A, %B %d, %Y")

    sections = [f"Good morning! Here's your briefing for {today}:"]

    if include_weather:
        sections.append("- Current weather and forecast")

    if include_calendar:
        sections.append("- Today's schedule and important events")

    for area in focus_areas:
        sections.append(f"- Updates and insights about {area}")

    sections.append("\nPrioritize the most important information and actionable items.")

    return "\n".join(sections)

@mcp.prompt()
def project_status_prompt(
    project_name: str,
    team_size: int,
    deadline: str,
    current_phase: str
) -> list[UserMessage]:
    """Generate project status review prompt."""

    return [
        UserMessage(f"Project Status Review: {project_name}"),
        UserMessage(f"Team size: {team_size} members"),
        UserMessage(f"Deadline: {deadline}"),
        UserMessage(f"Current phase: {current_phase}"),
        UserMessage("""
        Please provide a comprehensive status update including:
        1. Progress against timeline
        2. Key accomplishments this period
        3. Current blockers or risks
        4. Resource needs
        5. Next steps and priorities
        6. Team performance insights
        """)
    ]
```

### Multi-Modal Prompts

```python
from mcp.types import EmbeddedResource, ImageContent

@mcp.prompt()
def image_analysis_prompt(
    image_uri: str,
    analysis_type: Literal["description", "technical", "artistic", "business"] = "description"
) -> list[dict]:
    """Generate prompts for image analysis."""

    analysis_instructions = {
        "description": "Describe what you see in detail, including objects, people, setting, and mood",
        "technical": "Analyze composition, lighting, color theory, and photographic techniques",
        "artistic": "Discuss artistic style, aesthetic elements, and creative expression",
        "business": "Evaluate commercial potential, target audience, and marketing applications"
    }

    return [
        {
            "role": "user",
            "content": EmbeddedResource(
                type="resource",
                resource={"uri": image_uri}
            )
        },
        {
            "role": "user",
            "content": f"Please analyze this image with a {analysis_type} focus: {analysis_instructions[analysis_type]}"
        }
    ]

@mcp.prompt()
def document_review_prompt(
    document_uri: str,
    review_type: Literal["content", "style", "accuracy", "compliance"]
) -> list[dict]:
    """Generate document review prompts."""

    return [
        {
            "role": "user",
            "content": "Please review the following document:"
        },
        {
            "role": "user",
            "content": EmbeddedResource(
                type="resource",
                resource={"uri": document_uri}
            )
        },
        {
            "role": "user",
            "content": f"Focus on {review_type} review with specific feedback and recommendations."
        }
    ]
```

## Error Handling

### Validation and Error Messages

```python
@mcp.prompt()
def validated_prompt(
    task_type: str,
    priority: Literal["low", "medium", "high"],
    deadline: str
) -> str:
    """Prompt with validation and error handling."""

    # Validate inputs
    valid_tasks = ["research", "analysis", "writing", "coding", "design"]
    if task_type not in valid_tasks:
        raise ValueError(f"Invalid task type. Must be one of: {', '.join(valid_tasks)}")

    try:
        # Validate date format
        datetime.strptime(deadline, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Deadline must be in YYYY-MM-DD format")

    urgency = {"low": "when convenient", "medium": "with moderate urgency", "high": "as a priority"}

    return f"""
    Task: {task_type}
    Priority: {priority} - handle this {urgency[priority]}
    Deadline: {deadline}

    Please approach this systematically and provide regular updates on progress.
    """
```

## Best Practices

### 1. Clear Parameter Documentation

```python
@mcp.prompt()
def well_documented_prompt(
    objective: str = Field(description="The main goal or outcome you want to achieve"),
    context: str = Field(description="Background information or situation details"),
    constraints: list[str] = Field(
        description="Any limitations, requirements, or boundaries to consider",
        default=[]
    ),
    format: Literal["bullet", "paragraph", "outline"] = Field(
        description="Preferred response format",
        default="paragraph"
    )
) -> str:
    """Generate a well-structured prompt with clear documentation."""

    prompt_parts = [f"Objective: {objective}", f"Context: {context}"]

    if constraints:
        prompt_parts.append(f"Constraints: {', '.join(constraints)}")

    format_instructions = {
        "bullet": "Please respond in bullet point format",
        "paragraph": "Please respond in paragraph format",
        "outline": "Please respond as a structured outline"
    }
    prompt_parts.append(format_instructions[format])

    return "\n\n".join(prompt_parts)
```

### 2. Reusable Prompt Components

```python
def create_role_context(role: str, expertise: str) -> str:
    """Create consistent role context for prompts."""
    return f"You are a {role} with expertise in {expertise}."

def create_output_format(format_type: str) -> str:
    """Create consistent output format instructions."""
    formats = {
        "executive": "Provide an executive summary with key points and recommendations",
        "detailed": "Provide comprehensive analysis with supporting details",
        "actionable": "Focus on specific, actionable steps and next actions"
    }
    return formats.get(format_type, "Provide a clear and helpful response")

@mcp.prompt()
def consulting_prompt(
    domain: str,
    problem: str,
    output_format: Literal["executive", "detailed", "actionable"] = "detailed"
) -> str:
    """Generate consulting-style prompts with reusable components."""

    role = create_role_context("senior consultant", domain)
    format_instruction = create_output_format(output_format)

    return f"""
    {role}

    Problem: {problem}

    {format_instruction}

    Structure your response with:
    1. Problem analysis
    2. Root cause identification
    3. Solution recommendations
    4. Implementation roadmap
    5. Success metrics
    """
```

### 3. Conditional Prompt Logic

```python
@mcp.prompt()
def adaptive_learning_prompt(
    topic: str,
    current_knowledge: Literal["none", "basic", "intermediate", "advanced"],
    learning_style: Literal["visual", "auditory", "hands-on", "reading"] = "reading",
    time_available: int = 30  # minutes
) -> str:
    """Generate adaptive learning prompts based on user profile."""

    # Adjust complexity based on knowledge level
    complexity_map = {
        "none": "Start with fundamental concepts and basic definitions",
        "basic": "Build on basic knowledge with practical examples",
        "intermediate": "Dive deeper into advanced concepts and applications",
        "advanced": "Explore cutting-edge developments and expert perspectives"
    }

    # Adapt content format to learning style
    style_instructions = {
        "visual": "Include diagrams, charts, and visual examples",
        "auditory": "Use storytelling and verbal explanations",
        "hands-on": "Provide practical exercises and interactive examples",
        "reading": "Use detailed written explanations and references"
    }

    # Adjust scope based on time available
    if time_available <= 15:
        scope = "Provide a concise overview focusing on the most essential points"
    elif time_available <= 45:
        scope = "Provide a balanced explanation with key details and examples"
    else:
        scope = "Provide comprehensive coverage with multiple examples and deeper exploration"

    return f"""
    Topic: {topic}
    Learning level: {complexity_map[current_knowledge]}
    Learning style: {style_instructions[learning_style]}
    Time available: {time_available} minutes

    {scope}

    Make the content engaging and appropriate for the learner's profile.
    """
```
