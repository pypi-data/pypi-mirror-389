"""
Digital Twin Conversation Manager

Handles all DT-to-DT conversations with private storage in each participant's Drive.
This is the authoritative conversation layer - chat-app only renders.

Key principles:
- Each DT stores their own copy of conversations privately in LOCAL Drive
- Two-party conversations: both DTs keep their copy on their local machine
- All storage goes through Drive (local filesystem) for security and privacy
- Chat app is just a renderer with no storage responsibility
- Requests to api.oneaurica.com are forwarded to local execution node where Drive is accessible
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import json
import uuid

try:
    # Try to import storage client
    from apps.drive.be.api.storage_client import StorageClient
except ImportError:
    # Fallback for different import contexts
    import sys
    from pathlib import Path
    code_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(code_root / "apps" / "drive" / "be" / "api"))
    from storage_client import StorageClient


class ConversationManager:
    """
    Manages DT-to-DT conversations with private storage.
    
    Each DT maintains their own copy of conversations in their Drive.
    This ensures privacy and data ownership for each participant.
    """
    
    def __init__(self, dt_id: str, user_id: str):
        """
        Initialize conversation manager for a specific DT.
        
        Args:
            dt_id: Digital Twin identifier
            user_id: User identifier
        """
        self.dt_id = dt_id
        self.user_id = user_id
        
        # Initialize storage client for this DT
        # All conversations stored locally in data/digital-twin/conversations/{user_id}/
        # Drive is LOCAL ONLY - conversations stored on local machine's drive
        self.storage = StorageClient(app_name="digital-twin")
        self.conversations_base = f"conversations/{user_id}"
        
        # In-memory cache
        self._conversations_cache: Optional[Dict] = None
        self._messages_cache: Dict[str, List] = {}
    
    def _get_conversations_index_path(self) -> str:
        """Get path to conversations index file"""
        return f"{self.conversations_base}/index.json"
    
    def _get_conversation_messages_path(self, conversation_id: str) -> str:
        """Get path to conversation messages file"""
        return f"{self.conversations_base}/{conversation_id}/messages.json"
    
    def _get_conversation_metadata_path(self, conversation_id: str) -> str:
        """Get path to conversation metadata file"""
        return f"{self.conversations_base}/{conversation_id}/metadata.json"
    
    def _load_conversations_index(self) -> Dict:
        """Load the conversations index from Drive"""
        if self._conversations_cache is not None:
            return self._conversations_cache
        
        index_data = self.storage.read_json(self._get_conversations_index_path())
        
        if index_data is None:
            # Create new index
            index_data = {
                "dt_id": self.dt_id,
                "user_id": self.user_id,
                "created_at": datetime.utcnow().isoformat(),
                "conversations": {}
            }
            self.storage.write_json(self._get_conversations_index_path(), index_data)
        
        self._conversations_cache = index_data
        return index_data
    
    def _save_conversations_index(self, index_data: Dict) -> bool:
        """Save conversations index to Drive"""
        index_data["updated_at"] = datetime.utcnow().isoformat()
        success = self.storage.write_json(self._get_conversations_index_path(), index_data)
        if success:
            self._conversations_cache = index_data
        return success
    
    def create_conversation(
        self,
        other_dt_id: str,
        title: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Create a new conversation with another DT.
        
        Args:
            other_dt_id: The other DT's identifier
            title: Optional conversation title
            metadata: Optional metadata
            
        Returns:
            Conversation object with id and metadata
        """
        conversation_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        conversation = {
            "id": conversation_id,
            "participants": [self.dt_id, other_dt_id],
            "owner": self.dt_id,  # This DT owns this copy
            "created_at": timestamp,
            "updated_at": timestamp,
            "title": title or f"Conversation with {other_dt_id}",
            "metadata": metadata or {},
            "message_count": 0,
            "status": "active"
        }
        
        # Save conversation metadata
        self.storage.write_json(
            self._get_conversation_metadata_path(conversation_id),
            conversation
        )
        
        # Initialize empty messages file
        self.storage.write_json(
            self._get_conversation_messages_path(conversation_id),
            []
        )
        
        # Update index
        index = self._load_conversations_index()
        index["conversations"][conversation_id] = {
            "id": conversation_id,
            "other_dt": other_dt_id,
            "title": conversation["title"],
            "created_at": timestamp,
            "updated_at": timestamp,
            "message_count": 0,
            "last_message": None
        }
        self._save_conversations_index(index)
        
        return conversation
    
    def add_message(
        self,
        conversation_id: str,
        sender_dt_id: str,
        content: str,
        message_type: str = "text",
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: Conversation identifier
            sender_dt_id: DT that sent the message
            content: Message content
            message_type: Type of message (text, system, tool_result, etc.)
            metadata: Optional metadata (tools_used, etc.)
            
        Returns:
            Message object with id and timestamp
        """
        # Load existing messages
        messages = self.storage.read_json(
            self._get_conversation_messages_path(conversation_id)
        )
        
        if messages is None:
            messages = []
        
        # Create message
        message_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        message = {
            "id": message_id,
            "conversation_id": conversation_id,
            "sender": sender_dt_id,
            "content": content,
            "type": message_type,
            "timestamp": timestamp,
            "metadata": metadata or {},
            "read": sender_dt_id == self.dt_id  # Mark as read if we sent it
        }
        
        messages.append(message)
        
        # Save messages
        self.storage.write_json(
            self._get_conversation_messages_path(conversation_id),
            messages
        )
        
        # Update conversation metadata
        metadata_obj = self.storage.read_json(
            self._get_conversation_metadata_path(conversation_id)
        )
        
        if metadata_obj:
            metadata_obj["updated_at"] = timestamp
            metadata_obj["message_count"] = len(messages)
            self.storage.write_json(
                self._get_conversation_metadata_path(conversation_id),
                metadata_obj
            )
        
        # Update index
        index = self._load_conversations_index()
        if conversation_id in index["conversations"]:
            index["conversations"][conversation_id]["updated_at"] = timestamp
            index["conversations"][conversation_id]["message_count"] = len(messages)
            index["conversations"][conversation_id]["last_message"] = {
                "sender": sender_dt_id,
                "content": content[:100],  # Preview
                "timestamp": timestamp
            }
            self._save_conversations_index(index)
        
        # Clear cache for this conversation
        if conversation_id in self._messages_cache:
            del self._messages_cache[conversation_id]
        
        return message
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """
        Get conversation metadata.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Conversation metadata or None if not found
        """
        return self.storage.read_json(
            self._get_conversation_metadata_path(conversation_id)
        )
    
    def get_messages(
        self,
        conversation_id: str,
        limit: Optional[int] = None,
        before_timestamp: Optional[str] = None
    ) -> List[Dict]:
        """
        Get messages from a conversation.
        
        Args:
            conversation_id: Conversation identifier
            limit: Optional limit on number of messages
            before_timestamp: Optional timestamp to get messages before
            
        Returns:
            List of messages
        """
        # Check cache first
        if conversation_id in self._messages_cache:
            messages = self._messages_cache[conversation_id]
        else:
            messages = self.storage.read_json(
                self._get_conversation_messages_path(conversation_id)
            )
            
            if messages is None:
                return []
            
            self._messages_cache[conversation_id] = messages
        
        # Filter by timestamp if provided
        if before_timestamp:
            messages = [
                m for m in messages
                if m.get("timestamp", "") < before_timestamp
            ]
        
        # Apply limit
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    def list_conversations(
        self,
        other_dt_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        List all conversations for this DT.
        
        Args:
            other_dt_id: Optional filter by other participant
            limit: Optional limit on number of conversations
            
        Returns:
            List of conversation summaries
        """
        index = self._load_conversations_index()
        conversations = list(index["conversations"].values())
        
        # Filter by other_dt_id if provided
        if other_dt_id:
            conversations = [
                c for c in conversations
                if c.get("other_dt") == other_dt_id
            ]
        
        # Sort by updated_at descending (most recent first)
        conversations.sort(
            key=lambda c: c.get("updated_at", ""),
            reverse=True
        )
        
        # Apply limit
        if limit:
            conversations = conversations[:limit]
        
        return conversations
    
    def mark_as_read(self, conversation_id: str, message_ids: List[str]) -> bool:
        """
        Mark messages as read.
        
        Args:
            conversation_id: Conversation identifier
            message_ids: List of message IDs to mark as read
            
        Returns:
            True if successful
        """
        messages = self.storage.read_json(
            self._get_conversation_messages_path(conversation_id)
        )
        
        if messages is None:
            return False
        
        # Update read status
        modified = False
        for message in messages:
            if message.get("id") in message_ids and not message.get("read"):
                message["read"] = True
                modified = True
        
        if modified:
            self.storage.write_json(
                self._get_conversation_messages_path(conversation_id),
                messages
            )
            
            # Clear cache
            if conversation_id in self._messages_cache:
                del self._messages_cache[conversation_id]
        
        return modified
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation (soft delete - marks as deleted).
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            True if successful
        """
        # Update metadata to mark as deleted
        metadata = self.storage.read_json(
            self._get_conversation_metadata_path(conversation_id)
        )
        
        if metadata:
            metadata["status"] = "deleted"
            metadata["deleted_at"] = datetime.utcnow().isoformat()
            self.storage.write_json(
                self._get_conversation_metadata_path(conversation_id),
                metadata
            )
        
        # Remove from index
        index = self._load_conversations_index()
        if conversation_id in index["conversations"]:
            del index["conversations"][conversation_id]
            self._save_conversations_index(index)
        
        # Clear cache
        self._conversations_cache = None
        if conversation_id in self._messages_cache:
            del self._messages_cache[conversation_id]
        
        return True
    
    def get_conversation_stats(self) -> Dict:
        """
        Get statistics about conversations.
        
        Returns:
            Statistics dictionary
        """
        index = self._load_conversations_index()
        conversations = index["conversations"]
        
        total_messages = sum(
            c.get("message_count", 0)
            for c in conversations.values()
        )
        
        # Count unique participants
        participants = set()
        for c in conversations.values():
            other_dt = c.get("other_dt")
            if other_dt:
                participants.add(other_dt)
        
        return {
            "total_conversations": len(conversations),
            "total_messages": total_messages,
            "unique_participants": len(participants),
            "participants": list(participants)
        }
