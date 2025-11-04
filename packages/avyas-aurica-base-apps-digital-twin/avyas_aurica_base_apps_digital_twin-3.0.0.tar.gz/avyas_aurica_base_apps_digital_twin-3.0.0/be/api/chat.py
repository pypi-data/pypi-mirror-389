"""""""""

Digital Life Manager - AI that actually executes tools

"""Digital Life Manager - Simple & EffectiveDigital Life Manager



from fastapi import APIRouter, Request

from pydantic import BaseModel

from typing import List, Optional, Dict, AnyYour AI that actually DOES things, not just talks about them.Your personal AI that runs on your local machine and can:

from datetime import datetime

import os"""- Access and use all installed apps

import openai

import json- Read/write files on your local OS

import httpx

from pathlib import Pathfrom fastapi import APIRouter, Request- Execute commands and automate tasks



# Import authfrom pydantic import BaseModel- Manage your digital life with context awareness

try:

    from src.aurica_auth import protected, get_current_user, publicfrom typing import List, Optional, Dict, Any"""

except ImportError:

    def protected(func): return funcfrom datetime import datetime

    def get_current_user(request, required=True):

        return type('User', (), {"username": "unknown", "user_id": "unknown"})()import osfrom fastapi import APIRouter, Request

    def public(func): return func

import openaifrom pydantic import BaseModel



def discover_tools():import jsonfrom typing import List, Optional, Dict, Any

    """Discover all apps with dt_tools"""

    apps_dir = Path(os.getenv("APPS_DIR", "/Users/amit/aurica/code/apps"))import httpxfrom datetime import datetime

    tool_map = {}

    apps_list = []import os

    

    if not apps_dir.exists():# Import authimport openai

        return tool_map, apps_list

    try:import json

    for app_dir in apps_dir.iterdir():

        if not app_dir.is_dir():    from src.aurica_auth import protected, get_current_user, public

            continue

        except ImportError:# Import auth

        app_json = app_dir / "app.json"

        if not app_json.exists():    def protected(func): return functry:

            continue

            def get_current_user(request, required=True):    from src.aurica_auth import protected, get_current_user, public

        try:

            with open(app_json) as f:        return type('User', (), {"username": "unknown", "user_id": "unknown"})()except ImportError:

                app_data = json.load(f)

                def public(func): return func    def protected(func): return func

            dt_tools = app_data.get("dt_tools", [])

            if dt_tools:    def get_current_user(request, required=True):

                app_name = app_data.get("name", app_dir.name)

                tool_names = []# Discover tools        return type('User', (), {"username": "unknown", "user_id": "unknown"})()

                

                for tool in dt_tools:from pathlib import Path    def public(func): return func

                    tool_name = tool.get("name")

                    if tool_name:

                        tool_map[tool_name] = {

                            "app": app_name,def discover_tools():# Import execution node for app discovery

                            "endpoint": tool.get("endpoint"),

                            "method": tool.get("method", "GET"),    """Discover all apps with dt_tools and return mapping"""try:

                            "description": tool.get("description", ""),

                            "parameters": tool.get("parameters", {}),    apps_dir = Path(os.getenv("APPS_DIR", "/Users/amit/aurica/code/apps"))    from pathlib import Path

                        }

                        tool_names.append(tool_name)    tool_map = {}  # tool_name -> {app, endpoint, method, ...}    import json

                

                if tool_names:        

                    apps_list.append(f"{app_name}: {', '.join(tool_names)}")

        except Exception as e:    if not apps_dir.exists():    def discover_tools():

            print(f"Error loading {app_dir.name}: {e}")

            return {}, []        """Discover all apps with dt_tools"""

    return tool_map, apps_list

            apps_dir = Path(os.getenv("APPS_DIR", "/Users/amit/aurica/code/apps"))



router = APIRouter()    apps_list = []        tools_by_app = {}



openai.api_key = os.getenv("OPENAI_API_KEY")    for app_dir in apps_dir.iterdir():        

LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

        if not app_dir.is_dir():        if not apps_dir.exists():



class ThinkRequest(BaseModel):            continue            return {}

    input: str

    context: Optional[Dict[str, Any]] = None                

    history: Optional[List[Dict[str, Any]]] = None

        app_json = app_dir / "app.json"        for app_dir in apps_dir.iterdir():



