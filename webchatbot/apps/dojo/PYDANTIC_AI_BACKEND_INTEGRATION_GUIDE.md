# Pydantic AI Backend Integration Guide for AG-UI/Dojo

## Overview

This guide provides comprehensive instructions for integrating your Pydantic AI backend with the AG-UI/Dojo frontend. The integration follows the AG-UI protocol, enabling seamless communication between your Python-based AI agents and the React frontend.

## Prerequisites

- Python environment with Pydantic AI installed
- FastAPI server setup
- Understanding of the AG-UI protocol
- Access to the Dojo frontend codebase

## Required Endpoints

Your Pydantic AI backend must implement the following endpoints to work with the Dojo frontend:

### Base Configuration
- **Base URL**: `http://localhost:9000` (configurable via `PYDANTIC_AI_URL` environment variable)
- **Protocol**: HTTP/HTTPS with JSON payloads
- **Authentication**: Bearer token support (optional)

### Required Feature Endpoints

#### 1. Agentic Chat (`/agentic_chat/`)
**Purpose**: Basic conversational AI functionality
**Method**: POST
**Request Format**:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Hello, how are you?"
    }
  ],
  "stream": true
}
```

**Response Format** (Streaming):
```json
{
  "type": "text",
  "content": "Hello! I'm doing well, thank you for asking."
}
```

#### 2. Agentic Generative UI (`/agentic_generative_ui/`)
**Purpose**: Dynamic UI generation based on user requests
**Method**: POST
**Request Format**:
```json
{
  "messages": [
    {
      "role": "user", 
      "content": "Create a task planner for my project"
    }
  ],
  "stream": true
}
```

**Response Format** (with UI components):
```json
{
  "type": "ui",
  "component": "TaskPlanner",
  "props": {
    "tasks": ["Research", "Design", "Implementation"],
    "status": "active"
  }
}
```

#### 3. Human in the Loop (`/human_in_the_loop/`)
**Purpose**: Interactive task approval and step-by-step workflows
**Method**: POST
**Request Format**:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Plan a recipe with eggs and oven steps"
    }
  ],
  "stream": true
}
```

**Response Format** (with interactive elements):
```json
{
  "type": "ui",
  "component": "StepSelector",
  "props": {
    "steps": [
      {"id": "1", "text": "Preheat oven to 350°F", "checked": true},
      {"id": "2", "text": "Beat eggs", "checked": false},
      {"id": "3", "text": "Mix ingredients", "checked": true}
    ],
    "onConfirm": "confirm_steps"
  }
}
```

#### 4. Shared State (`/shared_state/`)
**Purpose**: State management between UI components and chat
**Method**: POST
**Request Format**:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Give me a pasta recipe with Pasta as an ingredient"
    }
  ],
  "stream": true
}
```

**Response Format** (with shared state):
```json
{
  "type": "ui",
  "component": "RecipeCard",
  "props": {
    "ingredients": ["Pasta", "Tomato sauce", "Cheese"],
    "instructions": ["Boil pasta", "Heat sauce", "Combine"]
  },
  "state": {
    "recipe_id": "pasta_001",
    "servings": 4
  }
}
```

#### 5. Tool-Based Generative UI (`/tool_based_generative_ui/`)
**Purpose**: UI generation based on tool execution results
**Method**: POST
**Request Format**:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Search for weather information and display it"
    }
  ],
  "stream": true
}
```

**Response Format** (with tool results):
```json
{
  "type": "tool_result",
  "tool": "weather_search",
  "result": {
    "location": "New York",
    "temperature": "72°F",
    "condition": "Sunny"
  },
  "ui": {
    "component": "WeatherCard",
    "props": {
      "location": "New York",
      "temperature": "72°F",
      "condition": "Sunny"
    }
  }
}
```

