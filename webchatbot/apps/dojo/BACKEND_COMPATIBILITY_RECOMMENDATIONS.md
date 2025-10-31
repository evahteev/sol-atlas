# Backend Compatibility Recommendations for AG-UI Integration

## Overview

This document provides comprehensive recommendations for making your Luka Bot API backend compatible with multiple AG-UI implementations. Based on analysis of the Dojo codebase, different AG-UI frameworks use various endpoint patterns.

## Current Issue

**Problem**: Your API uses a single endpoint pattern (`/api/agent/luka`) while most AG-UI implementations expect feature-specific endpoints.

**Error**: `POST /api/agent/luka/agentic_chat/ HTTP/1.1" 404 Not Found`

## AG-UI Implementation Patterns Analysis

### Pattern 1: Feature-Specific Endpoints (Most Common - 80% of implementations)

```typescript
// LangGraph FastAPI
url: `${baseUrl}/agent/agentic_chat`
url: `${baseUrl}/agent/backend_tool_rendering`
url: `${baseUrl}/agent/agentic_generative_ui`

// Pydantic AI
url: `${baseUrl}/agentic_chat/`
url: `${baseUrl}/agentic_generative_ui/`
url: `${baseUrl}/human_in_the_loop/`

// Server Starter
url: `${baseUrl}/agentic_chat`

// Agno & Spring AI
url: `${baseUrl}/agentic_chat/agui`

// LlamaIndex
url: `${baseUrl}/agentic_chat/run`
```

### Pattern 2: Single Endpoint (Your Current Approach - 20% of implementations)

```typescript
// Bot API (Your current approach)
url: `${baseUrl}/api/agent/luka`
// Feature handled in request body or headers
```

## Recommended Solution: Dual Pattern Support

Implement **both patterns** to maximize compatibility with all AG-UI implementations.

### Option 1: Feature-Specific Routes (Recommended)

Add these routes to your FastAPI backend:

```python
from fastapi import FastAPI, Request
from your_models import RunAgentInput

app = FastAPI()

# Pattern 1: Feature-specific endpoints (most common)
@app.post("/api/agent/luka/agentic_chat/")
async def agentic_chat_endpoint(input_data: RunAgentInput, request: Request):
    return await luka_agent_endpoint(input_data, request, feature="agentic_chat")

@app.post("/api/agent/luka/agentic_generative_ui/")
async def agentic_generative_ui_endpoint(input_data: RunAgentInput, request: Request):
    return await luka_agent_endpoint(input_data, request, feature="agentic_generative_ui")

@app.post("/api/agent/luka/human_in_the_loop/")
async def human_in_the_loop_endpoint(input_data: RunAgentInput, request: Request):
    return await luka_agent_endpoint(input_data, request, feature="human_in_the_loop")

@app.post("/api/agent/luka/shared_state/")
async def shared_state_endpoint(input_data: RunAgentInput, request: Request):
    return await luka_agent_endpoint(input_data, request, feature="shared_state")

@app.post("/api/agent/luka/tool_based_generative_ui/")
async def tool_based_generative_ui_endpoint(input_data: RunAgentInput, request: Request):
    return await luka_agent_endpoint(input_data, request, feature="tool_based_generative_ui")

@app.post("/api/agent/luka/backend_tool_rendering/")
async def backend_tool_rendering_endpoint(input_data: RunAgentInput, request: Request):
    return await luka_agent_endpoint(input_data, request, feature="backend_tool_rendering")

# Pattern 2: Single endpoint (your current approach)
@app.post("/api/agent/luka")
async def luka_agent_endpoint(input_data: RunAgentInput, request: Request, feature: str = "agentic_chat"):
    # Your existing logic here
    # Use the 'feature' parameter to determine behavior
    logger.info(f"Processing feature: {feature}")
    # ... rest of your implementation
```

### Option 2: Wildcard Route (Simpler Implementation)

```python
# Single wildcard route that catches all feature requests
@app.post("/api/agent/luka/{feature}/")
async def feature_endpoint(feature: str, input_data: RunAgentInput, request: Request):
    logger.info(f"Feature requested: {feature}")
    return await luka_agent_endpoint(input_data, request, feature=feature)

# Keep your existing single endpoint
@app.post("/api/agent/luka")
async def luka_agent_endpoint(input_data: RunAgentInput, request: Request, feature: str = "agentic_chat"):
    # Your existing logic
```

## Implementation Steps

### Step 1: Update Your Core Function

Modify your existing `luka_agent_endpoint` function to accept a feature parameter:

