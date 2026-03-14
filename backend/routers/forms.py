from fastapi import APIRouter, HTTPException, Depends
from models import Form, VoiceFormRequest, MockServiceRequest, MockServiceResponse
from services.llm_service import llm_service
from services.form_service import form_service
from database import get_database
from routers.auth import verify_token
from datetime import datetime, timezone
from typing import List
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/forms", tags=["forms"])


@router.post("/process-voice", response_model=Form, status_code=201)
async def process_voice_to_form(
    request: VoiceFormRequest,
    username: str = Depends(verify_token),
):
    """
    Receives transcribed text in the request body (never in URL params —
    this is PII/medical/banking data).
    """
    try:
        extracted_data = await llm_service.extract_form_data(
            request.text, request.form_type
        )
        form = await form_service.create_form_from_data(
            username, request.form_type, extracted_data
        )
        db = get_database()
        await db.forms.insert_one(form.model_dump(mode="json"))
        logger.info(f"Form {form.form_id} created for user {username}")
        return form

    except Exception as e:
        logger.error(f"Form processing error for user {username}: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Form processing failed")


@router.get("/list", response_model=List[Form])
async def list_forms(username: str = Depends(verify_token)):
    try:
        db = get_database()
        # Exclude MongoDB _id from results — it breaks Pydantic validation on the frontend
        forms = await db.forms.find(
            {"user_id": username}, {"_id": 0}
        ).to_list(length=100)
        return forms

    except Exception as e:
        logger.error(f"Form list error for user {username}: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Failed to retrieve forms")


@router.get("/{form_id}", response_model=Form)
async def get_form(form_id: str, username: str = Depends(verify_token)):
    try:
        db = get_database()
        form = await db.forms.find_one(
            {"form_id": form_id, "user_id": username}, {"_id": 0}
        )
        if not form:
            raise HTTPException(status_code=404, detail="Form not found")
        return form

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Form retrieval error: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Failed to retrieve form")


@router.put("/{form_id}", response_model=Form)
async def update_form(
    form_id: str,
    form: Form,
    username: str = Depends(verify_token),
):
    # Validate path param matches body — prevents cross-form corruption
    if form.form_id != form_id:
        raise HTTPException(
            status_code=400,
            detail="form_id in URL does not match form_id in body",
        )

    try:
        db = get_database()
        existing = await db.forms.find_one({"form_id": form_id, "user_id": username})
        if not existing:
            raise HTTPException(status_code=404, detail="Form not found")

        update_data = form.model_dump(mode="json")
        # Always stamp updated_at server-side — never trust client timestamp
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

        await db.forms.update_one(
            {"form_id": form_id},
            {"$set": update_data},
        )
        logger.info(f"Form {form_id} updated by {username}")
        return form

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Form update error: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Failed to update form")


@router.post("/mock-service", response_model=MockServiceResponse)
async def mock_service_integration(
    request: MockServiceRequest,
    username: str = Depends(verify_token),
):
    service_responses = {
        "bank": {
            "kyc": "KYC verification initiated. Reference ID: KYC-2024-001",
            "account": "Account details retrieved successfully",
        },
        "health": {
            "appointment": "Appointment scheduled for next available slot",
            "records": "Medical records accessed",
        },
        "government": {
            "form": "Government form submitted successfully",
            "status": "Application status: Processing",
        },
    }

    message = (
        service_responses.get(request.service_type, {})
        .get(request.action, "Operation completed")
    )

    return MockServiceResponse(
        service_type=request.service_type,
        status="success",
        message=message,
        data={
            "request_id": f"{request.service_type}-{request.action}-001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
