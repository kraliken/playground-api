from fastapi import APIRouter, UploadFile, File, HTTPException
from services.pdf_service import extract_tax_ids_from_pdf
from services.partner_service import get_partner_by_tax_number
from services.blob_service import upload_pdf_to_blob
from services.email_service import send_email_with_attachment
from database.connection import SessionDep
from database.models import UploadedInvoice, Status
from typing import List
from sqlmodel import select

router = APIRouter(prefix="/upload", tags=["upload"])

OWN_TAX_ID = "25892941-2-41"


@router.post("/invoices")
async def upload_invoice(
    session: SessionDep,
    invoices: List[UploadFile] = File(...),
):
    errors = []

    for file in invoices:

        blob_url = None

        if file.content_type != "application/pdf" or not file.filename.lower().endswith(
            ".pdf"
        ):
            errors.append(
                {"filename": file.filename, "error": "Csak PDF fájl tölthető fel!"}
            )
            continue

        try:

            file_bytes = await file.read()
            own_tax_id, partner_tax_id = extract_tax_ids_from_pdf(
                file_bytes, OWN_TAX_ID
            )

            partner = (
                get_partner_by_tax_number(session, partner_tax_id)
                if partner_tax_id
                else None
            )
            # if partner:
            #     partner_data = partner.model_dump()
            #     partner_data["emails"] = [
            #         email.model_dump() for email in partner.emails
            #     ]

            blob_url = upload_pdf_to_blob(file_bytes, file.filename)

            invoice_db = UploadedInvoice(
                filename=file.filename,
                own_tax_id=own_tax_id,
                partner_tax_id=partner_tax_id,
                partner_id=partner.id if partner else None,
                blob_url=blob_url,
                status=Status.pending,  # vagy dönthetsz: Status.ready, ha minden adat megvan!
            )

            session.add(invoice_db)
            session.commit()
            session.refresh(invoice_db)

        except Exception as e:
            errors.append({"filename": file.filename, "error": str(e)})

    if errors and len(errors) == len(invoices):
        return {
            "success": False,
            "message": "Egyik számlát sem sikerült elmenteni.",
            "errors": errors,
        }
    elif errors:
        return {
            "success": False,
            "message": "Néhány számlát nem sikerült elmenteni.",
            "errors": errors,
        }
    else:
        return {"success": True, "message": "Az összes számla sikeresen elmentve."}
