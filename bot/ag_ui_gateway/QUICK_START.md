# Quick Start Guide

## Frontend + Backend Integration

### Architecture

**Development (2 servers):**
- React dev server: `http://localhost:3000` (with proxy to :8000)
- FastAPI backend: `http://localhost:8000`

**Production (1 server):**
- FastAPI serves everything on `:8000`
- React built files in `web_app/dist/`
- Routes: `/api/*` → API, `/ws/*` → WebSocket, `/*` → React SPA

---

## Quick Start

### 1. Backend Development

```bash
# Navigate to parent bot directory
cd /path/to/dexguru/bot

# Create and activate virtual environment
cd ag_ui_gateway
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run backend (from parent directory for luka_bot access)
cd ..
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
uvicorn ag_ui_gateway.ag_ui_gateway.main:app --reload --port 8000

# API docs at: http://localhost:8000/docs
```

### 2. Frontend Development

```bash
# Navigate to frontend
cd web_app

# Install dependencies
npm install

# Run dev server (proxies to backend :8000)
npm run dev

# Open: http://localhost:3000
```

### 3. Production Build

```bash
# Build frontend
cd ag_ui_gateway/web_app
npm run build  # Creates dist/ folder

# Use build script (includes luka_bot)
cd ..
./build.sh

# Or run directly with uvicorn
cd /path/to/dexguru/bot
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
uvicorn ag_ui_gateway.ag_ui_gateway.main:app --port 8000

# Open: http://localhost:8000 (everything on one port)
```

### 4. Docker (Full Stack)

**Note:** Docker builds from parent directory to include `luka_bot`.

```bash
# Using build script (recommended)
cd ag_ui_gateway
./build.sh

# Using docker-compose (builds from parent context automatically)
docker-compose up -d

# Development mode (separate frontend server)
docker-compose --profile dev up

# View logs
docker-compose logs -f ag_ui_gateway
```

---

## How It Works

### Development Mode

1. **Vite dev server** runs on `:3000`
2. **Proxies** `/api` and `/ws` requests to `:8000`
3. **Hot reload** for both frontend and backend
4. **CORS enabled** in FastAPI

```
Browser → :3000 (Vite) → /api → :8000 (FastAPI)
                       → /ws  → :8000 (WebSocket)
```

### Production Mode

1. **Frontend built** into `web_app/dist/`
2. **FastAPI serves** static files
3. **SPA fallback** - all routes → `index.html`
4. **No CORS needed** (same origin)

```
Browser → :8000 (FastAPI) → /api/* → API handlers
                          → /ws/*  → WebSocket
                          → /*     → React SPA
```

---

## Key Files

### Frontend Serving (main.py)

```python
if not settings.DEBUG:
    static_dir = Path(__file__).parent.parent / "web_app" / "dist"
    app.mount("/assets", StaticFiles(directory=static_dir / "assets"))
    
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Serve React for all non-API routes
```

### Vite Proxy (vite.config.ts)

```typescript
server: {
  port: 3000,
  proxy: {
    '/api': 'http://localhost:8000',
    '/ws': { target: 'ws://localhost:8000', ws: true }
  }
}
```

### API Client (api.ts)

```typescript
const API_BASE_URL = import.meta.env.PROD 
  ? '/api'  // Production: relative
  : 'http://localhost:8000/api';  // Dev: absolute
```

---

## Environment Variables

### Backend (.env)

```bash
DEBUG=true                    # Dev: true, Prod: false
BOT_TOKEN=...
AUTHJWT_SECRET_KEY=...        # Reuses luka_bot's auth key
ALLOWED_ORIGINS=http://localhost:3000,https://t.me
```

### Frontend (.env.development)

```bash
VITE_API_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/ws
```

---

## Testing

```bash
# Backend tests
poetry run pytest

# Frontend tests
cd web_app && npm test
```

---

## Deployment

### Option 1: Single Container (Recommended)

```bash
# Build frontend
cd web_app && npm run build

# Build image
docker build -t ag-ui-gateway .

# Run
docker run -p 8000:8000 ag-ui-gateway
```

### Option 2: Docker Compose

```bash
docker-compose --profile prod up
```

---

## Documentation

- **Full Docs:** [docs/](docs/)
- **Frontend Integration:** [docs/FRONTEND_INTEGRATION.md](docs/FRONTEND_INTEGRATION.md)
- **API Reference:** [docs/API_SPECIFICATION.md](docs/API_SPECIFICATION.md)
- **WebSocket Protocol:** [docs/WEBSOCKET_PROTOCOL.md](docs/WEBSOCKET_PROTOCOL.md)

---

## Troubleshooting

**"Static files not found"**
→ Run `cd web_app && npm run build` first

**"CORS error in development"**
→ Check `ALLOWED_ORIGINS` in backend .env

**"WebSocket connection failed"**
→ Ensure backend is running and `DEBUG=true` for dev

**"API calls fail from frontend"**
→ Check Vite proxy configuration in `vite.config.ts`

---

**Ready to start coding!** 🚀
