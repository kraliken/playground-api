from fastapi import APIRouter, HTTPException
from database.models import PartnerEmail, PartnerEmailLink, PartnerEmailResponse
from database.connection import SessionDep
from typing import List
from sqlmodel import select


router = APIRouter(prefix="/emails", tags=["emails"])


@router.get("/all", response_model=List[PartnerEmailResponse])
def get_emails(session: SessionDep):

    emails = session.exec(select(PartnerEmail)).all()

    return emails


@router.get("/available-to/{partner_id}", response_model=List[PartnerEmailResponse])
def get_available_to_emails(partner_id: int, session: SessionDep):
    # 1. Lekérjük azokat az email_id-kat, amik ehhez a partnerhez már kapcsolódnak
    linked_email_ids = session.exec(
        select(PartnerEmailLink.email_id).where(
            PartnerEmailLink.partner_id == partner_id
        )
    ).all()

    # 2. Lekérjük azokat az emaileket, amik "to" típusúak és NINCSENEK összekötve ezzel a partnerrel
    statement = (
        select(PartnerEmail)
        .where(PartnerEmail.type == "to")
        .where(PartnerEmail.id.notin_(linked_email_ids if linked_email_ids else [0]))
    )
    emails = session.exec(statement).all()

    return emails


@router.get("/available-cc/{partner_id}", response_model=List[PartnerEmailResponse])
def get_available_to_emails(partner_id: int, session: SessionDep):
    # 1. Lekérjük azokat az email_id-kat, amik ehhez a partnerhez már kapcsolódnak
    linked_email_ids = session.exec(
        select(PartnerEmailLink.email_id).where(
            PartnerEmailLink.partner_id == partner_id
        )
    ).all()

    # 2. Lekérjük azokat az emaileket, amik "to" típusúak és NINCSENEK összekötve ezzel a partnerrel
    statement = (
        select(PartnerEmail)
        .where(PartnerEmail.type == "cc")
        .where(PartnerEmail.id.notin_(linked_email_ids if linked_email_ids else [0]))
    )
    emails = session.exec(statement).all()

    return emails
