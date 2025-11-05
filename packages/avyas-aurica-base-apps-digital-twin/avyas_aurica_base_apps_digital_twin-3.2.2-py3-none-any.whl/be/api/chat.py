"""Digital Life Manager - AI that executes tools"""
from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import openai
import json
import httpx
from pathlib import Path

try:
    from src.aurica_auth import protected, get_current_user, public
except ImportError:
    def protected(func): return func
    def get_current_user(request, required=True):
        return type('User', (), {"username": "unknown", "user_id": "unknown"})()
    def public(func): return func

def discover_tools():
    apps_dir = Path(os.getenv("APPS_DIR", "/Users/amit/aurica/code/apps"))
    tool_map = {}
    apps_list = []
    if not apps_dir.exists():
        return tool_map, apps_list
    for app_dir in apps_dir.iterdir():
        if not app_dir.is_dir():
            continue
        app_json = app_dir / "app.json"
        if not app_json.exists():
            continue
        try:
            with open(app_json) as f:
                app_data = json.load(f)
            dt_tools = app_data.get("dt_tools", [])
            if dt_tools:
                app_name = app_data.get("name", app_dir.name)
                tool_names = []
                for tool in dt_tools:
                    tool_name = tool.get("name")
                    if tool_name:
                        tool_map[tool_name] = {
                            "app": app_name,
                            "endpoint": tool.get("endpoint"),
                            "method": tool.get("method", "GET"),
                            "description": tool.get("description", ""),
                            "parameters": tool.get("parameters", {}),
                        }
                        tool_names.append(tool_name)
                if tool_names:
                    apps_list.append(f"{app_name}: {', '.join(tool_names)}")
        except Exception as e:
            print(f"Error loading {app_dir.name}: {e}")
    return tool_map, apps_list

router = APIRouter()
openai.api_key = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

class ThinkRequest(BaseModel):
    input: str
    context: Optional[Dict[str, Any]] = None
    history: Optional[List[Dict[str, Any]]] = None

