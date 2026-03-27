"""Billing endpoints — usage, subscriptions, Stripe checkout, and webhooks."""
from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from packages.cloud.api.deps import CurrentUser, get_current_user, get_db, require_role
from packages.cloud.database import SubscriptionCRUD, UsageRecordCRUD

router = APIRouter(prefix="/v2/billing", tags=["billing"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class UsageResponse(BaseModel):
    org_id: str
    period_start: str
    period_end: str
    agent_runs: int = 0
    tokens_used: int = 0
    limit: int = 0
    limit_reached: bool = False


class SubscriptionResponse(BaseModel):
    id: str
    org_id: str
    plan: str
    status: str
    current_period_start: str
    current_period_end: str
    stripe_subscription_id: str | None = None


class CheckoutRequest(BaseModel):
    plan: str = Field(..., description="Plan slug, e.g. 'pro' or 'team'")
    success_url: str = Field(..., description="URL to redirect to after successful checkout")
    cancel_url: str = Field(..., description="URL to redirect to if checkout is cancelled")


class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str


class InvoiceResponse(BaseModel):
    id: str
    amount_due: int
    currency: str = "usd"
    status: str
    created_at: str
    pdf_url: str | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UsageResponse:
    """Get the current billing-period usage for the organisation."""
    usage = await UsageRecordCRUD.get_current_period_usage(db, org_id=user.org_id)
    if usage is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No usage data found for the current period.",
        )
    return UsageResponse(**usage)


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionResponse:
    """Get the active subscription for the organisation."""
    sub = await SubscriptionCRUD.get_active(db, org_id=user.org_id)
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found.",
        )
    return SubscriptionResponse(
        id=str(sub.id),
        org_id=str(sub.org_id),
        plan=sub.plan,
        status=sub.status,
        current_period_start=str(sub.current_period_start),
        current_period_end=str(sub.current_period_end),
        stripe_subscription_id=sub.stripe_subscription_id,
    )


@router.post("/checkout", response_model=CheckoutResponse, status_code=status.HTTP_201_CREATED)
async def create_checkout_session(
    body: CheckoutRequest,
    user: CurrentUser = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> CheckoutResponse:
    """Create a Stripe Checkout session for plan purchase or upgrade."""
    import stripe

    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

    plan_price_map: dict[str, str] = {
        "pro": os.getenv("STRIPE_PRICE_PRO", ""),
        "team": os.getenv("STRIPE_PRICE_TEAM", ""),
        "enterprise": os.getenv("STRIPE_PRICE_ENTERPRISE", ""),
    }

    price_id = plan_price_map.get(body.plan)
    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown plan: '{body.plan}'.",
        )

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=body.success_url,
            cancel_url=body.cancel_url,
            client_reference_id=user.org_id,
            metadata={"org_id": user.org_id, "user_id": user.user_id},
        )
    except stripe.error.StripeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Stripe error: {exc}",
        ) from exc

    return CheckoutResponse(checkout_url=session.url, session_id=session.id)


@router.post("/webhooks/stripe", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Handle incoming Stripe webhook events."""
    import stripe

    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(payload, stripe_signature, webhook_secret)
    except (ValueError, stripe.error.SignatureVerificationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Webhook signature verification failed: {exc}",
        ) from exc

    event_type: str = event["type"]

    if event_type == "checkout.session.completed":
        session_data = event["data"]["object"]
        org_id = session_data["metadata"].get("org_id", "")
        await SubscriptionCRUD.activate_from_checkout(db, org_id=org_id, session=session_data)
        await db.commit()

    elif event_type in (
        "customer.subscription.updated",
        "customer.subscription.deleted",
    ):
        sub_data = event["data"]["object"]
        await SubscriptionCRUD.sync_from_stripe(db, stripe_data=sub_data)
        await db.commit()

    elif event_type == "invoice.paid":
        invoice_data = event["data"]["object"]
        await SubscriptionCRUD.record_invoice(db, invoice_data=invoice_data)
        await db.commit()

    return {"status": "ok"}


@router.get("/invoices", response_model=list[InvoiceResponse])
async def list_invoices(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[InvoiceResponse]:
    """List invoices for the current organisation."""
    invoices = await SubscriptionCRUD.list_invoices(db, org_id=user.org_id)
    return [
        InvoiceResponse(
            id=str(inv.id),
            amount_due=inv.amount_due,
            currency=inv.currency or "usd",
            status=inv.status,
            created_at=str(inv.created_at),
            pdf_url=inv.pdf_url,
        )
        for inv in invoices
    ]