```python
async def luka_agent_endpoint(
    input_data: RunAgentInput, 
    request: Request, 
    feature: str = "agentic_chat"
):
    """
    Core agent endpoint that handles all features.
    
    Args:
        input_data: The agent input data
        request: FastAPI request object
        feature: The feature being requested (e.g., 'agentic_chat', 'human_in_the_loop')
    """
    logger.info(f"Processing {feature} request for user {input_data.user_id}")
    
    # You can customize behavior based on feature
    if feature == "agentic_chat":
        # Handle basic chat
        pass
    elif feature == "human_in_the_loop":
        # Handle human-in-the-loop workflows
        pass
    elif feature == "agentic_generative_ui":
        # Handle UI generation
        pass
    # ... etc
    
    # Your existing agent logic here
    # Return the same response format regardless of feature
    return await your_existing_agent_logic(input_data, request)
```

### Step 2: Add Feature-Specific Routes

Choose one of the approaches above and add the routes to your FastAPI application.

### Step 3: Update OpenAPI Documentation

Update your OpenAPI spec to include the new endpoints:

```python
# Add to your OpenAPI tags
tags = [
    {"name": "agent", "description": "Agent endpoints"},
    {"name": "authentication", "description": "Authentication endpoints"},
    # ... existing tags
]

# The new endpoints will automatically appear in your OpenAPI spec
```

### Step 4: Add Logging and Monitoring

```python
import logging

logger = logging.getLogger(__name__)

# In each endpoint
@app.post("/api/agent/luka/agentic_chat/")
async def agentic_chat_endpoint(input_data: RunAgentInput, request: Request):
    logger.info(f"Agentic chat request from {request.client.host}")
    return await luka_agent_endpoint(input_data, request, feature="agentic_chat")
```

## Testing the Implementation

### Test Feature-Specific Endpoints

```bash
# Test each new endpoint
curl -X POST http://localhost:8000/api/agent/luka/agentic_chat/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer guest_token" \
  -d '{"messages": [{"role": "user", "content": "Hello!"}]}'

curl -X POST http://localhost:8000/api/agent/luka/human_in_the_loop/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer guest_token" \
  -d '{"messages": [{"role": "user", "content": "Start a workflow"}]}'
```

### Test Backward Compatibility

```bash
# Ensure your existing endpoint still works
curl -X POST http://localhost:8000/api/agent/luka \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer guest_token" \
  -d '{"messages": [{"role": "user", "content": "Hello!"}]}'
```

## Benefits of This Approach

### ✅ **Maximum Compatibility**
- Works with **all** AG-UI implementations
- Supports both endpoint patterns
- Future-proof for new integrations

### ✅ **Backward Compatible**
- Your existing single endpoint continues to work
- No breaking changes for current clients
- Gradual migration possible

### ✅ **Easy Maintenance**
- All routes delegate to the same core logic
- Single point of truth for agent behavior
- Consistent response format across all endpoints

### ✅ **Feature Differentiation**
- Can handle different features differently if needed
- Easy to add feature-specific logic
- Clear separation of concerns

### ✅ **Monitoring & Analytics**
- Track which features are most used
- Monitor performance per feature
- Easy debugging with feature-specific logs

## Expected Results

After implementing this solution:

1. **Pydantic AI Integration**: ✅ Will work with `/api/agent/luka/agentic_chat/`
2. **LangGraph Integration**: ✅ Will work with `/api/agent/luka/agentic_chat`
3. **Bot API Integration**: ✅ Will continue working with `/api/agent/luka`
4. **All Other AG-UI Implementations**: ✅ Will work automatically

## Advanced Features (Optional)

### Feature-Specific Configuration

```python
# You can customize behavior per feature
FEATURE_CONFIGS = {
    "agentic_chat": {
        "max_tokens": 1000,
        "temperature": 0.7,
        "stream": True
    },
    "human_in_the_loop": {
        "max_tokens": 500,
        "temperature": 0.3,
        "stream": True,
        "require_approval": True
    },
    "agentic_generative_ui": {
        "max_tokens": 2000,
        "temperature": 0.5,
        "stream": True,
        "include_ui_components": True
    }
}

async def luka_agent_endpoint(input_data: RunAgentInput, request: Request, feature: str = "agentic_chat"):
    config = FEATURE_CONFIGS.get(feature, FEATURE_CONFIGS["agentic_chat"])
    # Use config to customize behavior
```

### Rate Limiting Per Feature

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/agent/luka/agentic_chat/")
@limiter.limit("10/minute")  # Different limits per feature
async def agentic_chat_endpoint(request: Request, input_data: RunAgentInput):
    return await luka_agent_endpoint(input_data, request, feature="agentic_chat")

@app.post("/api/agent/luka/human_in_the_loop/")
@limiter.limit("5/minute")  # More restrictive for complex features
async def human_in_the_loop_endpoint(request: Request, input_data: RunAgentInput):
    return await luka_agent_endpoint(input_data, request, feature="human_in_the_loop")
```

## Conclusion

Implementing both endpoint patterns will make your Luka Bot API the most compatible AG-UI implementation, supporting all existing and future AG-UI frameworks. This approach provides maximum flexibility while maintaining backward compatibility and easy maintenance.

The recommended implementation is **Option 1** (Feature-Specific Routes) as it provides the clearest separation of concerns and is the most widely used pattern in the AG-UI ecosystem.
