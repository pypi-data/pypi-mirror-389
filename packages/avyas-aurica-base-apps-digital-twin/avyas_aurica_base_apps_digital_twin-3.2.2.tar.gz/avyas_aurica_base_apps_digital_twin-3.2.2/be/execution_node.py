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
        """Scan all apps and extract DT tools"""
        discovered = []
        
        # Scan apps directory
        if not self.apps_dir.exists():
            print(f"⚠️  Apps directory not found: {self.apps_dir}")
            return discovered
        
        for app_dir in self.apps_dir.iterdir():
            if not app_dir.is_dir():
                continue
                
            app_json_path = app_dir / "app.json"
            if not app_json_path.exists():
                continue
            
            try:
                with open(app_json_path, 'r') as f:
                    app_data = json.load(f)
                
                app_name = app_data.get("name", app_dir.name)
                
                # Extract DT tools if present
                dt_tools = app_data.get("dt_tools", [])
                tools_found = []
                
                for tool_data in dt_tools:
                    tool = DTTool(tool_data, app_name)
                    self.tools[tool.name] = tool
                    tools_found.append(tool.name)
                
                if tools_found:
                    discovered.append({
                        "name": app_name,
                        "version": app_data.get("version", "unknown"),
                        "description": app_data.get("description", ""),
                        "tools": tools_found,
                        "tool_count": len(tools_found)
                    })
                    print(f"  📦 {app_name}: {len(tools_found)} tools")
                    
            except Exception as e:
                print(f"  ⚠️  Error scanning {app_dir.name}: {e}")
                continue
        
        self.apps_discovered = discovered
        return discovered
    
    def scan_system_resources(self) -> dict:
        """Discover system-level capabilities"""
        return {
            "filesystem": {
                "accessible": True,
                "read": True,
                "write": True
            },
            "network": {
                "accessible": True,
                "external": True
            },
            "compute": {
                "available": True
            }
        }
    
    def count_by_autonomy(self, level: str) -> int:
        """Count tools by autonomy level"""
        return sum(1 for tool in self.tools.values() if tool.autonomy_level.value == level)
    
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
