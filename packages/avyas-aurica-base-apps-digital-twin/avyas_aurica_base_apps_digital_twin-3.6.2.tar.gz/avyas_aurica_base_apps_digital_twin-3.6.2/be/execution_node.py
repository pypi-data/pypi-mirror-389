"""
Execution Node Manager

The Digital Twin's interface to the execution node (local machine).
Discovers all apps, tools, and capabilities available on the execution node.
"""

import json
import httpx
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime
import os
import time

# Import security components
try:
    # Try absolute imports first (works in app loader context)
    from autonomy_controller import AutonomyController, validate_tool_parameters
    from rate_limiter import DTRateLimiter
    from audit_logger import DTAuditLogger
except ImportError:
    # Fall back to relative imports (for package imports)
    from .autonomy_controller import AutonomyController, validate_tool_parameters
    from .rate_limiter import DTRateLimiter
    from .audit_logger import DTAuditLogger


class AutonomyLevel(Enum):
    """Tool autonomy levels"""
    FULL = "full"           # DT can use freely
    ASK = "ask"             # DT should ask first
    RESTRICTED = "restricted"  # Never without explicit command


class DTTool:
    """Represents a tool the Digital Twin can use"""
    
    def __init__(self, tool_data: dict, app_name: str):
        self.name = tool_data["name"]
        self.description = tool_data["description"]
        self.endpoint = tool_data["endpoint"]
        self.method = tool_data.get("method", "GET")
        self.parameters = tool_data.get("parameters", {})
        self.returns = tool_data.get("returns", {})
        self.requires_auth = tool_data.get("requires_auth", False)
        self.autonomy_level = AutonomyLevel(tool_data.get("autonomy_level", "full"))
        self.side_effects = tool_data.get("side_effects", "none")
        self.examples = tool_data.get("examples", [])
        self.app_name = app_name
        
    def __repr__(self):
        return f"DTTool(name={self.name}, app={self.app_name}, autonomy={self.autonomy_level.value})"
    
    def to_openai_function(self) -> dict:
        """Convert to OpenAI function calling format"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": f"{self.description} [App: {self.app_name}, Autonomy: {self.autonomy_level.value}, Side effects: {self.side_effects}]",
                "parameters": self.parameters
            }
        }
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "app": self.app_name,
            "endpoint": self.endpoint,
            "method": self.method,
            "autonomy_level": self.autonomy_level.value,
            "side_effects": self.side_effects,
            "requires_auth": self.requires_auth
        }


class ExecutionNode:
    """
    Digital Twin's interface to the execution node (local machine).
    Discovers and executes tools on behalf of the user.
    """
    
    def __init__(self, apps_dir: Path, user_id: str, jwt_token: str, base_url: str = "http://localhost:8000"):
        self.apps_dir = apps_dir
        self.user_id = user_id
        self.jwt_token = jwt_token
        self.base_url = base_url
        self.tools: Dict[str, DTTool] = {}
        self.apps_discovered: List[dict] = []
        
        # Initialize security components
        self.autonomy = AutonomyController(user_id)
        self.rate_limiter = DTRateLimiter(
            max_actions_per_minute=50,
            max_actions_per_hour=200,
            max_tool_calls_per_minute=20
        )
        self.audit_logger = DTAuditLogger(user_id)
        
    async def discover_all(self) -> dict:
        """
        Discover ALL capabilities on execution node
        - All apps and their tools
        - System resources
        - Available services
        """
        print(f"🔍 Discovering execution node capabilities for user {self.user_id}...")
        
        apps = await self.scan_apps()
        system = self.scan_system_resources()
        
        result = {
            "apps": apps,
            "system": system,
            "total_tools": len(self.tools),
            "autonomous_tools": self.count_by_autonomy("full"),
            "ask_tools": self.count_by_autonomy("ask"),
            "restricted_tools": self.count_by_autonomy("restricted"),
            "execution_node_status": "connected",
            "discovery_timestamp": datetime.utcnow().isoformat()
        }
        
        print(f"✅ Discovery complete: {len(apps)} apps, {len(self.tools)} tools")
        return result
        
    async def scan_apps(self) -> List[dict]:
        """
        Scan all apps and auto-discover tools from OpenAPI schemas.
        
        Strategy:
        1. Call /apps API to get all apps and their endpoints
        2. For each app, fetch its OpenAPI schema from /{app_name}/openapi.json
        3. Convert OpenAPI operations to DT tools automatically
        4. No need for dt_tools in app.json!
        """
        discovered = []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {self.jwt_token}"}
                
                # Step 1: Get all apps
                response = await client.get(f"{self.base_url}/apps", headers=headers)
                
                if response.status_code != 200:
                    print(f"⚠️  Failed to fetch apps: {response.status_code}")
                    return discovered
                
                apps_data = response.json()
                apps_dict = apps_data.get('apps', {})
                print(f"✅ Discovered {len(apps_dict)} apps via /apps API")
                
                # Step 2: Process each app
                for app_name, app_info in apps_dict.items():
                    print(f"\n🔍 Processing app: {app_name}")
                    
                    tools_found = []
                    
                    # Step 3: Fetch OpenAPI schema for this app
                    try:
                        openapi_url = f"{self.base_url}/{app_name}/openapi.json"
                        openapi_response = await client.get(openapi_url, headers=headers)
                        
                        if openapi_response.status_code == 200:
                            openapi_schema = openapi_response.json()
                            
                            # Step 4: Convert OpenAPI paths to tools
                            paths = openapi_schema.get("paths", {})
                            components = openapi_schema.get("components", {})
                            schemas = components.get("schemas", {})
                            
                            for path, path_item in paths.items():
                                for method, operation in path_item.items():
                                    if method.lower() not in ["get", "post", "put", "delete", "patch"]:
                                        continue
                                    
                                    # Create tool from OpenAPI operation
                                    tool = self._create_tool_from_openapi(
                                        app_name=app_name,
                                        path=path,
                                        method=method.upper(),
                                        operation=operation,
                                        schemas=schemas
                                    )
                                    
                                    if tool:
                                        self.tools[tool.name] = tool
                                        tools_found.append(tool.name)
                            
                            print(f"  ✅ {app_name}: Discovered {len(tools_found)} tools from OpenAPI")
                        else:
                            print(f"  ⚠️  No OpenAPI schema for {app_name} (status: {openapi_response.status_code})")
                    
                    except Exception as e:
                        print(f"  ⚠️  Error fetching OpenAPI for {app_name}: {e}")
                    
                    # Add to discovered apps
                    discovered.append({
                        "name": app_name,
                        "version": app_info.get("metadata", {}).get("version", "unknown"),
                        "description": app_info.get("metadata", {}).get("description", ""),
                        "tools": tools_found,
                        "tool_count": len(tools_found),
                        "api_endpoints": app_info.get("api_endpoints", []),
                        "has_static": app_info.get("has_static", False),
                        "docs_url": app_info.get("docs_url", "")
                    })
                
                self.apps_discovered = discovered
                return discovered
        
        except Exception as e:
            print(f"❌ App discovery error: {e}")
            import traceback
            traceback.print_exc()
            return discovered
    
    def scan_system_resources(self) -> dict:
        """Discover system-level capabilities and accessible resources"""
        
        # Get project directories
        project_root = self.apps_dir.parent
        
        return {
            "filesystem": {
                "accessible": True,
                "read": True,
                "write": True,
                "project_root": str(project_root),
                "apps_directory": str(self.apps_dir),
                "accessible_paths": {
                    "apps": {
                        "path": str(self.apps_dir),
                        "read": True,
                        "write": False,  # Code is read-only
                        "description": "All app source code (read-only)"
                    },
                    "app_data": {
                        "path": str(self.apps_dir / "*/data"),
                        "read": True,
                        "write": True,
                        "description": "App-specific data directories (read/write via drive app)"
                    }
                },
                "access_via": ["drive", "agent-cli"]
            },
            "network": {
                "accessible": True,
                "external": True
            },
            "compute": {
                "available": True,
                "execution_via": ["agent-cli"]
            },
            "storage": {
                "managed_by": "drive",
                "operations": ["list", "read", "write", "delete", "create-dir"],
                "data_separation": "per-app"
            },
            "cli": {
                "managed_by": "agent-cli",
                "operations": ["execute", "execute-async", "system-info"],
                "working_directory": str(project_root)
            }
        }
    
    def count_by_autonomy(self, level: str) -> int:
        """Count tools by autonomy level"""
        return sum(1 for tool in self.tools.values() if tool.autonomy_level.value == level)
    
    def _create_tool_from_openapi(
        self, 
        app_name: str, 
        path: str, 
        method: str, 
        operation: dict,
        schemas: dict = None
    ) -> Optional[DTTool]:
        """
        Convert an OpenAPI operation to a DT Tool.
        
        Args:
            app_name: Name of the app
            path: API path (e.g., /api/profile)
            method: HTTP method (GET, POST, etc.)
            operation: OpenAPI operation object
            schemas: OpenAPI component schemas for resolving $ref
        
        Returns:
            DTTool instance or None if it should be skipped
        """
        if schemas is None:
            schemas = {}
        
        try:
            # Generate tool name from operationId or path
            operation_id = operation.get("operationId")
            if operation_id:
                tool_name = f"{app_name}_{operation_id}"
            else:
                # Generate from path and method
                path_parts = [p for p in path.split("/") if p and not p.startswith("{")]
                tool_name = f"{app_name}_{'_'.join(path_parts)}_{method.lower()}"
            
            # OpenAI requires tool names to be max 64 characters
            if len(tool_name) > 64:
                # Truncate but keep app_name prefix and method suffix readable
                max_middle = 64 - len(app_name) - len(method.lower()) - 3  # 3 for underscores
                if max_middle > 0:
                    path_parts = [p for p in path.split("/") if p and not p.startswith("{")]
                    middle = '_'.join(path_parts)
                    if len(middle) > max_middle:
                        middle = middle[:max_middle-3] + "___"  # Truncate with indicator
                    tool_name = f"{app_name}_{middle}_{method.lower()}"
                else:
                    # Last resort: just truncate
                    tool_name = tool_name[:64]
            
            # Get description
            description = operation.get("summary") or operation.get("description") or f"{method} {path}"
            
            # Build endpoint URL (path only, app_name will be added during execution)
            endpoint = path  # Don't prepend app_name here, it's added in _make_request()
            
            # Extract parameters (for OpenAI function calling format)
            parameters = {
                "type": "object",
                "properties": {},
                "required": []
            }
            
            # Handle path parameters, query parameters, and request body
            for param in operation.get("parameters", []):
                param_name = param.get("name")
                param_schema = param.get("schema", {})
                param_in = param.get("in")  # path, query, header, etc.
                
                if param_in in ["path", "query"]:
                    parameters["properties"][param_name] = {
                        "type": param_schema.get("type", "string"),
                        "description": param.get("description", "")
                    }
                    
                    if param.get("required", False):
                        parameters["required"].append(param_name)
            
            # Handle request body (for POST/PUT/PATCH)
            request_body = operation.get("requestBody", {})
            if request_body:
                content = request_body.get("content", {})
                json_schema = content.get("application/json", {}).get("schema", {})
                
                # Resolve $ref if present
                if "$ref" in json_schema:
                    ref_path = json_schema["$ref"]
                    # Extract schema name from #/components/schemas/SchemaName
                    if ref_path.startswith("#/components/schemas/"):
                        schema_name = ref_path.split("/")[-1]
                        json_schema = schemas.get(schema_name, {})
                
                if json_schema:
                    # Merge body properties into parameters
                    body_props = json_schema.get("properties", {})
                    for prop_name, prop_schema in body_props.items():
                        param_def = {}
                        
                        # Handle anyOf/oneOf unions
                        if "anyOf" in prop_schema:
                            # For anyOf, use the first non-null type
                            for option in prop_schema["anyOf"]:
                                if option.get("type") != "null":
                                    param_def["type"] = option.get("type", "string")
                                    if "items" in option:
                                        param_def["items"] = option["items"]
                                    break
                        elif "oneOf" in prop_schema:
                            # For oneOf, use the first option
                            first_option = prop_schema["oneOf"][0]
                            param_def["type"] = first_option.get("type", "string")
                            if "items" in first_option:
                                param_def["items"] = first_option["items"]
                        else:
                            param_def["type"] = prop_schema.get("type", "string")
                            # For arrays, include items schema
                            if param_def["type"] == "array" and "items" in prop_schema:
                                param_def["items"] = prop_schema["items"]
                        
                        # Add description
                        param_def["description"] = prop_schema.get("description", prop_schema.get("title", ""))
                        
                        # For arrays without items, add a default items schema
                        if param_def.get("type") == "array" and "items" not in param_def:
                            param_def["items"] = {"type": "string"}
                        
                        # For objects with additionalProperties, handle it
                        if param_def.get("type") == "object":
                            if "additionalProperties" in prop_schema:
                                param_def["additionalProperties"] = prop_schema["additionalProperties"]
                            if "properties" in prop_schema:
                                param_def["properties"] = prop_schema["properties"]
                        
                        parameters["properties"][prop_name] = param_def
                    
                    # Add required fields from body
                    body_required = json_schema.get("required", [])
                    parameters["required"].extend(body_required)
            
            # Determine autonomy level based on app, method, and operation
            # Special handling for core infrastructure apps
            if app_name in ["drive", "agent-cli"]:
                # Drive and agent-cli are core capabilities - grant full autonomy
                # These are safe because they have their own security checks
                if method == "GET":
                    autonomy_level = "full"
                    side_effects = "none"
                elif app_name == "agent-cli":
                    # CLI execution needs autonomy for basic commands
                    autonomy_level = "full"
                    side_effects = "execute"
                elif app_name == "drive" and path.startswith("/api/storage/list"):
                    autonomy_level = "full"
                    side_effects = "none"
                elif app_name == "drive" and path.startswith("/api/storage/read"):
                    autonomy_level = "full"
                    side_effects = "none"
                else:
                    # Write operations still need full autonomy for drive
                    autonomy_level = "full"
                    side_effects = "write"
            # Chat-app gets full autonomy - it's the main UI for the DT
            elif app_name == "chat-app":
                # Chat operations are core to DT interaction
                autonomy_level = "full"
                if method == "GET":
                    side_effects = "none"
                elif "delete" in description.lower():
                    side_effects = "delete"
                else:
                    side_effects = "write"
            # Default autonomy rules for other apps
            elif method == "GET":
                autonomy_level = "full"
                side_effects = "none"
            elif method == "POST" and "create" not in description.lower():
                autonomy_level = "ask"
                side_effects = "write"
            else:
                autonomy_level = "ask"
                side_effects = "write"
            
            # Create tool data
            tool_data = {
                "name": tool_name,
                "description": f"[{app_name}] {description}",
                "endpoint": endpoint,
                "method": method,
                "parameters": parameters,
                "autonomy_level": autonomy_level,
                "side_effects": side_effects,
                "requires_auth": True
            }
            
            return DTTool(tool_data, app_name)
        
        except Exception as e:
            print(f"  ⚠️  Error creating tool from {method} {path}: {e}")
            return None
    
    async def _fetch_app_json(self, app_name: str) -> Optional[dict]:
        """
        Fetch app.json for a specific app.
        First tries via API, then falls back to filesystem.
        """
        # Try filesystem first (fastest)
        if self.apps_dir.exists():
            app_json_path = self.apps_dir / app_name / "app.json"
            if app_json_path.exists():
                try:
                    with open(app_json_path, 'r') as f:
                        return json.load(f)
                except Exception as e:
                    print(f"⚠️  Error reading {app_name}/app.json: {e}")
        
        return None
    
    def can_use_autonomously(self, tool_name: str) -> bool:
        """Check if DT can use tool without asking"""
        tool = self.tools.get(tool_name)
        return tool and tool.autonomy_level == AutonomyLevel.FULL
    
    def get_tool(self, tool_name: str) -> Optional[DTTool]:
        """Get tool by name"""
        return self.tools.get(tool_name)
    
    async def execute_as_user(
        self, 
        tool_name: str, 
        parameters: dict,
        autonomous: bool = True
    ) -> dict:
        """
        Execute tool on behalf of user with full security checks.
        The DT acts WITH user's authority.
        """
        start_time = time.time()
        dt_id = f"dt_{self.user_id}"
        
        tool = self.tools.get(tool_name)
        if not tool:
            error_msg = f"Tool '{tool_name}' not found"
            self.audit_logger.log_dt_action(
                action_type="tool_execution",
                tool_name=tool_name,
                parameters=parameters,
                autonomous=autonomous,
                error=error_msg
            )
            return {
                "success": False,
                "error": error_msg,
                "available_tools": list(self.tools.keys())
            }
        
        # 1. Check autonomy level via AutonomyController
        can_exec, reason = await self.autonomy.can_execute(
            tool_name,
            tool.autonomy_level.value,
            autonomous
        )
        
        if not can_exec:
            self.audit_logger.log_dt_action(
                action_type="tool_execution",
                tool_name=tool_name,
                parameters=parameters,
                autonomous=autonomous,
                error=f"Autonomy check failed: {reason}"
            )
            
            return {
                "success": False,
                "error": "autonomy_check_failed",
                "message": reason,
                "requires_confirmation": reason == "requires_user_confirmation"
            }
        
        # 2. Check rate limiting
        can_act, limit_msg = self.rate_limiter.can_act(dt_id)
        if not can_act:
            self.audit_logger.log_dt_action(
                action_type="tool_execution",
                tool_name=tool_name,
                parameters=parameters,
                autonomous=autonomous,
                error=limit_msg
            )
            return {
                "success": False,
                "error": "rate_limit_exceeded",
                "message": limit_msg
            }
        
        can_call, call_msg = self.rate_limiter.can_call_tool(dt_id, tool_name)
        if not can_call:
            self.audit_logger.log_dt_action(
                action_type="tool_execution",
                tool_name=tool_name,
                parameters=parameters,
                autonomous=autonomous,
                error=call_msg
            )
            return {
                "success": False,
                "error": "rate_limit_exceeded",
                "message": call_msg
            }
        
        # 3. Validate parameters
        # Build tool definition for validation
        tool_definition = {
            "parameters": tool.parameters
        }
        valid, validation_msg = validate_tool_parameters(tool_definition, parameters)
        if not valid:
            self.audit_logger.log_dt_action(
                action_type="tool_execution",
                tool_name=tool_name,
                parameters=parameters,
                autonomous=autonomous,
                error=f"Parameter validation failed: {validation_msg}"
            )
            return {
                "success": False,
                "error": "invalid_parameters",
                "message": validation_msg
            }
        
        # 4. Record the action/tool call
        self.rate_limiter.record_tool_call(dt_id, tool_name)
        
        # 5. Make request
        try:
            result = await self._make_request(tool, parameters)
            execution_time = (time.time() - start_time) * 1000
            
            # 6. Log success
            self.audit_logger.log_dt_action(
                action_type="tool_execution",
                tool_name=tool_name,
                parameters=parameters,
                result=result,
                autonomous=autonomous,
                execution_time_ms=execution_time,
                metadata={
                    "app": tool.app_name,
                    "autonomy_level": tool.autonomy_level.value,
                    "side_effects": tool.side_effects
                }
            )
            
            return {
                "success": True,
                "result": result,
                "tool": tool_name,
                "app": tool.app_name,
                "execution_time_ms": execution_time
            }
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = str(e)
            
            # Log failure
            self.audit_logger.log_dt_action(
                action_type="tool_execution",
                tool_name=tool_name,
                parameters=parameters,
                autonomous=autonomous,
                error=error_msg,
                execution_time_ms=execution_time,
                metadata={
                    "app": tool.app_name,
                    "exception_type": type(e).__name__
                }
            )
            
            return {
                "success": False,
                "error": error_msg,
                "tool": tool_name,
                "execution_time_ms": execution_time
            }
    
    async def refresh_discovery(self) -> Dict:
        """
        Refresh app and tool discovery.
        Useful when new apps are installed or updated.
        """
        print(f"🔄 Refreshing tool discovery...")
        
        # Clear current tools and apps
        self.tools.clear()
        self.apps_discovered.clear()
        
        # Re-discover
        return await self.discover_all()
    
    def get_app_list(self) -> List[str]:
        """Get list of discovered app names"""
        return [app["name"] for app in self.apps_discovered]
    
    def get_tools_by_app(self, app_name: str) -> List[DTTool]:
        """Get all tools for a specific app"""
        return [tool for tool in self.tools.values() if tool.app_name == app_name]
    
    async def _make_request(self, tool: DTTool, parameters: dict) -> Any:
        """Make HTTP request to tool endpoint"""
        url = f"{self.base_url}/{tool.app_name}{tool.endpoint}"
        
        headers = {}
        if tool.requires_auth:
            headers["Authorization"] = f"Bearer {self.jwt_token}"
        
        async with httpx.AsyncClient() as client:
            if tool.method.upper() == "GET":
                response = await client.get(url, params=parameters, headers=headers, timeout=10.0)
            elif tool.method.upper() == "POST":
                response = await client.post(url, json=parameters, headers=headers, timeout=10.0)
            elif tool.method.upper() == "PUT":
                response = await client.put(url, json=parameters, headers=headers, timeout=10.0)
            elif tool.method.upper() == "DELETE":
                response = await client.delete(url, params=parameters, headers=headers, timeout=10.0)
            else:
                raise ValueError(f"Unsupported HTTP method: {tool.method}")
            
            response.raise_for_status()
            return response.json()
    
    def to_dt_tool_format(self) -> List[dict]:
        """Convert tools to format for DT's LLM brain (OpenAI function calling)"""
        return [tool.to_openai_function() for tool in self.tools.values()]
    
    def get_tools_by_autonomy(self, level: str) -> List[DTTool]:
        """Get all tools with specific autonomy level"""
        return [tool for tool in self.tools.values() if tool.autonomy_level.value == level]
    
    def get_security_summary(self) -> dict:
        """Get security and autonomy settings summary"""
        dt_id = f"dt_{self.user_id}"
        return {
            "autonomy_settings": self.autonomy.get_autonomy_summary(),
            "rate_limits": self.rate_limiter.get_stats(dt_id),
            "recent_audit_logs": len(self.audit_logger.get_recent_logs(limit=10))
        }
    
    def get_capabilities_summary(self) -> dict:
        """Get summary of all capabilities"""
        return {
            "total_apps": len(self.apps_discovered),
            "total_tools": len(self.tools),
            "tools_by_autonomy": {
                "full": self.count_by_autonomy("full"),
                "ask": self.count_by_autonomy("ask"),
                "restricted": self.count_by_autonomy("restricted")
            },
            "apps": [
                {
                    "name": app["name"],
                    "tools": app["tool_count"]
                }
                for app in self.apps_discovered
            ]
        }
