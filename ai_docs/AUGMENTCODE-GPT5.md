## AUGMENTCODE-GPT5.md

This guide orients Augment Agent (GPT‑5 by OpenAI) for working effectively in the Boss-Bot codebase. It explains what the project is, how it works, how we develop and test, and the checklists to follow for safe, high‑quality changes.

---

## 1) Project TL;DR

- Boss-Bot is an AI-powered Discord bot focused on intelligent media downloading and orchestration.
- Core: modern Python 3.12+, async/await, LangChain + LangGraph multi‑agent workflows.
- Scope: platform-aware downloads (Twitter/X, Reddit, YouTube, Instagram), queueing, progress, error recovery.
- Quality: UV-managed deps, Ruff, pre-commit, 400+ tests with pytest, CI via GitHub Actions, structured logging.

---

## 2) What GPT‑5 Should Know (Operating Rules)

- Package management
  - Use UV and Just. Never manually edit pyproject.toml for deps.
  - Prefer: `uv add <pkg>`, `uv sync --dev`, or the Just wrappers.
- Testing discipline
  - Always write/modify tests for changes; run `just test` locally.
  - Use pytest + pytest-mock (avoid direct unittest.mock). Use dpytest for Discord cogs.
  - Keep recorded HTTP via pytest-recording/VCR as needed.
- Style and quality gates
  - Format with Ruff; lint + type-check via `just check` or individual just recipes.
  - Add type hints; follow existing patterns; small, focused changes preferred.
- Safety and permissions
  - Do not install, deploy, commit, or push without explicit user approval.
  - Use environment variables from .env; never hardcode secrets; mask in logs.
- Execution/verification
  - Favor quick, safe verification: run unit tests, `--help` commands, linters.
  - If a run fails, propose minimal fixes, re-run targeted checks.

---

## 3) Quick Start (Local)

```bash
# Install toolchain and deps
uv sync --dev
just install                      # git hooks, setup
cp .env.example .env

# Quality + tests
just check                        # lint, type, format, security
just test                         # full test suite
just test-ci                      # CI-like run with coverage

# Run the bot / CLI
uv run python -m boss_bot         # start Discord bot
uv run bossctl --help            # CLI
```

Common troubleshooting:
- Verify Python 3.12+; install UV per https://astral.sh/uv
- Ensure .env is present and populated; set ENABLE_AI, tokens, keys as needed.

---

## 4) Architecture Snapshot

- src/boss_bot/
  - ai/
    - agents/ (BaseAgent, StrategySelector, ContentAnalyzer)
    - workflows/ (LangGraph orchestrations e.g., DownloadWorkflow)
    - strategies/ (AI-enhanced strategies)
    - assistants/ (LangGraph Cloud integration)
  - bot/
    - client.py (BossBot entry)
    - cogs/ (Discord commands)
  - core/
    - downloads/ (managers, handlers per platform, queue)
    - queue/
    - env.py (Pydantic settings)
  - monitoring/, storage/, utils/
- tests/
  - test_ai/, test_bot/, test_core/ (+ shared fixtures)

Key flows
- Discord command -> parse/validate -> AI agent route -> strategy select -> optional content analysis -> download manager -> progress -> delivery.
- State across agents via LangGraph; queue for download jobs with retry and backoff.

---

## 5) Development Workflow

- Branching: short-lived feature/fix branches; open PRs early for feedback.
- Commits: conventional, small, descriptive; keep diffs minimal.
- Adding deps: `uv add <pkg>` (or `just uv-add <pkg>`). Never manual edits for deps.
- Formatting: `just format` (Ruff); enforce pre-commit.
- Lint/Type/Sec: `just check` or the specific `just check-*` recipes.
- Running: `uv run python -m boss_bot` for bot; `uv run bossctl` for CLI.

---

## 6) Testing Strategy

Structure
- tests/test_core/: downloads, queue, config, handlers
- tests/test_ai/: agents, workflows, integration
- tests/test_bot/: client, cogs (use dpytest)

Guidelines
- Prefer pytest-mock's `mocker` fixture.
- Use async tests with pytest-asyncio; set timeouts for long-running logic.
- Use VCR (pytest-recording) for HTTP integrations.
- Ensure deterministic tests; isolate side effects; prefer fixtures.

Commands
```bash
just test                 # all tests
uv run pytest -k NAME -v  # focused test
uv run pytest --cov=src --cov-report=term-missing
```

---

## 7) CI/CD Summary

- GitHub Actions: checkout -> setup UV -> `uv sync --dev` -> `just ci` -> Codecov.
- CI env vars: keys for AI providers; use fake Discord token for tests.
- UV frozen installs for reproducibility.

---

## 8) AI Integration Guidance (GPT‑5)

Principles
- Keep the BaseAgent API stable; follow AgentRequest/AgentResponse patterns.
- Workflows should compose via LangGraph state machines. Prefer explicit states and conditional edges.
- Multi-provider support via configuration; choose models via settings.

