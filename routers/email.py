from fastapi import APIRouter, Depends, HTTPException, status
from database.models import (
    PartnerEmail,
    PartnerEmailUpdate,
    PartnerEmailCreate,
    PartnerEmailResponse,
    PartnerEmailLink,
)
from database.connection import SessionDep
from sqlmodel import select


router = APIRouter(prefix="/email", tags=["email"])


@router.post(
    "/create", status_code=status.HTTP_201_CREATED, response_model=PartnerEmailResponse
)
def create_partner_email(email_in: PartnerEmailCreate, session: SessionDep):

    db_email = PartnerEmail(email=email_in.email, type=email_in.type)
    session.add(db_email)
    session.commit()
    session.refresh(db_email)

    # if email_in.partner_ids:
    #     for partner_id in email_in.partner_ids:
    #         link = PartnerEmailLink(partner_id=partner_id, email_id=db_email.id)
    #         session.add(link)
    #     session.commit()

    return db_email


@router.patch("/{email_id}", response_model=PartnerEmailUpdate)
def update_email(email_id: int, email_update: PartnerEmailUpdate, session: SessionDep):
    email = session.get(PartnerEmail, email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    email_data = email_update.model_dump(exclude_unset=True)
    for key, value in email_data.items():
        setattr(email, key, value)

    session.add(email)
    session.commit()
    session.refresh(email)

    return email


@router.delete("/{email_id}")
def delete_partner(email_id: int, session: SessionDep):

    statement = select(PartnerEmailLink).where(PartnerEmailLink.email_id == email_id)
    links = session.exec(statement).all()
    for link in links:
        session.delete(link)
    session.commit()

    email = session.get(PartnerEmail, email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    session.delete(email)
    session.commit()
    return {"success": "true"}
