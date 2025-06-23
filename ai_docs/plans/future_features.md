# templates for plans
- mcp client library
- multi hierachy langgraph agent


I want you to help me create some new plans for features I want implemented.

each plan should be a seperate file in the ai_docs/plans directory.

first I want you to create a plan for a mcp client library using mcp-server-fastmcp which is the modelcontextprotocol/python-sdk repo. look at how they implement clients in the examples directory and also look at tests/client/*.

for the mvp version I want the client to simply support stdio, with no authentication.

Use this prompt as inspiration and be sure to include steps like this to help claude iterate on the changes:

```
# Standard Workflow

1. First think through the problem, read the codebase for relevant files, and write a plan to projectplan.md
2. The plan should have a list of todo items that you can check off as you complete them
3. Before you begin working, check in with me and I will verify the plan
4. Then, begin working on the todo items, marking them as complete as you go
5. Please every step of the way just give me a high level explanation of what changes you made
6. Make every task and code change you do as simple as possible. We want to avoid making any massive or complex changes. Every change should impact as little code as possible. Everything is about simplicity
7. Finally, add a review section to the projectplan.md file with a summary of the changes you made and any other relevant information
```