#### 6. Backend Tool Rendering (`/backend_tool_rendering`)
**Purpose**: Visualization of backend tool execution
**Method**: POST
**Request Format**:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Execute a database query and show results"
    }
  ],
  "stream": true
}
```

**Response Format** (with tool visualization):
```json
{
  "type": "tool_execution",
  "tool": "database_query",
  "status": "completed",
  "result": {
    "rows": 5,
    "columns": ["id", "name", "email"]
  },
  "visualization": {
    "component": "DataTable",
    "props": {
      "data": [...],
      "columns": ["id", "name", "email"]
    }
  }
}
```

## Implementation Example

Here's a basic FastAPI implementation structure:

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import json

app = FastAPI(title="Pydantic AI AG-UI Integration")

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Dojo frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    stream: bool = True

class ChatResponse(BaseModel):
    type: str
    content: Optional[str] = None
    component: Optional[str] = None
    props: Optional[Dict[str, Any]] = None
    state: Optional[Dict[str, Any]] = None

@app.post("/agentic_chat/")
async def agentic_chat(request: ChatRequest):
    """Basic conversational AI endpoint"""
    try:
        # Process with your Pydantic AI agent
        response = await your_pydantic_agent.process(request.messages)
        
        return ChatResponse(
            type="text",
            content=response.content
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agentic_generative_ui/")
async def agentic_generative_ui(request: ChatRequest):
    """Dynamic UI generation endpoint"""
    try:
        # Process with your Pydantic AI agent
        response = await your_pydantic_agent.generate_ui(request.messages)
        
        return ChatResponse(
            type="ui",
            component=response.component,
            props=response.props
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/human_in_the_loop/")
async def human_in_the_loop(request: ChatRequest):
    """Human-in-the-loop workflow endpoint"""
    try:
        # Process with your Pydantic AI agent
        response = await your_pydantic_agent.create_workflow(request.messages)
        
        return ChatResponse(
            type="ui",
            component="StepSelector",
            props=response.steps
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/shared_state/")
async def shared_state(request: ChatRequest):
    """Shared state management endpoint"""
    try:
        # Process with your Pydantic AI agent
        response = await your_pydantic_agent.process_with_state(request.messages)
        
        return ChatResponse(
            type="ui",
            component=response.component,
            props=response.props,
            state=response.state
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tool_based_generative_ui/")
async def tool_based_generative_ui(request: ChatRequest):
    """Tool-based UI generation endpoint"""
    try:
        # Process with your Pydantic AI agent
        response = await your_pydantic_agent.execute_tools(request.messages)
        
        return ChatResponse(
            type="tool_result",
            tool=response.tool_name,
            result=response.result,
            ui=response.ui_component
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/backend_tool_rendering")
async def backend_tool_rendering(request: ChatRequest):
    """Backend tool rendering endpoint"""
    try:
        # Process with your Pydantic AI agent
        response = await your_pydantic_agent.render_tools(request.messages)
        
        return ChatResponse(
            type="tool_execution",
            tool=response.tool_name,
            status=response.status,
            result=response.result,
            visualization=response.visualization
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "pydantic-ai-ag-ui"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
```

## Key Implementation Requirements

### 1. Response Format Consistency
- All responses must follow the AG-UI protocol format
- Include proper `type` field to indicate response type
- Use consistent field names across all endpoints

### 2. Streaming Support
- Implement streaming responses for real-time updates
- Use Server-Sent Events (SSE) or WebSocket for streaming
- Handle connection management properly

### 3. Error Handling
- Return proper HTTP status codes
- Include descriptive error messages
- Handle timeout scenarios gracefully

### 4. CORS Configuration
- Allow requests from Dojo frontend (typically `http://localhost:3000`)
- Include necessary headers for AG-UI protocol
- Support preflight requests

### 5. Authentication (Optional)
- Implement Bearer token authentication if needed
- Validate tokens on protected endpoints
- Handle authentication errors appropriately

## Testing Your Integration

### 1. Health Check
```bash
curl http://localhost:9000/health
```

### 2. Test Agentic Chat
```bash
curl -X POST http://localhost:9000/agentic_chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": true
  }'
```

### 3. Test with Dojo Frontend
1. Set `PYDANTIC_AI_URL=http://localhost:9000` in your environment
2. Start the Dojo frontend: `npm run dev`
3. Navigate to `/pydantic-ai/feature/agentic_chat`
4. Test the chat functionality

## Common Issues and Solutions

### 1. CORS Errors
- Ensure CORS middleware is properly configured
- Check that frontend URL is in allowed origins
- Verify preflight request handling

### 2. Response Format Issues
- Validate response structure matches AG-UI protocol
- Check field names and types
- Ensure proper JSON serialization

### 3. Streaming Problems
- Implement proper streaming response handling
- Check connection management
- Verify frontend can handle streaming responses

### 4. Authentication Issues
- Validate token format and expiration
- Check authorization headers
- Implement proper error responses

## Advanced Features

### 1. Predictive State Updates (Currently Disabled)
This feature is temporarily disabled in the frontend due to production build issues. When implementing:
- Support for predictive UI updates
- State change notifications
- User approval workflows

### 2. Custom Tools Integration
- Implement custom tool execution
- Support tool result visualization
- Handle tool error scenarios

### 3. Multi-Agent Support
- Support multiple agent types
- Implement agent routing
- Handle agent-specific configurations

## Resources

- [Pydantic AI Documentation](https://ai.pydantic.dev/)
- [AG-UI Protocol Documentation](https://docs.ag-ui.com/)
- [Dojo Frontend Repository](https://github.com/your-org/dojo)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## Support

For integration support:
1. Check the Dojo frontend logs for error messages
2. Verify endpoint responses match the expected format
3. Test individual endpoints with curl or Postman
4. Review the AG-UI protocol documentation for updates

Remember to test your integration thoroughly with the Dojo frontend before deploying to production!
