"""
Auto-registration service for execution nodes

When a user authenticates locally, automatically establish a WebSocket tunnel
to the cloud API, enabling transparent proxying of requests.
"""

import asyncio
import os
from datetime import datetime
from typing import Optional

CLOUD_URL = os.getenv("CLOUD_URL", "https://api.oneaurica.com")
IS_EXECUTION_NODE = os.getenv("IS_EXECUTION_NODE", "false").lower() == "true"


async def register_execution_node(user_id: str, auth_token: str) -> bool:
    """
    Establish WebSocket tunnel to cloud for this execution node.
    Called automatically when user logs in locally.
    
    Skips registration if IS_EXECUTION_NODE=false (cloud deployment).
    """
    # Only register if we ARE an execution node
    if not IS_EXECUTION_NODE:
        print(f"⏭️  Skipping tunnel registration (IS_EXECUTION_NODE=false)")
        print(f"   Running in cloud mode - not an execution node")
        return True  # Return True to indicate "success" (no action needed)
    
    try:
        print(f"� Establishing WebSocket tunnel to cloud...")
        print(f"   User ID: {user_id}")
        print(f"   Cloud URL: {CLOUD_URL}")
        
        # Import tunnel client
        try:
            from src.tunnel_client import establish_tunnel
        except ImportError:
            # Try relative import if absolute fails
            import sys
            from pathlib import Path
            base_be = Path(__file__).parent.parent.parent.parent / "aurica-base-be"
            if str(base_be) not in sys.path:
                sys.path.insert(0, str(base_be))
            from src.tunnel_client import establish_tunnel
        
        # Start tunnel in background
        # Convert http/https to ws/wss
        ws_cloud_url = CLOUD_URL.replace("https://", "wss://").replace("http://", "ws://")
        
        # Create background task for tunnel
        asyncio.create_task(establish_tunnel(user_id, auth_token, ws_cloud_url))
        
        print(f"✅ Tunnel connection initiated")
        print(f"   Your execution node will be accessible via {CLOUD_URL}")
        return True
                
    except Exception as e:
        print(f"⚠️  Could not establish tunnel: {e}")
        import traceback
        traceback.print_exc()
        return False

# Remove the old heartbeat_loop function - not needed with WebSocket tunnel
# The tunnel maintains its own connection with automatic heartbeats


async def unregister_execution_node(user_id: str, auth_token: str):
    """
    Unregister execution node on logout or shutdown.
    Optional - nodes auto-expire after 5 minutes without heartbeat.
    """
    # Implementation if needed for explicit cleanup
    pass
