"""Pydantic models for the case endpoints (Steps 9.3 / 9.4)."""
from __future__ import annotations

from pydantic import BaseModel


class CaseSummary(BaseModel):
    id: str
    case_number: str
    subject: str | None = None
    caller_name: str | None = None
    callback_number: str | None = None
    status: str | None = None
    created_date: str | None = None
    has_attachment: bool = False


class CaseListResponse(BaseModel):
    cases: list[CaseSummary]
    total: int


class AttachmentDetail(BaseModel):
    content_document_id: str
    title: str | None = None
    file_type: str | None = None
    content_size: int | None = None
    created_date: str | None = None


class CaseDetail(BaseModel):
    id: str
    case_number: str
    subject: str | None = None
    caller_name: str | None = None
    callback_number: str | None = None
    status: str | None = None
    origin: str | None = None
    created_date: str | None = None
    description: str | None = None
    external_id: str | None = None
    attachments: list[AttachmentDetail] = []
