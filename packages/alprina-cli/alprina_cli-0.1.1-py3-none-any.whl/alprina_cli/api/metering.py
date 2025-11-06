"""
Metering Service for Credit Management
Checks credit availability and tracks usage in database
"""
import os
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
import logging
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class MeteringService:
    """Manage credit limits and usage tracking"""

    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            logger.error("SUPABASE_URL or SUPABASE_KEY not set")
            self.supabase = None
        else:
            self.supabase: Client = create_client(supabase_url, supabase_key)

    async def get_user_subscription(self, user_email: str) -> Optional[Dict[str, Any]]:
        """
        Get user's current subscription details.

        Args:
            user_email: User's email address

        Returns:
            Subscription data or None if not found
        """
        if not self.supabase:
            return None

        try:
            response = self.supabase.table('user_subscriptions') \
                .select('*') \
                .eq('email', user_email) \
                .eq('status', 'active') \
                .single() \
                .execute()

            return response.data if response.data else None

        except Exception as e:
            logger.error(f"Failed to get subscription for {user_email}: {str(e)}")
            return None

    async def check_credit_availability(
        self,
        user_email: str,
        credits_needed: int = 1
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Check if user has enough credits for an operation.

        Args:
            user_email: User's email address
            credits_needed: Number of credits required

        Returns:
            Tuple of (allowed: bool, message: str, subscription_data: dict)
        """
        subscription = await self.get_user_subscription(user_email)

        if not subscription:
            return False, "No active subscription found", None

        # Get current usage
        scan_limit = subscription.get('scan_limit', 0)
        scans_used = subscription.get('scans_used', 0)
        tier = subscription.get('tier', 'free')

        # Check if within hard limit (for Free tier only)
        if tier == 'free' and (scans_used + credits_needed) > scan_limit:
            return False, f"Credit limit exceeded. Upgrade to continue. ({scans_used}/{scan_limit} credits used)", subscription

        # Paid tiers: Allow overage (will be billed via Polar)
        if tier in ['developer', 'pro', 'team', 'enterprise']:
            remaining = scan_limit - scans_used
            if remaining < credits_needed:
                # Will incur overage charges
                overage = credits_needed - remaining
                return True, f"⚠️  Using {overage} overage credits (will be billed)", subscription
            else:
                return True, f"✅ {remaining - credits_needed} credits remaining", subscription

        return True, "OK", subscription

    async def record_usage(
        self,
        subscription_id: str,
        user_id: str,
        scan_type: str,
        target: str,
        credits_used: int = 1,
        duration_ms: Optional[int] = None,
        vulnerabilities_found: Optional[int] = None
    ) -> bool:
        """
        Record scan usage in database.

        Args:
            subscription_id: Subscription UUID
            user_id: User ID
            scan_type: Type of scan (red_team, owasp, etc.)
            target: Scan target
            credits_used: Number of credits consumed
            duration_ms: Scan duration in milliseconds
            vulnerabilities_found: Number of vulnerabilities detected

        Returns:
            True if recorded successfully
        """
        if not self.supabase:
            logger.error("Supabase not initialized")
            return False

        try:
            # Insert usage record
            self.supabase.table('scan_usage').insert({
                'subscription_id': subscription_id,
                'user_id': user_id,
                'scan_type': scan_type,
                'target': target,
                'credits_used': credits_used,
                'duration_ms': duration_ms,
                'vulnerabilities_found': vulnerabilities_found,
                'created_at': datetime.utcnow().isoformat()
            }).execute()

            # Increment usage counter atomically
            self.supabase.rpc('increment_scans_used', {
                'subscription_id': subscription_id
            }).execute()

            logger.info(f"✅ Recorded {credits_used} credits for {scan_type} scan")
            return True

        except Exception as e:
            logger.error(f"Failed to record usage: {str(e)}")
            return False

    async def get_usage_stats(self, user_email: str) -> Optional[Dict[str, Any]]:
        """
        Get usage statistics for user's dashboard.

        Args:
            user_email: User's email address

        Returns:
            {
                "tier": "developer",
                "scan_limit": 100,
                "scans_used": 45,
                "scans_remaining": 55,
                "overage": 0,
                "current_period_start": "2025-01-01T00:00:00Z",
                "current_period_end": "2025-02-01T00:00:00Z",
                "recent_scans": [...]
            }
        """
        subscription = await self.get_user_subscription(user_email)

        if not subscription:
            return None

        scan_limit = subscription.get('scan_limit', 0)
        scans_used = subscription.get('scans_used', 0)
        overage = max(0, scans_used - scan_limit)

        # Get recent scan history
        try:
            recent_scans = self.supabase.table('scan_usage') \
                .select('*') \
                .eq('subscription_id', subscription['id']) \
                .order('created_at', desc=True) \
                .limit(10) \
                .execute()

            return {
                "tier": subscription.get('tier'),
                "scan_limit": scan_limit,
                "scans_used": scans_used,
                "scans_remaining": max(0, scan_limit - scans_used),
                "overage": overage,
                "current_period_start": subscription.get('current_period_start'),
                "current_period_end": subscription.get('current_period_end'),
                "recent_scans": recent_scans.data if recent_scans.data else []
            }

        except Exception as e:
            logger.error(f"Failed to get usage stats: {str(e)}")
            return None

    async def reset_monthly_usage(self, subscription_id: str) -> bool:
        """
        Reset usage counter at billing period renewal.
        Called by webhook handler.

        Args:
            subscription_id: Subscription UUID

        Returns:
            True if reset successfully
        """
        if not self.supabase:
            return False

        try:
            self.supabase.table('user_subscriptions').update({
                'scans_used': 0,
                'current_period_start': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', subscription_id).execute()

            logger.info(f"✅ Reset usage for subscription {subscription_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to reset usage: {str(e)}")
            return False
