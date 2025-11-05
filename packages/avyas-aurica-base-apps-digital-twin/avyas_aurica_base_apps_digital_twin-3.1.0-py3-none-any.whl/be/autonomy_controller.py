"""
Autonomy Controller for Digital Twin

Controls what the Digital Twin can do autonomously and enforces
security boundaries based on tool autonomy levels and user preferences.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
import os
from pathlib import Path


class AutonomyLevel(Enum):
    """Autonomy levels for tools"""
    FULL = "full"           # DT can use freely without asking
    ASK = "ask"             # DT should ask for confirmation first
    RESTRICTED = "restricted"  # Never without explicit user command


class AutonomyController:
    """
    Controls what the Digital Twin can do autonomously.
    
    Enforces:
    - Tool autonomy levels (full/ask/restricted)
    - User preferences (blocked tools, standing permissions)
    - Security boundaries for the DT
    """
    
    def __init__(self, user_id: str, preferences_path: Optional[str] = None):
        """
        Initialize autonomy controller for a user.
        
        Args:
            user_id: User ID this controller is for
            preferences_path: Path to user preferences file (optional)
        """
        self.user_id = user_id
        self.preferences_path = preferences_path or self._default_preferences_path()
        self.preferences = self._load_user_preferences()
        
    def _default_preferences_path(self) -> str:
        """Get default path for user preferences"""
        base_path = os.getenv("DT_STATE_STORAGE_PATH", "/tmp/dt_state")
        return f"{base_path}/user_{self.user_id}_preferences.json"
    
    def _load_user_preferences(self) -> dict:
        """Load user preferences from storage"""
        try:
            if os.path.exists(self.preferences_path):
                with open(self.preferences_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ Could not load user preferences: {e}")
        
        # Return default preferences
        return self._default_preferences()
    
    def _default_preferences(self) -> dict:
        """Default autonomy preferences for new users"""
        return {
            "autonomy_mode": "full",  # full, assisted, manual
            "blocked_tools": [],
            "standing_permissions": [],  # Tools user always allows
            "require_confirmation_for": [],
            "rate_limits": {
                "actions_per_minute": 50,
                "tool_calls_per_hour": 200
            },
            "audit_retention_days": 90,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    
    async def save_preferences(self):
        """Persist user preferences"""
        try:
            os.makedirs(os.path.dirname(self.preferences_path), exist_ok=True)
            self.preferences["updated_at"] = datetime.utcnow().isoformat()
            with open(self.preferences_path, 'w') as f:
                json.dump(self.preferences, f, indent=2)
        except Exception as e:
            print(f"❌ Could not save preferences: {e}")
    
    async def can_execute(
        self, 
        tool_name: str,
        autonomy_level: str,
        autonomous: bool = True
    ) -> Tuple[bool, str]:
        """
        Check if DT can execute this tool.
        
        Args:
            tool_name: Name of the tool
            autonomy_level: Tool's autonomy level (full/ask/restricted)
            autonomous: Whether this is an autonomous execution
            
        Returns:
            Tuple of (can_execute: bool, reason: str)
        """
        # Check if tool is blocked by user preferences
        if tool_name in self.preferences.get("blocked_tools", []):
            return False, f"Tool '{tool_name}' is blocked by user preferences"
        
        # Convert string to enum
        try:
            level = AutonomyLevel(autonomy_level)
        except ValueError:
            return False, f"Invalid autonomy level: {autonomy_level}"
        
        # Check autonomy mode
        autonomy_mode = self.preferences.get("autonomy_mode", "full")
        
        if autonomy_mode == "manual":
            # Manual mode: nothing autonomous
            if autonomous:
                return False, "User is in manual mode - all actions require explicit command"
        
        # RESTRICTED tools never autonomous
        if level == AutonomyLevel.RESTRICTED:
            if autonomous:
                return False, "This tool requires explicit user command (autonomy=restricted)"
            # Even non-autonomous, check if it's allowed
            return True, "ok"
        
        # ASK level tools need confirmation
        if level == AutonomyLevel.ASK:
            if autonomous:
                # Check for standing permission
                if self.has_standing_permission(tool_name):
                    return True, "ok (standing permission)"
                # Check if user specifically requires confirmation
                if tool_name in self.preferences.get("require_confirmation_for", []):
                    return False, "requires_user_confirmation"
                # Default for ASK: need confirmation
                return False, "requires_user_confirmation"
        
        # FULL autonomy tools - generally allowed
        if level == AutonomyLevel.FULL:
            # Even full autonomy tools can be restricted by user
            if tool_name in self.preferences.get("require_confirmation_for", []):
                if autonomous:
                    return False, "requires_user_confirmation (user preference)"
            return True, "ok"
        
        return True, "ok"
    
    def has_standing_permission(self, tool_name: str) -> bool:
        """
        Check if user has given standing permission for this tool.
        Standing permission = "always allow this tool autonomously"
        """
        standing = self.preferences.get("standing_permissions", [])
        return tool_name in standing
    
    async def grant_standing_permission(self, tool_name: str):
        """Grant standing permission for a tool"""
        standing = self.preferences.get("standing_permissions", [])
        if tool_name not in standing:
            standing.append(tool_name)
            self.preferences["standing_permissions"] = standing
            await self.save_preferences()
            print(f"✅ Granted standing permission for {tool_name}")
    
    async def revoke_standing_permission(self, tool_name: str):
        """Revoke standing permission for a tool"""
        standing = self.preferences.get("standing_permissions", [])
        if tool_name in standing:
            standing.remove(tool_name)
            self.preferences["standing_permissions"] = standing
            await self.save_preferences()
            print(f"🚫 Revoked standing permission for {tool_name}")
    
    async def block_tool(self, tool_name: str):
        """Block a tool completely"""
        blocked = self.preferences.get("blocked_tools", [])
        if tool_name not in blocked:
            blocked.append(tool_name)
            self.preferences["blocked_tools"] = blocked
            await self.save_preferences()
            print(f"🚫 Blocked tool: {tool_name}")
    
    async def unblock_tool(self, tool_name: str):
        """Unblock a tool"""
        blocked = self.preferences.get("blocked_tools", [])
        if tool_name in blocked:
            blocked.remove(tool_name)
            self.preferences["blocked_tools"] = blocked
            await self.save_preferences()
            print(f"✅ Unblocked tool: {tool_name}")
    
    def get_autonomy_summary(self) -> dict:
        """Get summary of autonomy settings"""
        return {
            "user_id": self.user_id,
            "autonomy_mode": self.preferences.get("autonomy_mode"),
            "blocked_tools": self.preferences.get("blocked_tools", []),
            "standing_permissions": self.preferences.get("standing_permissions", []),
            "require_confirmation": self.preferences.get("require_confirmation_for", []),
            "rate_limits": self.preferences.get("rate_limits", {})
        }


def validate_tool_parameters(tool_definition: dict, parameters: dict) -> Tuple[bool, str]:
    """
    Validate tool parameters against the tool's schema.
    
    Args:
        tool_definition: Tool definition from app.json
        parameters: Parameters to validate
        
    Returns:
        Tuple of (valid: bool, message: str)
    """
    # Get parameter schema
    param_schema = tool_definition.get("parameters", {})
    properties = param_schema.get("properties", {})
    required = param_schema.get("required", [])
    
    # Check required parameters
    for req_param in required:
        if req_param not in parameters:
            return False, f"Missing required parameter: {req_param}"
    
    # Check parameter types
    for param_name, param_value in parameters.items():
        if param_name not in properties:
            return False, f"Unknown parameter: {param_name}"
        
        param_def = properties[param_name]
        expected_type = param_def.get("type")
        
        # Type checking
        if expected_type == "string" and not isinstance(param_value, str):
            return False, f"Parameter '{param_name}' must be a string"
        elif expected_type == "number" and not isinstance(param_value, (int, float)):
            return False, f"Parameter '{param_name}' must be a number"
        elif expected_type == "boolean" and not isinstance(param_value, bool):
            return False, f"Parameter '{param_name}' must be a boolean"
        elif expected_type == "object" and not isinstance(param_value, dict):
            return False, f"Parameter '{param_name}' must be an object"
        elif expected_type == "array" and not isinstance(param_value, list):
            return False, f"Parameter '{param_name}' must be an array"
        
        # Check enum values
        if "enum" in param_def:
            if param_value not in param_def["enum"]:
                return False, f"Parameter '{param_name}' must be one of: {param_def['enum']}"
    
    return True, "ok"


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_autonomy_controller():
        """Test autonomy controller"""
        controller = AutonomyController("test_user_123")
        
        print("=== Testing Autonomy Controller ===\n")
        
        # Test 1: FULL autonomy tool
        can_exec, reason = await controller.can_execute(
            "get_weather",
            "full",
            autonomous=True
        )
        print(f"✅ FULL autonomy tool (autonomous): {can_exec} - {reason}")
        
        # Test 2: ASK level tool without standing permission
        can_exec, reason = await controller.can_execute(
            "send_email",
            "ask",
            autonomous=True
        )
        print(f"⚠️ ASK level tool (no permission): {can_exec} - {reason}")
        
        # Test 3: Grant standing permission
        await controller.grant_standing_permission("send_email")
        can_exec, reason = await controller.can_execute(
            "send_email",
            "ask",
            autonomous=True
        )
        print(f"✅ ASK level tool (with permission): {can_exec} - {reason}")
        
        # Test 4: RESTRICTED tool
        can_exec, reason = await controller.can_execute(
            "delete_all",
            "restricted",
            autonomous=True
        )
        print(f"🚫 RESTRICTED tool (autonomous): {can_exec} - {reason}")
        
        # Test 5: Block a tool
        await controller.block_tool("get_weather")
        can_exec, reason = await controller.can_execute(
            "get_weather",
            "full",
            autonomous=True
        )
        print(f"🚫 Blocked tool: {can_exec} - {reason}")
        
        # Summary
        print(f"\n=== Autonomy Summary ===")
        print(json.dumps(controller.get_autonomy_summary(), indent=2))
    
    asyncio.run(test_autonomy_controller())
