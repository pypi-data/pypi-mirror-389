"""
Streaming Think Endpoint

Provides real-time streaming responses from the Digital Twin.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import json
import asyncio
import os

# Import OpenAI
try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

# Import from parent directory
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dt_identity import DTIdentity

router = APIRouter()

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# Initialize OpenAI client
client = None
if AsyncOpenAI and OPENAI_API_KEY:
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    print(f"✅ Digital Twin Streaming: OpenAI client initialized with model: {LLM_MODEL}")
else:
    print(f"⚠️  Digital Twin Streaming: OpenAI not configured")


class StreamThinkRequest(BaseModel):
    """Request model for streaming think endpoint"""
    input: str
    conversation_id: Optional[str] = None
    context: Optional[Dict] = None
    history: Optional[List[Dict]] = None


async def stream_digital_twin_response(user_input: str, history: List[Dict], identity: DTIdentity):
    """
    Stream Digital Twin response using OpenAI's streaming API
    """
    if not client:
        yield f"data: {json.dumps({'type': 'error', 'error': 'OpenAI not configured'})}\n\n"
        return

    try:
        # Build messages for OpenAI
        messages = [
            {
                "role": "system",
                "content": f"""You are {identity.username}'s Digital Twin - an AI assistant that represents them in the digital world.

You are helpful, friendly, and intelligent. You can:
- Answer questions and provide information
- Help with tasks and problem-solving
- Have natural conversations
- Provide explanations and insights

You maintain the user's interests and preferences in mind while being helpful and engaging."""
            }
        ]
        
        # Add conversation history (last 10 messages for context)
        if history:
            for msg in history[-10:]:
                sender = msg.get("sender", "user")
                role = "assistant" if sender in ["assistant", "digital_twin"] else "user"
                content = msg.get("content", "")
                if content:
                    messages.append({
                        "role": role,
                        "content": content
                    })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": user_input
        })

        # Stream response from OpenAI
        stream = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            stream=True,
            temperature=0.7,
            max_tokens=2000
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                await asyncio.sleep(0)  # Allow other tasks to run

        yield f"data: {json.dumps({'type': 'done', 'metadata': {'dt_active': True, 'model': LLM_MODEL}})}\n\n"

    except Exception as e:
        print(f"❌ Error streaming Digital Twin response: {e}")
        yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"


@router.post("/")
async def stream_think(request: Request, req: StreamThinkRequest):
    """
    Streaming Digital Twin thinking/reasoning endpoint.
    
    Streams responses in real-time using Server-Sent Events (SSE).
    
    Requires: JWT authentication (user must be logged in)
    """
    print(f"🤖 Stream endpoint called with input: {req.input[:50]}...")
    
    # Extract JWT from Authorization header
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        print("❌ Missing or invalid authorization header")
        return StreamingResponse(
            iter([f"data: {json.dumps({'type': 'error', 'error': 'Missing or invalid authorization'})}\n\n"]),
            media_type="text/event-stream"
        )
    
    jwt_token = auth_header.replace("Bearer ", "")
    
    try:
        # Create DT identity from JWT
        identity = DTIdentity.from_jwt(jwt_token)
        print(f"✅ Digital Twin streaming for user: {identity.username}")
        
        # Check if OpenAI is configured
        if not client:
            print("❌ OpenAI client not configured")
            return StreamingResponse(
                iter([f"data: {json.dumps({'type': 'error', 'error': 'OpenAI not configured. Please set OPENAI_API_KEY.'})}\n\n"]),
                media_type="text/event-stream"
            )
        
        async def generate():
            try:
                # Send metadata first
                yield f"data: {json.dumps({'type': 'start', 'dt_id': identity.dt_id, 'user_id': identity.user_id})}\n\n"
                
                # Stream the response
                async for chunk in stream_digital_twin_response(req.input, req.history or [], identity):
                    yield chunk
                
                yield f"data: [DONE]\n\n"
            except Exception as e:
                print(f"❌ Error in generate: {e}")
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
        
    except ValueError as e:
        print(f"❌ JWT error: {e}")
        return StreamingResponse(
            iter([f"data: {json.dumps({'type': 'error', 'error': f'Invalid JWT: {str(e)}'})}\n\n"]),
            media_type="text/event-stream"
        )
    except Exception as e:
        print(f"❌ Error in stream think endpoint: {e}")
        import traceback
        traceback.print_exc()
        return StreamingResponse(
            iter([f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"]),
            media_type="text/event-stream"
        )


@router.get("/health")
async def health_check():
    """Check if streaming service is available."""
    return {
        "status": "ok" if client else "unavailable",
        "model": LLM_MODEL,
        "openai_configured": bool(OPENAI_API_KEY),
        "streaming_enabled": True
    }
