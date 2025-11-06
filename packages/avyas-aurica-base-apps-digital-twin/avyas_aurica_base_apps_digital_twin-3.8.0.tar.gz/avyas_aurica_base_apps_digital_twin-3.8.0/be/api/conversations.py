"""
Digital Twin Conversation API

Provides API endpoints for managing DT-to-DT conversations.
All conversations are stored privately in each DT's Drive.
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import sys
from pathlib import Path

# Import Aurica Auth SDK
from src.aurica_auth import protected, get_current_user

# Import conversation manager
sys.path.insert(0, str(Path(__file__).parent.parent))
from conversation_manager import ConversationManager
from dt_identity import DTIdentity

router = APIRouter()


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation"""
    other_dt_id: str
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AddMessageRequest(BaseModel):
    """Request to add a message to a conversation"""
    conversation_id: str
    content: str
    message_type: str = "text"
    metadata: Optional[Dict[str, Any]] = None


class MarkReadRequest(BaseModel):
    """Request to mark messages as read"""
    conversation_id: str
    message_ids: List[str]


@router.post("/conversations/create")
@protected
async def create_conversation(request: Request, req: CreateConversationRequest):
    """
    Create a new conversation with another DT.
    
    This initializes a conversation in the current DT's private storage.
    The other DT will create their own copy when they participate.
    """
    user = get_current_user(request)
    
    # Extract JWT from Authorization header
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    jwt_token = auth_header.replace("Bearer ", "")
    
    try:
        # Create DT identity from JWT
        identity = DTIdentity.from_jwt(jwt_token)
        
        # Initialize conversation manager
        conv_manager = ConversationManager(
            dt_id=identity.dt_id,
            user_id=identity.user_id
        )
        
        # Create conversation
        conversation = conv_manager.create_conversation(
            other_dt_id=req.other_dt_id,
            title=req.title,
            metadata=req.metadata
        )
        
        return {
            "success": True,
            "conversation": conversation
        }
        
    except Exception as e:
        print(f"❌ Error creating conversation: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations/message")
@protected
async def add_message(request: Request, req: AddMessageRequest):
    """
    Add a message to a conversation.
    
    This stores the message in the current DT's private storage.
    """
    user = get_current_user(request)
    
    # Extract JWT from Authorization header
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    jwt_token = auth_header.replace("Bearer ", "")
    
    try:
        # Create DT identity from JWT
        identity = DTIdentity.from_jwt(jwt_token)
        
        # Initialize conversation manager
        conv_manager = ConversationManager(
            dt_id=identity.dt_id,
            user_id=identity.user_id
        )
        
        # Add message
        message = conv_manager.add_message(
            conversation_id=req.conversation_id,
            sender_dt_id=identity.dt_id,
            content=req.content,
            message_type=req.message_type,
            metadata=req.metadata
        )
        
        return {
            "success": True,
            "message": message
        }
        
    except Exception as e:
        print(f"❌ Error adding message: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/list")
@protected
async def list_conversations(
    request: Request,
    other_dt_id: Optional[str] = None,
    limit: Optional[int] = None
):
    """
    List all conversations for the current DT.
    
    Returns conversations from the DT's private storage.
    """
    user = get_current_user(request)
    
    # Extract JWT from Authorization header
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    jwt_token = auth_header.replace("Bearer ", "")
    
    try:
        # Create DT identity from JWT
        identity = DTIdentity.from_jwt(jwt_token)
        
        # Initialize conversation manager
        conv_manager = ConversationManager(
            dt_id=identity.dt_id,
            user_id=identity.user_id
        )
        
        # List conversations
        conversations = conv_manager.list_conversations(
            other_dt_id=other_dt_id,
            limit=limit
        )
        
        return {
            "success": True,
            "conversations": conversations,
            "count": len(conversations)
        }
        
    except Exception as e:
        print(f"❌ Error listing conversations: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}")
@protected
async def get_conversation(request: Request, conversation_id: str):
    """
    Get a specific conversation's metadata.
    """
    user = get_current_user(request)
    
    # Extract JWT from Authorization header
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    jwt_token = auth_header.replace("Bearer ", "")
    
    try:
        # Create DT identity from JWT
        identity = DTIdentity.from_jwt(jwt_token)
        
        # Initialize conversation manager
        conv_manager = ConversationManager(
            dt_id=identity.dt_id,
            user_id=identity.user_id
        )
        
        # Get conversation
        conversation = conv_manager.get_conversation(conversation_id)
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {
            "success": True,
            "conversation": conversation
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting conversation: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}/messages")
@protected
async def get_messages(
    request: Request,
    conversation_id: str,
    limit: Optional[int] = None,
    before_timestamp: Optional[str] = None
):
    """
    Get messages from a conversation.
    """
    user = get_current_user(request)
    
    # Extract JWT from Authorization header
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    jwt_token = auth_header.replace("Bearer ", "")
    
    try:
        # Create DT identity from JWT
        identity = DTIdentity.from_jwt(jwt_token)
        
        # Initialize conversation manager
        conv_manager = ConversationManager(
            dt_id=identity.dt_id,
            user_id=identity.user_id
        )
        
        # Get messages
        messages = conv_manager.get_messages(
            conversation_id=conversation_id,
            limit=limit,
            before_timestamp=before_timestamp
        )
        
        return {
            "success": True,
            "messages": messages,
            "count": len(messages)
        }
        
    except Exception as e:
        print(f"❌ Error getting messages: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations/mark-read")
@protected
async def mark_messages_read(request: Request, req: MarkReadRequest):
    """
    Mark messages as read in a conversation.
    """
    user = get_current_user(request)
    
    # Extract JWT from Authorization header
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    jwt_token = auth_header.replace("Bearer ", "")
    
    try:
        # Create DT identity from JWT
        identity = DTIdentity.from_jwt(jwt_token)
        
        # Initialize conversation manager
        conv_manager = ConversationManager(
            dt_id=identity.dt_id,
            user_id=identity.user_id
        )
        
        # Mark as read
        success = conv_manager.mark_as_read(
            conversation_id=req.conversation_id,
            message_ids=req.message_ids
        )
        
        return {
            "success": success
        }
        
    except Exception as e:
        print(f"❌ Error marking messages as read: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversations/{conversation_id}")
@protected
async def delete_conversation(request: Request, conversation_id: str):
    """
    Delete a conversation (soft delete).
    """
    user = get_current_user(request)
    
    # Extract JWT from Authorization header
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    jwt_token = auth_header.replace("Bearer ", "")
    
    try:
        # Create DT identity from JWT
        identity = DTIdentity.from_jwt(jwt_token)
        
        # Initialize conversation manager
        conv_manager = ConversationManager(
            dt_id=identity.dt_id,
            user_id=identity.user_id
        )
        
        # Delete conversation
        success = conv_manager.delete_conversation(conversation_id)
        
        return {
            "success": success
        }
        
    except Exception as e:
        print(f"❌ Error deleting conversation: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/stats")
@protected
async def get_conversation_stats(request: Request):
    """
    Get statistics about the DT's conversations.
    """
    user = get_current_user(request)
    
    # Extract JWT from Authorization header
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    jwt_token = auth_header.replace("Bearer ", "")
    
    try:
        # Create DT identity from JWT
        identity = DTIdentity.from_jwt(jwt_token)
        
        # Initialize conversation manager
        conv_manager = ConversationManager(
            dt_id=identity.dt_id,
            user_id=identity.user_id
        )
        
        # Get stats
        stats = conv_manager.get_conversation_stats()
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        print(f"❌ Error getting conversation stats: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
