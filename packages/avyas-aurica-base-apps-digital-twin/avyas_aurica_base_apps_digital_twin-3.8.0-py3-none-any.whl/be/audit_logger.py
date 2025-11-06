"""
Audit Logger for Digital Twin

Comprehensive logging of all DT actions for security, compliance, and debugging.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import os
from pathlib import Path


class DTAuditLogger:
    """
    Comprehensive audit logging for Digital Twin actions.
    
    Logs everything the DT does including:
    - Tool executions
    - Autonomous vs manual actions
    - Parameters and results
    - Errors and failures
    - User confirmations
    """
    
    def __init__(self, user_id: str, storage_path: Optional[str] = None):
        """
        Initialize audit logger.
        
        Args:
            user_id: User ID this logger is for
            storage_path: Where to store audit logs (optional)
        """
        self.user_id = user_id
        self.dt_id = f"dt_{user_id}"
        self.storage_path = storage_path or self._default_storage_path()
        self._ensure_storage_exists()
        
        # In-memory buffer for recent logs
        self.recent_logs: List[dict] = []
        self.max_recent = 100
    
    def _default_storage_path(self) -> str:
        """Get default path for audit logs"""
        base_path = os.getenv("DT_AUDIT_STORAGE_PATH", "/tmp/dt_audit")
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        return f"{base_path}/{self.user_id}/audit_{date_str}.jsonl"
    
    def _ensure_storage_exists(self):
        """Create storage directory if it doesn't exist"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
    
    def _sanitize_params(self, params: dict) -> dict:
        """
        Sanitize parameters to remove sensitive information.
        
        Removes/masks:
        - Passwords
        - API keys
        - Tokens
        - Credit card numbers
        """
        sanitized = {}
        sensitive_keys = ['password', 'api_key', 'token', 'secret', 'credit_card']
        
        for key, value in params.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_params(value)
            else:
                sanitized[key] = value
        
        return sanitized
    
    def log_dt_action(
        self,
        action_type: str,
        tool_name: Optional[str] = None,
        parameters: Optional[dict] = None,
        result: Optional[dict] = None,
        autonomous: bool = False,
        user_confirmed: bool = False,
        error: Optional[str] = None,
        execution_time_ms: Optional[float] = None,
        metadata: Optional[dict] = None
    ):
        """
        Log a DT action.
        
        Args:
            action_type: Type of action (tool_execution, decision, state_update, etc.)
            tool_name: Name of tool used (if applicable)
            parameters: Parameters passed to action
            result: Result of the action
            autonomous: Whether this was autonomous
            user_confirmed: Whether user confirmed this action
            error: Error message if failed
            execution_time_ms: Execution time in milliseconds
            metadata: Additional metadata
        """
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "dt_id": self.dt_id,
            "user_id": self.user_id,
            "action_type": action_type,
            "tool": tool_name,
            "parameters": self._sanitize_params(parameters or {}),
            "result_status": "success" if not error else "failed",
            "error": error,
            "autonomous": autonomous,
            "user_confirmed": user_confirmed,
            "execution_time_ms": execution_time_ms,
            "authority": "user_jwt",
            "metadata": metadata or {}
        }
        
        # Log to console
        self._log_to_console(audit_entry)
        
        # Store in file
        self._store_audit_log(audit_entry)
        
        # Keep in recent buffer
        self.recent_logs.append(audit_entry)
        if len(self.recent_logs) > self.max_recent:
            self.recent_logs.pop(0)
        
        # Alert on sensitive actions
        if tool_name and self._is_sensitive_action(tool_name, action_type):
            self._alert_sensitive_action(audit_entry)
    
    def _log_to_console(self, entry: dict):
        """Log to console with emoji indicators"""
        status_emoji = "✅" if entry["result_status"] == "success" else "❌"
        autonomous_emoji = "🤖" if entry["autonomous"] else "👤"
        
        log_msg = (
            f"{status_emoji} {autonomous_emoji} DT Audit: "
            f"{entry['action_type']}"
        )
        
        if entry["tool"]:
            log_msg += f" [{entry['tool']}]"
        
        if entry["error"]:
            log_msg += f" - Error: {entry['error']}"
        
        if entry["execution_time_ms"]:
            log_msg += f" ({entry['execution_time_ms']:.2f}ms)"
        
        print(log_msg)
    
    def _store_audit_log(self, entry: dict):
        """Store audit log to file (JSONL format)"""
        try:
            with open(self.storage_path, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            print(f"❌ Failed to write audit log: {e}")
    
    def _is_sensitive_action(self, tool_name: str, action_type: str) -> bool:
        """Check if this is a sensitive action that needs alerting"""
        sensitive_tools = [
            'delete', 'remove', 'destroy', 'drop',
            'admin', 'sudo', 'grant', 'revoke',
            'payment', 'transfer', 'send_money'
        ]
        
        tool_lower = tool_name.lower()
        return any(sensitive in tool_lower for sensitive in sensitive_tools)
    
    def _alert_sensitive_action(self, entry: dict):
        """Alert on sensitive actions (could send notification, email, etc.)"""
        print(f"⚠️ SENSITIVE ACTION ALERT: {entry['tool']} by {entry['dt_id']}")
        # TODO: Implement actual alerting (email, SMS, push notification)
    
    def get_recent_logs(self, limit: int = 50) -> List[dict]:
        """Get recent audit logs from memory"""
        return self.recent_logs[-limit:]
    
    def get_logs_for_date(self, date: datetime) -> List[dict]:
        """
        Get all audit logs for a specific date.
        
        Args:
            date: Date to get logs for
            
        Returns:
            List of audit log entries
        """
        date_str = date.strftime("%Y-%m-%d")
        log_file = f"{os.path.dirname(self.storage_path)}/audit_{date_str}.jsonl"
        
        logs = []
        try:
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    for line in f:
                        logs.append(json.loads(line.strip()))
        except Exception as e:
            print(f"❌ Failed to read audit logs: {e}")
        
        return logs
    
    def get_action_summary(self, days: int = 7) -> dict:
        """
        Get summary of DT actions over the last N days.
        
        Args:
            days: Number of days to summarize
            
        Returns:
            Summary statistics
        """
        # For now, use recent logs (in production, query storage)
        logs = self.recent_logs
        
        total_actions = len(logs)
        autonomous_actions = sum(1 for log in logs if log.get("autonomous"))
        failed_actions = sum(1 for log in logs if log.get("result_status") == "failed")
        
        # Count by tool
        tool_usage = {}
        for log in logs:
            tool = log.get("tool")
            if tool:
                tool_usage[tool] = tool_usage.get(tool, 0) + 1
        
        # Count by action type
        action_types = {}
        for log in logs:
            action_type = log.get("action_type")
            action_types[action_type] = action_types.get(action_type, 0) + 1
        
        return {
            "dt_id": self.dt_id,
            "period_days": days,
            "total_actions": total_actions,
            "autonomous_actions": autonomous_actions,
            "manual_actions": total_actions - autonomous_actions,
            "failed_actions": failed_actions,
            "success_rate": (total_actions - failed_actions) / total_actions if total_actions > 0 else 0,
            "tool_usage": tool_usage,
            "action_types": action_types,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def search_logs(
        self,
        tool_name: Optional[str] = None,
        action_type: Optional[str] = None,
        autonomous: Optional[bool] = None,
        failed_only: bool = False,
        limit: int = 100
    ) -> List[dict]:
        """
        Search audit logs with filters.
        
        Args:
            tool_name: Filter by tool name
            action_type: Filter by action type
            autonomous: Filter by autonomous flag
            failed_only: Only return failed actions
            limit: Maximum number of results
            
        Returns:
            Filtered audit logs
        """
        filtered = self.recent_logs.copy()
        
        if tool_name:
            filtered = [log for log in filtered if log.get("tool") == tool_name]
        
        if action_type:
            filtered = [log for log in filtered if log.get("action_type") == action_type]
        
        if autonomous is not None:
            filtered = [log for log in filtered if log.get("autonomous") == autonomous]
        
        if failed_only:
            filtered = [log for log in filtered if log.get("result_status") == "failed"]
        
        return filtered[-limit:]


# Example usage
if __name__ == "__main__":
    import time
    
    def test_audit_logger():
        """Test audit logger"""
        logger = DTAuditLogger("test_user_123")
        
        print("=== Testing Audit Logger ===\n")
        
        # Test 1: Successful autonomous tool execution
        print("Test 1: Logging autonomous tool execution...")
        logger.log_dt_action(
            action_type="tool_execution",
            tool_name="get_weather",
            parameters={"city": "London"},
            result={"temperature": 15, "condition": "cloudy"},
            autonomous=True,
            execution_time_ms=250.5
        )
        
        # Test 2: Failed tool execution
        print("\nTest 2: Logging failed tool execution...")
        logger.log_dt_action(
            action_type="tool_execution",
            tool_name="send_email",
            parameters={"to": "user@example.com", "subject": "Test"},
            autonomous=False,
            user_confirmed=True,
            error="SMTP connection failed",
            execution_time_ms=1000.0
        )
        
        # Test 3: Sensitive action
        print("\nTest 3: Logging sensitive action...")
        logger.log_dt_action(
            action_type="tool_execution",
            tool_name="delete_user_data",
            parameters={"user_id": "123"},
            autonomous=False,
            user_confirmed=True,
            execution_time_ms=50.0
        )
        
        # Test 4: Parameter sanitization
        print("\nTest 4: Testing parameter sanitization...")
        logger.log_dt_action(
            action_type="authentication",
            tool_name="login",
            parameters={"username": "john", "password": "secret123", "api_key": "sk-1234"},
            autonomous=False,
            execution_time_ms=100.0
        )
        
        # Test 5: Get recent logs
        print("\nTest 5: Recent logs...")
        recent = logger.get_recent_logs(limit=3)
        for log in recent:
            print(f"  - {log['action_type']} [{log.get('tool', 'N/A')}] - {log['result_status']}")
        
        # Test 6: Action summary
        print("\nTest 6: Action summary...")
        summary = logger.get_action_summary()
        print(json.dumps(summary, indent=2))
        
        # Test 7: Search logs
        print("\nTest 7: Search for failed actions...")
        failed = logger.search_logs(failed_only=True)
        print(f"  Found {len(failed)} failed actions")
    
    test_audit_logger()
