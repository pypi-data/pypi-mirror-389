"""
Capabilities Endpoint

List what the Digital Twin can do.
"""

from fastapi import APIRouter, Request, HTTPException

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dt_core import DigitalTwin
from dt_identity import DTIdentity

router = APIRouter()


@router.get("/")
async def get_capabilities(request: Request):
    """
    List DT capabilities.
    
    Returns what the Digital Twin can currently do:
    - Available tools discovered from execution node
    - Execution node access
    - Autonomy level
    - Features
    
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
        
        # Initialize Digital Twin
        dt = DigitalTwin(identity)
        
        # Discover tools if not done yet
        if not dt.tools_discovered:
            await dt.discover_tools()
        
        # Get capabilities
        capabilities = dt.get_capabilities()
        
        # Add DT introduction
        capabilities["introduction"] = identity.get_dt_introduction()
        
        return capabilities
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid JWT: {str(e)}")
    except Exception as e:
        print(f"❌ Error in capabilities endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Digital Twin error: {str(e)}")