When adding/modifying AI features
- Add feature flags in settings (enable_ai, ai_strategy_selection_enabled, etc.).
- Provide sane defaults; document .env requirements.
- Mock LLM calls in tests; validate confidence scores, reasoning fields, and fallbacks.

Minimal examples
```python
# Agent request/response (sketch)
resp = await strategy_selector.process_request(request)
assert resp.success and resp.confidence >= 0.7
```

---

## 9) Configuration and Secrets

- Use .env: Discord tokens, AI provider keys (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.), feature flags, storage paths.
- Pydantic settings in core/env.py handle validation and defaults.
- Never log raw secrets; use masking helpers; keep logs structured.

---

## 10) Operations (Local + Docker)

Local
- Logs: logs/ directory, Loguru config with rotation and JSON serialize.
- Health: utility functions or endpoints can report status, uptime, queue size.

Docker
```bash
docker build -t boss-bot .
docker run -d --env-file .env -v $(pwd)/storage:/app/storage boss-bot
```
- Optional Redis for caching/state.

---

## 11) High-Confidence Checklists

Pre-task triage (before coding)
- [ ] Clarify user intent and acceptance criteria.
- [ ] Identify files likely involved; scan tests first.
- [ ] Confirm local run prerequisites (.env, uv sync, just install).
- [ ] Run `just test` to ensure a green baseline.

Design pass
- [ ] Choose minimal viable change; avoid cross-cutting edits.
- [ ] Determine new/updated tests; list scenarios (happy-path, errors, edge cases).
- [ ] Plan config, flags, and docs updates.

Implementation pass
- [ ] Write or update tests first (TDD if practical).
- [ ] Implement code to satisfy tests; maintain type hints.
- [ ] Keep public interfaces stable; add deprecation notes if needed.

Validation pass
- [ ] Run unit tests and focused suites.
- [ ] `just check` (lint, type, format, security) must pass.
- [ ] Manual smoke: `uv run bossctl --help` and critical codepaths where safe.

Pre-PR checklist
- [ ] Tests added/updated; coverage unchanged or improved.
- [ ] All checks green locally.
- [ ] Changelog/README/docs updated if user-facing.
- [ ] Screenshots/logs/traces for complex changes.

Post-merge / release
- [ ] Monitor logs for regressions.
- [ ] Confirm CI artifacts (coverage, wheels) as applicable.
- [ ] Update deployment manifests if env/config changed.

Incident/hotfix
- [ ] Reproduce with a failing test.
- [ ] Apply minimal fix; add regression test.
- [ ] Backport as needed; communicate impact/scope.

AI change-safety review
- [ ] Provider timeouts, retries, and rate limits in place.
- [ ] Deterministic tests with mocked LLM calls.
- [ ] Reasoning text non-sensitive; mask PII and secrets.
- [ ] Feature flags to disable risky paths quickly.

---

## 12) PR and Commit Templates

Commit message (suggested)
- feat(scope): concise summary
- fix(scope): concise summary
- test(scope): what/why
- chore/refactor/docs/build: as appropriate

PR description (suggested)
- What/Why
- Implementation notes
- Screenshots/Logs (if relevant)
- Tests added/updated
- Risks/roll-back strategy

---

## 13) Common Commands Cheat Sheet

```bash
# Install, quality, tests
uv sync --dev
just install && just check && just test

# Lint/format/type/security individually
just check-code
just format
just check-type
just check-security

# Focused tests, coverage
uv run pytest -k download -vv
uv run pytest --cov=src --cov-report=term-missing

# Run bot/CLI
uv run python -m boss_bot
uv run bossctl --help
```

---

## 14) FAQ (Quick Answers)

- How do I add a new platform handler?
  - Implement a handler in core/downloads/ following the strategy pattern; add tests in test_core/test_handlers; wire into the manager and, if AI-enhanced, add StrategySelector coverage.
- Can I call external APIs in tests?
  - Use pytest-recording/VCR; default to using cassettes. For AI calls, prefer mocks.
- What if tests are flaky?
  - Stabilize with deterministic inputs, timeouts, and recorded I/O; split slow/integration tests and mark with pytest markers.
- How do I enable/disable AI features?
  - Use environment flags (ENABLE_AI, ai_* settings in env.py). Provide defaults and clear docs.
- Where do I start for a large change?
  - Write a design note in the PR; start with tests and minimal scaffolding; iterate with small commits.

---

## 15) Maintaining This Document

- Keep commands aligned with Just and UV.
- Update supported platforms and test counts when they change.
- Ensure checklists reflect our latest CI, security, and AI practices.

---

## 16) Open Questions for the Maintainer

To ensure perfect alignment, please confirm:
- Are current supported platforms precisely: Twitter/X, Reddit, YouTube, and Instagram (any others planned or enabled by default)?
- Is the CLI named bossctl and expected to ship with the package? Any subcommands we should highlight?
- Do we actively use LangSmith/observability in CI, and are tokens available in CI secrets?
- Should Redis be considered optional or recommended in production?
- What is the current authoritative test count target (e.g., 407+) we should reference in badges/docs?

If any of the above differ, I'll update this guide accordingly in a follow-up pass.
