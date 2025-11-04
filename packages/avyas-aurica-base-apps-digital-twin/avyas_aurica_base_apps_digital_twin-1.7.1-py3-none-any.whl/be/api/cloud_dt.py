"""
Smart Cloud Digital Twin

This is a cloud-based DT that:
1. Responds directly to simple queries (no local execution needed)
2. For complex tasks, it provides connection info to user's local execution node
3. Acts as a bridge/router based on task complexity

This enables:
- Instant responses from anywhere (mobile, desktop)
- Local execution only when truly needed
- No polling required!
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import openai

# Import auth decorator
try:
    from src.aurica_auth import protected, get_current_user, public
except ImportError:
    def protected(func):
        return func
    def get_current_user(request, required=True):
        return type('User', (), {"username": "unknown", "user_id": "unknown"})()
    def public(func):
        return func
router = APIRouter()

# OpenAI configuration
openai.api_key = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")


class ThinkRequest(BaseModel):
    """Request for DT to think/respond"""
    input: str
    context: Optional[Dict[str, Any]] = None
    history: Optional[List[Dict[str, Any]]] = None  # Changed from Dict[str, str] to Dict[str, Any]


class SmartRoutingDecision(BaseModel):
    """Decision about where to execute"""
    execution_mode: str  # "cloud", "local", "hybrid"
    reason: str
    requires_local: bool
    local_capabilities_needed: List[str] = []


async def analyze_execution_needs(user_input: str, context: Dict) -> SmartRoutingDecision:
    """
    Analyze if task needs local execution or can run in cloud.
    
    Local execution needed for:
    - File system access
    - Running local apps/tools
    - Accessing local data
    - System commands
    
    Cloud execution sufficient for:
    - General conversation
    - Information queries
    - Advice/recommendations
    - Explanations
    """
    
    # Simple keyword detection (can be enhanced with LLM classification)
    local_keywords = [
        "file", "folder", "directory", "execute", "run", "install",
        "my computer", "my machine", "local", "system", "app",
        "weather", "profile", "dashboard"  # Your local apps
    ]
    
    user_input_lower = user_input.lower()
    needs_local = any(keyword in user_input_lower for keyword in local_keywords)
    
    if needs_local:
        return SmartRoutingDecision(
            execution_mode="local",
            reason="Task requires local execution node capabilities",
            requires_local=True,
            local_capabilities_needed=["execution_node", "local_apps"]
        )
    else:
        return SmartRoutingDecision(
            execution_mode="cloud",
            reason="Can be handled by cloud Digital Twin",
            requires_local=False
        )


@router.post("/cloud-think/")
@protected
async def cloud_think(request: Request, req: ThinkRequest):
    """
    Digital Twin thinking endpoint.
    
    This endpoint runs on the local execution node (accessed via tunnel from api.oneaurica.com)
    and has awareness of all 10 apps available on the execution node.
    """
    user = get_current_user(request)
    print(f"🤖 Digital Twin thinking for {user.username}")
    
    # Default values
    history = req.history or []
    context = req.context or {}
    
    # Build conversation for LLM with full app awareness
    messages = [
        {
            "role": "system",
            "content": f"""You are {user.username}'s Digital Twin - a helpful AI assistant running on their local execution node.

You have access to the following 10 apps on the execution node:
1. **app-manager** - Manages and lists installed applications
2. **app-sync** - Synchronizes and publishes apps to registry
3. **aurica-storage** - Handles file storage and S3 integration
4. **auth-app** - User authentication and authorization
5. **chat-app** - Chat interface for conversations
6. **dashboard-app** - System dashboard and statistics
7. **digital-twin** - Your core AI capabilities (this app)
8. **nl-generator** - Natural language app generation
9. **node-connection** - Node and tunnel management
10. **weather-app** - Weather information and forecasts

When users ask about your capabilities or available tools, mention these apps and explain what they do.

You provide clear, friendly, and intelligent responses. You can:
- Answer questions and provide information
- Explain what apps and tools are available
- Have natural conversations
- Provide insights about the system

