"""Case query endpoints. Bodies implemented in Steps 9.3 / 9.4."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends

from app.models.case_models import CaseDetail, CaseListResponse
from app.services.auth import verify_api_key

router = APIRouter(prefix="/api/cases", tags=["cases"])


@router.get("", response_model=CaseListResponse)
def list_cases(
    status: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    _: bool = Depends(verify_api_key),
):
    # TODO Step 9.3: query Case WHERE Origin='Phone' (+ optional filters),
    # ORDER BY CreatedDate DESC LIMIT 50; set has_attachment per ContentDocumentLink.
    raise NotImplementedError("Implemented in Step 9.3")


@router.get("/{case_id}", response_model=CaseDetail)
def get_case(case_id: str, _: bool = Depends(verify_api_key)):
    # TODO Step 9.4: query Case by Id with ContentDocumentLinks sub-query;
    # 404 if not found; return full detail + attachments.
    raise NotImplementedError("Implemented in Step 9.4")
