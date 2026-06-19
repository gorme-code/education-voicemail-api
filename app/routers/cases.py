"""Case query endpoints. Bodies implemented in Steps 9.3 / 9.4."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.case_models import (
    AttachmentDetail,
    CaseDetail,
    CaseListResponse,
    CaseSummary,
)
from app.services.auth import verify_api_key
from app.services.salesforce import sf

router = APIRouter(prefix="/api/cases", tags=["cases"])


def _soql_escape(value: str) -> str:
    """Escape a value for safe inclusion in a SOQL string literal."""
    return value.replace("\\", "\\\\").replace("'", "\\'")


@router.get("", response_model=CaseListResponse)
def list_cases(
    status: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    _: bool = Depends(verify_api_key),
):
    # Always scope to voicemail-origin Cases; layer on any provided filters.
    clauses = ["Origin = 'Phone'"]
    if status:
        clauses.append(f"Status = '{_soql_escape(status)}'")
    if start_date:
        clauses.append(f"CreatedDate >= {start_date.isoformat()}T00:00:00Z")
    if end_date:
        clauses.append(f"CreatedDate <= {end_date.isoformat()}T23:59:59Z")
    where = " AND ".join(clauses)

    result = sf.query(
        "SELECT Id, CaseNumber, Subject, Caller_Name__c, Callback_Number__c, Status, CreatedDate "
        f"FROM Case WHERE {where} ORDER BY CreatedDate DESC LIMIT 50"
    )
    records = result["records"]

    # One bulk query tells us which of these Cases have at least one linked file.
    case_ids = [r["Id"] for r in records]
    with_attachment: set[str] = set()
    if case_ids:
        id_list = ", ".join(f"'{cid}'" for cid in case_ids)
        links = sf.query(
            f"SELECT LinkedEntityId FROM ContentDocumentLink WHERE LinkedEntityId IN ({id_list})"
        )
        with_attachment = {link["LinkedEntityId"] for link in links["records"]}

    cases = [
        CaseSummary(
            id=r["Id"],
            case_number=r["CaseNumber"],
            subject=r.get("Subject"),
            caller_name=r.get("Caller_Name__c"),
            callback_number=r.get("Callback_Number__c"),
            status=r.get("Status"),
            created_date=r.get("CreatedDate"),
            has_attachment=r["Id"] in with_attachment,
        )
        for r in records
    ]
    return CaseListResponse(cases=cases, total=len(cases))


@router.get("/{case_id}", response_model=CaseDetail)
def get_case(case_id: str, _: bool = Depends(verify_api_key)):
    result = sf.query(
        "SELECT Id, CaseNumber, Subject, Caller_Name__c, Callback_Number__c, Status, Origin, "
        "CreatedDate, Description, External_Id__c, "
        "(SELECT ContentDocument.Id, ContentDocument.Title, ContentDocument.FileType, "
        "ContentDocument.ContentSize, ContentDocument.CreatedDate FROM ContentDocumentLinks) "
        f"FROM Case WHERE Id = '{_soql_escape(case_id)}' LIMIT 1"
    )
    if result["totalSize"] == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "NOT_FOUND", "message": f"Case {case_id} not found."},
        )
    rec = result["records"][0]

    attachments = []
    links = rec.get("ContentDocumentLinks")  # None when the Case has no files
    if links:
        for link in links["records"]:
            doc = link["ContentDocument"]
            attachments.append(
                AttachmentDetail(
                    content_document_id=doc["Id"],
                    title=doc.get("Title"),
                    file_type=doc.get("FileType"),
                    content_size=doc.get("ContentSize"),
                    created_date=doc.get("CreatedDate"),
                )
            )

    return CaseDetail(
        id=rec["Id"],
        case_number=rec["CaseNumber"],
        subject=rec.get("Subject"),
        caller_name=rec.get("Caller_Name__c"),
        callback_number=rec.get("Callback_Number__c"),
        status=rec.get("Status"),
        origin=rec.get("Origin"),
        created_date=rec.get("CreatedDate"),
        description=rec.get("Description"),
        external_id=rec.get("External_Id__c"),
        attachments=attachments,
    )
