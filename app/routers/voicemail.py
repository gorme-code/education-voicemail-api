"""Voicemail endpoints. Bodies implemented in Steps 9.1 / 9.2."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.models.voicemail_models import (
    AttachmentResponse,
    VoicemailCreateRequest,
    VoicemailCreateResponse,
)
from app.services.auth import verify_api_key

router = APIRouter(prefix="/api/voicemail", tags=["voicemail"])


@router.post("", response_model=VoicemailCreateResponse)
def create_voicemail_case(
    payload: VoicemailCreateRequest,
    _: bool = Depends(verify_api_key),
):
    # TODO Step 9.1: query Case WHERE External_Id__c = payload.external_id;
    # if found return existing (duplicate=true), else create Case with the field mapping
    # (incl. OwnerId = SF_EDUCATION_QUEUE_ID and RecordTypeId = SF_VOICEMAIL_RECORD_TYPE_ID).
    raise NotImplementedError("Implemented in Step 9.1")


@router.post("/{case_id}/attachment", response_model=AttachmentResponse)
def upload_attachment(
    case_id: str,
    file: UploadFile = File(...),
    filename: str = Form(...),
    caller_phone: str = Form(...),
    email_timestamp: str = Form(...),
    _: bool = Depends(verify_api_key),
):
    # TODO Step 9.2: verify Case exists (404 if not); if file empty -> NO_ATTACHMENT;
    # else ContentVersion (base64 VersionData) + ContentDocumentLink (ShareType 'V').
    raise NotImplementedError("Implemented in Step 9.2")
