# Create a Custom Slash Command for your project in Claude Code

Here's how to use it:

## How to Set Up the Slash Command

1. **Create the commands directory** (if it doesn't exist):
   ```bash
   mkdir -p .claude/commands
   ```

2. **Save the command file**:
   Copy the content from the artifact above and save it as `.claude/commands/create-slash-command.md`

3. **Use the command**:
   ```bash
   # In Claude Code, run:
   /project:create-slash-command my-new-command
   ```

## How It Works

The slash command will:

1. **Guide you step-by-step** through gathering all the necessary information for your project
2. **Use our standardized template** with XML tags for optimal Claude usage
3. **Generate the complete `.claude/commands/<name>.md` file** with all your project-specific information
4. **Save it automatically** so your team can use the new command immediately

## Example Usage Flow

```bash
# Start the command creation process
> /project:create-slash-command api-setup

# Claude will then ask you questions like:
# "What is the name of this project?"
# "What command installs dependencies?"
# "How do you run tests?"
# etc.

# After answering all questions, you'll get a new file:
# .claude/commands/api-setup.md

# Your team can then use:
> /project:api-setup
```

## Benefits

- **Consistency**: All your project commands follow the same structure
- **Team efficiency**: New team members get standardized setup instructions
- **AI optimization**: XML tags help Claude parse and use the information effectively
- **Maintainability**: Easy to update and modify project setup procedures

The generated commands will include all the key information agents need: installation steps, dependency management, testing, linting, troubleshooting, and AI-specific guidelines.
