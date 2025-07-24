from fastapi import APIRouter, Depends
from sqlalchemy.orm import joinedload
from sqlmodel import Session, select
from database.connection import SessionDep
from database.models import UploadedInvoice, Partner
from collections import defaultdict
from services.blob_service import download_pdf_from_blob, delete_blob_from_url
from services.email_service import send_email_with_attachment
import base64

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get("/all")
def get_uploaded_invoices(
    session: SessionDep,
):
    # Feltöltött számlák partnerrel, partner emailcímekkel együtt
    statement = select(UploadedInvoice).options(
        joinedload(UploadedInvoice.partner).joinedload(Partner.emails)
    )
    invoices = session.exec(statement).unique().all()

    complete = []
    incomplete = []

    partner_invoice_map = defaultdict(lambda: {"partner_data": None, "invoices": []})

    for invoice in invoices:
        # Partner és annak emailcímei előkészítve frontendnek
        partner_data = None
        if invoice.partner:
            emails = [email.model_dump() for email in invoice.partner.emails]
            partner_data = invoice.partner.model_dump()
            partner_data["emails"] = emails

            to_emails = [email for email in emails if email["type"] == "to"]

            if to_emails:  # van partner ÉS van legalább 1 "to" típusú email
                partner_id = invoice.partner.id
                # Itt csak egyszer állítod be az emails-t (többszörös hozzáadás esetén sincs gond)
                if not partner_invoice_map[partner_id]["partner_data"]:
                    partner_invoice_map[partner_id]["partner_data"] = partner_data
                partner_invoice_map[partner_id]["invoices"].append(
                    {
                        "id": invoice.id,
                        "filename": invoice.filename,
                        "own_tax_id": invoice.own_tax_id,
                        "partner_tax_id": invoice.partner_tax_id,
                        "blob_url": invoice.blob_url,
                        "status": invoice.status,
                        "uploaded_at": invoice.uploaded_at,
                    }
                )
            else:  # van partner, de nincs emailcím
                incomplete.append(
                    {
                        "id": invoice.id,
                        "filename": invoice.filename,
                        "own_tax_id": invoice.own_tax_id,
                        "partner_tax_id": invoice.partner_tax_id,
                        "blob_url": invoice.blob_url,
                        "status": invoice.status,
                        "uploaded_at": invoice.uploaded_at,
                        "partner_data": partner_data,
                    }
                )
        else:  # nincs partner
            incomplete.append(
                {
                    "id": invoice.id,
                    "filename": invoice.filename,
                    "own_tax_id": invoice.own_tax_id,
                    "partner_tax_id": invoice.partner_tax_id,
                    "blob_url": invoice.blob_url,
                    "status": invoice.status,
                    "uploaded_at": invoice.uploaded_at,
                    "partner_data": None,
                }
            )

    complete_grouped = list(partner_invoice_map.values())
    return {
        "complete": complete_grouped,
        "incomplete": incomplete,
    }


@router.get("/send")
def send_complete_invoices(
    session: SessionDep,
):
    statement = select(UploadedInvoice).options(
        joinedload(UploadedInvoice.partner).joinedload(Partner.emails)
    )
    invoices = session.exec(statement).unique().all()

    partner_invoice_map = defaultdict(
        lambda: {"partner": None, "to_emails": [], "cc_emails": [], "invoices": []}
    )
    for invoice in invoices:
        partner = invoice.partner
        if not partner:
            continue
        # csak akkor, ha van "to" típusú email
        to_emails = [e for e in partner.emails if e.type == "to"]
        cc_emails = [e for e in partner.emails if e.type == "cc"]
        if not to_emails:
            continue

        partner_id = partner.id
        if not partner_invoice_map[partner_id]["partner"]:
            partner_invoice_map[partner_id]["partner"] = partner
            partner_invoice_map[partner_id]["to_emails"] = to_emails
            partner_invoice_map[partner_id]["cc_emails"] = cc_emails
        partner_invoice_map[partner_id]["invoices"].append(invoice)

    sent = []
    failed = []

    for p in partner_invoice_map.values():
        to_email_addresses = [e.email for e in p["to_emails"]]
        cc_email_addresses = [e.email for e in p["cc_emails"]]
        partner_name = p["partner"].name
        attachments = []

        for invoice in p["invoices"]:
            try:
                pdf_bytes = download_pdf_from_blob(invoice.blob_url)
            except Exception as e:
                failed.append(
                    {
                        "partner": partner_name,
                        "error": f"Nem sikerült a PDF-et letölteni: {invoice.filename} ({str(e)})",
                    }
                )
                continue

            attachments.append(
                {
                    "name": invoice.filename,
                    "contentType": "application/pdf",
                    "contentInBase64": base64.b64encode(pdf_bytes).decode(),
                }
            )
        if not attachments:
            failed.append(
                {"partner": partner_name, "error": "Nincs letölthető számla."}
            )
            continue

        try:

            html = f"""
                    <p>Kedves Partnerünk,</p><br><br>
                    <p>csatolva küldjük az Önök részére kiállított <strong>{len(attachments)} db számlát</strong>.</p>
                    <br><br>
                    <p>Üdvözlettel,</p>
                    <p>X.Y. Kft.,</p>
                    """
            send_email_with_attachment(
                partner=partner_name,
                to_emails=to_email_addresses,
                cc_emails=cc_email_addresses,
                subject=f"Beérkezett számlák – {partner_name}",
                html=html,
                attachments=attachments,
            )

            for invoice in p["invoices"]:
                delete_blob_from_url(invoice.blob_url)
                print("Blob törlés sikeres")

            for invoice in p["invoices"]:
                session.delete(invoice)

            session.commit()

            sent.append(
                {
                    "partner": partner_name,
                    "emails": to_email_addresses,
                    "invoices": [a["name"] for a in attachments],
                }
            )
        except Exception as e:
            session.rollback()
            failed.append(
                {"partner": partner_name, "error": f"E-mail küldési hiba: {str(e)}"}
            )
    return {
        "success": len(failed) == 0,
        "sent": sent,
        "failed": failed,
        "message": f"{len(sent)} email elküldve, {len(failed)} hibás.",
    }


@router.delete("/delete")
def delete_invoices(
    session: SessionDep,
):
    invoices = session.exec(select(UploadedInvoice)).all()
    errors = []

    for invoice in invoices:
        try:
            if invoice.blob_url:
                delete_blob_from_url(invoice.blob_url)
        except Exception as e:
            errors.append({"filename": invoice.filename, "error": str(e)})

        session.delete(invoice)

    session.commit()

    if errors:
        return {
            "success": False,
            "message": f"{len(errors)} számla blob törlése sikertelen volt.",
            "errors": errors,
        }
    else:
        return {
            "success": True,
            "message": "Az összes számla és blob sikeresen törölve.",
        }
