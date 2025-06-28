# Claude GitHub Actions Workflow Documentation

## Overview

The Claude GitHub Actions workflow (`claude.yml`) integrates Anthropic's Claude AI assistant directly into our GitHub repository workflow. This automation enables intelligent code assistance, issue management, and pull request reviews through natural language interactions.

## Workflow Location

- **File**: `.github/workflows/claude.yml`
- **Action Source**: `anthropics/claude-code-action@beta`
- **Documentation**: [Claude Code Actions](https://docs.anthropic.com/en/docs/claude-code/github-actions)

## How It Works

### Trigger Mechanism

The workflow activates when `@claude` is mentioned in:

1. **Issue Comments**: When someone comments `@claude` on any issue
2. **Pull Request Review Comments**: When `@claude` is mentioned in PR review comments
3. **Pull Request Reviews**: When submitting a PR review containing `@claude`
4. **New Issues**: When creating issues with `@claude` in the title or body

### Workflow Execution

1. **Event Detection**: GitHub detects the trigger events listed above
2. **Conditional Check**: Workflow only runs if `@claude` is present in the triggering content
3. **Environment Setup**:
   - Checks out repository code
   - Configures Git with bot credentials
   - Sets up Ubuntu runner environment
4. **Claude Execution**: Runs the Claude Code action with configured parameters

## Configuration Details

### Required Secrets

The workflow requires these GitHub secrets to be configured:

- `ANTHROPIC_API_KEY`: Your Anthropic API key for Claude access
- `GITHUB_TOKEN`: Automatically provided by GitHub Actions

### Permissions

The workflow requires these permissions:

- `contents: write` - Create branches, commit files
- `pull-requests: write` - Create/update PRs and comments
- `issues: write` - Create/update issues and comments
- `id-token: write` - OIDC authentication

### Security: Allowed Tools

Claude is restricted to a whitelist of tools for security:

#### Shell Commands
- Basic operations: `cd`, `cp`, `find`, `ls`, `mv`, `tree`
- Git operations: `git status`, `git diff`, `git log`, etc.
- Project tools: `just`, `uv`, `pytest`, `ruff`, `python`

#### Code Operations
- File operations: `Read`, `Write`, `Edit`, `MultiEdit`
- Search tools: `Grep`, `Glob`, `RipgrepSearch`
- Code analysis: `View`, `LS`

#### GitHub Integration (via MCP)
- Issue management: Create, update, comment on issues
- PR management: Create, review, merge pull requests
- Repository operations: Branch creation, file operations
- Security: Access to code scanning and secret scanning alerts

#### Documentation Access
Restricted web access to trusted domains:
- `docs.anthropic.com` - Anthropic documentation
- `discordpy.readthedocs.io` - Discord.py documentation
- `python.langchain.com` - LangChain documentation
- `docs.astral.sh` - UV/Ruff documentation
- And other project-relevant documentation sites

## Usage Examples

### Basic Issue Assistance

```
@claude Can you help debug this error in the Discord bot startup?
```

### Code Review Request

```
@claude Please review this pull request and check for potential issues
```

### Feature Development

```
@claude Implement a new command for downloading media from Twitter
```

### Testing Assistance

```
@claude Run the test suite and fix any failing tests
```

## Advanced Configuration Options

### Custom Instructions (Optional)

```yaml
custom_instructions: |
  This is the boss-bot project. Always read CLAUDE.md first.
  Focus on the immediate success criteria.
  Follow conventional commits and create focused, working code.
  Always read the codebase and the documentation first.
```

### Model Selection (Optional)

```yaml
# Use Claude Opus instead of default Sonnet
model: "claude-opus-4-20250514"
```

### Custom Trigger Phrase (Optional)

```yaml
# Use /claude instead of @claude
trigger_phrase: "/claude"
```

### Environment Variables (Optional)

```yaml
claude_env: |
  NODE_ENV: test
  DEBUG: true
```

## Best Practices

### For Users

1. **Be Specific**: Provide clear, detailed requests to Claude
2. **Reference Context**: Mention relevant files, issues, or PRs
3. **Follow Up**: Engage in conversation to refine solutions
4. **Review Changes**: Always review Claude's suggestions before merging

### For Maintainers

1. **Monitor Usage**: Track Claude interactions for effectiveness
2. **Update Permissions**: Regularly review and update allowed tools
3. **Secure Secrets**: Ensure API keys are properly stored as secrets
4. **Test Changes**: Validate workflow changes in a safe environment

## Troubleshooting

### Common Issues

1. **No Response from Claude**
   - Check if `@claude` is properly mentioned
   - Verify `ANTHROPIC_API_KEY` secret is set
   - Ensure workflow has proper permissions

2. **Permission Errors**
   - Review repository permissions settings
   - Check if bot has necessary access rights
   - Verify token permissions are sufficient

3. **Tool Restrictions**
   - Claude may be blocked from certain operations
   - Review `allowed_tools` configuration
   - Add necessary tools to the whitelist

### Debugging Steps

1. Check workflow run logs in GitHub Actions tab
2. Verify trigger conditions are met
3. Review Claude's error messages in comments
4. Test with simple requests first

## Security Considerations

### Tool Restrictions
- Claude is limited to whitelisted tools only
- No access to sensitive operations like deployment
- Web access restricted to trusted documentation domains

### Secrets Management
- API keys stored as encrypted GitHub secrets
- No sensitive data exposed in workflow files
- Bot identity clearly marked in commits

### Access Control
- Workflow only responds to explicit `@claude` mentions
- No automatic execution without user trigger
- All actions are logged and auditable

## Integration with Boss-Bot

### Project-Specific Features

- **CLAUDE.md Awareness**: Claude reads project instructions automatically
- **Just Task Runner**: Integration with project build system
- **UV Package Manager**: Python dependency management support
- **Discord.py Patterns**: Understanding of Discord bot architecture
- **AI Architecture**: Knowledge of LangChain/LangGraph components

### Development Workflow

1. **Issue Creation**: Claude can help create detailed issues
2. **Code Development**: Assists with implementation and debugging
3. **Testing**: Runs test suites and fixes failures
4. **Code Review**: Provides automated PR reviews
5. **Documentation**: Updates documentation as needed

## Future Enhancements

### Planned Improvements

- **Custom Prompts**: Project-specific behavioral instructions
- **Advanced Triggers**: More sophisticated activation conditions
- **Integration Webhooks**: Better integration with external tools
- **Performance Monitoring**: Usage analytics and optimization

### Monitoring and Analytics

- Track Claude usage patterns
- Measure resolution effectiveness
- Monitor response times and accuracy
- Collect user feedback for improvements

---

*This documentation covers the Claude GitHub Actions workflow as of the current implementation. For the latest updates and features, refer to the official [Anthropic Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code/github-actions).*
