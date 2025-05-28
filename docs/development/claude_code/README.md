# Claude Code Custom Slash Commands

This guide documents the custom slash commands available in the boss-bot project for Claude Code development workflows. These commands provide specialized automation for common development tasks, testing patterns, and code review processes.

## Available Commands

### 1. `/context_prime` - Basic Project Context

**File**: `.claude/commands/context_prime.md`

**Purpose**: Establishes basic project context by reading the README and understanding the project structure.

**Command**:
```
READ README.md, THEN run git ls-files to understand the context of the project.
```

**Usage Example**:
```
/context_prime
```

**When to Use**:
- Starting a new Claude Code session
- Need quick project overview
- Working on unfamiliar parts of the codebase
- Onboarding new contributors

### 2. `/context_prime_w_lead` - Enhanced Context Priming

**File**: `.claude/commands/context_prime_w_lead.md`

**Purpose**: Enhanced version that includes specific file reading capabilities alongside basic project context.

**Command**:
```
READ README.md, THEN run git ls-files to understand the context of the project. Be sure to also READ: $ARGUMENTS and nothing else.
```

**Usage Examples**:
```
/context_prime_w_lead src/boss_bot/core/env.py
/context_prime_w_lead tests/conftest.py pyproject.toml
/context_prime_w_lead src/boss_bot/bot/cogs/downloads.py src/boss_bot/core/downloads/handlers/base_handler.py
```

**When to Use**:
- Starting work on specific modules or features
- Need context for particular files before making changes
- Debugging specific components
- Code review preparation

### 3. `/jprompt_ultra_diff_review` - Multi-LLM Code Review

**File**: `.claude/commands/jprompt_ultra_diff_review.md`

**Purpose**: Comprehensive code review workflow using multiple AI models for thorough analysis and synthesis.

**Workflow**:
1. **Primary Analysis** (openai:o3-mini): Initial code review and analysis
2. **Alternative Perspective** (anthropic:claude-3-7-sonnet-20250219:4k): Secondary review with different model
3. **Technical Deep-dive** (gemini:gemini-2.0-flash-thinking-exp): Detailed technical analysis
4. **Synthesis**: Combine insights from all three models
5. **Final Recommendations**: Actionable improvement suggestions

**Usage Examples**:
```
# Review current staged changes
/jprompt_ultra_diff_review

# Review specific commit
git show abc123 | /jprompt_ultra_diff_review

# Review pull request changes
gh pr diff 42 | /jprompt_ultra_diff_review
```

**When to Use**:
- Major feature implementations
- Critical bug fixes
- Code refactoring efforts
- Architecture changes
- Pre-merge code review

### 4. `/tdd_dpytest` - Test-Driven Development Workflow

**File**: `.claude/commands/tdd_dpytest.md`

**Purpose**: Comprehensive TDD workflow specifically designed for Discord bot development using dpytest framework.

**Workflow** (RED-GREEN-REFACTOR Cycle):
1. **Analyze Requirements**: Understand what needs to be implemented
2. **Write Failing Tests**: Create tests that define expected behavior
3. **Run Tests (RED)**: Verify tests fail as expected
4. **Implement Minimal Code**: Write just enough code to make tests pass
5. **Run Tests (GREEN)**: Verify tests now pass
6. **Refactor**: Improve code while keeping tests green
7. **Advanced Testing**: Add edge cases, concurrency, permissions
8. **Integration Testing**: Test with actual Discord bot integration
9. **Documentation**: Update docs and examples

**Usage Examples**:
```
# Start TDD for new Discord command
/tdd_dpytest

# Apply TDD to specific cog feature
/tdd_dpytest (when working on downloads cog)

# TDD for error handling improvements
/tdd_dpytest (when implementing robust error handling)

# Implement new platform support with TDD
/project:tdd_dpytest "new download command for TikTok platform with URL validation and metadata extraction"

# Add advanced error handling
/project:tdd_dpytest "enhance download command to handle rate limiting and network timeouts gracefully"

# Complex workflow testing
/project:tdd_dpytest "multi-step command workflow for bulk download management with progress tracking"
```

