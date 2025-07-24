from fastapi import APIRouter
from database.models import Partner, PartnerRead
from database.connection import SessionDep
from typing import List
from sqlmodel import select

router = APIRouter(prefix="/partners", tags=["partners"])

@router.get("/all", response_model=List[PartnerRead])
def get_partners(session: SessionDep):
    partners = session.exec(select(Partner)).all()
    
    return partners
