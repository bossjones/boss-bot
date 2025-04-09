# Cursor Rules Visualization - Production Environment

## Current Rule Structure Overview

Based on the current audit, we have the following distribution of rules:

| Rule Type | Count | Description |
|-----------|-------|-------------|
| Agent Selected | 9 | Rules that require AI judgment to apply |
| Always | 4 | Rules applied to every interaction |
| Auto Select+desc | 9 | Rules with glob patterns and descriptions |
| Manual | 7 | Rules that require explicit invocation |

## Rule Types Legend

| Rule Type | Color | Border Style | Usage |
|-----------|--------|--------------|--------|
| Always | #f0f (Magenta) | Bold | Applied to every chat and cmd-k request |
| Agent Selected | #0dd (Cyan) | Normal | AI decides when to apply based on context |
| Auto Select | #0d0 (Green) | Normal | Applied to matching file patterns |
| Auto Select+desc | #00f (Blue) | Normal | Applied to matching patterns with context |
| Manual | #ff0 (Yellow) | Dashed | Must be explicitly referenced |

## Token Impact Categories

- Low Impact: < 500 tokens
- Medium Impact: 500-2000 tokens
- High Impact: > 2000 tokens

## Core Rule Categories

```mermaid
graph TD
    subgraph CoreRules["Core Rules"]
        RG[rule-generating-agent<br/>Always Rule] --> |manages| NR[New Rules]
        RG --> |updates| ER[Existing Rules]

        PS[project-status-tracker-agent<br/>Auto Select+desc] --> |tracks| AI[.ai directory]
        PS --> |monitors| Progress[Project Progress]

        PD[phased-development-agent<br/>Auto Select+desc] --> |controls| Features[Feature Implementation]
        PD --> |enforces| Phases[Development Phases]
    end

    subgraph TestingRules["Testing Rules"]
        TDD[python-tdd-auto<br/>Always Rule] --> |enforces| TDDCycle[TDD Cycle]
        PF[pytest-fixtures-agent<br/>Auto Select+desc] --> |manages| Fixtures[Test Fixtures]
        PM[pytest-mock-agent<br/>Auto Select+desc] --> |handles| Mocking[Test Mocking]
    end

    subgraph ToolRules["Tool Rules"]
        UV[uv-package-manager-agent<br/>Always Rule] --> |manages| Deps[Dependencies]
        GC[git-commit-push-agent<br/>Agent Selected] --> |enforces| Git[Git Standards]
    end

    style RG fill:#f0f,stroke:#333,stroke-width:4px
    style TDD fill:#f0f,stroke:#333,stroke-width:4px
    style UV fill:#f0f,stroke:#333,stroke-width:4px
    style PS fill:#00f,stroke:#333
    style PD fill:#00f,stroke:#333
    style PF fill:#00f,stroke:#333
    style PM fill:#00f,stroke:#333
    style GC fill:#0dd,stroke:#333
</code>
```

## Analysis and Recommendations

1. **High-Impact Rules to Consider Converting**:
   - Rules with extensive descriptions (>2000 tokens) should be considered for manual invocation
   - Complex workflow rules should be split into smaller, more focused rules

2. **Rule Consolidation Opportunities**:
   - Testing-related rules could be consolidated to reduce overlap
   - Development phase rules could be combined with implementation rules

3. **Optimization Suggestions**:
   - Keep Always rules minimal and focused
   - Use Manual rules for complex, situational logic
   - Leverage Agent Selected rules for context-sensitive decisions

4. **Best Practices**:
   - Maintain clear rule descriptions
   - Use glob patterns judiciously
   - Keep rule hierarchies shallow
   - Document rule relationships
