# Update Documentation Command

Automatically analyze recent code changes and update corresponding documentation in the `docs/` directory.

## Instructions

You are tasked with keeping documentation synchronized with code changes. Follow these steps systematically:

### Step 1: Analyze Recent Changes
1. **Check git status and recent commits**:
   - Run `git status` to see current changes
   - Run `git log --oneline -10` to see recent commits
   - Run `git diff HEAD~3..HEAD --name-only` to see recently changed files
   - Focus on changes in the last 3-5 commits unless user specifies otherwise

### Step 2: Identify Documentation Impact
2. **Categorize changes by documentation type needed**:
   - **API Changes**: New functions, classes, or method signatures → Update API reference docs
   - **Architecture Changes**: New modules, refactored structure → Update architecture docs
   - **Configuration Changes**: New settings, environment variables → Update configuration docs
   - **Feature Changes**: New functionality, workflows → Update user guides and examples
   - **Testing Changes**: New test patterns, fixtures → Update testing documentation
   - **Build/Deploy Changes**: Dependencies, scripts, CI/CD → Update development workflow docs

### Step 3: Map Code to Documentation Files
3. **Identify which documentation files need updates**:
   - **Core changes** → `docs/core/`
   - **CLI changes** → `docs/cli.md`
   - **Download system changes** → `docs/core/download-system.md`
   - **Discord bot changes** → `docs/core/discord-integration.md`
   - **Configuration changes** → `docs/core/configuration-management.md`, `docs/environment.md`
   - **Testing changes** → `docs/core/testing-patterns.md`
   - **Architecture changes** → `docs/core/architecture-overview.md`
   - **Development workflow changes** → `docs/core/development-workflow.md`

### Step 4: Analyze Code Changes in Detail
4. **For each changed file, examine**:
   - **New public APIs**: Functions, classes, methods that users will interact with
   - **Changed behavior**: Modified functionality that affects existing documentation
   - **New configuration**: Settings, environment variables, command-line options
   - **Removed features**: Deprecated or deleted functionality
   - **Dependencies**: New libraries or version changes that affect setup/usage

### Step 5: Update Documentation
5. **Update documentation systematically**:
   - **Read existing documentation** to understand current state and style
   - **Update relevant sections** with new information
   - **Add new sections** for entirely new features
   - **Remove outdated information** for deprecated features
   - **Update code examples** to reflect current API usage
   - **Add cross-references** between related documentation
   - **Ensure consistency** in tone, formatting, and style

### Step 6: Validate Documentation Quality
6. **Quality checks**:
   - **Accuracy**: All code examples work with current codebase
   - **Completeness**: All significant changes are documented
   - **Clarity**: Explanations are clear and actionable
   - **Examples**: Include practical, working code examples
   - **Links**: Internal references are correct and up-to-date
   - **Formatting**: Follows markdown conventions and existing style

## Documentation Structure Reference

### Core Documentation Files:
- `docs/core/architecture-overview.md` - System architecture and design patterns
- `docs/core/configuration-management.md` - Settings, environment variables, configuration
- `docs/core/development-workflow.md` - Build, test, dev setup instructions
- `docs/core/discord-integration.md` - Discord bot functionality and commands
- `docs/core/download-system.md` - Download strategies, handlers, queue management
- `docs/core/testing-patterns.md` - Test setup, fixtures, patterns, and guidelines

### Other Important Files:
- `docs/cli.md` - Command-line interface documentation
- `docs/environment.md` - Environment setup and variables
- `docs/logging.md` - Logging configuration and usage
- `docs/README.md` - Main documentation index

## Change Detection Patterns

### High-Impact Changes (Always Document):
- **New public classes or functions** in `src/boss_bot/`
- **Configuration changes** in `src/boss_bot/core/env.py`
- **New command-line options** in CLI modules
- **Database schema changes** or model updates
- **New Discord commands** in cog files
- **API changes** in public interfaces

### Medium-Impact Changes (Often Document):
- **Internal refactoring** that affects usage patterns
- **Test fixture changes** that affect how others write tests
- **New utilities** or helper functions
- **Performance improvements** worth highlighting
- **Bug fixes** that change expected behavior

### Low-Impact Changes (Selectively Document):
- **Internal implementation details** without user impact
- **Code formatting** or style changes
- **Comment updates** without functionality changes
- **Minor bug fixes** that restore expected behavior

## Example Workflow

```bash
# User runs: "Update docs based on recent changes"

# Step 1: Analyze recent changes
git log --oneline -5
git diff HEAD~3..HEAD --name-only

# Step 2: Identify impacted files
# Example: Changes to src/boss_bot/core/compression/
# → Update docs/core/download-system.md

# Step 3: Read and update documentation
# - Add new compression features to download-system.md
# - Update examples with new API usage
# - Add configuration options to configuration-management.md

# Step 4: Validate updates
# - Check that all code examples are syntactically correct
# - Ensure cross-references are working
# - Verify new content fits existing documentation style
```

## Code Analysis Guidelines

### When examining code changes:
1. **Look for user-facing changes**: What will developers or users notice?
2. **Identify breaking changes**: What existing code or workflows will break?
3. **Find new capabilities**: What new things can users do?
4. **Spot configuration changes**: What new settings or environment variables exist?
5. **Check dependencies**: Are there new setup requirements?

### Documentation Update Priorities:
1. **Critical**: Breaking changes, new required configuration
2. **High**: New public APIs, major features, workflow changes
3. **Medium**: Enhanced functionality, new utilities, test patterns
4. **Low**: Internal improvements, minor bug fixes, style changes

## Quality Standards

Your documentation updates must:
- **Be accurate**: Reflect the actual current codebase state
- **Be practical**: Include working examples users can copy/paste
- **Be complete**: Cover all user-facing aspects of changes
- **Be consistent**: Match existing documentation style and tone
- **Be current**: Reference the latest version of APIs and patterns
- **Be helpful**: Solve real problems users will encounter

## Validation Checklist

Before completing documentation updates:
- [ ] Analyzed recent git commits and identified all relevant changes ✓
- [ ] Mapped code changes to appropriate documentation files ✓
- [ ] Updated all impacted documentation sections ✓
- [ ] Added or updated code examples for new features ✓
- [ ] Verified all code examples are syntactically correct ✓
- [ ] Checked cross-references and internal links ✓
- [ ] Ensured consistency with existing documentation style ✓
- [ ] Covered configuration changes and setup requirements ✓

## Usage Examples

```
User: "Update docs based on recent changes"
→ Analyzes last 3-5 commits, identifies changed files, updates relevant documentation

User: "Update docs for the new compression system"
→ Focuses specifically on compression-related changes and documentation

User: "Check if docs need updating after the last merge"
→ Examines the most recent merge commit for documentation impacts
```

## Important Notes

- **Focus on user impact**: Document changes that affect how people use the system
- **Preserve existing style**: Match the tone and formatting of existing docs
- **Be selective**: Not every code change requires documentation updates
- **Stay current**: Use the latest API patterns and best practices
- **Think holistically**: Consider how changes affect the overall system documentation
