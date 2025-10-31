# Deployment Guide: AG-UI Gateway

**Version:** 1.0  
**Date:** October 18, 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Docker Setup](#docker-setup)
3. [Environment Variables](#environment-variables)
4. [Nginx Configuration](#nginx-configuration)
5. [Monitoring](#monitoring)
6. [Health Checks](#health-checks)
7. [Scaling](#scaling)

---

## Overview

The AG-UI Gateway is deployed as Docker containers alongside existing Luka Bot infrastructure. It shares Redis, Postgres, Elasticsearch, and Camunda with the Telegram bot.

---

## Docker Setup

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

# Copy application
COPY ag_ui_gateway/ ./ag_ui_gateway/
COPY luka_bot/ ./luka_bot/

# Expose port
EXPOSE 8000

# Run with Uvicorn
CMD ["uvicorn", "ag_ui_gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  # AG-UI Gateway (NEW)
  ag_ui_gateway:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_HOST=redis
      - POSTGRES_HOST=postgres
      - ES_HOST=elasticsearch
      - CAMUNDA_URL=http://camunda:8080
      - FLOW_API_URL=${FLOW_API_URL}
      - WAREHOUSE_WS_URL=${WAREHOUSE_WS_URL}
      - BOT_TOKEN=${BOT_TOKEN}
      - AUTHJWT_SECRET_KEY=${AUTHJWT_SECRET_KEY}
    depends_on:
      - redis
      - postgres
      - elasticsearch
      - camunda
    volumes:
      - ./luka_bot:/app/luka_bot:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # Web Frontend (NEW)
  web_app:
    build: ./web_app
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=https://api.your-domain.com
      - REACT_APP_WS_URL=wss://api.your-domain.com/ws
    restart: unless-stopped

  # Existing services (unchanged)
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=luka_bot
      - POSTGRES_USER=luka
      - POSTGRES_PASSWORD=${DB_PASS}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - es_data:/usr/share/elasticsearch/data
    restart: unless-stopped

  camunda:
    image: camunda/camunda-bpm-platform:latest
    ports:
      - "8080:8080"
    restart: unless-stopped

  # Telegram bot (existing)
  luka_bot:
    build: ./luka_bot
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - REDIS_HOST=redis
      - POSTGRES_HOST=postgres
    depends_on:
      - redis
      - postgres
    restart: unless-stopped

volumes:
  redis_data:
  postgres_data:
  es_data:
```

---

## Environment Variables

### .env.example

```bash
# Bot Configuration
BOT_TOKEN=your_bot_token_here
AUTHJWT_SECRET_KEY=your_jwt_secret_here  # Reuses luka_bot's auth key

# Database (PostgreSQL is optional, disabled by default)
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=luka
POSTGRES_PASSWORD=your_password
POSTGRES_DB=luka_bot

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=

# Elasticsearch
ES_HOST=elasticsearch
ES_PORT=9200

# Camunda
CAMUNDA_URL=http://camunda:8080/engine-rest

# Flow API
FLOW_API_URL=https://flow-api.your-domain.com
FLOW_API_SYS_KEY=your_system_key

# Warehouse WebSocket
WAREHOUSE_WS_URL=wss://warehouse.your-domain.com/ws

# CORS
ALLOWED_ORIGINS=https://your-domain.com,https://t.me

# Rate Limiting
GUEST_RATE_LIMIT=20
AUTH_RATE_LIMIT=60
```

---

## Nginx Configuration

### /etc/nginx/sites-available/ag-ui-gateway

```nginx
# API Gateway
server {
    listen 443 ssl http2;
    server_name api.your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/api.your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.your-domain.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    # REST API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # WebSocket
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;  # 24 hours
    }
    
    # Health check
    location /health {
        proxy_pass http://localhost:8000;
        access_log off;
    }
    
    # Metrics (restricted)
    location /metrics {
        proxy_pass http://localhost:8000;
        allow 10.0.0.0/8;  # Internal network only
        deny all;
    }
}

# Web Frontend
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    root /var/www/web_app/build;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # Static assets with caching
    location /static/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name api.your-domain.com your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

---

## Monitoring

### Prometheus Configuration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'ag_ui_gateway'
    scrape_interval: 15s
    static_configs:
      - targets: ['ag_ui_gateway:8000']
```

### Grafana Dashboard

Import dashboard JSON for:
- Request rate (req/s)
- Response time (P50, P95, P99)
- Error rate (%)
- WebSocket connections (active)
- Rate limit hits

---

## Health Checks

### Endpoint: GET /health

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "dependencies": {
    "redis": "healthy",
    "postgres": "healthy",
    "elasticsearch": "healthy"
  }
}
```

### Liveness Probe (Kubernetes)

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 30
```

---

## Scaling

### Horizontal Scaling

```bash
# Scale to 3 replicas
docker-compose up -d --scale ag_ui_gateway=3
```

### Load Balancing

```nginx
upstream ag_ui_backend {
    least_conn;
    server ag_ui_gateway_1:8000;
    server ag_ui_gateway_2:8000;
    server ag_ui_gateway_3:8000;
}

server {
    location / {
        proxy_pass http://ag_ui_backend;
    }
}
```

---

**Document Version:** 1.0  
**Last Updated:** October 18, 2025
