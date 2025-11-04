"""
Act Endpoint

Execute actions autonomously on behalf of the user.
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dt_core import DigitalTwin
from dt_identity import DTIdentity

router = APIRouter()


class ActRequest(BaseModel):
    """Request model for act endpoint"""
    action: str
    tool: Optional[str] = None
    parameters: Optional[Dict] = None
    on_behalf_of: Optional[str] = None


@router.post("/")
async def act(request: Request, req: ActRequest):
    """
    Execute an action autonomously.
    
    The DT acts with full user authority using discovered tools.
    
    Requires: JWT authentication
    """
    # Extract JWT
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    jwt_token = auth_header.replace("Bearer ", "")
    
    try:
        # Create DT identity
        identity = DTIdentity.from_jwt(jwt_token)
        
        # Verify on_behalf_of matches token (if provided)
        if req.on_behalf_of and req.on_behalf_of != identity.user_id:
            raise HTTPException(status_code=403, detail="Cannot act on behalf of another user")
        
        # Initialize Digital Twin
        dt = DigitalTwin(identity)
        
        # Discover tools if not done yet
        if not dt.tools_discovered:
            await dt.discover_tools()
        
        # DT executes the action
        result = await dt.act(
            action=req.action,
            tool=req.tool,
            parameters=req.parameters
        )
        
        return {
            **result,
            "dt_id": identity.dt_id,
            "user_id": identity.user_id,
            "authority": "user_jwt"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid JWT: {str(e)}")
    except Exception as e:
        print(f"❌ Error in act endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Digital Twin error: {str(e)}")
