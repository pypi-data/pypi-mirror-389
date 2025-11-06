"""
Device Authorization Flow - OAuth for CLI
Similar to GitHub CLI, Vercel CLI, etc.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any

from ..services.supabase_service import supabase_service
from ..middleware.auth import get_current_user

router = APIRouter()


class DeviceAuthResponse(BaseModel):
    device_code: str
    user_code: str
    verification_url: str
    expires_in: int = 900  # 15 minutes
    interval: int = 5  # Poll every 5 seconds


class DeviceTokenRequest(BaseModel):
    device_code: str


class AuthorizeDeviceRequest(BaseModel):
    user_code: str


@router.post("/auth/device", response_model=DeviceAuthResponse)
async def request_device_authorization():
    """
    Step 1: CLI requests device authorization.

    Returns device_code and user_code.
    CLI will poll /auth/device/token with device_code.
    User will visit verification_url and enter user_code.

    **Example (CLI):**
    ```bash
    curl -X POST http://localhost:8000/v1/auth/device
    ```

    **Response:**
    ```json
    {
      "device_code": "abc123...",
      "user_code": "ABC-DEF",
      "verification_url": "http://localhost:3000/authorize",
      "expires_in": 900,
      "interval": 5
    }
    ```

    **CLI Flow:**
    1. GET device_code and user_code
    2. Open browser to verification_url
    3. Poll /auth/device/token every 5 seconds
    4. Receive API key when user authorizes
    """
    if not supabase_service.is_enabled():
        raise HTTPException(
            status_code=503,
            detail="Database not configured"
        )

    try:
        auth = await supabase_service.create_device_authorization()

        return DeviceAuthResponse(
            device_code=auth["device_code"],
            user_code=auth["user_code"],
            verification_url="http://localhost:3000/authorize",
            expires_in=900,
            interval=5
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create device authorization: {str(e)}"
        )


@router.post("/auth/device/token")
async def poll_device_authorization(request: DeviceTokenRequest):
    """
    Step 2: CLI polls for authorization status.

    CLI calls this endpoint every 5 seconds with device_code.
    Returns 400 (pending) until user authorizes.
    Returns 200 with API key when authorized.

    **Example (CLI):**
    ```bash
    curl -X POST http://localhost:8000/v1/auth/device/token \\
      -H "Content-Type: application/json" \\
      -d '{"device_code": "abc123..."}'
    ```

    **Response (pending):**
    ```json
    {
      "error": "authorization_pending",
      "message": "User hasn't authorized yet"
    }
    ```

    **Response (authorized):**
    ```json
    {
      "api_key": "alprina_sk_live_...",
      "user": {...}
    }
    ```
    """
    if not supabase_service.is_enabled():
        raise HTTPException(
            status_code=503,
            detail="Database not configured"
        )

    try:
        auth = await supabase_service.check_device_authorization(request.device_code)

        if not auth:
            raise HTTPException(
                status_code=404,
                detail="Invalid device code"
            )

        if auth["status"] == "expired":
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "expired_token",
                    "message": "Device code has expired. Please request a new one."
                }
            )

        if auth["status"] == "pending":
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "authorization_pending",
                    "message": "User hasn't authorized yet. Keep polling."
                }
            )

        if auth["status"] == "authorized":
            # Get user and API key
            user_id = auth["user_id"]
            user = await supabase_service.get_user_by_id(user_id)

            if not user:
                raise HTTPException(404, "User not found")

            # Get user's API keys
            api_keys = await supabase_service.list_api_keys(user_id)

            if not api_keys:
                # Create a new API key for CLI
                api_key = supabase_service.generate_api_key()
                await supabase_service.create_api_key(
                    user_id=user_id,
                    api_key=api_key,
                    name="CLI (Device Authorization)"
                )
            else:
                # Use existing key (we don't store the actual key, so create new one)
                api_key = supabase_service.generate_api_key()
                await supabase_service.create_api_key(
                    user_id=user_id,
                    api_key=api_key,
                    name=f"CLI (Device Authorization) - {auth['user_code']}"
                )

            # Clean up device code
            supabase_service.client.table("device_codes").delete().eq("device_code", request.device_code).execute()

            return {
                "api_key": api_key,
                "user": {
                    "id": user["id"],
                    "email": user["email"],
                    "full_name": user["full_name"],
                    "tier": user["tier"]
                }
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check authorization: {str(e)}"
        )


@router.post("/auth/device/authorize")
async def authorize_device(
    request: AuthorizeDeviceRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Step 3: User authorizes device from browser.

    User visits /authorize page, logs in, enters user_code.
    This endpoint marks the device as authorized.

    **Example (Browser):**
    ```bash
    curl -X POST http://localhost:8000/v1/auth/device/authorize \\
      -H "Authorization: Bearer alprina_sk_live_..." \\
      -H "Content-Type: application/json" \\
      -d '{"user_code": "ABC-DEF"}'
    ```

    **Response:**
    ```json
    {
      "message": "Device authorized successfully"
    }
    ```
    """
    if not supabase_service.is_enabled():
        raise HTTPException(
            status_code=503,
            detail="Database not configured"
        )

    try:
        success = await supabase_service.authorize_device(
            user_code=request.user_code.upper(),
            user_id=user["id"]
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail="Invalid user code or authorization expired"
            )

        return {
            "message": "Device authorized successfully",
            "user_code": request.user_code
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to authorize device: {str(e)}"
        )
