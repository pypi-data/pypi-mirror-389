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
    print(f"💬 {user.username}: {req.input[:80]}...")
    if not openai.api_key:
        def error_stream():
            yield f"data: {json.dumps({'type': 'error', 'error': 'OpenAI not configured'})}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")
    async def generate():
        try:
            yield f"data: {json.dumps({'type': 'start'})}\n\n"
            yield f": keepalive\n\n"
            await asyncio.sleep(0)
            tool_map, apps_list = discover_tools()
            apps_text = "\\n".join(apps_list) if apps_list else "No tools"
            print(f"�� Discovered {len(tool_map)} tools")
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
            yield f": keepalive\n\n"
            response = openai.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                tools=openai_functions if openai_functions else None,
                tool_choice="auto" if openai_functions else None,
                temperature=0.7,
                max_tokens=2000
            )
            message = response.choices[0].message
            if message.tool_calls:
                newline = '\n'
                yield f"data: {json.dumps({'type': 'content', 'content': f'⚡ Executing...{newline}{newline}'})}\n\n"
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                    yield f"data: {json.dumps({'type': 'content', 'content': f'• Calling {function_name}(){newline}'})}\n\n"
                    
                    if function_name in tool_map:
                        tool_info = tool_map[function_name]
                        url = f"http://localhost:8000/{tool_info['app']}{tool_info['endpoint']}"
                        print(f"🔧 Calling: {tool_info['method']} {url}")
                        print(f"   Auth token length: {len(auth_token)}")
                        print(f"   Args: {function_args}")
                        
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
                                else:
                                    error_text = result.text[:200]
                                    content = f'❌ Error {result.status_code}: {error_text}{newline}'
                                    yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                        except Exception as e:
                            content = f'❌ Exception: {str(e)}{newline}'
                            yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                    await asyncio.sleep(0)
            else:
                content = message.content or "Not sure how to help."
                for char in content:
                    yield f"data: {json.dumps({'type': 'content', 'content': char})}\n\n"
                    await asyncio.sleep(0.01)
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            yield f"data: [DONE]\n\n"
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"})

@router.get("/health/")
@public
async def health():
    tool_map, _ = discover_tools()
    return {"status": "healthy", "service": "digital-life-manager", "tools_count": len(tool_map), "timestamp": datetime.utcnow().isoformat()}
