---
description: Answer questions about LangGraph using official documentation
allowed-tools:
  - mcp__langgraph-docs-mcp__list_doc_sources
  - mcp__langgraph-docs-mcp__fetch_docs
---

For the question "$ARGUMENTS", use the langgraph-docs-mcp server to provide a comprehensive answer:

1. Call `mcp__langgraph-docs-mcp__list_doc_sources` to get available documentation sources
2. Call `mcp__langgraph-docs-mcp__fetch_docs` to read the main llms.txt file
3. Analyze the URLs in the documentation index and identify which ones are relevant to: $ARGUMENTS
4. Call `mcp__langgraph-docs-mcp__fetch_docs` on the most relevant URLs for this question
5. Provide a detailed answer based on the official LangGraph documentation, including code examples where appropriate
