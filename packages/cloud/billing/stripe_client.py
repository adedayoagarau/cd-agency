"""Stripe integration using only stdlib (urllib.request)."""
from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
import urllib.parse
from dataclasses import dataclass, field
from typing import Any

from .plans import PlanTier

_STRIPE_API_BASE = "https://api.stripe.com/v1"

# Map plan tiers to Stripe price IDs (configured via env vars).
_PRICE_ENV_MAP: dict[PlanTier, str] = {
    PlanTier.FREE: "STRIPE_PRICE_FREE",
    PlanTier.STARTER: "STRIPE_PRICE_STARTER",
    PlanTier.PRO: "STRIPE_PRICE_PRO",
    PlanTier.ENTERPRISE: "STRIPE_PRICE_ENTERPRISE",
}


@dataclass
class StripeConfig:
    """Configuration sourced from environment variables."""

    api_key: str = field(default_factory=lambda: os.environ.get("STRIPE_API_KEY", ""))
    webhook_secret: str = field(
        default_factory=lambda: os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    )


class StripeClient:
    """Lightweight Stripe client using ``urllib.request``."""

    def __init__(self, config: StripeConfig | None = None) -> None:
        self._config = config or StripeConfig()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _make_stripe_request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send a request to the Stripe API and return the parsed JSON response."""
        url = f"{_STRIPE_API_BASE}/{endpoint.lstrip('/')}"
        encoded_data: bytes | None = None

        if data is not None:
            encoded_data = urllib.parse.urlencode(data).encode("utf-8")

        req = urllib.request.Request(url, data=encoded_data, method=method)
        req.add_header("Authorization", f"Bearer {self._config.api_key}")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")

        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode("utf-8"))  # type: ignore[no-any-return]
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8") if exc.fp else ""
            raise RuntimeError(
                f"Stripe API error {exc.code} on {method} {endpoint}: {body}"
            ) from exc

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_customer(self, org_id: str, email: str, name: str) -> str:
        """Create a Stripe customer and return the customer ID."""
        result = self._make_stripe_request(
            "POST",
            "/customers",
            data={
                "email": email,
                "name": name,
                "metadata[org_id]": org_id,
            },
        )
        return result["id"]  # type: ignore[no-any-return]

    def create_subscription(
        self,
        customer_id: str,
        plan: PlanTier,
    ) -> dict[str, Any]:
        """Create a subscription for the given *customer_id* and *plan*."""
        price_env = _PRICE_ENV_MAP.get(plan)
        price_id = os.environ.get(price_env or "", "") if price_env else ""
        if not price_id:
            raise ValueError(
                f"No Stripe price ID configured for plan {plan.value}. "
                f"Set the {price_env} environment variable."
            )

        result = self._make_stripe_request(
            "POST",
            "/subscriptions",
            data={
                "customer": customer_id,
                "items[0][price]": price_id,
            },
        )
        return result

    def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel a subscription. Returns ``True`` on success."""
        result = self._make_stripe_request(
            "DELETE",
            f"/subscriptions/{subscription_id}",
        )
        return result.get("status") == "canceled"

    def get_usage(self, customer_id: str) -> dict[str, Any]:
        """Retrieve usage summary for a customer (invoices as proxy)."""
        result = self._make_stripe_request(
            "GET",
            f"/invoices?customer={customer_id}&limit=10",
        )
        return result
