from typing import Dict, Any, List, Tuple
from models import Form, FormField
import uuid
import logging

logger = logging.getLogger(__name__)

FIELD_TYPE_MAP = {
    "name": "text",
    "date_of_birth": "date",
    "address": "textarea",
    "phone": "tel",
    "email": "email",
    "additional_info": "textarea",
}


class FormService:

    async def create_form_from_data(
        self, user_id: str, form_type: str, extracted_data: Dict[str, Any]
    ) -> Form:
        extraction_failed = extracted_data.pop("_extraction_failed", False)

        fields = [
            FormField(
                field_name=key,
                field_value=value if value is not None else "",
                field_type=FIELD_TYPE_MAP.get(key, "text"),
            )
            for key, value in extracted_data.items()
        ]

        status = "extraction_failed" if extraction_failed else "draft"

        form = Form(
            form_id=str(uuid.uuid4()),
            form_type=form_type,
            user_id=user_id,
            fields=fields,
            status=status,
        )
        logger.info(f"Form {form.form_id} created (status={status}) for user {user_id}")
        return form

    async def validate_form(self, form: Form) -> Tuple[bool, List[str]]:
        errors = []
        field_names = {f.field_name for f in form.fields}
        for required in ["name"]:
            if required not in field_names:
                errors.append(f"Missing required field: {required}")
        return (len(errors) == 0), errors

    async def generate_form_summary(self, form: Form) -> str:
        return ". ".join(
            f"{f.field_name.replace('_', ' ').title()}: {f.field_value}"
            for f in form.fields
            if f.field_value
        )


form_service = FormService()
