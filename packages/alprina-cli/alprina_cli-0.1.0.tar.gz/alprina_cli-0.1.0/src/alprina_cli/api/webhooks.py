"""
Polar Webhook Handler
Processes subscription lifecycle events from Polar
"""
import os
import hmac
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
import logging
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class PolarWebhookHandler:
    """Handle Polar webhook events for subscription management"""

    WEBHOOK_SECRET = os.getenv("POLAR_WEBHOOK_SECRET")

    # Polar Product IDs (from your configuration)
    PRODUCT_IDS = {
        "free": "a1a52dd9-42ad-4c60-a87c-3cd99827f69e",
        "developer": "68443920-6061-434f-880d-83d4efd50fde",
        "pro": "fa25e85e-5295-4dd5-bdd9-5cb5cac15a0b",
        "team": "41768ba5-f37d-417d-a10e-fb240b702cb6"
    }

    # Tier configuration
    TIER_CONFIG = {
        "free": {"scan_limit": 10, "seats": 1, "price": 0},
        "developer": {"scan_limit": 100, "seats": 1, "price": 29},
        "pro": {"scan_limit": 500, "seats": 1, "price": 49},
        "team": {"scan_limit": 2000, "seats": 5, "price": 99}
    }

    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            logger.error("SUPABASE_URL or SUPABASE_KEY not set")
            self.supabase = None
        else:
            self.supabase: Client = create_client(supabase_url, supabase_key)

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify webhook signature from Polar.

        Args:
            payload: Raw request body
            signature: Signature from X-Polar-Signature header

        Returns:
            True if signature is valid
        """
        if not self.WEBHOOK_SECRET:
            logger.warning("POLAR_WEBHOOK_SECRET not set - skipping verification")
            return True

        expected_signature = hmac.new(
            self.WEBHOOK_SECRET.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)

    def get_tier_from_product_id(self, product_id: str) -> Optional[str]:
        """Get tier name from Polar product ID"""
        for tier, pid in self.PRODUCT_IDS.items():
            if pid == product_id:
                return tier
        return None

    async def log_webhook_event(self, event_type: str, payload: Dict[str, Any], error: Optional[str] = None) -> None:
        """Log webhook event to database"""
        if not self.supabase:
            return

        try:
            self.supabase.table('webhook_events').insert({
                'event_type': event_type,
                'payload': payload,
                'processed': error is None,
                'error': error,
                'created_at': datetime.utcnow().isoformat()
            }).execute()
        except Exception as e:
            logger.error(f"Failed to log webhook event: {str(e)}")

    async def handle_subscription_created(self, data: Dict[str, Any]) -> None:
        """
        Handle subscription.created event.
        Create new subscription record in database.
        """
        if not self.supabase:
            raise Exception("Supabase not initialized")

        subscription = data.get('data', {})
        product_id = subscription.get('product_id')
        user_email = subscription.get('customer_email') or subscription.get('user', {}).get('email')
        polar_subscription_id = subscription.get('id')

        if not user_email:
            raise Exception("No customer email in subscription data")

        tier = self.get_tier_from_product_id(product_id)
        if not tier:
            raise Exception(f"Unknown product ID: {product_id}")

        config = self.TIER_CONFIG[tier]

        # Check if subscription already exists
        existing = self.supabase.table('user_subscriptions') \
            .select('*') \
            .eq('polar_subscription_id', polar_subscription_id) \
            .execute()

        if existing.data:
            logger.info(f"Subscription {polar_subscription_id} already exists")
            return

        # Create new subscription
        self.supabase.table('user_subscriptions').insert({
            'email': user_email,
            'polar_subscription_id': polar_subscription_id,
            'polar_product_id': product_id,
            'tier': tier,
            'status': 'active',
            'scan_limit': config['scan_limit'],
            'scans_used': 0,
            'seats_limit': config['seats'],
            'seats_used': 1,
            'price_amount': config['price'],
            'price_currency': 'EUR',
            'current_period_start': datetime.utcnow().isoformat(),
            'current_period_end': (datetime.utcnow() + timedelta(days=30)).isoformat(),
            'created_at': datetime.utcnow().isoformat()
        }).execute()

        logger.info(f"✅ Created subscription for {user_email} - {tier} tier")

    async def handle_subscription_updated(self, data: Dict[str, Any]) -> None:
        """
        Handle subscription.updated event.
        Update subscription details (plan changes, etc).
        """
        if not self.supabase:
            raise Exception("Supabase not initialized")

        subscription = data.get('data', {})
        polar_subscription_id = subscription.get('id')
        product_id = subscription.get('product_id')
        status = subscription.get('status', 'active')

        tier = self.get_tier_from_product_id(product_id)
        if not tier:
            raise Exception(f"Unknown product ID: {product_id}")

        config = self.TIER_CONFIG[tier]

        # Update subscription
        self.supabase.table('user_subscriptions').update({
            'polar_product_id': product_id,
            'tier': tier,
            'status': status,
            'scan_limit': config['scan_limit'],
            'seats_limit': config['seats'],
            'price_amount': config['price'],
            'updated_at': datetime.utcnow().isoformat()
        }).eq('polar_subscription_id', polar_subscription_id).execute()

        logger.info(f"✅ Updated subscription {polar_subscription_id} to {tier} tier")

    async def handle_subscription_canceled(self, data: Dict[str, Any]) -> None:
        """
        Handle subscription.canceled event.
        Mark subscription as canceled.
        """
        if not self.supabase:
            raise Exception("Supabase not initialized")

        subscription = data.get('data', {})
        polar_subscription_id = subscription.get('id')

        # Update subscription status
        self.supabase.table('user_subscriptions').update({
            'status': 'canceled',
            'canceled_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }).eq('polar_subscription_id', polar_subscription_id).execute()

        logger.info(f"✅ Canceled subscription {polar_subscription_id}")

    async def handle_subscription_revoked(self, data: Dict[str, Any]) -> None:
        """
        Handle subscription.revoked event.
        Revoke access immediately (payment failed, etc).
        """
        if not self.supabase:
            raise Exception("Supabase not initialized")

        subscription = data.get('data', {})
        polar_subscription_id = subscription.get('id')

        # Update subscription status
        self.supabase.table('user_subscriptions').update({
            'status': 'revoked',
            'revoked_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }).eq('polar_subscription_id', polar_subscription_id).execute()

        logger.info(f"✅ Revoked subscription {polar_subscription_id}")

    async def handle_subscription_renewed(self, data: Dict[str, Any]) -> None:
        """
        Handle subscription billing period renewal.
        Reset usage counters for new billing period.
        """
        if not self.supabase:
            raise Exception("Supabase not initialized")

        subscription = data.get('data', {})
        polar_subscription_id = subscription.get('id')

        # Reset usage and update period
        self.supabase.table('user_subscriptions').update({
            'scans_used': 0,
            'current_period_start': datetime.utcnow().isoformat(),
            'current_period_end': (datetime.utcnow() + timedelta(days=30)).isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }).eq('polar_subscription_id', polar_subscription_id).execute()

        logger.info(f"✅ Renewed subscription {polar_subscription_id} - reset usage counters")

    async def process_webhook(self, request: Request) -> Dict[str, Any]:
        """
        Main webhook processor.

        Args:
            request: FastAPI request object

        Returns:
            Response data

        Raises:
            HTTPException: If signature invalid or processing fails
        """
        # Get raw body for signature verification
        body = await request.body()
        signature = request.headers.get('X-Polar-Signature', '')

        # Verify signature
        if not self.verify_signature(body, signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )

        # Parse JSON
        import json
        payload = json.loads(body)

        event_type = payload.get('type')
        logger.info(f"📥 Received webhook: {event_type}")

        try:
            # Route to appropriate handler
            if event_type == 'subscription.created':
                await self.handle_subscription_created(payload)
            elif event_type == 'subscription.updated':
                await self.handle_subscription_updated(payload)
            elif event_type == 'subscription.canceled':
                await self.handle_subscription_canceled(payload)
            elif event_type == 'subscription.revoked':
                await self.handle_subscription_revoked(payload)
            elif event_type == 'subscription.renewed':
                await self.handle_subscription_renewed(payload)
            else:
                logger.warning(f"Unhandled event type: {event_type}")

            # Log successful processing
            await self.log_webhook_event(event_type, payload)

            return {"status": "success", "event": event_type}

        except Exception as e:
            logger.error(f"Failed to process webhook: {str(e)}")
            await self.log_webhook_event(event_type, payload, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Webhook processing failed: {str(e)}"
            )
