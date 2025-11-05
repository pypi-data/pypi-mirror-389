"""
Think Endpoint

Main Digital Twin reasoning and decision-making endpoint.
This is where the DT processes user input and decides what to do.
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional

# Import from parent directory
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dt_core import DigitalTwin
from dt_identity import DTIdentity

router = APIRouter()


class ThinkRequest(BaseModel):
    """Request model for think endpoint"""
    input: str
    context: Optional[Dict] = None
    history: Optional[List[Dict]] = None


@router.post("/")
async def think(request: Request, req: ThinkRequest):
    """
    Main DT thinking/reasoning endpoint.
    
    The DT receives user input, processes it, and decides what to do.
    This is where the DT's "brain" operates.
    
    Requires: JWT authentication (user must be logged in)
    """
    # Extract JWT from Authorization header
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    jwt_token = auth_header.replace("Bearer ", "")
    
    try:
        # Create DT identity from JWT
        identity = DTIdentity.from_jwt(jwt_token)
        
        # Initialize Digital Twin
        dt = DigitalTwin(identity)
        
        # Discover tools on first use
        if not dt.tools_discovered:
            print("🔍 First-time tool discovery...")
            await dt.discover_tools()
        
        # DT thinks about the input
        result = await dt.think(
            user_input=req.input,
            context=req.context,
            history=req.history
        )
        
        return {
            **result,
            "dt_id": identity.dt_id,
            "user_id": identity.user_id,
            "dt_active": True,
            "tools_available": len(dt.execution_node.tools)
        }
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid JWT: {str(e)}")
    except Exception as e:
        print(f"❌ Error in think endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Digital Twin error: {str(e)}")
