from sqlmodel import SQLModel, Field, Relationship, Column, ForeignKey
from typing import List, Optional
from enum import Enum
from datetime import datetime


class EmailType(str, Enum):
    to = "to"
    cc = "cc"
    bcc = "bcc"


class Status(str, Enum):
    pending = "pending"
    ready = "ready"


class PartnerEmailLink(SQLModel, table=True):
    __tablename__ = "partner_email_link"

    # partner_id: Optional[int] = Field(
    #     default=None,
    #     sa_column=Column(
    #         "partner_id",
    #         ForeignKey("partners.id", ondelete="CASCADE"),
    #         primary_key=True,
    #     ),
    # )
    # email_id: Optional[int] = Field(
    #     default=None,
    #     sa_column=Column(
    #         "email_id",
    #         ForeignKey("partner_emails.id", ondelete="CASCADE"),
    #         primary_key=True,
    #     ),
    # )

    partner_id: Optional[int] = Field(
        default=None, foreign_key="partners.id", primary_key=True
    )
    email_id: Optional[int] = Field(
        default=None, foreign_key="partner_emails.id", primary_key=True
    )

    # LÉNYEG!!! Ezt tedd hozzá:
    partner: Optional["Partner"] = Relationship(back_populates="partner_links")
    email: Optional["PartnerEmail"] = Relationship(back_populates="email_links")


class Partner(SQLModel, table=True):
    __tablename__ = "partners"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, nullable=False)
    tax_number: str = Field(max_length=32, nullable=False)
    contact: Optional[str] = Field(default=None, max_length=255, nullable=True)

    emails: List["PartnerEmail"] = Relationship(
        back_populates="partners", link_model=PartnerEmailLink
    )
    partner_links: List["PartnerEmailLink"] = Relationship(back_populates="partner")
    invoices: List["UploadedInvoice"] = Relationship(back_populates="partner")


class PartnerCreate(SQLModel):
    name: str
    tax_number: str
    contact: Optional[str] = None


class PartnerEmail(SQLModel, table=True):
    __tablename__ = "partner_emails"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(max_length=255, nullable=False)
    type: EmailType = Field(nullable=False)

    partners: List[Partner] = Relationship(
        back_populates="emails", link_model=PartnerEmailLink
    )
    email_links: List["PartnerEmailLink"] = Relationship(back_populates="email")


class UploadedInvoice(SQLModel, table=True):
    __tablename__ = "uploaded_invoices"

    id: int | None = Field(default=None, primary_key=True)
    filename: str = Field(nullable=False)
    own_tax_id: str | None = Field(default=None)
    partner_tax_id: str | None = Field(default=None)
    partner_id: int | None = Field(default=None, foreign_key="partners.id")
    blob_url: str | None = Field(default=None)
    status: Status = Field(default=Status.pending, nullable=False)
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    partner: Optional["Partner"] = Relationship(back_populates="invoices")


class PartnerEmailResponse(SQLModel):
    id: int
    email: str
    type: EmailType


class PartnerEmailCreate(SQLModel):
    email: str
    type: EmailType
    # partner_ids: Optional[List[int]] = None


class PartnerEmailUpdate(SQLModel):
    email: Optional[str] = None
    type: Optional[EmailType] = None


class PartnerRead(SQLModel):
    id: int
    name: str
    tax_number: str
    contact: Optional[str] = None
    emails: List[PartnerEmailResponse] = []


class PartnerUpdate(SQLModel):
    name: Optional[str] = None
    tax_number: Optional[str] = None
    contact: Optional[str] = None
