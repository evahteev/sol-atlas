# Testing Strategy: AG-UI Gateway

**Version:** 1.0  
**Date:** October 18, 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Testing Pyramid](#testing-pyramid)
3. [Unit Tests](#unit-tests)
4. [Integration Tests](#integration-tests)
5. [E2E Tests](#e2e-tests)
6. [Performance Tests](#performance-tests)
7. [Security Tests](#security-tests)

---

## Overview

Comprehensive testing strategy covering unit, integration, end-to-end, performance, and security testing.

---

## Testing Pyramid

```
        /\
       /  \  E2E (10%)
      /____\
     /      \  Integration (30%)
    /________\
   /          \  Unit (60%)
  /__________  \
```

**Target Coverage:**
- Unit Tests: 80%+
- Integration Tests: 70%+
- E2E Tests: Critical paths only

---

## Unit Tests

### Authentication Tests

```python
# tests/test_auth.py
import pytest
from ag_ui_gateway.auth.telegram_miniapp import validate_telegram_webapp_data
from ag_ui_gateway.auth.tokens import GuestToken, create_jwt_token

def test_valid_telegram_signature():
    init_data = "..."  # Valid signed data
    bot_token = "test_token"
    
    result = validate_telegram_webapp_data(init_data, bot_token)
    assert result['telegram_user_id'] == 123456789

def test_invalid_signature():
    init_data = "hash=invalid"
    bot_token = "test_token"
    
    with pytest.raises(HTTPException) as exc:
        validate_telegram_webapp_data(init_data, bot_token)
    assert exc.value.status_code == 401

def test_guest_token_generation():
    token = GuestToken.generate()
    assert token.startswith("guest_")
    assert len(token) > 20

def test_jwt_creation():
    token = create_jwt_token(123456, "secret")
    assert token is not None
    assert len(token.split('.')) == 3
```

### Adapter Tests

```python
# tests/test_adapters.py
import pytest
from ag_ui_gateway.adapters.catalog_adapter import CatalogAdapter

@pytest.mark.asyncio
async def test_catalog_listing():
    adapter = CatalogAdapter(user_id=123)
    kbs = await adapter.list_catalog(visibility="public")
    
    assert isinstance(kbs, list)
    assert all('id' in kb for kb in kbs)
```

---

## Integration Tests

### API Endpoint Tests

```python
# tests/integration/test_catalog_api.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_catalog_list(client: AsyncClient, auth_token: str):
    response = await client.get(
        "/api/catalog",
        params={"visibility": "public", "limit": 10},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) <= 10

@pytest.mark.asyncio
async def test_guest_catalog_access(client: AsyncClient):
    # Create guest session
    response = await client.post("/api/auth/guest")
    guest_token = response.json()['token']
    
    # Access catalog
    response = await client.get(
        "/api/catalog",
        headers={"Authorization": f"Bearer {guest_token}"}
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_private_kb_access_denied_for_guest(client: AsyncClient):
    response = await client.post("/api/auth/guest")
    guest_token = response.json()['token']
    
    response = await client.get(
        "/api/kb/private-kb-123",
        headers={"Authorization": f"Bearer {guest_token}"}
    )
    assert response.status_code == 403
    assert "UPGRADE_REQUIRED" in response.json()['error']
```

### WebSocket Tests

```python
# tests/integration/test_websocket.py
import pytest
from fastapi.testclient import TestClient

def test_websocket_auth(client: TestClient):
    with client.websocket_connect("/ws/chat") as websocket:
        # Send auth
        websocket.send_json({
            "type": "auth",
            "token": "guest_test_token"
        })
        
        # Receive auth_success
        data = websocket.receive_json()
        assert data['type'] == 'auth_success'
        assert data['mode'] == 'guest'

def test_websocket_chat_message(client: TestClient, auth_token: str):
    with client.websocket_connect("/ws/chat") as websocket:
        # Auth
        websocket.send_json({"type": "auth", "token": auth_token})
        websocket.receive_json()  # auth_success
        
        # Send message
        websocket.send_json({
            "type": "user_message",
            "message": "Hello"
        })
        
        # Receive streaming response
        response = websocket.receive_json()
        assert response['type'] in ['textStreamDelta', 'stateUpdate']
```

---

## E2E Tests

### Critical User Flows

```typescript
// tests/e2e/catalog.test.ts
import { test, expect } from '@playwright/test';

test('user can browse KB catalog as guest', async ({ page }) => {
  // Land on homepage
  await page.goto('/');
  
  // Click "Browse as Guest"
  await page.click('[data-testid="browse-as-guest"]');
  
  // Should see catalog
  await expect(page.locator('[data-testid="catalog-page"]')).toBeVisible();
  
  // Should see KB cards
  const kbCards = page.locator('[data-testid="kb-card"]');
  await expect(kbCards).toHaveCount(10, { timeout: 5000 });
  
  // Click on first KB
  await kbCards.first().click();
  
  // Should see details modal
  await expect(page.locator('[data-testid="kb-details"]')).toBeVisible();
});

test('guest user can chat and hit message limit', async ({ page }) => {
  await page.goto('/');
  await page.click('[data-testid="browse-as-guest"]');
  
  // Navigate to chat
  await page.click('[data-testid="chat-link"]');
  
  // Send 20 messages
  for (let i = 0; i < 20; i++) {
    await page.fill('[data-testid="chat-input"]', `Test message ${i}`);
    await page.press('[data-testid="chat-input"]', 'Enter');
    await page.waitForTimeout(200);
  }
  
  // Should see upgrade prompt
  await expect(page.locator('[data-testid="upgrade-prompt"]')).toBeVisible();
});

test('authenticated user can complete task', async ({ page }) => {
  // Sign in
  await page.goto('/auth/telegram');
  // ... Telegram auth flow
  
  // Navigate to tasks
  await page.click('[data-testid="tasks-link"]');
  
  // Click on first task
  await page.click('[data-testid="task-item"]:first-child');
  
  // Fill form
  await page.fill('[name="description"]', 'Test description');
  
  // Upload file
  await page.setInputFiles('[name="s3_document"]', 'test-file.pdf');
  
  // Submit
  await page.click('[data-testid="submit-button"]');
  
  // Should see success message
  await expect(page.locator('text=Task completed')).toBeVisible();
});
```

---

## Performance Tests

### Load Testing (Locust)

```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Create guest session
        response = self.client.post("/api/auth/guest")
        self.token = response.json()['token']
    
    @task(3)
    def browse_catalog(self):
        self.client.get(
            "/api/catalog",
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    @task(2)
    def view_kb_details(self):
        self.client.get(
            "/api/kb/crypto-kb",
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    @task(1)
    def search_kb(self):
        self.client.post(
            "/api/commands/search",
            json={"args": {"query": "DeFi"}},
            headers={"Authorization": f"Bearer {self.token}"}
        )
```

**Run:**
```bash
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

**Targets:**
- 1000 concurrent users
- <200ms P95 response time
- <1% error rate

---

## Security Tests

### OWASP Top 10 Coverage

1. **Injection** - Parameterized queries, input validation
2. **Broken Authentication** - JWT expiry, signature validation
3. **Sensitive Data Exposure** - HTTPS only, no logs
4. **XXE** - Pydantic validation
5. **Broken Access Control** - Permission system
6. **Security Misconfiguration** - Security headers
7. **XSS** - Output encoding
8. **Insecure Deserialization** - Pydantic models
9. **Components with Known Vulnerabilities** - Dependency scanning
10. **Insufficient Logging** - Structured logging

### Security Test Examples

```python
# tests/security/test_auth_security.py
def test_expired_token_rejected():
    expired_token = create_expired_jwt()
    response = client.get(
        "/api/profile",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401

def test_rate_limiting():
    for i in range(25):
        response = client.get("/api/catalog")
    
    assert response.status_code == 429
    assert "retry_after" in response.json()

def test_sql_injection_prevented():
    response = client.get("/api/kb/'; DROP TABLE users; --")
    assert response.status_code == 404
```

---

## CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install poetry
          poetry install
      
      - name: Run unit tests
        run: poetry run pytest tests/ -v --cov
      
      - name: Run integration tests
        run: poetry run pytest tests/integration/ -v
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Test Data Management

### Fixtures

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def auth_token():
    return create_jwt_token(123456, "test_secret")

@pytest.fixture
async def guest_token():
    return GuestToken.generate()

@pytest.fixture
def sample_kb():
    return {
        "id": "test-kb",
        "name": "Test KB",
        "visibility": "public",
        "status": "enabled"
    }
```

---

## Coverage Targets

| Test Type | Target | Current |
|-----------|--------|---------|
| Unit | 80% | - |
| Integration | 70% | - |
| E2E | Critical paths | - |
| Overall | 75% | - |

---

**Document Version:** 1.0  
**Last Updated:** October 18, 2025
