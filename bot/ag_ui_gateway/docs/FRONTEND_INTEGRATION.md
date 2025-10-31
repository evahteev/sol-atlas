# Frontend Integration Guide

**Version:** 1.0  
**Date:** October 18, 2025

---

## Overview

The AG-UI Gateway serves a React frontend that communicates via REST API and WebSocket. We support two deployment modes:

1. **Development:** Separate servers (FastAPI:8000, React:3000) with CORS
2. **Production:** FastAPI serves built React files as static assets

---

## Architecture

```
Development:
┌─────────────┐         ┌─────────────┐
│   React     │ CORS    │   FastAPI   │
│  Dev Server │◄───────►│   Backend   │
│   :3000     │         │    :8000    │
└─────────────┘         └─────────────┘

Production:
┌─────────────────────────────┐
│        FastAPI :8000        │
├─────────────────────────────┤
│  /api/*    → API endpoints  │
│  /ws/*     → WebSocket      │
│  /*        → React static   │
└─────────────────────────────┘
```

---

## Project Structure

```
ag_ui_gateway/
├── web_app/                      # React frontend
│   ├── public/
│   │   ├── index.html
│   │   └── favicon.ico
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat.tsx
│   │   │   ├── TaskForm.tsx
│   │   │   ├── KBCard.tsx
│   │   │   └── Profile.tsx
│   │   ├── pages/
│   │   │   ├── HomePage.tsx
│   │   │   ├── CatalogPage.tsx
│   │   │   ├── ChatPage.tsx
│   │   │   └── TasksPage.tsx
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   ├── websocket.ts
│   │   │   └── auth.ts
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   ├── useWebSocket.ts
│   │   │   └── useCatalog.ts
│   │   ├── contexts/
│   │   │   └── AuthContext.tsx
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── Dockerfile
├── ag_ui_gateway/                # FastAPI backend
│   └── main.py                   # Configured to serve static files
└── docker-compose.yml            # Both services
```

---

## FastAPI Static File Serving

### Updated `main.py`

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

app = FastAPI(...)

# CORS for development
if settings.DEBUG:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# API routes
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(catalog.router, prefix="/api", tags=["catalog"])
# ... other routers

# WebSocket routes
app.add_websocket_route("/ws/chat", chat.websocket_chat)

# Serve static files in production
if not settings.DEBUG:
    # Path to built React app
    static_dir = Path(__file__).parent.parent / "web_app" / "dist"
    
    if static_dir.exists():
        # Serve static assets (JS, CSS, images)
        app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")
        
        # Serve index.html for all other routes (SPA)
        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            # Skip API and WebSocket routes
            if full_path.startswith(("api/", "ws/", "health", "metrics")):
                raise HTTPException(404)
            
            index_file = static_dir / "index.html"
            return FileResponse(index_file)
    else:
        logger.warning(f"Static files not found at {static_dir}")

@app.get("/")
async def root():
    """Root endpoint - serves React app in production, API info in development."""
    if settings.DEBUG:
        return {
            "name": "AG-UI Gateway API",
            "version": "1.0.0",
            "docs": "/docs"
        }
    else:
        # In production, this is caught by serve_spa
        pass
```

---

## React Frontend Setup

### `web_app/package.json`

```json
{
  "name": "ag-ui-web",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx",
    "test": "vitest"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.18.0",
    "@ag-ui-protocol/ag-ui": "^0.1.0",
    "zustand": "^4.4.0",
    "axios": "^1.5.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.1.0",
    "typescript": "^5.2.0",
    "vite": "^4.5.0",
    "vitest": "^0.34.0"
  }
}
```

### `web_app/vite.config.ts`

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  
  // Development server
  server: {
    port: 3000,
    proxy: {
      // Proxy API calls to FastAPI backend
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
  
  // Build configuration
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
  },
})
```

### `web_app/src/services/api.ts`

```typescript
import axios from 'axios';

// API base URL - works in both dev and production
const API_BASE_URL = import.meta.env.PROD 
  ? '/api'  // Production: relative to same domain
  : 'http://localhost:8000/api';  // Development: explicit URL

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// API methods
export const authAPI = {
  authenticateTelegram: (initData: string) =>
    api.post('/auth/telegram-miniapp', { initData }),
  
  createGuestSession: () =>
    api.post('/auth/guest'),
};

export const catalogAPI = {
  listKBs: (params?: any) =>
    api.get('/catalog', { params }),
  
  getKBDetails: (kbId: string) =>
    api.get(`/kb/${kbId}`),
};
```

### `web_app/src/services/websocket.ts`

```typescript
// WebSocket URL - works in both dev and production
const WS_BASE_URL = import.meta.env.PROD
  ? `wss://${window.location.host}/ws`  // Production: same domain
  : 'ws://localhost:8000/ws';  // Development: explicit URL

export class ChatWebSocket {
  private ws: WebSocket | null = null;
  
  connect(token: string): Promise<void> {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(`${WS_BASE_URL}/chat`);
      
      this.ws.onopen = () => {
        // Authenticate
        this.send({ type: 'auth', token });
      };
      
      this.ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        
        if (message.type === 'auth_success') {
          resolve();
        }
        
        this.handleMessage(message);
      };
      
      this.ws.onerror = reject;
    });
  }
  
  send(message: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }
  
  private handleMessage(message: any) {
    // Handle different message types
    // Emit to event bus or state management
  }
}
```

---

## Docker Configuration

### Frontend Dockerfile (`web_app/Dockerfile`)

```dockerfile
# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source
COPY . .