@router.post("/stream/")        if not app_json.exists():            if not app_dir.is_dir():

@protected

async def chat_stream(request: Request, req: ThinkRequest):            continue                continue

    """Main chat endpoint - executes tools and streams results"""

    from fastapi.responses import StreamingResponse                    

    import asyncio

            try:            app_json = app_dir / "app.json"

    user = get_current_user(request)

    auth_token = request.headers.get("authorization", "").replace("Bearer ", "")            with open(app_json) as f:            if not app_json.exists():

    

    print(f"💬 {user.username}: {req.input[:80]}...")                app_data = json.load(f)                continue

    

    if not openai.api_key:                        

        def error_stream():

            yield f"data: {json.dumps({'type': 'error', 'error': 'OpenAI not configured'})}\n\n"            dt_tools = app_data.get("dt_tools", [])            try:

        return StreamingResponse(error_stream(), media_type="text/event-stream")

                if dt_tools:                with open(app_json) as f:

    async def generate():

        try:                app_name = app_data.get("name", app_dir.name)                    app_data = json.load(f)

            yield f"data: {json.dumps({'type': 'start'})}\n\n"

            yield f": keepalive\n\n"                tool_names = []                

            await asyncio.sleep(0)

                                            dt_tools = app_data.get("dt_tools", [])

            # Discover tools

            tool_map, apps_list = discover_tools()                for tool in dt_tools:                if dt_tools:

            apps_text = "\n".join(apps_list) if apps_list else "No tools available"

                                tool_name = tool.get("name")                    app_name = app_data.get("name", app_dir.name)

            print(f"🔧 Discovered {len(tool_map)} tools from {len(apps_list)} apps")

                                if tool_name:                    tools_by_app[app_name] = dt_tools

            # Build OpenAI functions

            openai_functions = []                        tool_map[tool_name] = {            except Exception:

            for tool_name, tool_info in tool_map.items():

                openai_functions.append({                            "app": app_name,                continue

                    "type": "function",

                    "function": {                            "endpoint": tool.get("endpoint"),        

                        "name": tool_name,

                        "description": f"{tool_info['description']} [App: {tool_info['app']}]",                            "method": tool.get("method", "GET"),        return tools_by_app

                        "parameters": tool_info['parameters']

                    }                            "description": tool.get("description", ""),except ImportError:

                })

                                        "parameters": tool.get("parameters", {}),    def discover_tools(): 

            # Build messages

            messages = [                        }        return {}

                {

                    "role": "system",                        tool_names.append(tool_name)

                    "content": f"""You are {user.username}'s Digital Life Manager.

                router = APIRouter()

AVAILABLE TOOLS:

{apps_text}                if tool_names:



When asked to do something, USE THE TOOLS.                    apps_list.append(f"{app_name} ({len(tool_names)} tools): {', '.join(tool_names)}")# OpenAI configuration

Examples:

- "list apps" → List the tools above        except Exception as e:openai.api_key = os.getenv("OPENAI_API_KEY")

- "list my machines" → Call list_machines()

- "get my profile" → Call get_profile()            print(f"Error loading {app_dir.name}: {e}")LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")



Be helpful and execute tasks!"""            continue

                }

            ]    

            

            # Add history    return tool_map, apps_listclass ThinkRequest(BaseModel):

            for msg in (req.history or [])[-10:]:

                role = "assistant" if msg.get("sender") in ["assistant", "digital_twin"] else "user"    """Chat request"""

                messages.append({"role": role, "content": msg.get("content", "")})

                input: str

            messages.append({"role": "user", "content": req.input})

            router = APIRouter()    context: Optional[Dict[str, Any]] = None

            # Call OpenAI

            yield f": keepalive\n\n"    history: Optional[List[Dict[str, Any]]] = None

            

            response = openai.chat.completions.create(# OpenAI configuration

                model=LLM_MODEL,

                messages=messages,openai.api_key = os.getenv("OPENAI_API_KEY")

                tools=openai_functions if openai_functions else None,

                tool_choice="auto" if openai_functions else None,LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")@router.post("/stream/")

                temperature=0.7,

                max_tokens=2000@protected

            )

            async def chat_stream(request: Request, req: ThinkRequest):

            message = response.choices[0].message

            class ThinkRequest(BaseModel):    """

            # Check if AI wants to call tools

            if message.tool_calls:    """Chat request"""    Main chat endpoint - streams AI responses in real-time.

                yield f"data: {json.dumps({'type': 'content', 'content': '🔧 Executing...\\n\\n'})}\n\n"

                    input: str    This is your Digital Life Manager running on your local machine.

                for tool_call in message.tool_calls:

                    function_name = tool_call.function.name    context: Optional[Dict[str, Any]] = None    """

                    function_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}

                        history: Optional[List[Dict[str, Any]]] = None    from fastapi.responses import StreamingResponse

                    yield f"data: {json.dumps({'type': 'content', 'content': f'• {function_name}()\\n'})}\n\n"

                        import asyncio

                    # Execute the tool

                    if function_name in tool_map:    

                        tool_info = tool_map[function_name]

                        url = f"http://localhost:8000/{tool_info['app']}{tool_info['endpoint']}"@router.post("/stream/")    user = get_current_user(request)

                        

                        try:@protected    print(f"💬 {user.username}: {req.input[:80]}...")

                            async with httpx.AsyncClient() as client:

                                if tool_info['method'] == "GET":async def chat_stream(request: Request, req: ThinkRequest):    

                                    result = await client.get(url, headers={"Authorization": f"Bearer {auth_token}"})

                                elif tool_info['method'] == "POST":    """    if not openai.api_key:

                                    result = await client.post(url, json=function_args, headers={"Authorization": f"Bearer {auth_token}"})

                                else:    Main chat endpoint - actually executes tools and streams results.        def error_stream():

                                    result = await client.request(tool_info['method'], url, json=function_args, headers={"Authorization": f"Bearer {auth_token}"})

                                    """            yield f"data: {json.dumps({'type': 'error', 'error': 'OpenAI not configured'})}\n\n"

                                if result.status_code == 200:

                                    result_data = result.json()    from fastapi.responses import StreamingResponse        return StreamingResponse(error_stream(), media_type="text/event-stream")

                                    result_str = json.dumps(result_data, indent=2)

                                    yield f"data: {json.dumps({'type': 'content', 'content': f'```json\\n{result_str}\\n```\\n\\n'})}\n\n"    import asyncio    

                                else:

                                    yield f"data: {json.dumps({'type': 'content', 'content': f'❌ Error {result.status_code}\\n'})}\n\n"        async def generate():

                        except Exception as e:

                            yield f"data: {json.dumps({'type': 'content', 'content': f'❌ {str(e)}\\n'})}\n\n"    user = get_current_user(request)        try:

                    

                    await asyncio.sleep(0)    auth_token = request.headers.get("authorization", "").replace("Bearer ", "")            # Establish connection

            else:

                # No tools called, just return the response                yield f"data: {json.dumps({'type': 'start'})}\n\n"

                content = message.content or "Not sure how to help."

                for char in content:    print(f"💬 {user.username}: {req.input[:80]}...")            yield f": keepalive\n\n"

                    yield f"data: {json.dumps({'type': 'content', 'content': char})}\n\n"

                    await asyncio.sleep(0.01)                await asyncio.sleep(0)

            

            yield f"data: {json.dumps({'type': 'done'})}\n\n"    if not openai.api_key:            

            yield f"data: [DONE]\n\n"

                    def error_stream():            # Discover what apps and tools are available

        except Exception as e:

            print(f"❌ Error: {e}")            yield f"data: {json.dumps({'type': 'error', 'error': 'OpenAI not configured'})}\n\n"            tools_by_app = discover_tools()

            import traceback

            traceback.print_exc()        return StreamingResponse(error_stream(), media_type="text/event-stream")            

            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

                    # Build capabilities list and OpenAI functions

    return StreamingResponse(

        generate(),    async def generate():            capabilities_list = []

        media_type="text/event-stream",

        headers={        try:            openai_tools = []

            "Cache-Control": "no-cache",

            "Connection": "keep-alive",            yield f"data: {json.dumps({'type': 'start'})}\n\n"            

            "X-Accel-Buffering": "no"

        }            yield f": keepalive\n\n"            if tools_by_app:

    )

            await asyncio.sleep(0)                for app_name, tools in tools_by_app.items():



