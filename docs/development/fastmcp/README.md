# FastMCP Documentation

FastMCP is a high-level, ergonomic Python framework for building MCP (Model Context Protocol) servers. This documentation provides comprehensive guides for building production-ready servers.

## Documentation Status

### ✅ **Completed Documentation**
- [x] **[Overview](overview.md)** - Introduction and quick start guide
- [x] **[Transport Protocols](transports.md)** - stdio, streamable-http, SSE comparison and usage
- [x] **[Tools](tools.md)** - Function registration, validation, context injection
- [x] **[Resources](resources.md)** - Static and template resources for data exposure
- [x] **[Prompts](prompts.md)** - Message templates and conversation builders
- [x] **[Context](context.md)** - Logging, progress reporting, resource access
- [x] **[Configuration](configuration.md)** - Settings and environment variables
- [x] **[Authentication](authentication.md)** - OAuth2 setup for HTTP transports
- [x] **[Examples](examples.md)** - Complete server implementations and best practices

### ❌ **Missing Core Documentation**

#### **Essential Missing**
- [x] **[API Reference](api-reference.md)** - Complete class/method documentation with signatures
- [x] **[Development Workflow](development-workflow.md)** - Local development, testing, debugging
- [x] **[Troubleshooting](troubleshooting.md)** - Common issues, error diagnosis, solutions

#### **Important Missing**
- [x] **[Testing Guide](testing-guide.md)** - Unit testing, integration testing, mocking strategies
- [x] **[Performance Guide](performance-guide.md)** - Optimization, benchmarking, scaling
- [x] **[Security Guide](security-guide.md)** - Security best practices beyond OAuth
- [x] **[Monitoring & Observability](monitoring-observability.md)** - Logging, metrics, health checks, alerting
- [x] **[Migration Guide](migration-guide.md)** - From raw MCP SDK to FastMCP

#### **Advanced Topics Missing**
- [x] **[Custom Middleware](custom-middleware.md)** - Request/response middleware patterns and auth customization
- [x] **[Session Management](session-management.md)** - Advanced session handling for StreamableHTTP
- [x] **[Event Store Integration](event-store-integration.md)** - Detailed event store usage and patterns
- [x] **[Lifespan Management](lifespan-management.md)** - Advanced server lifecycle patterns
- [x] **[Custom Routes](custom-routes.md)** - HTTP endpoint customization beyond examples

#### **Developer Experience Missing**
- [x] **[Debugging](debugging.md)** - Debugging FastMCP servers effectively

#### **Production Missing**
- [ ] **Graceful Shutdown** - Proper server termination

#### **Reference Missing**
- [x] **[FAQ](faq.md)** - Common questions and answers
- [ ] **Limitations** - What FastMCP can't do, known issues
- [ ] **Comparison** - FastMCP vs raw MCP SDK vs other frameworks

#### **Integration Missing**
- [ ] **Database Integration** - ORM patterns, connection pooling
- [ ] **Message Queues** - Redis, RabbitMQ, async task patterns
- [ ] **External APIs** - HTTP clients, rate limiting, caching
- [ ] **File Systems** - File handling, cloud storage integration

#### **Specialized Missing**
- [ ] **WebSocket Support** - If FastMCP supports WebSocket transport
- [ ] **Streaming Responses** - Large data streaming patterns
- [ ] **Binary Data** - Handling images, files, binary content
- [ ] **Rate Limiting** - Request throttling implementation

## Getting Started

1. Start with the **[Overview](overview.md)** for a general introduction
2. Follow the **[Examples](examples.md)** for practical implementations
3. Read **[Tools](tools.md)**, **[Resources](resources.md)**, and **[Prompts](prompts.md)** for core concepts
4. Configure your server with **[Configuration](configuration.md)**
5. Choose your transport in **[Transport Protocols](transports.md)**

## Documentation Guidelines

When creating new documentation:

1. **Read this README.md first** to understand the current state
2. **Follow existing patterns** from completed documentation
3. **Include practical examples** with working code
4. **Add error handling** and security considerations
5. **Update this checklist** when documentation is complete

## File Naming Convention

- Use lowercase with hyphens: `api-reference.md`
- Keep names descriptive but concise
- Update the checklist with the exact filename and link

## Content Structure

Each documentation file should include:

1. **Clear title and overview**
2. **Table of contents** for longer documents
3. **Practical examples** with complete, working code
4. **Best practices** section
5. **Error handling** and troubleshooting tips
6. **Links to related documentation**

## Priority Order

Complete documentation in this suggested order:

1. **API Reference** (Essential)
2. **Development Workflow** (Essential)
3. **Troubleshooting** (Essential)
4. **Testing Guide** (Important)
5. **Performance Guide** (Important)
6. **Security Guide** (Important)
7. **Monitoring & Observability** (Important)
8. **Migration Guide** (Important)

## Contributing

When adding new documentation:

1. Create the markdown file in this directory
2. Add practical, tested examples
3. Update this README.md checklist
4. Follow the existing documentation style
5. Include cross-references to related topics
