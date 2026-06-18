"""API key authentication (Step 8.5).

MuleSoft authenticates to this API with a shared secret in the X-API-Key header. Every router
injects verify_api_key as a dependency.
"""
from __future__ import annotations

from fastapi import Header, HTTPException, status

from app.services.salesforce import settings


def verify_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> bool:
    """Validate the X-API-Key header against the configured API_KEY.

    Raises HTTP 401 if missing or mismatched; returns True if valid.
    """
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "UNAUTHORIZED",
                "message": "Invalid or missing API key.",
                "status_code": 401,
            },
        )
    return True
