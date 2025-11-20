# Testing Strategy - SOL Atlas Monorepo

This document describes the testing strategy and CI/CD setup for the SOL Atlas monorepo.

## Overview

The SOL Atlas project uses a **phased testing approach** with GitHub Actions to ensure code quality across multiple services written in Python, Java, and TypeScript.

### Testing Philosophy

- **Fast feedback**: Unit tests run on every PR (< 10 minutes target)
- **Comprehensive validation**: Integration and E2E tests run nightly
- **Progressive enhancement**: Start with complete test suites, gradually expand coverage
- **Service isolation**: Each module has its own workflow for parallel execution

## Current Status

### Phase 1: Foundation ✅ (Implemented)

The following CI/CD workflows are now active:

#### 1. `test-bot-luka-agent.yml` - Luka Agent Unit Tests
- **Triggers**: PRs and pushes to `main` and `langgraph_migration` branches
- **Path filters**: `bot/luka_agent/**`, `bot/requirements.txt`
- **Python versions**: 3.10, 3.11 (matrix)
- **Services**: Redis, Elasticsearch (via GitHub Actions service containers)
- **Coverage**: pytest with coverage reporting to Codecov
- **Current pass rate**: 83% (106/128 tests)
- **Target**: < 10 minutes execution time

**What it tests:**
- All 9 test files in `bot/luka_agent/tests/`:
  - `test_adapters.py` - Platform adapters (Telegram, Web)
  - `test_checkpointer.py` - Redis state persistence
  - `test_graph.py` - LangGraph agent orchestration
  - `test_image_description.py` - Vision capabilities
  - `test_integration_telegram.py` - Telegram integration
  - `test_integration_web.py` - Web/AG-UI integration
  - `test_llm_config_priority.py` - LLM configuration
  - `test_state.py` - State management
  - `test_sub_agent_tools.py` - Sub-agent tool loading

#### 2. `lint-python.yml` - Python Code Quality
- **Triggers**: PRs and pushes affecting Python files in `bot/` or `worker/`
- **Tools**:
  - `flake8` - Syntax errors and style violations
  - `black` - Code formatting (PEP 8)
  - `isort` - Import sorting
- **Status**: Non-blocking (continue-on-error: true) until codebase is cleaned up

### Phase 2-5: Future Implementation 🚧