**When to Use**:
- Implementing new Discord commands
- Adding new cog functionality
- Fixing complex bugs with proper test coverage
- Refactoring existing Discord bot features

### 5. `/write_dpytest` - Quick Test Generation

**File**: `.claude/commands/write_dpytest.md`

**Purpose**: Rapid generation of dpytest tests for Discord bot components with support for multiple test types.

**Supported Test Types**:
- **basic**: Simple command testing
- **cog**: Cog-specific functionality testing
- **direct**: Direct method testing without Discord context
- **error**: Error handling and edge case testing
- **fixture**: Custom fixture creation and usage
- **integration**: Full Discord bot integration testing

**Usage Examples**:
```
# Generate basic command tests
/write_dpytest basic

# Create cog-specific tests
/write_dpytest cog

# Generate error handling tests
/write_dpytest error

# Create integration tests
/write_dpytest integration
```

**When to Use**:
- Quick test creation for new features
- Adding missing test coverage
- Creating test templates
- Prototyping test scenarios

## Workflow Examples

### New Feature Development

```bash
# 1. Start with enhanced context
/context_prime_w_lead src/boss_bot/bot/cogs/downloads.py

# 2. Use TDD workflow for implementation
/tdd_dpytest

# 3. Generate additional tests as needed
/write_dpytest error

# 4. Comprehensive code review before merge
/jprompt_ultra_diff_review
```

### Bug Investigation and Fix

```bash
# 1. Get project context with relevant files
/context_prime_w_lead tests/test_bot/test_downloads.py src/boss_bot/bot/cogs/downloads.py

# 2. Write tests that reproduce the bug
/write_dpytest error

# 3. Apply TDD to fix the issue
/tdd_dpytest

# 4. Review the fix
/jprompt_ultra_diff_review
```

### Code Review Process

```bash
# 1. Understand the changes in context
/context_prime_w_lead [modified files]

# 2. Comprehensive multi-model review
/jprompt_ultra_diff_review

# 3. If tests need improvement
/write_dpytest [appropriate type]
```

## Integration with Boss-Bot Development

### Quality Standards
All commands integrate with boss-bot's quality tools:
- **Testing**: `just check-test`
- **Linting**: `just check-code`
- **Type Checking**: `just check-type`
- **Full Suite**: `just check`

### Project Structure
Commands understand boss-bot's modular architecture:
- Discord cogs in `src/boss_bot/bot/cogs/`
- Core services in `src/boss_bot/core/`
- Test organization matching `src/` structure
- dpytest integration patterns

### Testing Patterns
Commands follow established patterns:
- Function-scoped fixtures with `fixture_` prefix
- `.callback()` pattern for testing decorated commands
- Proper async/await testing with `@pytest.mark.asyncio`
- Mock usage via `mocker.Mock()` and `mocker.AsyncMock()`

## Best Practices

### Command Selection
- Use `/context_prime` for quick orientation
- Use `/context_prime_w_lead` when working on specific files
- Use `/tdd_dpytest` for new feature development
- Use `/write_dpytest` for quick test additions
- Use `/jprompt_ultra_diff_review` for thorough code review

### Workflow Integration
- Start sessions with context priming
- Use TDD for complex features
- Apply multi-model review for critical changes
- Generate tests early and often
- Review code before committing

### Common Patterns
- Always run quality checks after implementing changes
- Follow the existing fixture naming conventions
- Use proper async testing patterns for Discord components
- Document new features and changes
- Maintain test coverage for all new functionality

## Troubleshooting

### Test Failures
If tests fail after using commands:
1. Check test isolation with function-scoped fixtures
2. Verify proper `.callback()` usage for Discord commands
3. Ensure async/await patterns are correct
4. Review mock setup for Discord components

### Integration Issues
If commands don't work as expected:
1. Verify file paths and project structure
2. Check that boss-bot dependencies are installed
3. Ensure git context is available
4. Validate dpytest configuration

### Performance Considerations
- Multi-model review commands may take longer to execute
- Context priming with many files may be slower
- TDD workflows are iterative and may require multiple runs
- Test generation should be followed by manual review and customization
