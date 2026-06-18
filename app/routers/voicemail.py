"""Voicemail endpoints (Steps 9.1 / 9.2)."""
from __future__ import annotations

import base64

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.models.voicemail_models import (
    AttachmentResponse,
    VoicemailCreateRequest,
    VoicemailCreateResponse,
)
from app.services.auth import verify_api_key
from app.services.salesforce import settings, sf

router = APIRouter(prefix="/api/voicemail", tags=["voicemail"])


def _soql_escape(value: str) -> str:
    """Escape a value for safe inclusion in a SOQL string literal."""
    return value.replace("\\", "\\\\").replace("'", "\\'")


@router.post("", response_model=VoicemailCreateResponse)
def create_voicemail_case(
    payload: VoicemailCreateRequest,
    _: bool = Depends(verify_api_key),
):
    # (1) Idempotency: if a Case already exists for this external_id, return it unchanged.
    existing = sf.query(
        "SELECT Id, CaseNumber FROM Case "
        f"WHERE External_Id__c = '{_soql_escape(payload.external_id)}' LIMIT 1"
    )
    if existing["totalSize"] > 0:
        record = existing["records"][0]
        return VoicemailCreateResponse(
            case_id=record["Id"],
            case_number=record.get("CaseNumber"),
            created=False,
            duplicate=True,
        )

    # (2) No match -> create the Case with the Phase 1 field mapping.
    case_fields = {
        "Subject": f"Voicemail from {payload.caller_name} — {payload.caller_phone}",
        "Origin": "Phone",
        "Status": "New",
        "OwnerId": settings.sf_education_queue_id,
        "Callback_Number__c": payload.caller_phone,
        "Caller_Name__c": payload.caller_name,
        "External_Id__c": payload.external_id,
        "Description": None,
    }
    # As-built: this org requires a Record Type on Case insert (see .env / Step 8.3 note).
    if settings.sf_voicemail_record_type_id:
        case_fields["RecordTypeId"] = settings.sf_voicemail_record_type_id

    result = sf.Case.create(case_fields)
    new_id = result["id"]
    # create() returns only the Id; fetch the auto-assigned CaseNumber for the response.
    new_number = sf.Case.get(new_id).get("CaseNumber")

    return VoicemailCreateResponse(
        case_id=new_id,
        case_number=new_number,
        created=True,
        duplicate=False,
    )


@router.post("/{case_id}/attachment", response_model=AttachmentResponse)
def upload_attachment(
    case_id: str,
    file: UploadFile = File(...),
    filename: str = Form(...),
    caller_phone: str = Form(...),
    email_timestamp: str = Form(...),
    _: bool = Depends(verify_api_key),
):
    # (1) Verify the Case exists; 404 if not.
    found = sf.query(f"SELECT Id FROM Case WHERE Id = '{_soql_escape(case_id)}' LIMIT 1")
    if found["totalSize"] == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "NOT_FOUND", "message": f"Case {case_id} not found."},
        )

    # (2) Read the bytes. Empty or missing file is not an error — report NO_ATTACHMENT.
    data = file.file.read() if file is not None else b""
    if not data:
        return AttachmentResponse(success=False, reason="NO_ATTACHMENT")

    # (3) Create the ContentVersion (base64-encoded VersionData).
    cv = sf.restful(
        "sobjects/ContentVersion/",
        method="POST",
        json={
            "Title": f"Voicemail_{caller_phone}_{email_timestamp}",
            "PathOnClient": filename,
            "VersionData": base64.b64encode(data).decode("ascii"),
        },
    )
    cv_id = cv["id"]

    # (4) Look up the ContentDocumentId Salesforce generated for that version.
    cd_id = sf.query(f"SELECT ContentDocumentId FROM ContentVersion WHERE Id = '{cv_id}'")[
        "records"
    ][0]["ContentDocumentId"]

    # (5) Link the document to the Case (ShareType 'V' = viewer).
    sf.restful(
        "sobjects/ContentDocumentLink/",
        method="POST",
        json={
            "ContentDocumentId": cd_id,
            "LinkedEntityId": case_id,
            "ShareType": "V",
        },
    )

    return AttachmentResponse(
        success=True,
        case_id=case_id,
        content_version_id=cv_id,
        content_document_id=cd_id,
        filename=filename,
    )
