"""
Streaming Think Endpoint

Provides real-time streaming responses from the Digital Twin.
Unified endpoint with conversation + tool execution capabilities.
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
from dt_core import DigitalTwin
from execution_node import ExecutionNode

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


async def stream_digital_twin_response(user_input: str, history: List[Dict], identity: DTIdentity, dt: DigitalTwin):
    """
    Stream Digital Twin response with full capabilities:
    - Conversation via OpenAI streaming
    - Tool execution via ExecutionNode
    - Function calling for complex tasks
    """
    if not client:
        yield f"data: {json.dumps({'type': 'error', 'error': 'OpenAI not configured'})}\n\n"
        return

    try:
        # Send keepalive
        yield f": keepalive\n\n"
        
        # Discover tools if not already done
        if not dt.tools_discovered:
            yield f"data: {json.dumps({'type': 'status', 'message': 'Discovering available tools...'})}\n\n"
            yield f": keepalive\n\n"
            await dt.discover_tools()
            yield f"data: {json.dumps({'type': 'status', 'message': f'Found {len(dt.execution_node.tools)} tools'})}\n\n"
            yield f": keepalive\n\n"
        
        # Build messages for OpenAI
        system_prompt = dt.generate_system_prompt()
        messages = [{"role": "system", "content": system_prompt}]
        
        # Send keepalive while building context
        yield f": keepalive\n\n"
        
        # Add conversation history (last 10 messages for context)
        if history:
            for msg in history[-10:]:
                sender = msg.get("sender", "user")
                role = "assistant" if sender in ["assistant", "digital_twin"] else "user"
                content = msg.get("content", "")
                if content:
                    messages.append({"role": role, "content": content})
        
        # Add current user message
        messages.append({"role": "user", "content": user_input})

        # Prepare tools for function calling (if available)
        tools = None
        if len(dt.execution_node.tools) > 0:
            tools = [tool.to_openai_function() for tool in dt.execution_node.tools.values()]
        
        # Stream response from OpenAI with optional function calling
        stream_params = {
            "model": LLM_MODEL,
            "messages": messages,
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        # Add tools if available
        if tools:
            stream_params["tools"] = tools
            stream_params["tool_choice"] = "auto"

        stream = await client.chat.completions.create(**stream_params)

        tool_calls = []
        current_tool_call = {"id": "", "name": "", "arguments": ""}
        
        async for chunk in stream:
            delta = chunk.choices[0].delta
            
            # Handle regular content streaming
            if delta.content:
                content = delta.content
                yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                await asyncio.sleep(0)
            
            # Handle tool calls
            if delta.tool_calls:
                for tool_call_delta in delta.tool_calls:
                    if tool_call_delta.id:
                        current_tool_call["id"] = tool_call_delta.id
                    if tool_call_delta.function:
                        if tool_call_delta.function.name:
                            current_tool_call["name"] = tool_call_delta.function.name
                        if tool_call_delta.function.arguments:
                            current_tool_call["arguments"] += tool_call_delta.function.arguments
        
        # Execute tool calls if any
        if current_tool_call["name"]:
            yield f"data: {json.dumps({'type': 'tool_call', 'tool': current_tool_call['name']})}\n\n"
            
            try:
                # Parse arguments
                import json as json_lib
                tool_args = json_lib.loads(current_tool_call["arguments"])
                
                # Execute the tool
                result = await dt.execution_node.execute_as_user(
                    tool_name=current_tool_call["name"],
                    parameters=tool_args,
                    autonomous=False
                )
                
                tool_name = current_tool_call['name']
                yield f"data: {json.dumps({'type': 'tool_result', 'tool': tool_name, 'result': result})}\n\n"
                
                # Stream a follow-up message with the tool result
                if result.get("success"):
                    content_msg = f'\n\n✅ Executed: {tool_name}'
                    yield f"data: {json.dumps({'type': 'content', 'content': content_msg})}\n\n"
                else:
                    error_msg = result.get("error", "Unknown error")
                    content_msg = f'\n\n❌ Error: {error_msg}'
                    yield f"data: {json.dumps({'type': 'content', 'content': content_msg})}\n\n"
                    
            except Exception as e:
                error_str = str(e)
                yield f"data: {json.dumps({'type': 'error', 'error': f'Tool execution error: {error_str}'})}\n\n"

        tools_count = len(dt.execution_node.tools)
        yield f"data: {json.dumps({'type': 'done', 'metadata': {'dt_active': True, 'model': LLM_MODEL, 'tools_available': tools_count}})}\n\n"

    except Exception as e:
        print(f"❌ Error streaming Digital Twin response: {e}")
        import traceback
        traceback.print_exc()
        yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"


@router.post("/")
async def stream_think(request: Request, req: StreamThinkRequest):
    """
    Unified Streaming Digital Twin endpoint.
    
    This endpoint provides:
    - Real-time conversation streaming via OpenAI
    - Access to all local tools via ExecutionNode
    - Function calling for complex task execution
    - Full Digital Twin capabilities
    
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
                # Send start immediately to establish connection
                yield f"data: {json.dumps({'type': 'start', 'dt_id': identity.dt_id, 'user_id': identity.user_id, 'mode': 'full_capabilities'})}\n\n"
                
                # Send multiple keepalives quickly to prevent CDN timeout
                yield f": keepalive\n\n"
                await asyncio.sleep(0)
                yield f": keepalive\n\n"
                await asyncio.sleep(0)
                
                # Initialize Digital Twin (this might take a moment)
                print(f"🤖 Initializing Digital Twin with ExecutionNode...")
                dt = DigitalTwin(identity)
                print(f"✅ Digital Twin initialized")
                
                yield f": keepalive\n\n"
                await asyncio.sleep(0)
                
                # Stream the response with full DT capabilities
                async for chunk in stream_digital_twin_response(req.input, req.history or [], identity, dt):
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
