from fastapi import APIRouter
from database.models import PartnerEmailLink, Partner, PartnerEmail, UploadedInvoice
from sqlalchemy.orm import joinedload
from sqlmodel import select, case
from database.connection import SessionDep

router = APIRouter(prefix="/connection", tags=["connection"])


@router.get("/all")
def get_connections(session: SessionDep):

    type_order = case((PartnerEmail.type == "to", 0), else_=1)

    statement = (
        select(PartnerEmailLink)
        .options(
            joinedload(PartnerEmailLink.partner), joinedload(PartnerEmailLink.email)
        )
        .join(Partner, PartnerEmailLink.partner_id == Partner.id)
        .join(PartnerEmail, PartnerEmailLink.email_id == PartnerEmail.id)
        .order_by(Partner.name, type_order)
    )

    links = session.exec(statement).all()
    result = []
    for link in links:
        partner = session.get(Partner, link.partner_id)
        email = session.get(PartnerEmail, link.email_id)
        result.append(
            {
                "partner_id": link.partner_id,
                "partner_name": partner.name if partner else None,
                "email_id": link.email_id,
                "email": email.email if email else None,
                "type": email.type if email else None,
            }
        )
    return result


@router.post("/create")
def link_email_to_partner(email_id: int, partner_id: int, session: SessionDep):
    link = PartnerEmailLink(partner_id=partner_id, email_id=email_id)
    session.add(link)
    session.commit()

    return {"message": "Email összekapcsolva a partnerrel."}


@router.delete("/delete")
def delete_connection(email_id: int, partner_id: int, session: SessionDep):
    statement = select(PartnerEmailLink).where(
        PartnerEmailLink.partner_id == partner_id,
        PartnerEmailLink.email_id == email_id,
    )
    link = session.exec(statement).first()
    if not link:
        return {"success": False, "message": "Kapcsolat nem található."}
    session.delete(link)
    session.commit()
    return {"success": True, "message": "Kapcsolat törölve."}
