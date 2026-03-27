"""Stripe webhook verification and event handling."""
from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def verify_webhook_signature(
    payload: bytes,
    sig_header: str,
    secret: str,
) -> bool:
    """Verify a Stripe webhook signature (``Stripe-Signature`` header).

    Stripe sends signatures in the form::

        t=<timestamp>,v1=<signature>[,v0=<legacy_signature>]

    The expected signature is ``HMAC-SHA256(secret, "<timestamp>.<payload>")``
    compared against the ``v1`` value.
    """
    parts: dict[str, str] = {}
    for item in sig_header.split(","):
        key, _, value = item.strip().partition("=")
        if key and value:
            parts[key] = value

    timestamp = parts.get("t")
    signature = parts.get("v1")
    if not timestamp or not signature:
        return False

    # Reject events older than 5 minutes to mitigate replay attacks.
    try:
        ts_int = int(timestamp)
    except ValueError:
        return False
    if abs(time.time() - ts_int) > 300:
        return False

    signed_payload = f"{timestamp}.".encode("utf-8") + payload
    expected = hmac.new(
        secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


def handle_webhook(
    event_type: str,
    event_data: dict[str, Any],
    session: Session,
) -> dict[str, Any]:
    """Route a Stripe webhook event to the appropriate handler.

    Returns a dict summarising the action taken.
    """
    handlers: dict[str, Any] = {
        "checkout.session.completed": _handle_checkout_completed,
        "invoice.paid": _handle_invoice_paid,
        "customer.subscription.updated": _handle_subscription_updated,
        "customer.subscription.deleted": _handle_subscription_deleted,
    }

    handler = handlers.get(event_type)
    if handler is None:
        return {"status": "ignored", "event_type": event_type}

    return handler(event_data, session)  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# Individual event handlers
# ---------------------------------------------------------------------------


def _handle_checkout_completed(
    data: dict[str, Any],
    session: Session,
) -> dict[str, Any]:
    """Create a subscription record when checkout completes."""
    from ..database import Subscription

    obj = data.get("object", data)
    subscription_id = obj.get("subscription", "")
    customer_id = obj.get("customer", "")
    org_id = obj.get("metadata", {}).get("org_id", "")
    plan_tier = obj.get("metadata", {}).get("plan_tier", "free")

    sub = Subscription(
        id=subscription_id,
        organization_id=org_id,
        stripe_customer_id=customer_id,
        stripe_subscription_id=subscription_id,
        plan_tier=plan_tier,
        status="active",
    )
    session.add(sub)
    session.commit()

    return {
        "status": "created",
        "subscription_id": subscription_id,
        "org_id": org_id,
    }


def _handle_invoice_paid(
    data: dict[str, Any],
    session: Session,
) -> dict[str, Any]:
    """Create an invoice record when an invoice is paid."""
    from ..database import Invoice

    obj = data.get("object", data)
    invoice_id = obj.get("id", "")
    customer_id = obj.get("customer", "")
    subscription_id = obj.get("subscription", "")
    amount_paid = obj.get("amount_paid", 0)
    currency = obj.get("currency", "usd")

    invoice = Invoice(
        id=invoice_id,
        stripe_customer_id=customer_id,
        stripe_subscription_id=subscription_id,
        amount_paid=amount_paid,
        currency=currency,
        status="paid",
    )
    session.add(invoice)
    session.commit()

    return {
        "status": "recorded",
        "invoice_id": invoice_id,
        "amount_paid": amount_paid,
    }


def _handle_subscription_updated(
    data: dict[str, Any],
    session: Session,
) -> dict[str, Any]:
    """Update an existing subscription record."""
    from ..database import Subscription

    obj = data.get("object", data)
    subscription_id = obj.get("id", "")
    new_status = obj.get("status", "active")

    sub = (
        session.query(Subscription)
        .filter_by(stripe_subscription_id=subscription_id)
        .first()
    )
    if sub is None:
        return {"status": "not_found", "subscription_id": subscription_id}

    sub.status = new_status  # type: ignore[assignment]

    # Update plan tier if present in the event items.
    items = obj.get("items", {}).get("data", [])
    if items:
        price_id = items[0].get("price", {}).get("id", "")
        if price_id:
            sub.stripe_price_id = price_id  # type: ignore[attr-defined]

    session.commit()

    return {
        "status": "updated",
        "subscription_id": subscription_id,
        "new_status": new_status,
    }


def _handle_subscription_deleted(
    data: dict[str, Any],
    session: Session,
) -> dict[str, Any]:
    """Mark a subscription as cancelled."""
    from ..database import Subscription

    obj = data.get("object", data)
    subscription_id = obj.get("id", "")

    sub = (
        session.query(Subscription)
        .filter_by(stripe_subscription_id=subscription_id)
        .first()
    )
    if sub is None:
        return {"status": "not_found", "subscription_id": subscription_id}

    sub.status = "cancelled"  # type: ignore[assignment]
    session.commit()

    return {"status": "cancelled", "subscription_id": subscription_id}
