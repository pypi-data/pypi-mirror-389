"""
Polar Webhooks - /v1/webhooks/polar

Handles Polar.sh webhook events for subscription management.
"""

from fastapi import APIRouter, HTTPException, Request, Header, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

from ..services.polar_service import polar_service
from ..services.supabase_service import supabase_service

router = APIRouter()


class WebhookResponse(BaseModel):
    """Webhook response model."""
    status: str
    event_type: str
    event_id: str
    processed: bool
    message: str


@router.post("/webhooks/polar", response_model=WebhookResponse)
async def handle_polar_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    polar_signature: Optional[str] = Header(None, alias="Polar-Signature")
):
    """
    Handle Polar.sh webhook events.

    Processes subscription creation, updates, cancellations, and payments.

    **Webhook Events:**
    - `subscription.created` - New subscription created
    - `subscription.updated` - Subscription modified
    - `subscription.cancelled` - Subscription cancelled
    - `payment.succeeded` - Payment successful
    - `payment.failed` - Payment failed

    **Example webhook payload:**
    ```json
    {
      "type": "subscription.created",
      "id": "evt_123...",
      "data": {
        "id": "sub_123...",
        "customer_id": "cus_123...",
        "product_id": "prod_123...",
        "status": "active"
      }
    }
    ```
    """
    # Get raw body for signature verification
    body = await request.body()

    # Verify webhook signature
    if polar_signature:
        is_valid = polar_service.verify_webhook_signature(
            body,
            polar_signature
        )

        if not is_valid:
            logger.error("Invalid Polar webhook signature")
            raise HTTPException(
                status_code=401,
                detail="Invalid webhook signature"
            )

    # Parse JSON payload
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload"
        )

    event_type = payload.get("type")
    event_id = payload.get("id")

    if not event_type or not event_id:
        raise HTTPException(
            status_code=400,
            detail="Missing event type or ID"
        )

    logger.info(f"Received Polar webhook: {event_type} ({event_id})")

    # Log webhook event
    if supabase_service.is_enabled():
        await supabase_service.log_webhook_event(
            event_type=event_type,
            event_id=event_id,
            payload=payload
        )

    # Process webhook in background
    background_tasks.add_task(
        process_webhook_background,
        event_type,
        event_id,
        payload
    )

    return WebhookResponse(
        status="received",
        event_type=event_type,
        event_id=event_id,
        processed=False,
        message="Webhook received and queued for processing"
    )


async def process_webhook_background(
    event_type: str,
    event_id: str,
    payload: Dict[str, Any]
):
    """
    Process webhook event in background.

    Args:
        event_type: Type of webhook event
        event_id: Unique event ID
        payload: Full webhook payload
    """
    try:
        logger.info(f"Processing Polar webhook: {event_type}")

        if event_type == "subscription.created":
            await handle_subscription_created(payload)
        elif event_type == "subscription.updated":
            await handle_subscription_updated(payload)
        elif event_type == "subscription.cancelled":
            await handle_subscription_cancelled(payload)
        elif event_type == "payment.succeeded":
            await handle_payment_succeeded(payload)
        elif event_type == "payment.failed":
            await handle_payment_failed(payload)
        else:
            logger.warning(f"Unhandled webhook event: {event_type}")

        # Mark as processed
        if supabase_service.is_enabled():
            await supabase_service.mark_webhook_processed(event_id)

        logger.info(f"Successfully processed webhook: {event_type}")

    except Exception as e:
        logger.error(f"Failed to process webhook {event_type}: {e}")

        # Log error
        if supabase_service.is_enabled():
            await supabase_service.mark_webhook_error(event_id, str(e))


async def handle_subscription_created(payload: Dict[str, Any]):
    """
    Handle subscription.created event.

    Creates or updates user with subscription info.
    """
    data = payload.get("data", {})

    subscription_id = data.get("id")
    customer_id = data.get("customer_id")
    product_id = data.get("product_id")
    status = data.get("status")
    customer_email = data.get("customer_email")

    logger.info(
        f"New subscription created: {subscription_id} "
        f"for customer {customer_id}"
    )

    # Get product details to determine tier
    try:
        product_info = await polar_service.get_subscription(subscription_id)
        product_name = product_info.get("product", {}).get("name", "")
        tier = polar_service.get_tier_from_product(product_name)

    except Exception as e:
        logger.error(f"Failed to get product info: {e}")
        tier = "developer"  # Default tier

    # Get or create user
    if supabase_service.is_enabled():
        user = await supabase_service.get_user_by_email(customer_email)

        if user:
            # Update existing user
            await supabase_service.update_user(
                user["id"],
                {
                    "tier": tier,
                    "polar_customer_id": customer_id,
                    "polar_subscription_id": subscription_id,
                    "subscription_status": status,
                    "subscription_started_at": datetime.utcnow().isoformat()
                }
            )
            logger.info(f"Updated user {user['id']} with subscription")

        else:
            # Create new user (will prompt for password on first login)
            user = await supabase_service.create_user_from_subscription(
                email=customer_email,
                polar_customer_id=customer_id,
                polar_subscription_id=subscription_id,
                tier=tier
            )
            logger.info(f"Created new user {user['id']} from subscription")

        # Initialize usage tracking
        await supabase_service.initialize_usage_tracking(
            user["id"],
            tier
        )


async def handle_subscription_updated(payload: Dict[str, Any]):
    """
    Handle subscription.updated event.

    Updates user tier or subscription status.
    """
    data = payload.get("data", {})

    subscription_id = data.get("id")
    status = data.get("status")

    logger.info(f"Subscription updated: {subscription_id}, status: {status}")

    if supabase_service.is_enabled():
        user = await supabase_service.get_user_by_subscription(subscription_id)

        if user:
            await supabase_service.update_user(
                user["id"],
                {
                    "subscription_status": status
                }
            )
            logger.info(f"Updated user {user['id']} subscription status")


async def handle_subscription_cancelled(payload: Dict[str, Any]):
    """
    Handle subscription.cancelled event.

    Downgrades user to free tier.
    """
    data = payload.get("data", {})

    subscription_id = data.get("id")
    cancelled_at = data.get("cancelled_at")

    logger.info(f"Subscription cancelled: {subscription_id}")

    if supabase_service.is_enabled():
        user = await supabase_service.get_user_by_subscription(subscription_id)

        if user:
            await supabase_service.update_user(
                user["id"],
                {
                    "tier": "free",
                    "subscription_status": "cancelled",
                    "subscription_ends_at": cancelled_at
                }
            )
            logger.info(f"Downgraded user {user['id']} to free tier")


async def handle_payment_succeeded(payload: Dict[str, Any]):
    """
    Handle payment.succeeded event.

    Ensures subscription is active.
    """
    data = payload.get("data", {})

    subscription_id = data.get("subscription_id")
    amount = data.get("amount")

    logger.info(
        f"Payment succeeded for subscription {subscription_id}: "
        f"${amount/100:.2f}"
    )

    if supabase_service.is_enabled():
        user = await supabase_service.get_user_by_subscription(subscription_id)

        if user:
            await supabase_service.update_user(
                user["id"],
                {
                    "subscription_status": "active"
                }
            )


async def handle_payment_failed(payload: Dict[str, Any]):
    """
    Handle payment.failed event.

    Marks subscription as past_due.
    """
    data = payload.get("data", {})

    subscription_id = data.get("subscription_id")
    error_message = data.get("error", {}).get("message", "Unknown error")

    logger.warning(
        f"Payment failed for subscription {subscription_id}: "
        f"{error_message}"
    )

    if supabase_service.is_enabled():
        user = await supabase_service.get_user_by_subscription(subscription_id)

        if user:
            await supabase_service.update_user(
                user["id"],
                {
                    "subscription_status": "past_due"
                }
            )
            logger.info(f"Marked user {user['id']} subscription as past_due")


@router.get("/webhooks/polar/test")
async def test_webhook():
    """
    Test endpoint to verify webhook configuration.

    Returns:
        Simple success message
    """
    return {
        "status": "ok",
        "message": "Polar webhook endpoint is configured correctly",
        "endpoint": "/v1/webhooks/polar"
    }