See [CI/CD Roadmap](#cicd-roadmap) below for planned enhancements.

## Repository Structure

```
sol-atlas/
├── bot/                    # Python - Telegram bot & LangGraph agent
│   ├── luka_agent/        # ✅ Tests: 9 files, 128 tests (106 passing)
│   ├── luka_bot/          # 🚧 Future: Telegram integration tests
│   ├── ag_ui_gateway/     # 🚧 Future: Web gateway tests
│   └── flow_client/       # 🚧 Future: BPMN flow tests
├── worker/                 # 🚧 Python - External workers (11 test files)
├── engine/                 # 🚧 Java - Camunda BPMN engine (7 test files)
├── frontend/               # 🚧 Next.js - Web dashboard (Playwright tests)
├── solexer/                # 🚧 TypeScript - Solana indexer (minimal tests)
└── webchatbot/             # 🚧 AG-UI protocol (Jest + Playwright)
```

## Running Tests Locally

### Prerequisites

1. **Start service dependencies:**
   ```bash
   cd bot/luka_agent
   docker-compose up -d  # Starts Redis & Elasticsearch
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r bot/luka_agent/requirements.txt
   pip install pytest pytest-cov pytest-asyncio
   ```

### Run Luka Agent Tests

```bash
# All tests
pytest bot/luka_agent/tests/ -v

# With coverage
pytest bot/luka_agent/tests/ -v --cov=bot/luka_agent --cov-report=term-missing

# Specific test file
pytest bot/luka_agent/tests/test_graph.py -v

# Specific test
pytest bot/luka_agent/tests/test_graph.py::test_agent_initialization -v
```

### Run Linting

```bash
# Install linting tools
pip install flake8 black isort

# Check syntax errors
flake8 bot/ worker/ --count --select=E9,F63,F7,F82 --show-source

# Check formatting
black --check bot/ worker/

# Check import sorting
isort --check-only bot/ worker/

# Auto-fix formatting
black bot/ worker/
isort bot/ worker/
```

## CI/CD Workflows

### Active Workflows

| Workflow | Trigger | Duration | Status |
|----------|---------|----------|--------|
| `test-bot-luka-agent.yml` | PR, Push to main/langgraph_migration | ~8-12 min | ✅ Active |
| `lint-python.yml` | PR, Push (Python files) | ~2-3 min | ✅ Active |

### Workflow Features

#### Service Containers
Both Redis and Elasticsearch run as GitHub Actions service containers with health checks:

```yaml
services:
  redis:
    image: redis:7-alpine
    health-cmd: "redis-cli ping"

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    health-cmd: "curl -f http://localhost:9200/_cluster/health"
```

#### Python Version Matrix
Tests run on both Python 3.10 and 3.11 to ensure compatibility:

```yaml
strategy:
  matrix:
    python-version: ['3.10', '3.11']
```

#### Smart Caching
- pip dependencies cached by `actions/setup-python@v5`
- Cache key includes requirements.txt hash for automatic invalidation

#### Coverage Reporting
- Coverage reports uploaded to Codecov (Python 3.11 only)
- Coverage thresholds defined in `bot/luka_agent/.coveragerc`
- HTML and XML reports generated

## CI/CD Roadmap

### Phase 2: Expand Python Coverage (Next)

- [ ] `test-worker.yml` - Worker unit tests (11 test files)
- [ ] `test-bot-integration.yml` - Bot integration tests
  - Requires: `TELEGRAM_BOT_TOKEN_TEST` secret

### Phase 3: Add Java/TypeScript Modules

- [ ] `test-engine.yml` - Camunda engine tests (Maven)
  - Java 11, 17 matrix
  - Services: PostgreSQL, RabbitMQ
- [ ] `test-frontend.yml` - Frontend tests
  - Node 18, 20 matrix
  - Linting, type checking, Playwright
- [ ] `test-webchatbot.yml` - AG-UI protocol tests
  - pnpm + Turbo orchestration
- [ ] `test-solexer.yml` - Solana indexer tests
  - Services: ClickHouse, RabbitMQ (optional)

### Phase 4: Monorepo Orchestration

- [ ] `ci-monorepo.yml` - Master orchestrator workflow
  - Path-based filtering (only test changed modules)
  - Reusable workflow calls
  - Combined status checks
- [ ] Turbo caching for TypeScript modules
- [ ] Dependency graph awareness

### Phase 5: Nightly Comprehensive Testing

- [ ] `nightly-full.yml` - Scheduled comprehensive tests
  - Run at 2 AM daily
  - Integration tests (bot ↔ engine ↔ worker)
  - E2E Playwright tests (frontend, webchatbot/dojo)
  - Performance benchmarks
  - Slack/Discord notifications on failure

### Phase 6: Advanced Features

- [ ] Code coverage trends and badges
- [ ] Performance regression detection
- [ ] Security scanning (Bandit, Snyk, Dependabot)
- [ ] Docker image builds and registry pushes
- [ ] Multi-stage deployments (dev → staging → production)
- [ ] Test results dashboard

## Configuration Files

### Created

- `.github/workflows/test-bot-luka-agent.yml` - Main test workflow
- `.github/workflows/lint-python.yml` - Linting workflow
- `.github/actions/setup-python-env/action.yml` - Reusable Python setup action
- `.github/dependabot.yml` - Automated dependency updates
- `bot/luka_agent/.coveragerc` - Coverage configuration

### Coverage Configuration

The `.coveragerc` file defines:
- **Source**: `bot/luka_agent`
- **Omit**: Test files, virtualenvs, caches
- **Exclude lines**: Pragmas, debug code, type checking blocks, abstract methods
- **Reports**: Terminal (with missing lines), XML (for Codecov), HTML

## Secrets Configuration

Required GitHub Secrets for full CI/CD:

| Secret | Purpose | Required For |
|--------|---------|-------------|
| `OPENAI_API_KEY_TEST` | LLM testing (optional) | bot/luka_agent tests |
| `TELEGRAM_BOT_TOKEN_TEST` | Telegram integration tests | bot/luka_bot tests |
| `CODECOV_TOKEN` | Coverage uploads (optional) | Public repos don't need this |

To add secrets: **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

## Dependabot

Automated dependency updates are configured for:
- **GitHub Actions** (weekly)
- **Python** (pip) - bot, worker (weekly, max 5 PRs)
- **Java** (Maven) - engine (weekly, max 5 PRs)
- **Node.js** (npm/yarn/pnpm) - frontend, solexer, webchatbot (weekly)
- **Docker** base images (monthly)

## Best Practices

### Writing Tests

1. **Async tests**: Use `pytest-asyncio` for async functions
   ```python
   @pytest.mark.asyncio
   async def test_async_function():
       result = await my_async_function()
       assert result == expected
   ```

2. **Fixtures**: Use `conftest.py` for shared fixtures
   ```python
   @pytest.fixture
   def redis_client():
       client = redis.Redis(host='localhost', port=6379)
       yield client
       client.flushdb()  # Cleanup
   ```

3. **Mocking external services**: Mock API calls, use test credentials
   ```python
   @patch('openai.ChatCompletion.create')
   def test_llm_call(mock_create):
       mock_create.return_value = {"choices": [...]}
       # Test code
   ```

### CI/CD Optimization

1. **Path filters**: Only run workflows when relevant files change
2. **Matrix builds**: Test across Python/Node/Java versions
3. **Caching**: Cache dependencies (pip, npm, Maven)
4. **Fail-fast**: Set `fail-fast: false` to see all matrix results
5. **Timeouts**: Set reasonable timeouts (20 min for tests)

### Test Organization

- **Unit tests**: Fast, isolated, no external dependencies
- **Integration tests**: Test service interactions (Redis, DB)
- **E2E tests**: Full user flows (Playwright, Selenium)

## Troubleshooting

### Services not ready

If tests fail with connection errors:
```yaml
- name: Wait for services to be ready
  run: |
    timeout 60 bash -c 'until curl -f http://localhost:9200/_cluster/health; do sleep 2; done'
    timeout 30 bash -c 'until redis-cli ping; do sleep 1; done'
```

### Coverage not uploading

Ensure `coverage.xml` exists:
```bash
pytest --cov=bot/luka_agent --cov-report=xml
ls -la coverage.xml
```

### Linting failures

Auto-fix most issues:
```bash
black bot/ worker/
isort bot/ worker/
```

## Contributing

When adding new tests:

1. **Follow naming convention**: `test_*.py` or `*_test.py`
2. **Add path filters** to relevant workflows
3. **Update this documentation** with new test files
4. **Aim for 70%+ coverage** for new code
5. **Keep tests fast**: Mock slow operations

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [pytest Documentation](https://docs.pytest.org/)
- [GitHub Actions Python Guide](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python)
- [Codecov Documentation](https://docs.codecov.com/)

---

**Last Updated**: 2025-01-19
**Status**: Phase 1 Complete ✅
**Next**: Implement Phase 2 (Worker tests)
