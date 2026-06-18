"""Settings + Salesforce connection helpers.

Step 8.4 implements the full connection (client credentials flow). This scaffold provides the
Settings object (used app-wide, including by auth.py) and a working get_sf_connection() skeleton.
"""
from __future__ import annotations

import httpx
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven configuration. Values come from .env (see .env.example)."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Salesforce Connected App (OAuth 2.0 client credentials)
    sf_client_id: str = ""
    sf_client_secret: str = ""
    sf_instance_url: str = ""
    sf_api_version: str = "62.0"

    # Phase 1 references
    sf_education_queue_id: str = ""
    sf_voicemail_record_type_id: str = ""

    # API auth
    api_key: str = ""
    api_env: str = "development"


settings = Settings()

# Simple module-level cache for the Salesforce client. Step 8.4 should add expiry handling
# (refresh on 401 / token expiry).
_sf_cache: dict = {"client": None}


def _request_token() -> dict:
    """Exchange Connected App client credentials for an access token."""
    resp = httpx.post(
        f"{settings.sf_instance_url}/services/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": settings.sf_client_id,
            "client_secret": settings.sf_client_secret,
        },
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()


def get_sf_connection(force_refresh: bool = False):
    """Return a cached, authenticated simple_salesforce.Salesforce instance.

    Imported lazily so the app/tests can import this module without simple-salesforce
    installed yet (Step 8.2 installs dependencies).
    """
    if _sf_cache["client"] is not None and not force_refresh:
        return _sf_cache["client"]

    from simple_salesforce import Salesforce

    token = _request_token()
    sf = Salesforce(
        instance_url=token["instance_url"],
        session_id=token["access_token"],
        version=settings.sf_api_version,
    )
    _sf_cache["client"] = sf
    return sf