@router.get("/health/")                                tool_names = []

@public

async def health():            # Discover tools                    for tool in tools:

    """Health check"""

    tool_map, _ = discover_tools()            tool_map, apps_list = discover_tools()                        tool_name = tool.get("name", "?")

    return {

        "status": "healthy",            apps_text = "\n".join(apps_list) if apps_list else "No tools available"                        tool_names.append(tool_name)

        "service": "digital-life-manager",

        "tools_count": len(tool_map),                                    

        "timestamp": datetime.utcnow().isoformat()

    }            print(f"🔧 Discovered {len(tool_map)} tools")                        # Convert to OpenAI function format


                                    openai_tools.append({

            # Build OpenAI functions                            "type": "function",

            openai_functions = []                            "function": {

            for tool_name, tool_info in tool_map.items():                                "name": tool_name,

                openai_functions.append({                                "description": f"{tool.get('description', tool_name)} [App: {app_name}]",

                    "type": "function",                                "parameters": tool.get("parameters", {"type": "object", "properties": {}})

                    "function": {                            }

                        "name": tool_name,                        })

                        "description": f"{tool_info['description']} [App: {tool_info['app']}]",                    

                        "parameters": tool_info['parameters']                    capabilities_list.append(f"- {app_name}: {', '.join(tool_names)}")

                    }                

                })                capabilities = "\n".join(capabilities_list)

                        else:

            # Build messages                capabilities = "No apps with tools currently available"

            messages = [            

                {            print(f"🔧 Discovered {len(openai_tools)} tools from {len(tools_by_app)} apps")

                    "role": "system",            

                    "content": f"""You are {user.username}'s Digital Life Manager.            # Build conversation

            messages = [

AVAILABLE APPS & TOOLS:                {

{apps_text}                    "role": "system",

                    "content": f"""You are {user.username}'s Digital Life Manager - an AI running on their local machine.

When asked to do something, USE THE TOOLS to actually do it.

- "list apps" or "what can you do" → List the tools aboveAVAILABLE TOOLS:

- "list my machines" → Call list_machines(){capabilities}

- "get my profile" → Call get_profile()

When the user asks you to do something, USE THE TOOLS to actually do it. Don't just say you'll do it - actually call the functions!

Be helpful and actually execute tasks!"""

                }Examples:

            ]- "list my machines" → Call list_machines()

            - "get my profile" → Call get_profile()

            # Add history- "register a machine" → Call register_machine() with parameters

            for msg in (req.history or [])[-10:]:

                role = "assistant" if msg.get("sender") in ["assistant", "digital_twin"] else "user"Keep responses natural and short. You have REAL capabilities - use them!"""

                messages.append({"role": role, "content": msg.get("content", "")})                }

                        ]

            # Add current input            

            messages.append({"role": "user", "content": req.input})            # Add history (last 10 messages)

                        for msg in (req.history or [])[-10:]:

            # Call OpenAI (non-streaming first to handle function calls)                role = "assistant" if msg.get("sender") in ["assistant", "digital_twin"] else "user"

            yield f": keepalive\n\n"                messages.append({"role": role, "content": msg.get("content", "")})

                        

            response = openai.chat.completions.create(            # Add current input

                model=LLM_MODEL,            messages.append({"role": "user", "content": req.input})

                messages=messages,            

                tools=openai_functions if openai_functions else None,            # Stream response from OpenAI

                tool_choice="auto" if openai_functions else None,            yield f": keepalive\n\n"

                temperature=0.7,            

                max_tokens=2000            # Prepare OpenAI request with or without tools

            )            openai_params = {

                            "model": LLM_MODEL,

            message = response.choices[0].message                "messages": messages,

                            "temperature": 0.7,

            # Check if AI wants to call tools                "max_tokens": 2000,

            if message.tool_calls:                "stream": True

                yield f"data: {json.dumps({'type': 'content', 'content': '🔧 Executing tools...\\n\\n'})}\n\n"            }

                            

                tool_results = []            # Add tools if available

                for tool_call in message.tool_calls:            if openai_tools:

                    function_name = tool_call.function.name                openai_params["tools"] = openai_tools

                    function_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}                openai_params["tool_choice"] = "auto"

                                

                    yield f"data: {json.dumps({'type': 'content', 'content': f'Calling {function_name}...\\n'})}\n\n"            response = openai.chat.completions.create(**openai_params)

                                

                    # Execute the tool            import time

                    if function_name in tool_map:            last_keepalive = time.time()

                        tool_info = tool_map[function_name]            tool_calls = []

                        app_name = tool_info['app']            

                        endpoint = tool_info['endpoint']            for chunk in response:

                        method = tool_info['method']                current_time = time.time()

                                        

                        url = f"http://localhost:8000/{app_name}{endpoint}"                # Keepalive every 1 second

                                        if current_time - last_keepalive > 1:

                        try:                    yield f": keepalive\n\n"

                            async with httpx.AsyncClient() as client:                    last_keepalive = current_time

                                if method == "GET":                    await asyncio.sleep(0)

                                    result = await client.get(url, headers={"Authorization": f"Bearer {auth_token}"})                

                                elif method == "POST":                delta = chunk.choices[0].delta

                                    result = await client.post(url, json=function_args, headers={"Authorization": f"Bearer {auth_token}"})                

                                else:                # Handle regular content

                                    result = await client.request(method, url, json=function_args, headers={"Authorization": f"Bearer {auth_token}"})                if delta.content:

                                                    content = delta.content

                                result_data = result.json() if result.status_code == 200 else {"error": result.text}                    yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"

                                tool_results.append({                    last_keepalive = current_time

                                    "tool": function_name,                    await asyncio.sleep(0)

                                    "result": result_data                

                                })                # Handle tool calls

                                                if delta.tool_calls:

                                yield f"data: {json.dumps({'type': 'content', 'content': f'✅ {function_name} complete\\n'})}\n\n"                    for tool_call in delta.tool_calls:

                        except Exception as e:                        if tool_call.function:

                            yield f"data: {json.dumps({'type': 'content', 'content': f'❌ Error: {str(e)}\\n'})}\n\n"                            tool_name = tool_call.function.name

                                                tool_args = tool_call.function.arguments

                    await asyncio.sleep(0)                            yield f"data: {json.dumps({'type': 'tool_call', 'tool': tool_name, 'args': tool_args})}\n\n"

                                            await asyncio.sleep(0)

                # Send results back to AI for final response            

                yield f"data: {json.dumps({'type': 'content', 'content': '\\nResults:\\n'})}\n\n"            yield f"data: {json.dumps({'type': 'done'})}\n\n"

                            yield f"data: [DONE]\n\n"

                for result in tool_results:            

                    result_str = json.dumps(result['result'], indent=2)        except Exception as e:

                    yield f"data: {json.dumps({'type': 'content', 'content': f'```json\\n{result_str}\\n```\\n\\n'})}\n\n"            print(f"❌ Error: {e}")

                            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

            else:    

                # No tools called, just stream the response    return StreamingResponse(

                content = message.content or "I'm not sure how to help with that."        generate(),

                for char in content:        media_type="text/event-stream",

                    yield f"data: {json.dumps({'type': 'content', 'content': char})}\n\n"        headers={

                    await asyncio.sleep(0.01)            "Cache-Control": "no-cache",

                        "Connection": "keep-alive",

            yield f"data: {json.dumps({'type': 'done'})}\n\n"            "X-Accel-Buffering": "no"

            yield f"data: [DONE]\n\n"        }

                )

        except Exception as e:

            print(f"❌ Error: {e}")

            import traceback@router.get("/health/")

            traceback.print_exc()@public

            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"async def health():

        """Health check"""

    return StreamingResponse(    return {

        generate(),        "status": "healthy",

        media_type="text/event-stream",        "service": "digital-life-manager",

        headers={        "timestamp": datetime.utcnow().isoformat()

            "Cache-Control": "no-cache",    }

            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/health/")
@public
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "digital-life-manager",
        "tools_count": len(discover_tools()[0]),
        "timestamp": datetime.utcnow().isoformat()
    }