Note: You're running on the execution node, so you have full access to all these apps."""
        }
    ]
    
    # Add history
    for msg in history[-10:]:  # Last 10 messages
        messages.append({
            "role": "user" if msg.get("sender") == "user" else "assistant",
            "content": msg.get("content", "")
        })
    
    # Add current input
    messages.append({
        "role": "user",
        "content": req.input
    })
    
    try:
        # Call OpenAI
        response = openai.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        ai_response = response.choices[0].message.content
        
        return {
            "dt_active": True,
            "execution_mode": "local_via_tunnel",
            "response": ai_response,
            "thought_process": "Running on local execution node with full app access",
            "tools_used": [],
            "dt_confidence": 0.9,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"❌ OpenAI error: {e}")
        return {
            "dt_active": False,
            "error": "llm_error",
            "response": f"I encountered an error: {str(e)}",
            "thought_process": "Failed to get LLM response"
        }

@router.post("/cloud-stream/")
@protected
async def cloud_stream(request: Request, req: ThinkRequest):
    """
    Streaming version of cloud-think endpoint.
    Streams responses in real-time using Server-Sent Events.
    """
    from fastapi.responses import StreamingResponse
    import json
    import asyncio
    
    user = get_current_user(request)
    print(f"🤖 Cloud DT streaming for user: {user.username}")
    print(f"   Input: {req.input[:100]}...")
    print(f"   History length: {len(req.history or [])}")
    print(f"   Context: {req.context}")
    
    # Default values
    history = req.history or []
    context = req.context or {}
    
    # Check if OpenAI is configured
    if not openai.api_key:
        def error_stream():
            yield f"data: {json.dumps({'type': 'error', 'error': 'OpenAI not configured'})}\n\n"
        
        return StreamingResponse(
            error_stream(),
            media_type="text/event-stream"
        )
    
    async def generate():
        try:
            # Send start message immediately to establish connection
            yield f"data: {json.dumps({'type': 'start', 'user': user.username})}\n\n"
            
            # Send a keepalive to ensure connection is established
            yield f": keepalive\n\n"
            await asyncio.sleep(0)
            
            # Build conversation for LLM
            messages = [
                {
                    "role": "system",
                    "content": f"""You are {user.username}'s Digital Twin - a helpful AI assistant running on their local execution node.

You have access to the following 10 apps on the execution node:
1. **app-manager** - Manages and lists installed applications
2. **app-sync** - Synchronizes and publishes apps to registry
3. **aurica-storage** - Handles file storage and S3 integration
4. **auth-app** - User authentication and authorization
5. **chat-app** - Chat interface for conversations
6. **dashboard-app** - System dashboard and statistics
7. **digital-twin** - Your core AI capabilities (this app)
8. **nl-generator** - Natural language app generation
9. **node-connection** - Node and tunnel management
10. **weather-app** - Weather information and forecasts

When users ask about your capabilities or available tools, mention these apps and explain what they do.

You provide clear, friendly, and intelligent responses. You can:
- Answer questions and provide information
- Explain what apps and tools are available
- Have natural conversations
- Provide insights about the system

Note: While you're aware of these apps, direct tool execution requires the full DT endpoint."""
                }
            ]
            
            # Add history
            for msg in history[-10:]:
                role = "assistant" if msg.get("sender") in ["assistant", "digital_twin"] else "user"
                messages.append({
                    "role": role,
                    "content": msg.get("content", "")
                })
            
            # Add current input
            messages.append({
                "role": "user",
                "content": req.input
            })
            
            # Send another keepalive before OpenAI call
            yield f": keepalive\n\n"
            await asyncio.sleep(0)
            
            # Stream from OpenAI
            response = openai.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
                stream=True
            )
            
            chunk_count = 0
            import time
            last_keepalive = time.time()
            
            for chunk in response:
                current_time = time.time()
                
                # Send keepalive every 1 second to prevent aggressive CDN timeout
                if current_time - last_keepalive > 1:
                    yield f": keepalive {current_time}\n\n"
                    last_keepalive = current_time
                    await asyncio.sleep(0)
                
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                    chunk_count += 1
                    last_keepalive = current_time  # Reset keepalive timer on actual content
                    await asyncio.sleep(0)
            
            yield f"data: {json.dumps({'type': 'done', 'metadata': {'dt_active': True}})}\n\n"
            yield f"data: [DONE]\n\n"
            
        except Exception as e:
            print(f"❌ Streaming error: {e}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream",
            "Transfer-Encoding": "chunked"
        }
    )


@router.get("/cloud-health/")
@public
async def cloud_health():
    """Health check for cloud DT"""
    return {
        "status": "healthy",
        "service": "cloud-digital-twin",
        "mode": "smart_routing",
        "capabilities": [
            "conversation",
            "information_queries",
            "recommendations",
            "routing_to_local",
            "streaming"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }
