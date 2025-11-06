"""
Authentication endpoints - /v1/auth/*
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, Field
from typing import List, Dict, Any

from ..services.supabase_service import supabase_service
from ..middleware.auth import get_current_user

router = APIRouter()


# Request/Response Models
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    full_name: str | None = None

    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "full_name": "John Doe"
            }
        }


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterResponse(BaseModel):
    user_id: str
    email: str
    full_name: str | None
    tier: str
    api_key: str
    message: str = "Account created successfully"


class LoginResponse(BaseModel):
    user: Dict[str, Any]
    api_keys: List[Dict[str, Any]]
    session_key: str  # New session API key for immediate use
    message: str = "Login successful"


class CreateAPIKeyRequest(BaseModel):
    name: str = Field(default="API Key", description="Name for the API key")
    expires_days: int | None = Field(default=None, description="Expiration in days (optional)")


@router.post("/auth/register", response_model=RegisterResponse, status_code=201)
async def register(request: RegisterRequest):
    """
    Register a new user account using Supabase Auth.

    Creates a new user with email/password and generates an API key for CLI use.

    **New in Phase 1:**
    - Uses Supabase Auth for secure user management
    - Email verification (if enabled in Supabase dashboard)
    - Password reset capabilities
    - Foundation for social login and MFA

    **Example:**
    ```bash
    curl -X POST http://localhost:8000/v1/auth/register \\
      -H "Content-Type: application/json" \\
      -d '{
        "email": "user@example.com",
        "password": "SecurePass123!",
        "full_name": "John Doe"
      }'
    ```

    **Response:**
    - Returns user info and API key for CLI
    - Save the API key - it won't be shown again!
    - Check your email to verify your account (if email confirmation enabled)
    """
    if not supabase_service.is_enabled():
        raise HTTPException(
            status_code=503,
            detail="Database not configured. Please contact support."
        )

    # Create user via Supabase Auth
    try:
        # Sign up with Supabase Auth
        response = supabase_service.client.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {
                    "full_name": request.full_name or ""
                }
            }
        })

        # Check for errors
        if not response.user:
            raise HTTPException(
                status_code=400,
                detail="Failed to create account. Email may already be registered."
            )

        # The trigger will auto-create the profile in public.users
        # Wait a moment for the trigger to complete
        import asyncio
        await asyncio.sleep(0.5)

        # Get the created user profile
        user = await supabase_service.get_user_by_id(response.user.id)
        if not user:
            # Fallback: profile not created yet by trigger
            user = {
                "id": response.user.id,
                "email": response.user.email,
                "full_name": request.full_name,
                "tier": "free"
            }

        # Generate API key for CLI
        api_key = supabase_service.generate_api_key()
        await supabase_service.create_api_key(
            user_id=response.user.id,
            api_key=api_key,
            name="Default API Key"
        )

        return RegisterResponse(
            user_id=response.user.id,
            email=response.user.email,
            full_name=request.full_name,
            tier=user.get("tier", "free"),
            api_key=api_key,
            message="Account created! Check your email to verify your account."
        )

    except Exception as e:
        error_msg = str(e)
        if "already registered" in error_msg.lower() or "already exists" in error_msg.lower():
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "email_already_exists",
                    "message": f"An account with email '{request.email}' already exists",
                    "hint": "Use /v1/auth/login to sign in"
                }
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create account: {error_msg}"
        )


@router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Login with email and password using Supabase Auth.

    Returns user info, JWT token, and API keys.

    **New in Phase 1:**
    - Uses Supabase Auth for secure authentication
    - Returns JWT token for web/mobile apps
    - Returns API keys for CLI tools
    - Email must be verified (if verification enabled)

    **Example:**
    ```bash
    curl -X POST http://localhost:8000/v1/auth/login \\
      -H "Content-Type: application/json" \\
      -d '{
        "email": "user@example.com",
        "password": "SecurePass123!"
      }'
    ```
    """
    if not supabase_service.is_enabled():
        raise HTTPException(
            status_code=503,
            detail="Database not configured"
        )

    # Authenticate via Supabase Auth
    try:
        response = supabase_service.client.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })

        if not response.user or not response.session:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "invalid_credentials",
                    "message": "Invalid email or password"
                }
            )

        # Get user profile from public.users
        user = await supabase_service.get_user_by_id(response.user.id)
        if not user:
            # Fallback to auth data
            user = {
                "id": response.user.id,
                "email": response.user.email,
                "full_name": response.user.user_metadata.get("full_name", ""),
                "tier": "free",
                "total_scans": 0,
                "created_at": response.user.created_at
            }

        # Get API keys metadata
        api_keys = await supabase_service.list_api_keys(user["id"])

        # Create a new session API key for CLI use
        session_key = supabase_service.generate_api_key()
        await supabase_service.create_api_key(
            user_id=user["id"],
            api_key=session_key,
            name="Web Session"
        )

        # Remove sensitive data
        user_safe = {
            "id": user["id"],
            "email": user["email"],
            "full_name": user.get("full_name"),
            "tier": user.get("tier", "free"),
            "total_scans": user.get("total_scans", 0),
            "created_at": user.get("created_at")
        }

        return LoginResponse(
            user=user_safe,
            api_keys=api_keys,
            session_key=session_key  # Return API key for CLI
        )

    except Exception as e:
        error_msg = str(e)
        if "invalid" in error_msg.lower() or "credentials" in error_msg.lower():
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "invalid_credentials",
                    "message": "Invalid email or password"
                }
            )
        if "email not confirmed" in error_msg.lower():
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "email_not_confirmed",
                    "message": "Please verify your email before logging in",
                    "hint": "Check your inbox for the verification link"
                }
            )
        raise HTTPException(
            status_code=500,
            detail=f"Login failed: {error_msg}"
        )


@router.get("/auth/me")
async def get_current_user_info(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get current user information.

    Requires authentication via API key.

    **Example:**
    ```bash
    curl http://localhost:8000/v1/auth/me \\
      -H "Authorization: Bearer alprina_sk_live_..."
    ```
    """
    # Get usage stats
    stats = await supabase_service.get_user_stats(user["id"])

    return {
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "tier": user["tier"],
            "created_at": user["created_at"]
        },
        "usage": stats
    }


@router.get("/auth/api-keys")
async def list_api_keys(user: Dict[str, Any] = Depends(get_current_user)):
    """
    List all API keys for current user.

    **Example:**
    ```bash
    curl http://localhost:8000/v1/auth/api-keys \\
      -H "Authorization: Bearer alprina_sk_live_..."
    ```
    """
    api_keys = await supabase_service.list_api_keys(user["id"])

    return {
        "api_keys": api_keys,
        "total": len(api_keys)
    }


@router.post("/auth/api-keys", status_code=201)
async def create_api_key(
    request: CreateAPIKeyRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new API key.

    **Example:**
    ```bash
    curl -X POST http://localhost:8000/v1/auth/api-keys \\
      -H "Authorization: Bearer alprina_sk_live_..." \\
      -H "Content-Type: application/json" \\
      -d '{"name": "Production API Key", "expires_days": 365}'
    ```

    **Response:**
    - Returns the NEW API key
    - Save it - it won't be shown again!
    """
    # Generate new key
    api_key = supabase_service.generate_api_key()

    # Store in database
    key_data = await supabase_service.create_api_key(
        user_id=user["id"],
        api_key=api_key,
        name=request.name,
        expires_days=request.expires_days
    )

    return {
        "api_key": api_key,
        "key_info": {
            "id": key_data["id"],
            "name": key_data["name"],
            "key_prefix": key_data["key_prefix"],
            "created_at": key_data["created_at"],
            "expires_at": key_data["expires_at"]
        },
        "message": "API key created successfully. Save it securely - it won't be shown again!"
    }


@router.delete("/auth/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Revoke (deactivate) an API key.

    **Example:**
    ```bash
    curl -X DELETE http://localhost:8000/v1/auth/api-keys/{key_id} \\
      -H "Authorization: Bearer alprina_sk_live_..."
    ```
    """
    success = await supabase_service.deactivate_api_key(key_id, user["id"])

    if not success:
        raise HTTPException(404, "API key not found")

    return {
        "message": "API key revoked successfully",
        "key_id": key_id
    }


# ============================================
# Supabase Auth - Password Reset (Phase 1)
# ============================================

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordUpdateRequest(BaseModel):
    password: str = Field(..., min_length=8, description="New password (minimum 8 characters)")


@router.post("/auth/reset-password")
async def request_password_reset(request: PasswordResetRequest):
    """
    Request a password reset email.

    Sends an email with a secure link to reset the password.

    **New in Phase 1:**
    - Uses Supabase Auth email templates
    - Secure password reset flow
    - Customizable email templates

    **Example:**
    ```bash
    curl -X POST http://localhost:8000/v1/auth/reset-password \\
      -H "Content-Type: application/json" \\
      -d '{"email": "user@example.com"}'
    ```
    """
    if not supabase_service.is_enabled():
        raise HTTPException(503, "Database not configured")

    try:
        # Request password reset via Supabase Auth
        supabase_service.client.auth.reset_password_for_email(
            request.email,
            options={
                "redirect_to": "https://platform.alprina.ai/auth/reset-password"
            }
        )

        # Always return success (don't reveal if email exists)
        return {
            "message": "If an account exists with that email, we've sent a password reset link",
            "hint": "Check your inbox and spam folder"
        }

    except Exception as e:
        # Don't reveal errors (security best practice)
        return {
            "message": "If an account exists with that email, we've sent a password reset link"
        }


@router.post("/auth/update-password")
async def update_password(
    request: PasswordUpdateRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update password for authenticated user.

    **Example:**
    ```bash
    curl -X POST http://localhost:8000/v1/auth/update-password \\
      -H "Authorization: Bearer alprina_sk_live_..." \\
      -H "Content-Type: application/json" \\
      -d '{"password": "NewSecurePass123!"}'
    ```
    """
    if not supabase_service.is_enabled():
        raise HTTPException(503, "Database not configured")

    try:
        # Update password via Supabase Auth
        # Note: This requires a valid JWT session token, not API key
        supabase_service.client.auth.update_user({
            "password": request.password
        })

        return {
            "message": "Password updated successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update password: {str(e)}"
        )


# ============================================
# OAuth User Sync (GitHub, Google, etc.)
# ============================================

class SyncOAuthUserRequest(BaseModel):
    """Request to sync an OAuth user to backend database."""
    user_id: str = Field(..., description="Supabase auth.users ID")
    email: EmailStr
    full_name: str | None = None
    provider: str = Field(default="github", description="OAuth provider (github, google, etc.)")

    class Config:
        schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "full_name": "John Doe",
                "provider": "github"
            }
        }


