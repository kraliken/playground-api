from fastapi import APIRouter, status, HTTPException
from database.models import (
    Partner,
    PartnerCreate,
    PartnerRead,
    PartnerUpdate,
    PartnerEmailLink,
    UploadedInvoice,
)
from database.connection import SessionDep
from sqlmodel import select

router = APIRouter(prefix="/partner", tags=["partner"])


@router.get("/{partner_id}", response_model=PartnerRead)
def get_partner(partner_id: int, session: SessionDep):
    partner = session.get(Partner, partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")

    return partner


@router.patch("/{partner_id}", response_model=PartnerUpdate)
def update_partner(partner_id: int, partner_update: PartnerUpdate, session: SessionDep):
    partner = session.get(Partner, partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    partner_data = partner_update.model_dump(exclude_unset=True)
    for key, value in partner_data.items():
        setattr(partner, key, value)

    session.add(partner)
    session.commit()
    session.refresh(partner)

    return partner


@router.post("/create", status_code=status.HTTP_201_CREATED, response_model=PartnerRead)
def create_partner(partner: PartnerCreate, session: SessionDep):

    db_partner = Partner(
        name=partner.name, tax_number=partner.tax_number, contact=partner.contact
    )
    session.add(db_partner)
    session.commit()
    session.refresh(db_partner)

    statement = select(UploadedInvoice).where(
        UploadedInvoice.partner_id == None,
        UploadedInvoice.partner_tax_id == db_partner.tax_number,
    )
    invoices_to_update = session.exec(statement).all()

    for inv in invoices_to_update:
        inv.partner_id = db_partner.id
    if invoices_to_update:
        session.commit()

    session.refresh(db_partner)
    return db_partner


@router.delete("/{partner_id}")
def delete_partner(partner_id: int, session: SessionDep):

    statement = select(PartnerEmailLink).where(
        PartnerEmailLink.partner_id == partner_id
    )
    links = session.exec(statement).all()
    for link in links:
        session.delete(link)
    session.commit()

    partner = session.get(Partner, partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    session.delete(partner)
    session.commit()
    return {"success": "true"}
