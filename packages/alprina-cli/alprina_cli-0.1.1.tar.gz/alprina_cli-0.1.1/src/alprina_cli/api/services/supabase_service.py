"""
Supabase service for Alprina API.
Handles database operations, authentication, and user management.
"""

import os
import secrets
import hashlib
import bcrypt
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from supabase import create_client, Client
from loguru import logger


class SupabaseService:
    """Service class for Supabase database operations."""

    def __init__(self):
        """Initialize Supabase client."""
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")

        if not self.url or not self.key:
            logger.warning("Supabase credentials not found in environment variables")
            logger.warning("Database features will be disabled")
            self.client: Optional[Client] = None
            self.enabled = False
        else:
            try:
                self.client: Client = create_client(self.url, self.key)
                self.enabled = True
                logger.info("Supabase client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                self.client = None
                self.enabled = False

    def is_enabled(self) -> bool:
        """Check if Supabase is properly configured."""
        return self.enabled and self.client is not None

    # ==========================================
    # User Management
    # ==========================================

    async def create_user(self, email: str, password: str, full_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new user with API key.

        Args:
            email: User email
            password: User password
            full_name: Optional full name

        Returns:
            Dict with user info and API key
        """
        if not self.is_enabled():
            raise Exception("Supabase not configured")

        # Hash password
        # This bcrypt wrapper expects string, not bytes
        if isinstance(password, bytes):
            password = password.decode('utf-8')
        password_hash = bcrypt.hashpw(password, bcrypt.gensalt())

        # Create user
        user_data = {
            "email": email,
            "password_hash": password_hash,
            "full_name": full_name,
            "tier": "free",
            "requests_per_hour": 100,
            "scans_per_month": 1000
        }

        response = self.client.table("users").insert(user_data).execute()
        user = response.data[0]

        # Generate API key
        api_key = self.generate_api_key()
        api_key_data = await self.create_api_key(user["id"], api_key, "Default API Key")

        logger.info(f"Created user: {email}")

        return {
            "user_id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "tier": user["tier"],
            "api_key": api_key,
            "created_at": user["created_at"]
        }

    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with email and password.

        Args:
            email: User email
            password: User password

        Returns:
            User dict if authenticated, None otherwise
        """
        if not self.is_enabled():
            raise Exception("Supabase not configured")

        # Get user by email
        response = self.client.table("users").select("*").eq("email", email).execute()

        if not response.data:
            return None

        user = response.data[0]

        # Verify password
        # This bcrypt wrapper doesn't have checkpw - it verifies by re-hashing with the stored hash
        if isinstance(password, bytes):
            password = password.decode('utf-8')

        # Re-hash password with stored hash (contains salt) and compare
        password_match = bcrypt.hashpw(password, user["password_hash"]) == user["password_hash"]

        if not password_match:
            return None

        # Update last login (optional - skip if column doesn't exist yet)
        try:
            self.client.table("users").update({
                "last_login_at": datetime.utcnow().isoformat()
            }).eq("id", user["id"]).execute()
        except Exception as e:
            logger.warning(f"Could not update last_login_at: {e}")

        logger.info(f"User authenticated: {email}")

        return user

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        if not self.is_enabled():
            return None

        response = self.client.table("users").select("*").eq("id", user_id).execute()
        return response.data[0] if response.data else None

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        if not self.is_enabled():
            return None

        response = self.client.table("users").select("*").eq("email", email).execute()
        return response.data[0] if response.data else None

    # ==========================================
    # API Key Management
    # ==========================================

    def generate_api_key(self) -> str:
        """Generate a new API key."""
        # Format: alprina_sk_live_<32 random characters>
        random_part = secrets.token_urlsafe(32)
        return f"alprina_sk_live_{random_part}"

    async def create_api_key(
        self,
        user_id: str,
        api_key: str,
        name: str = "API Key",
        expires_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a new API key for user.

        Args:
            user_id: User ID
            api_key: The API key (unhashed)
            name: Key name
            expires_days: Optional expiration in days

        Returns:
            API key data (without the actual key)
        """
        if not self.is_enabled():
            raise Exception("Supabase not configured")

        # Hash the key for storage
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key_prefix = api_key[:20]  # First 20 chars for display

        expires_at = None
        if expires_days:
            expires_at = (datetime.utcnow() + timedelta(days=expires_days)).isoformat()

        key_data = {
            "user_id": user_id,
            "key_hash": key_hash,
            "key_prefix": key_prefix,
            "name": name,
            "expires_at": expires_at,
            "is_active": True
        }

        response = self.client.table("api_keys").insert(key_data).execute()
        return response.data[0]

    async def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Verify API key and return associated user.

        Args:
            api_key: API key to verify

        Returns:
            User dict if valid, None otherwise
        """
        if not self.is_enabled():
            return None

        # Hash the provided key
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # Find API key
        response = self.client.table("api_keys").select("*").eq("key_hash", key_hash).eq("is_active", True).execute()

        if not response.data:
            return None

        api_key_record = response.data[0]

        # Check expiration
        if api_key_record["expires_at"]:
            expires_at = datetime.fromisoformat(api_key_record["expires_at"])
            if expires_at < datetime.utcnow():
                logger.warning(f"API key expired: {api_key_record['key_prefix']}")
                return None

        # Update last used
        self.client.table("api_keys").update({
            "last_used_at": datetime.utcnow().isoformat()
        }).eq("id", api_key_record["id"]).execute()

        # Get user
        user = await self.get_user_by_id(api_key_record["user_id"])

        if user:
            user["api_key_id"] = api_key_record["id"]

        return user

    async def list_api_keys(self, user_id: str) -> List[Dict[str, Any]]:
        """List all API keys for a user."""
        if not self.is_enabled():
            return []

        response = self.client.table("api_keys").select("id, name, key_prefix, is_active, created_at, last_used_at, expires_at").eq("user_id", user_id).execute()
        return response.data

    async def deactivate_api_key(self, key_id: str, user_id: str) -> bool:
        """Deactivate an API key."""
        if not self.is_enabled():
            return False

        self.client.table("api_keys").update({
            "is_active": False
        }).eq("id", key_id).eq("user_id", user_id).execute()

        return True

    # ==========================================
    # Scan Management
    # ==========================================

    async def create_scan(
        self,
        user_id: str,
        target: str,
        scan_type: str,
        profile: str = "default"
    ) -> Dict[str, Any]:
        """
        Create a new scan entry (before execution).

        Args:
            user_id: User ID
            target: Scan target (path, URL, etc.)
            scan_type: 'local' or 'remote'
            profile: Scan profile name

        Returns:
            Created scan data with ID
        """
        if not self.is_enabled():
            return {"id": str(secrets.token_urlsafe(16))}

        scan_data = {
            "user_id": user_id,
            "target": target,
            "scan_type": scan_type,
            "profile": profile,
            "status": "running",
            "findings_count": 0,
            "started_at": datetime.utcnow().isoformat()
        }

        response = self.client.table("scans").insert(scan_data).execute()
        logger.info(f"Created scan for user {user_id}: {target}")

        return response.data[0] if response.data else scan_data

    async def save_scan(
        self,
        scan_id: str,
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update scan with results after completion.

        Args:
            scan_id: Scan ID (UUID from database)
            results: Scan results dict

        Returns:
            Updated scan data
        """
        if not self.is_enabled():
            return results

        findings = results.get("findings", [])
        summary = results.get("summary", {})

        # Count findings by severity
        critical_count = sum(1 for f in findings if f.get("severity") == "CRITICAL")
        high_count = sum(1 for f in findings if f.get("severity") == "HIGH")
        medium_count = sum(1 for f in findings if f.get("severity") == "MEDIUM")
        low_count = sum(1 for f in findings if f.get("severity") == "LOW")
        info_count = sum(1 for f in findings if f.get("severity") == "INFO")

        scan_data = {
            "status": "completed",
            "findings_count": len(findings),
            "critical_count": critical_count,
            "high_count": high_count,
            "medium_count": medium_count,
            "low_count": low_count,
            "info_count": info_count,
            "results": results,  # Store full results as JSONB
            "completed_at": datetime.utcnow().isoformat()
        }

        response = self.client.table("scans").update(scan_data).eq("id", scan_id).execute()

        logger.info(f"Updated scan {scan_id} with results")

        return response.data[0] if response.data else scan_data

    async def get_scan(self, scan_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get scan by ID."""
        if not self.is_enabled():
            return None

        query = self.client.table("scans").select("*").eq("id", scan_id)

        if user_id:
            query = query.eq("user_id", user_id)

        response = query.execute()
        return response.data[0] if response.data else None

    async def list_scans(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 20,
        severity: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List scans for a user with pagination.

        Args:
            user_id: User ID
            page: Page number (1-indexed)
            limit: Items per page
            severity: Filter by severity

        Returns:
            Dict with scans and pagination info
        """
        if not self.is_enabled():
            return {"scans": [], "total": 0, "page": page, "pages": 0}

        # Build query
        query = self.client.table("scans").select("*", count="exact").eq("user_id", user_id)

        if severity:
            query = query.eq("max_severity", severity.upper())

        # Get total count
        count_response = query.execute()
        total = count_response.count if hasattr(count_response, 'count') else 0

        # Get paginated results
        offset = (page - 1) * limit
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

        response = query.execute()
        scans = response.data

        pages = (total + limit - 1) // limit if total > 0 else 0

        return {
            "scans": scans,
            "total": total,
            "page": page,
            "pages": pages,
            "limit": limit
        }

    # ==========================================
    # Usage Tracking
    # ==========================================

    async def increment_user_scans(self, user_id: str):
        """Increment user's scan counters."""
        if not self.is_enabled():
            return

        user = await self.get_user_by_id(user_id)
        if not user:
            return

        self.client.table("users").update({
            "total_scans": user["total_scans"] + 1,
            "monthly_scans": user["monthly_scans"] + 1,
            "last_scan_at": datetime.utcnow().isoformat()
        }).eq("id", user_id).execute()

    async def log_request(
        self,
        user_id: str,
        api_key_id: Optional[str],
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: int
    ):
        """Log API request for usage tracking."""
        if not self.is_enabled():
            return

        log_data = {
            "user_id": user_id,
            "api_key_id": api_key_id,
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "response_time_ms": response_time_ms
        }

        self.client.table("usage_logs").insert(log_data).execute()

    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get usage statistics for a user."""
        if not self.is_enabled():
            return {}

        user = await self.get_user_by_id(user_id)
        if not user:
            return {}

        # Get scans this month
        from datetime import date
        today = date.today()
        first_day = today.replace(day=1)

        response = self.client.table("scans").select("*").eq("user_id", user_id).gte("created_at", first_day.isoformat()).execute()
        scans_this_month = len(response.data)

        # Get total vulnerabilities found
        response = self.client.table("scans").select("findings_count").eq("user_id", user_id).execute()
        total_vulns = sum(scan["findings_count"] for scan in response.data)

        return {
            "user_id": user_id,
            "email": user["email"],
            "tier": user["tier"],
            "total_scans": user["total_scans"],
            "scans_this_month": scans_this_month,
            "monthly_limit": user["scans_per_month"],
            "remaining_scans": user["scans_per_month"] - user["monthly_scans"],
            "total_vulnerabilities_found": total_vulns,
            "created_at": user["created_at"]
        }

    # ==========================================
    # Rate Limiting
    # ==========================================

    async def check_rate_limit(self, user_id: str) -> Dict[str, Any]:
        """
        Check if user has exceeded rate limits.

        Returns:
            Dict with allowed status and remaining counts
        """
        if not self.is_enabled():
            return {"allowed": True}

        user = await self.get_user_by_id(user_id)
        if not user:
            return {"allowed": False, "reason": "User not found"}

        # Check monthly scans
        if user["monthly_scans"] >= user["scans_per_month"]:
            return {
                "allowed": False,
                "reason": "Monthly scan limit exceeded",
                "limit": user["scans_per_month"],
                "used": user["monthly_scans"]
            }

        # Check hourly requests (simplified - check last hour)
        hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        response = self.client.table("usage_logs").select("id", count="exact").eq("user_id", user_id).gte("created_at", hour_ago).execute()

        request_count = response.count if hasattr(response, 'count') else 0

        if request_count >= user["requests_per_hour"]:
            return {
                "allowed": False,
                "reason": "Hourly request limit exceeded",
                "limit": user["requests_per_hour"],
                "used": request_count
            }

        return {
            "allowed": True,
            "monthly_scans_remaining": user["scans_per_month"] - user["monthly_scans"],
            "hourly_requests_remaining": user["requests_per_hour"] - request_count
        }

    # ==========================================
    # Device Authorization Flow (OAuth for CLI)
    # ==========================================

    def generate_device_codes(self) -> tuple[str, str]:
        """Generate device code and user code."""
        # Device code: long random string for polling
        device_code = secrets.token_urlsafe(32)

        # User code: short, human-readable code (like GitHub's ABC-DEF)
        import random
        import string
        chars = string.ascii_uppercase + string.digits
        user_code = '-'.join([''.join(random.choices(chars, k=3)) for _ in range(2)])

        return device_code, user_code

    async def create_device_authorization(self) -> Dict[str, Any]:
        """Create a new device authorization request."""
        if not self.is_enabled():
            return {}

        device_code, user_code = self.generate_device_codes()

        auth_data = {
            "device_code": device_code,
            "user_code": user_code,
            "status": "pending"
        }

        response = self.client.table("device_codes").insert(auth_data).execute()

        logger.info(f"Created device authorization with user code: {user_code}")

        return response.data[0] if response.data else auth_data

    async def check_device_authorization(self, device_code: str) -> Optional[Dict[str, Any]]:
        """Check if device authorization has been approved."""
        if not self.is_enabled():
            return None

        response = self.client.table("device_codes").select("*").eq("device_code", device_code).execute()

        if not response.data:
            return None

        auth = response.data[0]

        # Check if expired
        from datetime import datetime
        expires_at = datetime.fromisoformat(auth["expires_at"].replace("Z", "+00:00"))
        if datetime.now().astimezone() > expires_at:
            return {"status": "expired"}

        return auth

    async def authorize_device(self, user_code: str, user_id: str) -> bool:
        """Authorize a device with user code."""
        if not self.is_enabled():
            return False

        # Find pending authorization with this user code
        response = self.client.table("device_codes").select("*").eq("user_code", user_code).eq("status", "pending").execute()

        if not response.data:
            return False

        # Update to authorized
        self.client.table("device_codes").update({
            "status": "authorized",
            "user_id": user_id,
            "authorized_at": datetime.utcnow().isoformat()
        }).eq("user_code", user_code).execute()

        logger.info(f"Device authorized with code {user_code} for user {user_id}")

        return True


# Global instance
supabase_service = SupabaseService()
