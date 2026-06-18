"""Pydantic models for the voicemail endpoints (Steps 9.1 / 9.2)."""
from __future__ import annotations

from pydantic import BaseModel


class VoicemailCreateRequest(BaseModel):
    caller_phone: str
    caller_name: str
    email_timestamp: str  # ISO 8601
    email_subject: str
    external_id: str


class VoicemailCreateResponse(BaseModel):
    case_id: str
    case_number: str | None = None
    created: bool
    duplicate: bool


class AttachmentResponse(BaseModel):
    success: bool
    case_id: str | None = None
    content_version_id: str | None = None
    content_document_id: str | None = None
    filename: str | None = None
    reason: str | None = None  # e.g. "NO_ATTACHMENT"
