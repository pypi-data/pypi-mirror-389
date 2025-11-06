"""
Digital Twin Chat API

Modern streaming chat interface for the Digital Twin.
Uses the full DigitalTwin class with ExecutionNode for comprehensive app discovery.
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import asyncio
import sys
from pathlib import Path

# Import Aurica Auth SDK
from src.aurica_auth import protected, get_current_user, public

# Import Digital Twin core
sys.path.insert(0, str(Path(__file__).parent.parent))

from dt_core import DigitalTwin
from dt_identity import DTIdentity

router = APIRouter()



class ChatRequest(BaseModel):
    """Chat request model"""
    input: str
    context: Optional[Dict[str, Any]] = None
    history: Optional[List[Dict[str, Any]]] = None


@router.post("/stream/")
@protected
async def chat_stream(request: Request, req: ChatRequest):
    """
    Streaming chat endpoint for Digital Twin.
    
    Uses the full DigitalTwin architecture with:
    - Automatic app discovery from OpenAPI schemas
    - Tool execution with autonomy control
    - Comprehensive capabilities awareness
    """
    user = get_current_user(request)
    
    # Extract JWT from Authorization header
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    jwt_token = auth_header.replace("Bearer ", "")
    
    print("=" * 80)
    print(f"🎯 Digital Twin Chat Stream - User: {user.username}")
    print(f"📥 Input: {req.input[:100]}...")
    print(f"📜 History items: {len(req.history) if req.history else 0}")
    print("=" * 80)
    
    async def generate():
        try:
            # Send start event immediately
            yield f"data: {json.dumps({'type': 'start', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
            await asyncio.sleep(0)
            
            # Keepalive
            yield f": keepalive-init\n\n"
            await asyncio.sleep(0)
            
            # Send thinking status
            yield f"data: {json.dumps({'type': 'thinking', 'message': 'Initializing Digital Twin...'})}\n\n"
            await asyncio.sleep(0)
            
            try:
                # Create DT identity from JWT
                identity = DTIdentity.from_jwt(jwt_token)
                
                # Initialize Digital Twin
                dt = DigitalTwin(identity)
                
                # Discover tools on first use
                if not dt.tools_discovered:
                    yield f"data: {json.dumps({'type': 'status', 'message': 'Discovering apps and tools...'})}\n\n"
                    await asyncio.sleep(0)
                    
                    await dt.discover_tools()
                    
                    # Report discovery
                    apps_count = len(dt.execution_node.apps_discovered)
                    tools_count = len(dt.execution_node.tools)
                    yield f"data: {json.dumps({'type': 'status', 'message': f'Found {apps_count} apps with {tools_count} tools'})}\n\n"
                    await asyncio.sleep(0)
                
                # Send thinking status
                yield f"data: {json.dumps({'type': 'thinking', 'message': 'Thinking...'})}\n\n"
                await asyncio.sleep(0)
                
                # DT thinks about the input
                result = await dt.think(
                    user_input=req.input,
                    context=req.context,
                    history=req.history
                )
                
                # Stream the response
                response_text = result.get("response", "")
                
                # If there were tool calls, include them in the response
                tool_calls = result.get("tool_calls", [])
                if tool_calls:
                    yield f"data: {json.dumps({'type': 'content', 'content': '⚡ Executing tools...\\n\\n'})}\n\n"
                    await asyncio.sleep(0)
                    
                    for tool_call in tool_calls:
                        tool_name = tool_call.get("tool")
                        tool_result = tool_call.get("result", {})
                        
                        # Show tool execution
                        content = f"• {tool_name}\\n"
                        yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                        await asyncio.sleep(0)
                        
                        # Show result if successful
                        if tool_result.get("success"):
                            result_data = tool_result.get("data", {})
                            result_str = json.dumps(result_data, indent=2)
                            content = f"✅ Result:\\n```json\\n{result_str}\\n```\\n\\n"
                            yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                            await asyncio.sleep(0)
                        else:
                            error_msg = tool_result.get("error", "Unknown error")
                            content = f"❌ Error: {error_msg}\\n\\n"
                            yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                            await asyncio.sleep(0)
                
                # Stream the main response character by character
                char_count = 0
                for char in response_text:
                    yield f"data: {json.dumps({'type': 'content', 'content': char})}\n\n"
                    char_count += 1
                    
                    # Keepalive every 50 characters
                    if char_count % 50 == 0:
                        yield f": keepalive-char-{char_count}\n\n"
                    
                    await asyncio.sleep(0.01)
                
                # Done
                yield f"data: {json.dumps({'type': 'done', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
                await asyncio.sleep(0)
                yield f"data: [DONE]\n\n"
                
            except ValueError as e:
                error_msg = f"Authentication error: {str(e)}"
                print(f"❌ {error_msg}")
                yield f"data: {json.dumps({'type': 'error', 'error': error_msg})}\n\n"
                
            except Exception as e:
                error_msg = f"Digital Twin error: {str(e)}"
                print(f"❌ {error_msg}")
                import traceback
                traceback.print_exc()
                yield f"data: {json.dumps({'type': 'error', 'error': error_msg})}\n\n"
        
        except Exception as e:
            print(f"❌ Stream generation error: {e}")
            import traceback
            traceback.print_exc()
            try:
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
            except:
                pass
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream",
            "Transfer-Encoding": "chunked",
            "X-Content-Type-Options": "nosniff"
        }
    )


@router.post("/")
@protected
async def chat_non_streaming(request: Request, req: ChatRequest):
    """
    Non-streaming chat endpoint for Digital Twin.
    Returns the complete response at once.
    """
    user = get_current_user(request)
    
    # Extract JWT from Authorization header
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    jwt_token = auth_header.replace("Bearer ", "")
    
    print(f"💬 Digital Twin Chat (non-streaming) - User: {user.username}: {req.input[:80]}...")
    
    try:
        # Create DT identity from JWT
        identity = DTIdentity.from_jwt(jwt_token)
        
        # Initialize Digital Twin
        dt = DigitalTwin(identity)
        
        # Discover tools on first use
        if not dt.tools_discovered:
            print("🔍 Discovering tools...")
            await dt.discover_tools()
            print(f"✅ Discovered {len(dt.execution_node.apps_discovered)} apps, {len(dt.execution_node.tools)} tools")
        
        # DT thinks about the input
        result = await dt.think(
            user_input=req.input,
            context=req.context,
            history=req.history
        )
        
        # Build response content
        content = ""
        
        # Add tool execution info if present
        tool_calls = result.get("tool_calls", [])
        if tool_calls:
            content += "⚡ Tool Execution:\\n\\n"
            for tool_call in tool_calls:
                tool_name = tool_call.get("tool")
                tool_result = tool_call.get("result", {})
                content += f"• {tool_name}\\n"
                
                if tool_result.get("success"):
                    result_data = tool_result.get("data", {})
                    result_str = json.dumps(result_data, indent=2)
                    content += f"✅ Result:\\n```json\\n{result_str}\\n```\\n\\n"
                else:
                    error_msg = tool_result.get("error", "Unknown error")
                    content += f"❌ Error: {error_msg}\\n\\n"
        
        # Add main response
        content += result.get("response", "")
        
        return {
            "type": "success",
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "dt_active": True,
            "tools_available": len(dt.execution_node.tools)
        }
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")
    
    except Exception as e:
        print(f"❌ Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Digital Twin error: {str(e)}")


@router.get("/health/")
@public
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "digital-twin",
        "version": "1.0.0",
        "dt_active": True,
        "timestamp": datetime.utcnow().isoformat()
    }

