"""
Digital Twin Identities API

Provides endpoints for managing multiple DT identities/roles.
Supports DT/role switching in the chat interface.
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import sys
from pathlib import Path

# Import Aurica Auth SDK
from src.aurica_auth import protected, get_current_user

# Import DT identity
sys.path.insert(0, str(Path(__file__).parent.parent))
from dt_identity import DTIdentity

router = APIRouter()


class CreateIdentityRequest(BaseModel):
    """Request to create a new DT identity/role"""
    role_name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@router.get("/list")
@protected
async def list_identities(request: Request):
    """
    List all DT identities/roles for the current user.
    
    This enables the DT switcher in the chat interface.
    Users can have multiple DT identities for different contexts.
    """
    user = get_current_user(request)
    
    # Extract JWT from Authorization header
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    jwt_token = auth_header.replace("Bearer ", "")
    
    try:
        # Create primary DT identity from JWT
        primary_identity = DTIdentity.from_jwt(jwt_token)
        
        # For now, return the primary identity
        # Future: Load additional identities from storage
        identities = [
            {
                "dt_id": primary_identity.dt_id,
                "user_id": primary_identity.user_id,
                "username": primary_identity.username,
                "role_name": "primary",
                "display_name": primary_identity.user_profile.get("name", primary_identity.username),
                "description": "Primary Digital Twin identity",
                "is_primary": True,
                "created_at": primary_identity.user_profile.get("created_at", datetime.utcnow().isoformat())
            }
        ]
        
        return {
            "success": True,
            "identities": identities,
            "count": len(identities),
            "current": primary_identity.dt_id
        }
        
    except Exception as e:
        print(f"❌ Error listing identities: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/current")
@protected
async def get_current_identity(request: Request):
    """
    Get the current DT identity from the JWT token.
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
        
        return {
            "success": True,
            "identity": {
                "dt_id": identity.dt_id,
                "user_id": identity.user_id,
                "username": identity.username,
                "display_name": identity.user_profile.get("name", identity.username),
                "email": identity.user_profile.get("email"),
                "role_name": "primary",
                "is_primary": True
            }
        }
        
    except Exception as e:
        print(f"❌ Error getting current identity: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create")
@protected
async def create_identity(request: Request, req: CreateIdentityRequest):
    """
    Create a new DT identity/role for the user.
    
    This allows users to have multiple DT personas for different contexts
    (e.g., professional, personal, creative, etc.)
    """
    user = get_current_user(request)
    
    # Extract JWT from Authorization header
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    jwt_token = auth_header.replace("Bearer ", "")
    
    try:
        # Create primary DT identity from JWT
        primary_identity = DTIdentity.from_jwt(jwt_token)
        
        # TODO: Implement creating additional identities
        # For now, return a placeholder response
        new_dt_id = f"dt_{primary_identity.user_id}_{req.role_name}"
        
        new_identity = {
            "dt_id": new_dt_id,
            "user_id": primary_identity.user_id,
            "username": primary_identity.username,
            "role_name": req.role_name,
            "display_name": req.display_name or req.role_name.title(),
            "description": req.description or f"{req.role_name.title()} identity",
            "is_primary": False,
            "created_at": datetime.utcnow().isoformat(),
            "metadata": req.metadata or {}
        }
        
        return {
            "success": True,
            "identity": new_identity,
            "message": "Identity creation placeholder - full implementation pending"
        }
        
    except Exception as e:
        print(f"❌ Error creating identity: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/switch")
@protected
async def switch_identity(request: Request, dt_id: str):
    """
    Switch to a different DT identity.
    
    Note: In the current implementation, this would require generating
    a new JWT token for the selected identity. This is a placeholder
    for future implementation with proper token management.
    """
    user = get_current_user(request)
    
    try:
        # TODO: Implement identity switching with proper token management
        # This would involve:
        # 1. Validating the user owns the requested dt_id
        # 2. Generating a new JWT with the new dt_id
        # 3. Returning the new token for the client to use
        
        return {
            "success": True,
            "message": "Identity switching placeholder - requires token management",
            "dt_id": dt_id,
            "note": "Client should request new token for this identity"
        }
        
    except Exception as e:
        print(f"❌ Error switching identity: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
