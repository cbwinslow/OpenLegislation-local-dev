from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Integer,
    PrimaryKeyConstraint,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

from .committee import ChamberEnum


class Agenda(Base):
    __tablename__ = "agenda"
    __table_args__ = {"schema": "master"}

    agenda_no: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    year: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    published_date_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    modified_date_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_date_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_fragment_id: Mapped[Optional[str]] = mapped_column(String)

    info_addenda: Mapped[List["AgendaInfoAddendum"]] = relationship(
        "AgendaInfoAddendum", back_populates="agenda", cascade="all, delete-orphan"
    )
    vote_addenda: Mapped[List["AgendaVoteAddendum"]] = relationship(
        "AgendaVoteAddendum", back_populates="agenda", cascade="all, delete-orphan"
    )


class AgendaInfoAddendum(Base):
    __tablename__ = "agenda_info_addendum"
    __table_args__ = (
        PrimaryKeyConstraint("agenda_no", "year", "addendum_id"),
        ForeignKeyConstraint(
            ["agenda_no", "year"],
            ["master.agenda.agenda_no", "master.agenda.year"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        {"schema": "master"},
    )

    agenda_no: Mapped[int] = mapped_column(SmallInteger)
    year: Mapped[int] = mapped_column(SmallInteger)
    addendum_id: Mapped[str] = mapped_column(String)
    modified_date_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    published_date_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_date_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_fragment_id: Mapped[Optional[str]] = mapped_column(String)
    week_of: Mapped[Optional[date]] = mapped_column(Date)

    agenda: Mapped[Agenda] = relationship("Agenda", back_populates="info_addenda")
    committees: Mapped[List["AgendaInfoCommittee"]] = relationship(
        "AgendaInfoCommittee", back_populates="info_addendum", cascade="all, delete-orphan"
    )


class AgendaInfoCommittee(Base):
    __tablename__ = "agenda_info_committee"
    __table_args__ = (
        PrimaryKeyConstraint("id"),
        ForeignKeyConstraint(
            ["agenda_no", "year", "addendum_id"],
            [
                "master.agenda_info_addendum.agenda_no",
                "master.agenda_info_addendum.year",
                "master.agenda_info_addendum.addendum_id",
            ],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["committee_name", "committee_chamber"],
            ["master.committee.name", "master.committee.chamber"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        {"schema": "master"},
    )

    id: Mapped[int] = mapped_column(Integer)
    agenda_no: Mapped[int] = mapped_column(SmallInteger)
    year: Mapped[int] = mapped_column(SmallInteger)
    addendum_id: Mapped[str] = mapped_column(String)
    committee_name: Mapped[str] = mapped_column(CITEXT)
    committee_chamber: Mapped[str] = mapped_column(ChamberEnum)
    chair: Mapped[Optional[str]] = mapped_column(Text)
    location: Mapped[Optional[str]] = mapped_column(Text)
    meeting_date_time: Mapped[datetime] = mapped_column(DateTime)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    last_fragment_id: Mapped[Optional[str]] = mapped_column(String)
    created_date_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    info_addendum: Mapped[AgendaInfoAddendum] = relationship(
        "AgendaInfoAddendum", back_populates="committees"
    )
    items: Mapped[List["AgendaInfoCommitteeItem"]] = relationship(
        "AgendaInfoCommitteeItem", back_populates="committee", cascade="all, delete-orphan"
    )


class AgendaInfoCommitteeItem(Base):
    __tablename__ = "agenda_info_committee_item"
    __table_args__ = (
        PrimaryKeyConstraint("id"),
        ForeignKeyConstraint(
            ["info_committee_id"],
            ["master.agenda_info_committee.id"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        {"schema": "master"},
    )

    id: Mapped[int] = mapped_column(Integer)
    info_committee_id: Mapped[int] = mapped_column(Integer)
    bill_print_no: Mapped[str] = mapped_column(String)
    bill_session_year: Mapped[int] = mapped_column(SmallInteger)
    bill_amend_version: Mapped[str] = mapped_column(String(1))
    message: Mapped[Optional[str]] = mapped_column(Text)
    created_date_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_fragment_id: Mapped[Optional[str]] = mapped_column(String)

    committee: Mapped[AgendaInfoCommittee] = relationship(
        "AgendaInfoCommittee", back_populates="items"
    )


class AgendaVoteAddendum(Base):
    __tablename__ = "agenda_vote_addendum"
    __table_args__ = (
        PrimaryKeyConstraint("agenda_no", "year", "addendum_id"),
        ForeignKeyConstraint(
            ["agenda_no", "year"],
            ["master.agenda.agenda_no", "master.agenda.year"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        {"schema": "master"},
    )

    agenda_no: Mapped[int] = mapped_column(SmallInteger)
    year: Mapped[int] = mapped_column(SmallInteger)
    addendum_id: Mapped[str] = mapped_column(String)
    modified_date_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    published_date_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_date_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_fragment_id: Mapped[Optional[str]] = mapped_column(String)

    agenda: Mapped[Agenda] = relationship("Agenda", back_populates="vote_addenda")
    committees: Mapped[List["AgendaVoteCommittee"]] = relationship(
        "AgendaVoteCommittee", back_populates="vote_addendum", cascade="all, delete-orphan"
    )


class AgendaVoteCommittee(Base):
    __tablename__ = "agenda_vote_committee"
    __table_args__ = (
        PrimaryKeyConstraint("id"),
        ForeignKeyConstraint(
            ["agenda_no", "year", "addendum_id"],
            [
                "master.agenda_vote_addendum.agenda_no",
                "master.agenda_vote_addendum.year",
                "master.agenda_vote_addendum.addendum_id",
            ],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        {"schema": "master"},
    )

    id: Mapped[int] = mapped_column(Integer)
    agenda_no: Mapped[int] = mapped_column(SmallInteger)
    year: Mapped[int] = mapped_column(SmallInteger)
    addendum_id: Mapped[str] = mapped_column(String)
    committee_name: Mapped[str] = mapped_column(CITEXT)
    committee_chamber: Mapped[str] = mapped_column(ChamberEnum)
    chair: Mapped[Optional[str]] = mapped_column(Text)
    meeting_date_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_fragment_id: Mapped[Optional[str]] = mapped_column(String)
    created_date_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    vote_addendum: Mapped[AgendaVoteAddendum] = relationship(
        "AgendaVoteAddendum", back_populates="committees"
    )
    attendance: Mapped[List["AgendaVoteCommitteeAttend"]] = relationship(
        "AgendaVoteCommitteeAttend", back_populates="vote_committee", cascade="all, delete-orphan"
    )
    votes: Mapped[List["AgendaVoteCommitteeVote"]] = relationship(
        "AgendaVoteCommitteeVote", back_populates="vote_committee", cascade="all, delete-orphan"
    )


class AgendaVoteCommitteeAttend(Base):
    __tablename__ = "agenda_vote_committee_attend"
    __table_args__ = (
        PrimaryKeyConstraint("id"),
        ForeignKeyConstraint(
            ["vote_committee_id"],
            ["master.agenda_vote_committee.id"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["session_member_id"],
            ["public.session_member.id"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        {"schema": "master"},
    )

    id: Mapped[int] = mapped_column(Integer)
    vote_committee_id: Mapped[int] = mapped_column(Integer)
    session_member_id: Mapped[int] = mapped_column(Integer)
    session_year: Mapped[int] = mapped_column(SmallInteger)
    lbdc_short_name: Mapped[str] = mapped_column(String)
    rank: Mapped[int] = mapped_column(SmallInteger)
    party: Mapped[Optional[str]] = mapped_column(String)
    attend_status: Mapped[Optional[str]] = mapped_column(String)
    created_date_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_fragment_id: Mapped[Optional[str]] = mapped_column(String)

    vote_committee: Mapped[AgendaVoteCommittee] = relationship(
        "AgendaVoteCommittee", back_populates="attendance"
    )
    session_member: Mapped["SessionMember"] = relationship("SessionMember", back_populates="agenda_attendance")


class AgendaVoteCommitteeVote(Base):
    __tablename__ = "agenda_vote_committee_vote"
    __table_args__ = (
        PrimaryKeyConstraint("id"),
        ForeignKeyConstraint(
            ["vote_committee_id"],
            ["master.agenda_vote_committee.id"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["refer_committee_name", "refer_committee_chamber"],
            ["master.committee.name", "master.committee.chamber"],
            onupdate="CASCADE",
            ondelete="SET NULL",
        ),
        {"schema": "master"},
    )

    id: Mapped[int] = mapped_column(Integer)
    vote_committee_id: Mapped[int] = mapped_column(Integer)
    vote_action: Mapped[str] = mapped_column(Text)
    vote_info_id: Mapped[Optional[int]] = mapped_column(Integer)
    refer_committee_name: Mapped[Optional[str]] = mapped_column(CITEXT)
    refer_committee_chamber: Mapped[Optional[str]] = mapped_column(ChamberEnum)
    with_amendment: Mapped[bool] = mapped_column(Boolean, default=False)
    created_date_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_fragment_id: Mapped[Optional[str]] = mapped_column(String)

    vote_committee: Mapped[AgendaVoteCommittee] = relationship(
        "AgendaVoteCommittee", back_populates="votes"
    )


from .member import SessionMember  # noqa: E402  pylint: disable=wrong-import-position
