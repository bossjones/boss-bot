# FastMCP Documentation Command

Create comprehensive FastMCP documentation following the established patterns and checklist.

## Instructions

You are tasked with creating high-quality documentation for FastMCP components. Follow these steps exactly:

### Step 1: Read Current Status
1. **ALWAYS start by reading `/docs/fastmcp/README.md`** to understand:
   - What documentation already exists
   - What documentation is missing
   - The current checklist status
   - Documentation guidelines and patterns

### Step 2: Choose Documentation Topic
2. Select a topic from the "Missing Core Documentation" section in the README.md checklist
3. Prioritize in this order:
   - Essential Missing (API Reference, Development Workflow, Troubleshooting)
   - Important Missing (Testing, Performance, Security, Monitoring, Migration)
   - Advanced Topics Missing
   - Developer Experience Missing
   - Production Missing
   - Reference Missing
   - Integration Missing
   - Specialized Missing

### Step 3: Research and Analyze
3. Before writing, examine the FastMCP codebase:
   - Read relevant source files in `src/mcp/server/fastmcp/`
   - Study existing examples in `examples/fastmcp/`
   - Look at test files in `tests/` for patterns
   - Review existing documentation for style and structure

### Step 4: Create Documentation
4. Write comprehensive documentation that includes:
   - **Clear title and overview** explaining the topic
   - **Practical examples** with complete, working code
   - **Step-by-step instructions** where applicable
   - **Error handling** and troubleshooting tips
   - **Best practices** section
   - **Security considerations** when relevant
   - **Cross-references** to related documentation
   - **Code examples** that follow FastMCP patterns

### Step 5: Follow Existing Patterns
5. Maintain consistency with existing documentation:
   - Use the same code style and formatting
   - Follow the same section structure
   - Include similar types of examples
   - Match the level of detail and explanation
   - Use the same tone (concise, practical, developer-focused)

### Step 6: Update Checklist
6. **After creating the documentation file**:
   - Open `/docs/fastmcp/README.md`
   - Find the topic you just documented
   - Change `- [ ]` to `- [x]`
   - Add the filename as a link: `- [x] **[Topic Name](filename.md)** - Description`
   - Save the updated README.md

## File Naming Convention

- Use lowercase with hyphens: `api-reference.md`, `development-workflow.md`
- Keep names descriptive but concise
- Match the topic name from the checklist

## Quality Standards

Your documentation must:
- **Be practical**: Include working code examples that users can copy/paste
- **Be complete**: Cover the full scope of the topic
- **Be accurate**: All code examples must be syntactically correct
- **Be helpful**: Solve real problems users will encounter
- **Be consistent**: Follow patterns from existing documentation
- **Be current**: Use the latest FastMCP features and best practices

## Code Example Requirements

- All code examples must be complete and runnable
- Include proper imports and setup
- Show both basic and advanced usage
- Include error handling where appropriate
- Follow FastMCP best practices
- Add comments for complex sections

## Example Usage

```
User: "Create documentation for API Reference"

Claude response:
1. Reads /docs/fastmcp/README.md ✓
2. Creates /docs/fastmcp/api-reference.md with complete API documentation ✓
3. Updates README.md checklist to mark API Reference as complete ✓
```

## Important Notes

- **ALWAYS read README.md first** - this contains critical context
- **Update the checklist** - this tracks our progress
- **Test your examples** - make sure code actually works
- **Be thorough** - these docs will be used by real developers
- **Follow the priority order** - work on Essential items first

## Validation

Before submitting documentation:
- [ ] Read README.md for current status ✓
- [ ] Created comprehensive documentation file ✓
- [ ] Included practical, working examples ✓
- [ ] Followed existing documentation patterns ✓
- [ ] Updated README.md checklist ✓
- [ ] Used proper file naming convention ✓
