"""
Security API endpoints for Digital Twin

Allows users to:
- View autonomy settings
- Manage tool permissions
- View audit logs
- Check rate limits
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dt_core import DigitalTwin
from dt_identity import DTIdentity

router = APIRouter()


async def get_dt_from_request(request: Request) -> DigitalTwin:
    """Helper to create DT instance from request JWT"""
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    jwt_token = auth_header.replace("Bearer ", "")
    identity = DTIdentity.from_jwt(jwt_token)
    dt = DigitalTwin(identity)
    
    # Discover tools on first use
    if not dt.tools_discovered:
        await dt.discover_tools()
    
    return dt


class GrantPermissionRequest(BaseModel):
    """Request to grant standing permission for a tool"""
    tool_name: str


class BlockToolRequest(BaseModel):
    """Request to block a tool"""
    tool_name: str


class UpdateAutonomyModeRequest(BaseModel):
    """Request to update autonomy mode"""
    mode: str  # full, assisted, manual


class AuditSearchRequest(BaseModel):
    """Request to search audit logs"""
    tool_name: Optional[str] = None
    action_type: Optional[str] = None
    autonomous: Optional[bool] = None
    failed_only: bool = False
    limit: int = 50


@router.get("/autonomy")
async def get_autonomy_settings(request: Request):
    """
    Get autonomy settings for the user's Digital Twin.
    
    Returns current autonomy mode, blocked tools, standing permissions, etc.
    """
    try:
        dt = await get_dt_from_request(request)
        
        summary = dt.execution_node.autonomy.get_autonomy_summary()
        
        return {
            "success": True,
            "autonomy_settings": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/autonomy/mode")
async def update_autonomy_mode(request: Request, req: UpdateAutonomyModeRequest):
    """
    Update the autonomy mode for the DT.
    
    Modes:
    - full: DT acts autonomously within tool autonomy levels
    - assisted: DT suggests but asks for confirmation
    - manual: DT never acts autonomously
    """
    try:
        # Removed unused user_id
        dt = await get_dt_from_request(request)
        
        valid_modes = ["full", "assisted", "manual"]
        if req.mode not in valid_modes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid mode. Must be one of: {valid_modes}"
            )
        
        dt.execution_node.autonomy.preferences["autonomy_mode"] = req.mode
        await dt.execution_node.autonomy.save_preferences()
        
        return {
            "success": True,
            "message": f"Autonomy mode updated to: {req.mode}",
            "autonomy_mode": req.mode
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/permissions/grant")
async def grant_standing_permission(request: Request, req: GrantPermissionRequest):
    """
    Grant standing permission for a tool.
    
    This allows the DT to use the tool autonomously even if it has 'ask' autonomy level.
    """
    try:
        # Removed unused user_id
        dt = await get_dt_from_request(request)
        
        await dt.execution_node.autonomy.grant_standing_permission(req.tool_name)
        
        return {
            "success": True,
            "message": f"Granted standing permission for: {req.tool_name}",
            "tool_name": req.tool_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/permissions/revoke")
async def revoke_standing_permission(request: Request, req: GrantPermissionRequest):
    """Revoke standing permission for a tool"""
    try:
        # Removed unused user_id
        dt = await get_dt_from_request(request)
        
        await dt.execution_node.autonomy.revoke_standing_permission(req.tool_name)
        
        return {
            "success": True,
            "message": f"Revoked standing permission for: {req.tool_name}",
            "tool_name": req.tool_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tools/block")
async def block_tool(request: Request, req: BlockToolRequest):
    """Block a tool completely (DT cannot use it at all)"""
    try:
        # Removed unused user_id
        dt = await get_dt_from_request(request)
        
        await dt.execution_node.autonomy.block_tool(req.tool_name)
        
        return {
            "success": True,
            "message": f"Blocked tool: {req.tool_name}",
            "tool_name": req.tool_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tools/unblock")
async def unblock_tool(request: Request, req: BlockToolRequest):
    """Unblock a tool"""
    try:
        # Removed unused user_id
        dt = await get_dt_from_request(request)
        
        await dt.execution_node.autonomy.unblock_tool(req.tool_name)
        
        return {
            "success": True,
            "message": f"Unblocked tool: {req.tool_name}",
            "tool_name": req.tool_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rate-limits")
async def get_rate_limits(request: Request):
    """Get current rate limit statistics"""
    try:
        # Removed unused user_id
        dt = await get_dt_from_request(request)
        
        dt_id = f"dt_{user_id}"
        stats = dt.execution_node.rate_limiter.get_stats(dt_id)
        
        return {
            "success": True,
            "rate_limits": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/recent")
async def get_recent_audit_logs(request: Request, limit: int = 50):
    """Get recent audit logs"""
    try:
        # Removed unused user_id
        dt = await get_dt_from_request(request)
        
        logs = dt.execution_node.audit_logger.get_recent_logs(limit=limit)
        
        return {
            "success": True,
            "count": len(logs),
            "logs": logs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audit/search")
async def search_audit_logs(request: Request, req: AuditSearchRequest):
    """Search audit logs with filters"""
    try:
        # Removed unused user_id
        dt = await get_dt_from_request(request)
        
        logs = dt.execution_node.audit_logger.search_logs(
            tool_name=req.tool_name,
            action_type=req.action_type,
            autonomous=req.autonomous,
            failed_only=req.failed_only,
            limit=req.limit
        )
        
        return {
            "success": True,
            "count": len(logs),
            "filters": {
                "tool_name": req.tool_name,
                "action_type": req.action_type,
                "autonomous": req.autonomous,
                "failed_only": req.failed_only
            },
            "logs": logs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/summary")
async def get_audit_summary(request: Request, days: int = 7):
    """Get audit summary for the last N days"""
    try:
        # Removed unused user_id
        dt = await get_dt_from_request(request)
        
        summary = dt.execution_node.audit_logger.get_action_summary(days=days)
        
        return {
            "success": True,
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_security_summary(request: Request):
    """Get comprehensive security summary"""
    try:
        # Removed unused user_id
        dt = await get_dt_from_request(request)
        
        summary = dt.execution_node.get_security_summary()
        
        return {
            "success": True,
            "dt_id": f"dt_{user_id}",
            "security": summary,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
