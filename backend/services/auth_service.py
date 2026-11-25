import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from backend.config import settings
from backend.database import db, supabase_client

logger = logging.getLogger("analytix.auth_service")

security = HTTPBearer(auto_error=False)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

class AuthService:
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Creates a JWT token for local development testing only.
        In production, all authentication tokens MUST be issued by Supabase Auth.
        """
        if settings.ENVIRONMENT == "production":
            raise RuntimeError(
                "Custom token generation is prohibited in production. "
                "All session tokens must be issued by Supabase Auth."
            )
            
        secret = settings.SUPABASE_JWT_SECRET or "dev-only-secret-do-not-use-in-production-12345678"
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, secret, algorithm=ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """
        Cryptographically validates an incoming Bearer token.
        Prioritizes authoritative Supabase Auth verification.
        Never trusts client-supplied claims without verification.
        """
        if not token or not isinstance(token, str):
            return None

        # 1. Authoritative Supabase Auth verification (checks active status, revocation, expiration)
        if supabase_client and settings.is_supabase_configured:
            try:
                user_resp = supabase_client.auth.get_user(token)
                if user_resp and user_resp.user:
                    return {
                        "sub": str(user_resp.user.id),
                        "email": str(user_resp.user.email).lower()
                    }
                # If Supabase actively rejected the token, do not fall through to unverified fallbacks in production
                if settings.ENVIRONMENT == "production":
                    logger.warning("Supabase auth.get_user returned no valid active user.")
                    return None
            except Exception as e:
                logger.debug(f"Supabase auth.get_user check: {e}")
                if settings.ENVIRONMENT == "production" and not settings.SUPABASE_JWT_SECRET:
                    return None

        # 2. Cryptographic JWT Secret verification (if SUPABASE_JWT_SECRET is configured)
        if settings.SUPABASE_JWT_SECRET:
            try:
                payload = jwt.decode(
                    token, 
                    settings.SUPABASE_JWT_SECRET, 
                    algorithms=[ALGORITHM, "HS384", "HS512"],
                    options={"verify_exp": True, "verify_aud": False}
                )
                # Verify audience if present
                aud = payload.get("aud")
                if aud and aud not in ["authenticated", "anon"]:
                    logger.warning(f"Invalid JWT audience claim: {aud}")
                    return None
                return payload
            except JWTError as e:
                logger.debug(f"JWT Secret decode failed: {e}")
                if settings.ENVIRONMENT == "production":
                    return None

        # 3. Fallback for non-production development/test mode only (when Supabase credentials are not configured)
        if settings.ENVIRONMENT != "production" and not settings.is_supabase_configured:
            dev_secret = "dev-only-secret-do-not-use-in-production-12345678"
            try:
                return jwt.decode(
                    token, 
                    dev_secret, 
                    algorithms=[ALGORITHM], 
                    options={"verify_exp": True, "verify_aud": False}
                )
            except JWTError:
                return None

        return None

auth_service = AuthService()

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    """
    Core authentication dependency.
    Extracts Bearer token, validates it against Supabase Auth, and fetches
    the user's authoritative profile from the database to strictly determine their role.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = auth_service.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub") or payload.get("id")
    email = payload.get("email")

    user_profile = None
    if user_id:
        user_profile = db.get_profile_by_id(user_id)
    if not user_profile and email:
        user_profile = db.get_profile_by_email(email)

    if not user_profile:
        # If user was authenticated via Supabase Auth but profile row is missing,
        # create profile row automatically with strict 'member' role.
        if email and user_id:
            logger.info(f"Auto-creating initial profile row for authenticated user {email}")
            user_profile = db.create_user({
                "id": user_id,
                "email": email,
                "full_name": email.split("@")[0],
                "role": "member",
                "team": "None"
            }, "")
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account not found or removed from database.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return user_profile

async def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Strict Admin Authorization Dependency.
    Verifies that the authenticated user possesses the 'admin' role in the database.
    Rejects normal members with 403 Forbidden.
    """
    role = current_user.get("role", "member")
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Admin authorization required."
        )
    return current_user

async def require_member(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Verifies that the user is authenticated (member or admin).
    """
    return current_user

async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict[str, Any]]:
    """
    Dependency for public routes that tailor content if a user happens to be logged in.
    """
    if not credentials:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
