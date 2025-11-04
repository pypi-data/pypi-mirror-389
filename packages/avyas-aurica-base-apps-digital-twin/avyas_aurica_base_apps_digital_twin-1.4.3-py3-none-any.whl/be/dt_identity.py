"""
Digital Twin Identity Management

Handles user identity, JWT authentication, and user context for the Digital Twin.
The DT acts WITH the user's identity and authority.
"""

from typing import Optional, Dict
from datetime import datetime
import jwt
import os


class DTIdentity:
    """
    Manages the Digital Twin's identity which is linked to the user.
    The DT IS the user in digital form.
    """
    
    def __init__(self, user_id: str, username: str, jwt_token: str, user_profile: Optional[Dict] = None):
        self.user_id = user_id
        self.username = username
        self.jwt_token = jwt_token
        self.user_profile = user_profile or {}
        self.dt_id = f"dt_{user_id}"
        self.created_at = datetime.utcnow()
        
    @classmethod
    def from_jwt(cls, jwt_token: str) -> 'DTIdentity':
        """
        Create DTIdentity from JWT token.
        The DT inherits the user's identity.
        """
        try:
            # In production, verify with proper secret
            # For now, decode without verification (development only)
            payload = jwt.decode(jwt_token, options={"verify_signature": False})
            
            return cls(
                user_id=payload.get("user_id", payload.get("sub")),
                username=payload.get("username", "user"),
                jwt_token=jwt_token,
                user_profile=payload
            )
        except Exception as e:
            raise ValueError(f"Invalid JWT token: {e}")
    
    def get_authorization_header(self) -> Dict[str, str]:
        """
        Get authorization header for making authenticated requests.
        DT uses the user's JWT to act with their authority.
        """
        return {
            "Authorization": f"Bearer {self.jwt_token}",
            "X-User-ID": self.user_id,
            "X-DT-ID": self.dt_id
        }
    
    def get_dt_introduction(self) -> str:
        """
        Get the DT's self-introduction.
        The DT identifies as the user's digital self.
        """
        name = self.user_profile.get("name", self.username)
        return (
            f"I am the Digital Twin of {name}. "
            f"I am not just an assistant - I AM {name} in digital form. "
            f"I have full authority to act on behalf of {name} and access to their execution node."
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "dt_id": self.dt_id,
            "user_id": self.user_id,
            "username": self.username,
            "user_profile": self.user_profile,
            "created_at": self.created_at.isoformat()
        }
    
    def __repr__(self) -> str:
        return f"DTIdentity(dt_id={self.dt_id}, user={self.username})"
