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
    history: Optional[List[Dict[str, str]]] = None


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
    Smart cloud-based thinking endpoint.
    
    This DT:
    - Responds directly when possible (fast!)
    - Routes to local when needed
    - Never polls - instant decisions
    """
    user = get_current_user(request)
    
    # Analyze execution needs
    routing = await analyze_execution_needs(req.input, req.context)
    
    if not routing.requires_local:
        # Handle in cloud - instant response!
        print(f"☁️ Handling in cloud for {user.username}")
        
        # Build conversation for LLM
        messages = [
            {
                "role": "system",
                "content": """You are a helpful Digital Twin assistant. You're running in the cloud,
so you can answer questions, provide information, and have conversations, but you cannot
access the user's local files or execute local commands.

If the user asks for something that requires local access, politely explain that they
need their local execution node running for that."""
            }
        ]
        
        # Add history
        for msg in req.history[-10:]:  # Last 10 messages
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
                "execution_mode": "cloud",
                "response": ai_response,
                "thought_process": "Handled directly in cloud - no local execution needed",
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
    
    else:
        # Needs local execution
        print(f"🏠 Requires local execution for {user.username}")
        
        return {
            "dt_active": False,
            "execution_mode": "local_required",
            "response": """🏠 This task requires your local execution node.

Your Digital Twin can handle this, but it needs to run on your computer where it can access local apps and files.

**To enable local execution:**
1. Your backend is already running at `localhost:8000`
2. Your Digital Twin is loaded and ready
3. Just make sure you're accessing it from `localhost:8000/chat-app/` when you need local execution

**Why?**
When you chat from `api.oneaurica.com`, I'm running in the cloud and can't access your local machine.
When you chat from `localhost:8000`, I can access your local apps directly!

Would you like me to help with something else, or would you prefer to switch to your local chat?""",
            "thought_process": "Task needs local capabilities - user should use localhost interface",
            "requires_local": True,
            "local_capabilities_needed": routing.local_capabilities_needed,
            "suggestion": "Access chat from localhost:8000/chat-app/ for local execution"
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
            # Send start message immediately to prevent timeout
            yield f"data: {json.dumps({'type': 'start', 'user': user.username})}\n\n"
            await asyncio.sleep(0)
            
            # Build conversation for LLM
            messages = [
                {
                    "role": "system",
                    "content": f"""You are {user.username}'s Digital Twin - a helpful AI assistant.

You provide clear, friendly, and intelligent responses. You can help with:
- Answering questions
- Providing information and explanations  
- Creative tasks and problem-solving
- General conversation

You're currently running in the cloud, so you can't access local files or apps."""
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
            
            # Stream from OpenAI
            response = openai.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
                stream=True
            )
            
            chunk_count = 0
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                    chunk_count += 1
                    await asyncio.sleep(0)
                elif chunk_count % 10 == 0:
                    # Send keepalive comment every 10 empty chunks
                    yield f": keepalive\n\n"
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
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
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
