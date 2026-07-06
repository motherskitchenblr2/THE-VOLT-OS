"""VOLT OS — Clerk Authentication middleware."""
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import os
import jwt
from functools import lru_cache


CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY", "")
CLERK_PUBLISHABLE_KEY = os.getenv("CLERK_PUBLISHABLE_KEY", "")
CLERK_JWKS_URL = f"https://api.clerk.com/v1/jwks"

security = HTTPBearer()


@lru_cache
def get_jwks():
    """Fetch Clerk JWKS for token verification."""
    if not CLERK_SECRET_KEY:
        return None
    try:
        resp = httpx.get(CLERK_JWKS_URL, headers={"Authorization": f"Bearer {CLERK_SECRET_KEY}"})
        return resp.json().get("keys", [])
    except Exception:
        return []


def decode_token(token: str) -> dict:
    """Decode and verify a Clerk JWT."""
    jwks = get_jwks()
    if not jwks:
        # Dev mode: decode without verification
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token")

    # Find matching key
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    key = next((k for k in jwks if k["kid"] == kid), None)
    if not key:
        raise HTTPException(status_code=401, detail="Invalid key")

    return jwt.decode(token, jwt.PyJWK(key).key, algorithms=["RS256"], options={"verify_aud": False})


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Extract user from Clerk JWT. Returns user dict with id, email, org."""
    token = credentials.credentials
    try:
        payload = decode_token(token)
        return {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "org_id": payload.get("org_id"),
            "org_role": payload.get("org_role"),
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication failed")


def require_role(*roles: str):
    """Dependency that requires specific org roles."""
    async def check(user: dict = Depends(get_current_user)):
        if user.get("org_role") not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return check
