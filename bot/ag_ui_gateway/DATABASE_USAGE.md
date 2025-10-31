# Database Usage in AG-UI Gateway

## Current Active Databases

### 1. Redis ✅ **REQUIRED**
**Status:** Actively used  
**Port:** 6379

**Used For:**
- User sessions (`guest_session:<token>`)
- JWT token caching (`flow_session:<user_id>`)
- Rate limiting counters (`ratelimit:minute:<user>:<timestamp>`)
- Flow API response caching (55 min TTL)

**Performance:**
- Connection pooling enabled
- Automatic reconnection
- Health checks every 30s

**Configuration:**
```env
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASS=  # Optional password
REDIS_DATABASE=0
```

---

### 2. Elasticsearch ✅ **REQUIRED**
**Status:** Actively used  
**Port:** 9200

**Used For:**
- Knowledge base indexing (via luka_bot)
- Full-text search
- Vector search (embeddings)
- Hybrid search
- KB metadata

**Integration:**
- Uses `luka_bot.services.elasticsearch_service`
- Accessed via `CatalogAdapter`

**Configuration:**
```env
ELASTICSEARCH_ENABLED=true
ELASTICSEARCH_URL=http://elasticsearch:9200
ELASTICSEARCH_TIMEOUT=30
ELASTICSEARCH_VERIFY_CERTS=false
```

---

### 3. PostgreSQL ⚠️ **OPTIONAL (Not Used)**
**Status:** Connected but NOT used  
**Port:** 5432

**Currently Used For:**
- Nothing! It connects and runs health checks, but no data is stored/retrieved

**Originally Planned For:**
- User profiles (✖️ now using luka_bot's UserProfileService + Redis)
- KB metadata (✖️ now in Elasticsearch)
- File upload tracking (✖️ not implemented)
- Future features (❓ maybe)

**Why It's There:**
- Reserved for future expansion
- Matches luka_bot's database setup
- Ready if you need relational data storage

**Recommendation:**
- **Keep it disabled** (default) to reduce dependencies
- **Enable it only if** you add features that need relational storage
- Currently adds ~20MB RAM and startup time with no benefit

**Configuration:**
```env
# Disabled by default (change to true if needed)
POSTGRES_ENABLED=false

# If enabled, configure these:
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=luka
POSTGRES_PASSWORD=your_password
POSTGRES_DB=luka_bot
```

---

## Summary

| Database | Required | Purpose | Can Disable? |
|----------|----------|---------|--------------|
| **Redis** | ✅ Yes | Sessions, tokens, cache, rate limiting | ❌ No |
| **Elasticsearch** | ✅ Yes | Knowledge base search | ❌ No |
| **PostgreSQL** | ❌ No | Reserved for future use | ✅ **Yes - Recommended** |

---

## Memory Usage (Estimated)

With all databases:
```
Redis:         ~50MB
Elasticsearch: ~500MB
PostgreSQL:    ~100MB (if enabled)
-----------------------------
Total:         ~650MB
```

Without PostgreSQL:
```
Redis:         ~50MB
Elasticsearch: ~500MB
-----------------------------
Total:         ~550MB (15% savings)
```

---

## How to Disable PostgreSQL

### Option 1: Environment Variable
```bash
# In .env file
POSTGRES_ENABLED=false
```

### Option 2: Already Disabled
As of this update, PostgreSQL is **disabled by default** in `config/settings.py`:
```python
POSTGRES_ENABLED: bool = False  # Default: disabled
```

---

## If You Want to Use PostgreSQL Later

1. **Enable it:**
   ```env
   POSTGRES_ENABLED=true
   POSTGRES_PASSWORD=your_secure_password
   ```

2. **Create models:**
   ```python
   # ag_ui_gateway/models/user.py
   from sqlalchemy import Column, Integer, String
   from sqlalchemy.ext.declarative import declarative_base
   
   Base = declarative_base()
   
   class User(Base):
       __tablename__ = "users"
       id = Column(Integer, primary_key=True)
       telegram_id = Column(Integer, unique=True)
       username = Column(String)
   ```

3. **Use it:**
   ```python
   from ag_ui_gateway.database import get_async_session
   
   async def save_user(user_data):
       async_session = get_async_session()
       async with async_session() as session:
           # Your SQLAlchemy queries here
           pass
   ```

---

## Recommended Setup

For **development/testing**:
```env
REDIS_HOST=localhost
ELASTICSEARCH_URL=http://localhost:9200
POSTGRES_ENABLED=false  # Don't need it
```

For **production**:
```env
REDIS_HOST=redis
ELASTICSEARCH_URL=http://elasticsearch:9200
POSTGRES_ENABLED=false  # Enable only if you use it

# If you enable PostgreSQL later:
POSTGRES_PASSWORD=<strong-password>
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
```

---

## Health Check Impact

With PostgreSQL disabled, health checks are faster:
```json
{
  "dependencies": {
    "redis": "healthy",
    "elasticsearch": "healthy"
    // No postgres check = faster response
  }
}
```

With PostgreSQL enabled:
```json
{
  "dependencies": {
    "redis": "healthy",
    "elasticsearch": "healthy",
    "postgres": "healthy"  // Adds ~10-20ms
  }
}
```

---

**Bottom Line:** PostgreSQL is currently **dead weight**. Disable it unless you have specific plans to use it!

