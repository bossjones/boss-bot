# Generate llms.txt files
[group('firecrawl')]
generate-llms url:
    #!/usr/bin/env bash
    # Validate URL format
    echo "Running: npx generate-llmstxt -k $FIRECRAWL_API_KEY -u \"{{url}}\" -m 50 -o ai_docs"
    npx generate-llmstxt -k $FIRECRAWL_API_KEY -u "{{url}}" -m 50 -o ai_docs
