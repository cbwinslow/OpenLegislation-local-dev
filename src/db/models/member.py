from __future__ import annotations

from typing import List, Optional

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class Person(Base):
    __tablename__ = "person"
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[Optional[str]] = mapped_column(String)
    first_name: Mapped[Optional[str]] = mapped_column(String)
    middle_name: Mapped[Optional[str]] = mapped_column(String)
    last_name: Mapped[Optional[str]] = mapped_column(String)
    email: Mapped[Optional[str]] = mapped_column(String)
    prefix: Mapped[Optional[str]] = mapped_column(String)
    suffix: Mapped[Optional[str]] = mapped_column(String)
    verified: Mapped[bool] = mapped_column(Boolean, default=True)
    img_name: Mapped[Optional[str]] = mapped_column(String)

    members: Mapped[List["Member"]] = relationship("Member", back_populates="person")


class Member(Base):
    __tablename__ = "member"
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    person_id: Mapped[int] = mapped_column(Integer)
    chamber: Mapped[str] = mapped_column(String)
    incumbent: Mapped[bool] = mapped_column(Boolean, default=False)
    full_name: Mapped[Optional[str]] = mapped_column(String)

    person: Mapped[Person] = relationship("Person", back_populates="members")
    session_members: Mapped[List["SessionMember"]] = relationship(
        "SessionMember", back_populates="member", cascade="all, delete-orphan"
    )


class SessionMember(Base):
    __tablename__ = "session_member"
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    member_id: Mapped[int] = mapped_column(Integer)
    lbdc_short_name: Mapped[str] = mapped_column(String)
    session_year: Mapped[int] = mapped_column(Integer)
    district_code: Mapped[Optional[int]] = mapped_column(Integer)
    alternate: Mapped[bool] = mapped_column(Boolean, default=False)

    member: Mapped[Member] = relationship("Member", back_populates="session_members")
    sponsored_bills: Mapped[List["BillSponsor"]] = relationship(
        "BillSponsor", back_populates="session_member"
    )
    additional_sponsored_bills: Mapped[List["BillSponsorAdditional"]] = relationship(
        "BillSponsorAdditional", back_populates="session_member"
    )
    cosponsored_amendments: Mapped[List["BillAmendmentCosponsor"]] = relationship(
        "BillAmendmentCosponsor", back_populates="session_member"
    )
    multi_sponsored_amendments: Mapped[List["BillAmendmentMultiSponsor"]] = relationship(
        "BillAmendmentMultiSponsor", back_populates="session_member"
    )
    committee_assignments: Mapped[List["CommitteeMember"]] = relationship(
        "CommitteeMember", back_populates="session_member"
    )
    agenda_attendance: Mapped[List["AgendaVoteCommitteeAttend"]] = relationship(
        "AgendaVoteCommitteeAttend", back_populates="session_member"
    )


from .bill import (  # noqa: E402  pylint: disable=wrong-import-position
    BillAmendmentCosponsor,
    BillAmendmentMultiSponsor,
    BillSponsor,
    BillSponsorAdditional,
)
from .committee import CommitteeMember  # noqa: E402  pylint: disable=wrong-import-position
from .agenda import AgendaVoteCommitteeAttend  # noqa: E402  pylint: disable=wrong-import-position
