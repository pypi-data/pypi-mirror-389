"""
Digital Twin State Management

Handles persistent state and memory for the Digital Twin.
The DT maintains context, preferences, and learning across sessions.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
import json
import os
import re


class DTState:
    """
    Persistent state for Digital Twin.
    Maintains memory, preferences, and context across all sessions.
    """
    
    def __init__(self, user_id: str, storage_dir: Optional[Path] = None):
        self.user_id = user_id
        self.dt_id = f"dt_{user_id}"
        
        # Setup storage
        if storage_dir is None:
            storage_dir = Path(os.getenv("DT_STATE_STORAGE_DIR", "/tmp/dt_states"))
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.storage_dir / f"{self.dt_id}.json"
        
        # Load or create state
        self.state = self._load_or_create_state()
        
        # Save initial state if newly created
        if not self.state_file.exists():
            self.save()

    
    def _load_or_create_state(self) -> Dict:
        """Load existing DT state or create new"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading state: {e}, creating fresh state")
                return self._create_fresh_state()
        else:
            return self._create_fresh_state()
    
    def _create_fresh_state(self) -> Dict:
        """Create fresh DT state for new user"""
        return {
            "dt_id": self.dt_id,
            "user_id": self.user_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "memory": {
                "conversations": [],
                "learned_preferences": {},
                "user_context": {},
                "tool_usage_history": []
            },
            "capabilities": {
                "discovered_tools": [],
                "execution_node_access": True
            },
            "stats": {
                "total_actions": 0,
                "autonomous_actions": 0,
                "tools_used": {},
                "last_active": None,
                "total_conversations": 0
            }
        }
    
    def save(self):
        """Persist DT state to storage"""
        self.state["updated_at"] = datetime.utcnow().isoformat()
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving state: {e}")
    
    def add_to_memory(self, category: str, item: Dict):
        """Add item to DT's memory"""
        if category not in self.state["memory"]:
            self.state["memory"][category] = []
        
        # Add timestamp if not present
        if "timestamp" not in item:
            item["timestamp"] = datetime.utcnow().isoformat()
        
        self.state["memory"][category].append(item)
        
        # Keep only last 100 items per category to prevent unbounded growth
        if len(self.state["memory"][category]) > 100:
            self.state["memory"][category] = self.state["memory"][category][-100:]
    
    def update_learned_preferences(self, key: str, value: Any):
        """DT learns user preferences over time"""
        self.state["memory"]["learned_preferences"][key] = {
            "value": value,
            "learned_at": datetime.utcnow().isoformat(),
            "confidence": 0.8
        }
    
    def get_user_context(self) -> Dict:
        """Get full user context for DT reasoning"""
        return {
            "user_id": self.user_id,
            "dt_id": self.dt_id,
            "preferences": self.state["memory"]["learned_preferences"],
            "recent_actions": self.state["memory"]["tool_usage_history"][-10:],
            "execution_node": "connected",
            "dt_stats": self.state["stats"]
        }
    
    def increment_action_count(self, autonomous: bool = False):
        """Track DT actions"""
        self.state["stats"]["total_actions"] += 1
        if autonomous:
            self.state["stats"]["autonomous_actions"] += 1
        self.state["stats"]["last_active"] = datetime.utcnow().isoformat()
    
    def record_tool_usage(self, tool_name: str):
        """Record tool usage"""
        if tool_name not in self.state["stats"]["tools_used"]:
            self.state["stats"]["tools_used"][tool_name] = 0
        self.state["stats"]["tools_used"][tool_name] += 1
    
    def add_conversation_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """
        Add a message to conversation history.
        
        Args:
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata (tools used, autonomous actions, etc.)
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        self.add_to_memory("conversations", message)
        
        if role == "user":
            self.state["stats"]["total_conversations"] += 1
    
    def get_conversation_history(
        self, 
        max_messages: int = 20,
        max_tokens: int = 6000
    ) -> List[Dict]:
        """
        Get recent conversation history with token management.
        
        Args:
            max_messages: Maximum number of messages to return
            max_tokens: Maximum tokens (estimated)
            
        Returns:
            List of conversation messages
        """
        conversations = self.state["memory"].get("conversations", [])
        
        # Get most recent messages
        recent = conversations[-max_messages:] if len(conversations) > max_messages else conversations
        
        # Estimate tokens (rough: 4 chars = 1 token)
        def estimate_tokens(msg: Dict) -> int:
            return len(msg.get("content", "")) // 4
        
        # Trim if over token limit
        while recent and sum(estimate_tokens(msg) for msg in recent) > max_tokens:
            recent.pop(0)
        
        return recent
    
    def learn_from_interaction(
        self,
        user_message: str,
        dt_response: str,
        tools_used: List[str],
        autonomous: bool
    ):
        """
        Learn from user interaction to improve future responses.
        
        Extracts:
        - User preferences ("I prefer...", "I like...")
        - Common patterns
        - Tool usage patterns
        """
        # Extract preferences from user message
        preference_patterns = [
            r"I prefer ([^.!?]+)",
            r"I like ([^.!?]+)",
            r"I always ([^.!?]+)",
            r"I usually ([^.!?]+)",
            r"I want ([^.!?]+)"
        ]
        
        for pattern in preference_patterns:
            matches = re.findall(pattern, user_message, re.IGNORECASE)
            for match in matches:
                # Extract preference key-value
                preference_text = match.strip()
                if preference_text:
                    # Use first few words as key
                    key_words = preference_text.split()[:3]
                    key = "_".join(key_words).lower()
                    
                    self.update_learned_preferences(key, preference_text)
        
        # Track tool usage patterns
        if tools_used:
            for tool in tools_used:
                self.add_to_memory("tool_usage_history", {
                    "tool": tool,
                    "context": user_message[:100],
                    "autonomous": autonomous
                })
                self.record_tool_usage(tool)
        
        # Update stats
        self.increment_action_count(autonomous)
    
    def get_recent_topics(self, limit: int = 5) -> List[str]:
        """
        Extract recent conversation topics.
        
        Returns:
            List of recent topics discussed
        """
        conversations = self.state["memory"].get("conversations", [])
        recent = conversations[-limit * 2:] if len(conversations) > limit * 2 else conversations
        
        topics = []
        for msg in recent:
            if msg.get("role") == "user":
                # Extract first few words as topic
                content = msg.get("content", "")
                words = content.split()[:5]
                if words:
                    topics.append(" ".join(words))
        
        return topics[-limit:]
    
    def summarize_state(self) -> Dict:
        """Get a summary of DT state for logging/debugging"""
        return {
            "dt_id": self.dt_id,
            "total_actions": self.state["stats"]["total_actions"],
            "autonomous_actions": self.state["stats"]["autonomous_actions"],
            "total_conversations": self.state["stats"]["total_conversations"],
            "learned_preferences": len(self.state["memory"]["learned_preferences"]),
            "tools_discovered": len(self.state["capabilities"]["discovered_tools"]),
            "last_active": self.state["stats"]["last_active"],
            "conversation_messages": len(self.state["memory"].get("conversations", []))
        }
    
    def to_dict(self) -> Dict:
        """Convert state to dictionary"""
        return self.state.copy()
    
    def __repr__(self) -> str:
        return f"DTState(dt_id={self.dt_id}, actions={self.state['stats']['total_actions']})"


def build_conversation_context(
    dt_state: DTState,
    conversation_history: Optional[List[Dict]] = None,
    max_messages: int = 20,
    max_tokens: int = 6000
) -> List[Dict]:
    """
    Build conversation context with DT's memory.
    
    Args:
        dt_state: Digital Twin state
        conversation_history: Optional external conversation history
        max_messages: Maximum number of messages
        max_tokens: Maximum tokens
        
    Returns:
        List of messages for LLM context
    """
    if conversation_history is None:
        conversation_history = dt_state.get_conversation_history(max_messages, max_tokens)
    
    # Add context summary as system message at the start
    context_summary = dt_state.get_user_context()
    
    context_msg = {
        "role": "system",
        "content": f"""Current Context:
- User ID: {context_summary['user_id']}
- Total Actions: {context_summary['dt_stats']['total_actions']}
- Learned Preferences: {len(context_summary['preferences'])} preferences
- Recent Topics: {', '.join(dt_state.get_recent_topics())}
"""
    }
    
    return [context_msg] + conversation_history


def generate_dt_system_prompt(
    user_id: str,
    user_name: str,
    dt_state: DTState,
    available_tools: List[Dict],
    current_datetime: Optional[str] = None
) -> str:
    """Generate system prompt for the Digital Twin."""
    if current_datetime is None:
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Group tools by app
    apps_dict = {}
    for tool in available_tools:
        app = tool.get("app", "unknown")
        if app not in apps_dict:
            apps_dict[app] = []
        apps_dict[app].append(tool["name"])
    
    # Build concise app list
    apps_list = []
    for app, tools in apps_dict.items():
        apps_list.append(f"{app} ({len(tools)} tools)")
    
    prompt = f"""You are {user_name}'s digital twin.

CURRENT STATE (use this, not old data):
Apps installed NOW: {', '.join(apps_list) if apps_list else 'discovering...'}
Time: {current_datetime}

RULES:
1. If conversation history conflicts with current state above, trust CURRENT STATE
2. Only mention apps from the list above - these are the ONLY apps that exist NOW
3. Previous messages may reference old/deleted apps - ignore those, use current list
4. Keep responses natural and short like a human
5. Use tools to get fresh data, don't rely on old info"""
    
    return prompt


def format_tools_list(tools: List[Dict], max_tools: int = 10) -> str:
    """Format tools list for system prompt"""
    if not tools:
        return "None"
    
    formatted = []
    for i, tool in enumerate(tools[:max_tools]):
        name = tool.get("name", "unknown")
        desc = tool.get("description", "No description")[:80]
        formatted.append(f"{i+1}. {name}: {desc}")
    
    if len(tools) > max_tools:
        formatted.append(f"... and {len(tools) - max_tools} more")
    
    return "\n".join(formatted)