@router.post("/stream/")
@protected
async def chat_stream(request: Request, req: ThinkRequest):
    from fastapi.responses import StreamingResponse
    import asyncio
    
    user = get_current_user(request)
    auth_token = request.headers.get("authorization", "").replace("Bearer ", "")
    
    # Log immediately to confirm endpoint is reached
    print("=" * 80)
    print(f"🎯 STREAM ENDPOINT HIT - User: {user.username}")
    print(f"📥 Input: {req.input[:80]}...")
    print(f"📜 History items: {len(req.history) if req.history else 0}")
    print(f"🔑 Auth token present: {bool(auth_token)}")
    print("=" * 80)
    
    if not openai.api_key:
        print("❌ OpenAI API key not configured!")
        async def error_stream():
            yield f"data: {json.dumps({'type': 'error', 'error': 'OpenAI not configured'})}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")
    
    async def generate():
        # CRITICAL: Log BEFORE any async operations
        print("🌊 Starting stream generation...")
        
        try:
            # CRITICAL: Send data immediately to prevent proxy timeout
            # This MUST be the very first thing yielded
            yield f"data: {json.dumps({'type': 'start', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
            
            print("✅ First data yielded")
            
            # Immediately yield keepalive
            yield f": keepalive {datetime.utcnow().isoformat()}\n\n"
            
            print("✅ Keepalive sent")
            # Send thinking status immediately
            yield f"data: {json.dumps({'type': 'thinking', 'message': 'Processing your request...'})}\n\n"
            await asyncio.sleep(0)
            
            tool_map, apps_list = discover_tools()
            apps_text = "\\n".join(apps_list) if apps_list else "No tools"
            print(f"🛠️ Discovered {len(tool_map)} tools")
            
            # Send status update
            yield f"data: {json.dumps({'type': 'status', 'message': f'Found {len(tool_map)} tools'})}\n\n"
            await asyncio.sleep(0)
            
            openai_functions = []
            for tool_name, tool_info in tool_map.items():
                openai_functions.append({
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "description": f"{tool_info['description']} [App: {tool_info['app']}]",
                        "parameters": tool_info['parameters']
                    }
                })
            messages = [{
                "role": "system",
                "content": f"You are {user.username}'s Digital Life Manager. AVAILABLE TOOLS: {apps_text}. When asked to do something, USE THE TOOLS."
            }]
            for msg in (req.history or [])[-10:]:
                role = "assistant" if msg.get("sender") in ["assistant", "digital_twin"] else "user"
                messages.append({"role": role, "content": msg.get("content", "")})
            messages.append({"role": "user", "content": req.input})
            
            # Send another status before calling OpenAI
            yield f"data: {json.dumps({'type': 'status', 'message': 'Thinking...'})}\n\n"
            await asyncio.sleep(0)
            
            # Use OpenAI streaming to keep connection alive
            print("🤖 Calling OpenAI API...")
            try:
                stream = openai.chat.completions.create(
                    model=LLM_MODEL,
                    messages=messages,
                    tools=openai_functions if openai_functions else None,
                    tool_choice="auto" if openai_functions else None,
                    temperature=0.7,
                    max_tokens=2000,
                    timeout=45.0,
                    stream=True  # Enable streaming to prevent timeouts
                )
                
                print("✅ OpenAI stream created successfully")
                
                # Send keepalive before starting to process stream
                yield f": keepalive-stream-start\n\n"
                await asyncio.sleep(0)
                
                # Collect streamed response
                collected_messages = []
                tool_calls_accumulator = []
                chunk_count = 0
                
                for chunk in stream:
                    chunk_count += 1
                    # Send keepalive every 10 chunks to prevent timeout
                    if chunk_count % 10 == 0:
                        yield f": keepalive-chunk-{chunk_count}\n\n"
                        await asyncio.sleep(0)
                    
                    collected_messages.append(chunk)
                    delta = chunk.choices[0].delta
                    
                    # Accumulate tool calls if present
                    if delta.tool_calls:
                        for tc in delta.tool_calls:
                            # Extend tool_calls_accumulator if needed
                            while len(tool_calls_accumulator) <= tc.index:
                                tool_calls_accumulator.append({
                                    "id": "",
                                    "type": "function",
                                    "function": {"name": "", "arguments": ""}
                                })
                            
                            if tc.id:
                                tool_calls_accumulator[tc.index]["id"] = tc.id
                            if tc.function.name:
                                tool_calls_accumulator[tc.index]["function"]["name"] += tc.function.name
                            if tc.function.arguments:
                                tool_calls_accumulator[tc.index]["function"]["arguments"] += tc.function.arguments
                
                # Reconstruct message from stream
                class Message:
                    def __init__(self):
                        self.content = None
                        self.tool_calls = None
                        
                        # Get content from last chunk
                        for chunk in collected_messages:
                            if chunk.choices[0].delta.content:
                                if self.content is None:
                                    self.content = ""
                                self.content += chunk.choices[0].delta.content
                        
                        # Create tool_calls if we have any
                        if tool_calls_accumulator:
                            self.tool_calls = []
                            for tc in tool_calls_accumulator:
                                tool_call = type('ToolCall', (), {
                                    'id': tc['id'],
                                    'type': tc['type'],
                                    'function': type('Function', (), {
                                        'name': tc['function']['name'],
                                        'arguments': tc['function']['arguments']
                                    })()
                                })()
                                self.tool_calls.append(tool_call)
                
                message = Message()
                
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'error': f'OpenAI error: {str(e)}'})}\n\n"
                return
            
            if message.tool_calls:
                newline = '\n'
                yield f"data: {json.dumps({'type': 'content', 'content': f'⚡ Executing...{newline}{newline}'})}\n\n"
                await asyncio.sleep(0)
                
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                    yield f"data: {json.dumps({'type': 'content', 'content': f'• Calling {function_name}(){newline}'})}\n\n"
                    await asyncio.sleep(0)
                    
                    if function_name in tool_map:
                        tool_info = tool_map[function_name]
                        url = f"http://localhost:8000/{tool_info['app']}{tool_info['endpoint']}"
                        print(f"🔧 Calling: {tool_info['method']} {url}")
                        print(f"   Auth token length: {len(auth_token)}")
                        print(f"   Args: {function_args}")
                        
                        # Send keepalive before tool call
                        yield f": keepalive-before-tool-{function_name}\n\n"
                        await asyncio.sleep(0)
                        
                        try:
                            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                                headers = {"Authorization": f"Bearer {auth_token}"}
                                if tool_info['method'] == "GET":
                                    result = await client.get(url, headers=headers)
                                elif tool_info['method'] == "POST":
                                    result = await client.post(url, json=function_args, headers=headers)
                                else:
                                    result = await client.request(tool_info['method'], url, json=function_args, headers=headers)
                                
                                newline = '\n'
                                if result.status_code == 200:
                                    result_data = result.json()
                                    result_str = json.dumps(result_data, indent=2)
                                    content = f'✅ {function_name}:{newline}```json{newline}{result_str}{newline}```{newline}{newline}'
                                    yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                                    await asyncio.sleep(0)
                                else:
                                    error_text = result.text[:200]
                                    content = f'❌ Error {result.status_code}: {error_text}{newline}'
                                    yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                                    await asyncio.sleep(0)
                        except Exception as e:
                            content = f'❌ Exception: {str(e)}{newline}'
                            yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                            await asyncio.sleep(0)
                    
                    # Send keepalive after each tool
                    yield f": keepalive-after-tool-{function_name}\n\n"
                    await asyncio.sleep(0)
            else:
                content = message.content or "Not sure how to help."
                # Stream character by character but with keepalives
                char_count = 0
                for char in content:
                    yield f"data: {json.dumps({'type': 'content', 'content': char})}\n\n"
                    char_count += 1
                    # Send keepalive every 50 characters
                    if char_count % 50 == 0:
                        yield f": keepalive-char-{char_count}\n\n"
                    await asyncio.sleep(0.01)
            
            # Final messages
            print("🎉 Stream completed successfully")
            yield f"data: {json.dumps({'type': 'done', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
            await asyncio.sleep(0)
            yield f"data: [DONE]\n\n"
        except Exception as e:
            print(f"❌ Stream Error: {e}")
            print(f"   Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            # Try to send error to client
            try:
                yield f"data: {json.dumps({'type': 'error', 'error': str(e), 'error_type': type(e).__name__})}\n\n"
            except:
                pass  # If we can't even send the error, just let it fail
    
    
    print("📤 Returning StreamingResponse with immediate execution...")
    
    # CRITICAL: Headers to prevent buffering and timeouts
    # Use StreamingResponse which will start consuming the generator immediately
    response = StreamingResponse(
        generate(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Content-Type": "text/event-stream",
            "Transfer-Encoding": "chunked",
            # Additional headers for Cloudflare/DigitalOcean
            "X-Content-Type-Options": "nosniff"
        }
    )
    
    print("✅ StreamingResponse created and ready to stream")
    return response


@router.post("/")
@protected
async def chat_non_streaming(request: Request, req: ThinkRequest):
    """
    Non-streaming fallback endpoint for environments that don't support SSE.
    Returns the complete response at once.
    """
    import asyncio
    user = get_current_user(request)
    auth_token = request.headers.get("authorization", "").replace("Bearer ", "")
    
    print(f"💬 Non-streaming request from {user.username}: {req.input[:80]}...")
    
    if not openai.api_key:
        return {"error": "OpenAI not configured", "type": "error"}
    
    try:
        tool_map, apps_list = discover_tools()
        apps_text = "\\n".join(apps_list) if apps_list else "No tools"
        
        openai_functions = []
        for tool_name, tool_info in tool_map.items():
            openai_functions.append({
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": f"{tool_info['description']} [App: {tool_info['app']}]",
                    "parameters": tool_info['parameters']
                }
            })
        
        messages = [{
            "role": "system",
            "content": f"You are {user.username}'s Digital Life Manager. AVAILABLE TOOLS: {apps_text}. When asked to do something, USE THE TOOLS."
        }]
        
        for msg in (req.history or [])[-10:]:
            role = "assistant" if msg.get("sender") in ["assistant", "digital_twin"] else "user"
            messages.append({"role": role, "content": msg.get("content", "")})
        messages.append({"role": "user", "content": req.input})
        
        # Call OpenAI (non-streaming)
        response = openai.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            tools=openai_functions if openai_functions else None,
            tool_choice="auto" if openai_functions else None,
            temperature=0.7,
            max_tokens=2000,
            timeout=45.0
        )
        
        message = response.choices[0].message
        result_content = ""
        
        # Handle tool calls
        if message.tool_calls:
            result_content += "⚡ Executing...\\n\\n"
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                result_content += f"• Calling {function_name}()\\n"
                
                if function_name in tool_map:
                    tool_info = tool_map[function_name]
                    url = f"http://localhost:8000/{tool_info['app']}{tool_info['endpoint']}"
                    
                    try:
                        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                            headers = {"Authorization": f"Bearer {auth_token}"}
                            if tool_info['method'] == "GET":
                                tool_result = await client.get(url, headers=headers)
                            elif tool_info['method'] == "POST":
                                tool_result = await client.post(url, json=function_args, headers=headers)
                            else:
                                tool_result = await client.request(tool_info['method'], url, json=function_args, headers=headers)
                            
                            if tool_result.status_code == 200:
                                result_data = tool_result.json()
                                result_str = json.dumps(result_data, indent=2)
                                result_content += f'✅ {function_name}:\\n```json\\n{result_str}\\n```\\n\\n'
                            else:
                                result_content += f'❌ Error {tool_result.status_code}\\n'
                    except Exception as e:
                        result_content += f'❌ Exception: {str(e)}\\n'
        else:
            result_content = message.content or "Not sure how to help."
        
        return {
            "type": "success",
            "content": result_content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error in non-streaming endpoint: {e}")
        import traceback
        traceback.print_exc()
        return {
            "type": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }


@router.get("/health/")
@public
async def health():
    tool_map, _ = discover_tools()
    return {"status": "healthy", "service": "digital-life-manager", "tools_count": len(tool_map), "timestamp": datetime.utcnow().isoformat()}