@router.post("/auth/sync-oauth-user", status_code=201)
async def sync_oauth_user(request: SyncOAuthUserRequest):
    """
    Sync an OAuth user from Supabase auth.users to public.users table.

    This endpoint is called after a user signs up via GitHub/Google OAuth
    to create their profile in the backend database and generate an API key.

    **Flow:**
    1. User signs in with GitHub OAuth → Supabase creates auth.users record
    2. Frontend calls this endpoint to sync to public.users
    3. Backend creates API key for the user
    4. User can now use the platform

    **Example:**
    ```bash
    curl -X POST http://localhost:8000/v1/auth/sync-oauth-user \\
      -H "Content-Type: application/json" \\
      -d '{
        "user_id": "auth-user-uuid",
        "email": "user@example.com",
        "full_name": "John Doe",
        "provider": "github"
      }'
    ```

    **Response:**
    - Returns user info and API key
    - If user already exists, returns existing data
    """
    if not supabase_service.is_enabled():
        raise HTTPException(503, "Database not configured")

    try:
        # Check if user already exists in public.users
        existing_user = await supabase_service.get_user_by_id(request.user_id)

        if existing_user:
            # User already synced, just get their API keys
            api_keys = await supabase_service.list_api_keys(request.user_id)

            # Get or create a session key
            if not api_keys:
                session_key = supabase_service.generate_api_key()
                await supabase_service.create_api_key(
                    user_id=request.user_id,
                    api_key=session_key,
                    name="OAuth Session"
                )
            else:
                # Return first active key
                session_key = None  # We don't store full keys, only prefixes

            return {
                "user_id": existing_user["id"],
                "email": existing_user["email"],
                "full_name": existing_user.get("full_name"),
                "tier": existing_user.get("tier", "free"),
                "api_key": session_key,  # Will be None if keys already exist
                "message": "User already exists",
                "is_new": False
            }

        # Create new user in public.users
        user_data = {
            "id": request.user_id,  # Use same ID as auth.users
            "email": request.email,
            "full_name": request.full_name,
            "tier": "free",
            "requests_per_hour": 100,
            "scans_per_month": 1000
        }

        response = supabase_service.client.table("users").insert(user_data).execute()
        user = response.data[0] if response.data else user_data

        # Generate API key for CLI/API use
        api_key = supabase_service.generate_api_key()
        await supabase_service.create_api_key(
            user_id=request.user_id,
            api_key=api_key,
            name=f"{request.provider.title()} OAuth"
        )

        logger.info(f"Synced OAuth user to backend: {request.email} (provider: {request.provider})")

        return {
            "user_id": user["id"],
            "email": user["email"],
            "full_name": user.get("full_name"),
            "tier": user.get("tier", "free"),
            "api_key": api_key,
            "message": "OAuth user synced successfully",
            "is_new": True
        }

    except Exception as e:
        logger.error(f"Failed to sync OAuth user: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync OAuth user: {str(e)}"
        )
