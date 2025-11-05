"""
Rate Limiter for Digital Twin

Prevents DT from over-executing and protects against abuse.
"""

from datetime import datetime, timedelta
from collections import defaultdict
from typing import Tuple, Dict, List
import json


class DTRateLimiter:
    """
    Rate limiter for Digital Twin actions.
    
    Prevents the DT from executing too many actions in a given time window.
    Useful for:
    - Preventing infinite loops
    - Protecting external APIs
    - Ensuring fair resource usage
    """
    
    def __init__(
        self, 
        max_actions_per_minute: int = 50,
        max_actions_per_hour: int = 200,
        max_tool_calls_per_minute: int = 20
    ):
        """
        Initialize rate limiter.
        
        Args:
            max_actions_per_minute: Maximum total actions per minute
            max_actions_per_hour: Maximum total actions per hour
            max_tool_calls_per_minute: Maximum tool calls per minute
        """
        self.max_actions_per_minute = max_actions_per_minute
        self.max_actions_per_hour = max_actions_per_hour
        self.max_tool_calls_per_minute = max_tool_calls_per_minute
        
        # Track actions per DT
        self.action_history: Dict[str, List[datetime]] = defaultdict(list)
        self.tool_call_history: Dict[str, List[datetime]] = defaultdict(list)
    
    def _clean_old_actions(self, dt_id: str, window_minutes: int):
        """Remove actions older than the window"""
        now = datetime.now()
        cutoff = now - timedelta(minutes=window_minutes)
        
        self.action_history[dt_id] = [
            t for t in self.action_history[dt_id] if t > cutoff
        ]
        self.tool_call_history[dt_id] = [
            t for t in self.tool_call_history[dt_id] if t > cutoff
        ]
    
    def can_act(self, dt_id: str) -> Tuple[bool, str]:
        """
        Check if DT can take another action.
        
        Args:
            dt_id: Digital Twin ID
            
        Returns:
            Tuple of (can_act: bool, message: str)
        """
        now = datetime.now()
        
        # Clean old actions (60 minute window for hour limit)
        self._clean_old_actions(dt_id, window_minutes=60)
        
        # Check per-minute limit
        one_minute_ago = now - timedelta(minutes=1)
        recent_actions = [t for t in self.action_history[dt_id] if t > one_minute_ago]
        
        if len(recent_actions) >= self.max_actions_per_minute:
            return False, f"Rate limit exceeded: {self.max_actions_per_minute} actions/minute"
        
        # Check per-hour limit
        if len(self.action_history[dt_id]) >= self.max_actions_per_hour:
            return False, f"Rate limit exceeded: {self.max_actions_per_hour} actions/hour"
        
        return True, "ok"
    
    def can_call_tool(self, dt_id: str, tool_name: str) -> Tuple[bool, str]:
        """
        Check if DT can call a tool.
        
        Args:
            dt_id: Digital Twin ID
            tool_name: Name of the tool
            
        Returns:
            Tuple of (can_call: bool, message: str)
        """
        now = datetime.now()
        
        # Clean old tool calls
        self._clean_old_actions(dt_id, window_minutes=1)
        
        # Check tool call limit
        one_minute_ago = now - timedelta(minutes=1)
        recent_tool_calls = [t for t in self.tool_call_history[dt_id] if t > one_minute_ago]
        
        if len(recent_tool_calls) >= self.max_tool_calls_per_minute:
            return False, f"Tool call rate limit exceeded: {self.max_tool_calls_per_minute} calls/minute"
        
        return True, "ok"
    
    def record_action(self, dt_id: str):
        """Record that an action was taken"""
        self.action_history[dt_id].append(datetime.now())
    
    def record_tool_call(self, dt_id: str, tool_name: str):
        """Record that a tool was called"""
        self.tool_call_history[dt_id].append(datetime.now())
        self.record_action(dt_id)  # Tool calls are also actions
    
    def get_stats(self, dt_id: str) -> dict:
        """Get rate limit statistics for a DT"""
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        one_hour_ago = now - timedelta(hours=1)
        
        # Clean old data
        self._clean_old_actions(dt_id, window_minutes=60)
        
        actions_last_minute = len([t for t in self.action_history[dt_id] if t > one_minute_ago])
        actions_last_hour = len(self.action_history[dt_id])
        tool_calls_last_minute = len([t for t in self.tool_call_history[dt_id] if t > one_minute_ago])
        
        return {
            "dt_id": dt_id,
            "actions_last_minute": actions_last_minute,
            "actions_last_hour": actions_last_hour,
            "tool_calls_last_minute": tool_calls_last_minute,
            "limits": {
                "max_actions_per_minute": self.max_actions_per_minute,
                "max_actions_per_hour": self.max_actions_per_hour,
                "max_tool_calls_per_minute": self.max_tool_calls_per_minute
            },
            "remaining": {
                "actions_this_minute": self.max_actions_per_minute - actions_last_minute,
                "actions_this_hour": self.max_actions_per_hour - actions_last_hour,
                "tool_calls_this_minute": self.max_tool_calls_per_minute - tool_calls_last_minute
            }
        }
    
    def reset(self, dt_id: str):
        """Reset rate limits for a DT (for testing or admin override)"""
        if dt_id in self.action_history:
            del self.action_history[dt_id]
        if dt_id in self.tool_call_history:
            del self.tool_call_history[dt_id]
        print(f"♻️ Reset rate limits for {dt_id}")


# Example usage
if __name__ == "__main__":
    import time
    
    def test_rate_limiter():
        """Test rate limiter"""
        limiter = DTRateLimiter(
            max_actions_per_minute=5,
            max_actions_per_hour=10,
            max_tool_calls_per_minute=3
        )
        
        dt_id = "test_dt_123"
        
        print("=== Testing Rate Limiter ===\n")
        
        # Test 1: Normal actions
        print("Test 1: Recording actions...")
        for i in range(5):
            can_act, msg = limiter.can_act(dt_id)
            if can_act:
                limiter.record_action(dt_id)
                print(f"  Action {i+1}: ✅ {msg}")
            else:
                print(f"  Action {i+1}: 🚫 {msg}")
        
        # Test 2: Exceed per-minute limit
        print("\nTest 2: Trying to exceed per-minute limit...")
        can_act, msg = limiter.can_act(dt_id)
        print(f"  Result: {'✅' if can_act else '🚫'} {msg}")
        
        # Test 3: Tool calls
        print("\nTest 3: Recording tool calls...")
        for i in range(4):
            can_call, msg = limiter.can_call_tool(dt_id, "test_tool")
            if can_call:
                limiter.record_tool_call(dt_id, "test_tool")
                print(f"  Tool call {i+1}: ✅ {msg}")
            else:
                print(f"  Tool call {i+1}: 🚫 {msg}")
        
        # Test 4: Stats
        print("\nTest 4: Rate limit statistics")
        stats = limiter.get_stats(dt_id)
        print(json.dumps(stats, indent=2))
        
        # Test 5: Reset
        print("\nTest 5: Resetting rate limits...")
        limiter.reset(dt_id)
        stats = limiter.get_stats(dt_id)
        print(f"  Actions after reset: {stats['actions_last_minute']}")
    
    test_rate_limiter()
