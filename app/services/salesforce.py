"""Settings + Salesforce connection helpers (Step 8.4).

Exports:
  * Settings           - pydantic-settings model loading SF_* / API_* vars from .env
  * settings           - shared Settings instance (used app-wide, incl. auth.py)
  * get_sf_connection() - cached, authenticated simple_salesforce.Salesforce instance
                          (client credentials flow); force_refresh=True re-authenticates
  * sf                 - module-level singleton imported by routers; connects lazily and
                          transparently re-authenticates if the session token expires
"""
from __future__ import annotations

import functools

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

# Module-level cache for the authenticated Salesforce client.
_sf_cache: dict = {"client": None}


def _request_token() -> dict:
    """Exchange Connected App client credentials for an access token."""
    if not (settings.sf_client_id and settings.sf_client_secret and settings.sf_instance_url):
        raise RuntimeError(
            "Salesforce credentials are not configured. Set SF_CLIENT_ID, "
            "SF_CLIENT_SECRET and SF_INSTANCE_URL in .env (see .env.example)."
        )
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

    Pass force_refresh=True to discard the cached client and re-authenticate — used
    automatically when a request fails with an expired session.

    Imported lazily so the module imports without a live token (tests, tooling).
    """
    if _sf_cache["client"] is not None and not force_refresh:
        return _sf_cache["client"]

    from simple_salesforce import Salesforce

    token = _request_token()
    sf_client = Salesforce(
        instance_url=token["instance_url"],
        session_id=token["access_token"],
        version=settings.sf_api_version,
    )
    _sf_cache["client"] = sf_client
    return sf_client


def _wrap_callable(func, rebind):
    """Wrap a Salesforce method so an expired session triggers one re-auth + retry.

    `rebind` re-resolves the method against a freshly authenticated connection.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from simple_salesforce import SalesforceExpiredSession

        try:
            return func(*args, **kwargs)
        except SalesforceExpiredSession:
            return rebind()(*args, **kwargs)

    return wrapper


class _SFTypeProxy:
    """Retry-aware wrapper around an SFType (e.g. ``sf.Case``).

    Makes mutating calls like ``sf.Case.create(...)`` re-authenticate and retry once
    if the session has expired.
    """

    def __init__(self, sobject_name: str):
        self._sobject_name = sobject_name

    def __getattr__(self, name: str):
        attr = getattr(getattr(get_sf_connection(), self._sobject_name), name)
        if not callable(attr):
            return attr
        return _wrap_callable(
            attr,
            rebind=lambda: getattr(
                getattr(get_sf_connection(force_refresh=True), self._sobject_name), name
            ),
        )


class _SalesforceProxy:
    """Module-level singleton imported by routers as ``sf``.

    Behaves like a ``simple_salesforce.Salesforce`` instance — e.g. ``sf.query(...)`` or
    ``sf.Case.create(...)`` — but the real connection is created lazily on first use and
    re-authenticated automatically (once) if the session token has expired.
    """

    def __getattr__(self, name: str):
        from simple_salesforce import SFType

        attr = getattr(get_sf_connection(), name)
        # SObject handles (sf.Case, sf.Contact, ...) get their own retry-aware proxy.
        if isinstance(attr, SFType):
            return _SFTypeProxy(name)
        # Methods (sf.query, sf.query_all, sf.restful, ...) retry on expiry.
        if callable(attr):
            return _wrap_callable(
                attr, rebind=lambda: getattr(get_sf_connection(force_refresh=True), name)
            )
        return attr


# Single shared instance: `from app.services.salesforce import sf`
sf = _SalesforceProxy()