# Build production bundle
RUN npm run build

# Production stage (nginx for serving)
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### Updated `docker-compose.yml`

```yaml
version: '3.8'

services:
  # Backend API
  ag_ui_gateway:
    build: .
    container_name: ag_ui_gateway
    ports:
      - "8000:8000"
    environment:
      - DEBUG=${DEBUG:-false}
      - BOT_TOKEN=${BOT_TOKEN}
      - AUTHJWT_SECRET_KEY=${AUTHJWT_SECRET_KEY}
      # ... other env vars
    depends_on:
      - redis
      - postgres
    volumes:
      # Mount built frontend in production
      - ./web_app/dist:/app/web_app/dist:ro
    restart: unless-stopped

  # Frontend (development only)
  web_app_dev:
    build:
      context: ./web_app
      target: builder
    container_name: web_app_dev
    ports:
      - "3000:3000"
    volumes:
      - ./web_app:/app
      - /app/node_modules
    command: npm run dev
    profiles:
      - dev
    restart: unless-stopped

  # Frontend (production - nginx)
  web_app_prod:
    build:
      context: ./web_app
    container_name: web_app_prod
    ports:
      - "80:80"
    profiles:
      - prod
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    # ... (unchanged)

  postgres:
    image: postgres:15-alpine
    # ... (unchanged)
```

### Run Commands

```bash
# Development mode (separate servers)
docker-compose --profile dev up

# Production mode (FastAPI serves built frontend)
docker-compose --profile prod up

# Or just backend + separate React dev server
docker-compose up ag_ui_gateway redis postgres
cd web_app && npm run dev
```

---

## Build Process

### Development Workflow

```bash
# Terminal 1: Start backend
cd ag_ui_gateway
poetry run uvicorn ag_ui_gateway.main:app --reload --port 8000

# Terminal 2: Start frontend
cd web_app
npm install
npm run dev  # Runs on port 3000 with proxy to :8000
```

### Production Build

```bash
# Build frontend
cd web_app
npm install
npm run build  # Creates dist/ folder

# Build Docker image with both
cd ..
docker build -t ag-ui-gateway:latest .
docker run -p 8000:8000 ag-ui-gateway:latest

# Or use docker-compose
docker-compose --profile prod up --build
```

### Nginx Configuration (for separate deployment)

If you want to deploy frontend separately with Nginx:

```nginx
# /etc/nginx/sites-available/ag-ui-web
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    root /var/www/ag-ui-web/dist;
    index index.html;
    
    # API proxy
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # WebSocket proxy
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # Cache static assets
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## Environment Variables

### Frontend `.env` files

**`.env.development`:**
```bash
VITE_API_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/ws
VITE_TELEGRAM_BOT_USERNAME=your_bot
```

**`.env.production`:**
```bash
VITE_API_URL=/api
VITE_WS_URL=/ws
VITE_TELEGRAM_BOT_USERNAME=your_bot
```

### Using in React

```typescript
const API_URL = import.meta.env.VITE_API_URL;
const WS_URL = import.meta.env.VITE_WS_URL;
```

---

## Telegram Mini App Integration

### `web_app/public/index.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Luka Bot</title>
  
  <!-- Telegram WebApp SDK -->
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/src/main.tsx"></script>
</body>
</html>
```

### `web_app/src/hooks/useTelegramAuth.ts`

```typescript
import { useEffect, useState } from 'react';

export function useTelegramAuth() {
  const [isReady, setIsReady] = useState(false);
  const [initData, setInitData] = useState<string>('');
  
  useEffect(() => {
    // Check if running in Telegram
    if (window.Telegram?.WebApp) {
      const tg = window.Telegram.WebApp;
      tg.ready();
      setInitData(tg.initData);
      setIsReady(true);
    } else {
      // Not in Telegram - use guest mode
      setIsReady(true);
    }
  }, []);
  
  return { isReady, initData, isTelegram: !!window.Telegram?.WebApp };
}
```

---

## CI/CD Pipeline

### GitHub Actions (`.github/workflows/build.yml`)

```yaml
name: Build and Deploy

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      # Build frontend
      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install frontend dependencies
        working-directory: ./web_app
        run: npm ci
      
      - name: Build frontend
        working-directory: ./web_app
        run: npm run build
      
      # Build backend Docker image
      - name: Build Docker image
        run: docker build -t ag-ui-gateway:${{ github.sha }} .
      
      # Deploy (example)
      - name: Deploy to server
        run: |
          # Your deployment commands
```

---

## Summary

### Recommended Approach

**Development:**
- Separate servers with Vite proxy
- Hot reload for both frontend and backend
- CORS enabled

**Production:**
- FastAPI serves built React files
- Single port (8000)
- No CORS needed
- Better security

### Key Benefits

1. **Simple deployment** - One service, one port
2. **No CORS issues** - Same origin in production
3. **Fast development** - Hot reload on both sides
4. **Flexible** - Can deploy separately if needed

---

**Related Documents:**
- [API Specification](./API_SPECIFICATION.md)
- [WebSocket Protocol](./WEBSOCKET_PROTOCOL.md)
- [Deployment Guide](./DEPLOYMENT.md)

---

**Document Version:** 1.0  
**Last Updated:** October 18, 2025

