"""API package initialization

Note: The app loader imports modules directly, so these imports are not used.
They're kept here for reference but commented out to avoid import errors.
"""

# Routers are loaded directly by the app loader, not through __init__.py
# from .health import router as health_router
# from .think import router as think_router
# from .act import router as act_router
# from .state import router as state_router
# from .capabilities import router as capabilities_router
# from .security import router as security_router

__all__ = [
    # "health_router",
    # "think_router",
    # "act_router",
    # "state_router",
    # "capabilities_router",
    # "security_router"
]
