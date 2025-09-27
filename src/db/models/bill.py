from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import (
    and_,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKeyConstraint,
    Integer,
    PrimaryKeyConstraint,
    SmallInteger,
    String,
    Text,
    types,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

if TYPE_CHECKING:  # pragma: no cover
    from .member import SessionMember


class PGVector(types.UserDefinedType):
    """Lightweight pgvector column type."""

    cache_ok = True

    def __init__(self, dim: int):
        self.dim = dim

    def get_col_spec(self, **kw):  # pragma: no cover - simple SQL repr
        return f"vector({self.dim})"

    def bind_processor(self, dialect):
        def process(value):  # pragma: no cover - minimal casting
            if value is None:
                return None
            if isinstance(value, list):
                return value
            try:
                return list(value)
            except TypeError:
                return value

        return process


class Bill(Base):
    __tablename__ = "bill"
    __table_args__ = {"schema": "master"}

    bill_print_no: Mapped[str] = mapped_column(String, primary_key=True)
    bill_session_year: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    title: Mapped[Optional[str]] = mapped_column(Text)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    active_version: Mapped[str] = mapped_column(String(1), default="")
    active_year: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[Optional[str]] = mapped_column(Text)
    status_date: Mapped[Optional[date]] = mapped_column(Date)
    program_info: Mapped[Optional[str]] = mapped_column(Text)
    program_info_num: Mapped[Optional[int]] = mapped_column(Integer)
    sub_bill_print_no: Mapped[Optional[str]] = mapped_column(String)
    committee_name: Mapped[Optional[str]] = mapped_column(String)
    bill_cal_no: Mapped[Optional[int]] = mapped_column(SmallInteger)
    committee_chamber: Mapped[Optional[str]] = mapped_column(String(16))
    data_source: Mapped[str] = mapped_column(String(16), default="state")
    congress: Mapped[Optional[int]] = mapped_column(Integer)
    bill_type: Mapped[Optional[str]] = mapped_column(String(16))
    package_number: Mapped[Optional[str]] = mapped_column(String)
    short_title: Mapped[Optional[str]] = mapped_column(Text)
    sponsor_party: Mapped[Optional[str]] = mapped_column(String(8))
    sponsor_state: Mapped[Optional[str]] = mapped_column(String(8))
    sponsor_district: Mapped[Optional[str]] = mapped_column(String(16))
    created_date_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_date_time: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)
    published_date_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_fragment_id: Mapped[Optional[str]] = mapped_column(String)
    blurb: Mapped[Optional[str]] = mapped_column(Text)
    reprint_no: Mapped[Optional[str]] = mapped_column(String)

    amendments: Mapped[List["BillAmendment"]] = relationship(
        "BillAmendment", back_populates="bill", cascade="all, delete-orphan"
    )
    actions: Mapped[List["BillAmendmentAction"]] = relationship(
        "BillAmendmentAction", back_populates="bill", cascade="all, delete-orphan"
    )
    sponsors: Mapped[List["BillSponsor"]] = relationship(
        "BillSponsor", back_populates="bill", cascade="all, delete-orphan"
    )
    additional_sponsors: Mapped[List["BillSponsorAdditional"]] = relationship(
        "BillSponsorAdditional", back_populates="bill", cascade="all, delete-orphan"
    )
    milestones: Mapped[List["BillMilestone"]] = relationship(
        "BillMilestone", back_populates="bill", cascade="all, delete-orphan"
    )
    embeddings: Mapped[List["BillEmbedding"]] = relationship(
        "BillEmbedding", back_populates="bill", cascade="all, delete-orphan"
    )


class BillAmendment(Base):
    __tablename__ = "bill_amendment"
    __table_args__ = (
        PrimaryKeyConstraint("bill_print_no", "bill_session_year", "bill_amend_version"),
        ForeignKeyConstraint(
            ["bill_print_no", "bill_session_year"],
            ["master.bill.bill_print_no", "master.bill.bill_session_year"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        {"schema": "master"},
    )

    bill_print_no: Mapped[str] = mapped_column(String)
    bill_session_year: Mapped[int] = mapped_column(SmallInteger)
    bill_amend_version: Mapped[str] = mapped_column(String(1))
    sponsor_memo: Mapped[Optional[str]] = mapped_column(Text)
    act_clause: Mapped[Optional[str]] = mapped_column(Text)
    full_text: Mapped[Optional[str]] = mapped_column(Text)
    full_text_html: Mapped[Optional[str]] = mapped_column(Text)
    stricken: Mapped[bool] = mapped_column(Boolean, default=False)
    uni_bill: Mapped[bool] = mapped_column(Boolean, default=False)
    law_code: Mapped[Optional[str]] = mapped_column(Text)
    law_section: Mapped[Optional[str]] = mapped_column(Text)
    created_date_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_fragment_id: Mapped[Optional[str]] = mapped_column(String)

    bill: Mapped[Bill] = relationship("Bill", back_populates="amendments")
    actions: Mapped[List["BillAmendmentAction"]] = relationship(
        "BillAmendmentAction", back_populates="amendment", cascade="all, delete-orphan"
    )
    publish_statuses: Mapped[List["BillAmendmentPublishStatus"]] = relationship(
        "BillAmendmentPublishStatus", back_populates="amendment", cascade="all, delete-orphan"
    )
    cosponsors: Mapped[List["BillAmendmentCosponsor"]] = relationship(
        "BillAmendmentCosponsor", back_populates="amendment", cascade="all, delete-orphan"
    )
    multi_sponsors: Mapped[List["BillAmendmentMultiSponsor"]] = relationship(
        "BillAmendmentMultiSponsor", back_populates="amendment", cascade="all, delete-orphan"
    )
    votes: Mapped[List["BillAmendmentVoteInfo"]] = relationship(
        "BillAmendmentVoteInfo", back_populates="amendment", cascade="all, delete-orphan"
    )


class BillAmendmentAction(Base):
    __tablename__ = "bill_amendment_action"
    __table_args__ = (
        PrimaryKeyConstraint("bill_print_no", "bill_session_year", "sequence_no"),
        ForeignKeyConstraint(
            ["bill_print_no", "bill_session_year", "bill_amend_version"],
            [
                "master.bill_amendment.bill_print_no",
                "master.bill_amendment.bill_session_year",
                "master.bill_amendment.bill_amend_version",
            ],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        {"schema": "master"},
    )

    bill_print_no: Mapped[str] = mapped_column(String)
    bill_session_year: Mapped[int] = mapped_column(SmallInteger)
    bill_amend_version: Mapped[str] = mapped_column(String(1))
    effect_date: Mapped[Optional[date]] = mapped_column(Date)
    text: Mapped[Optional[str]] = mapped_column(Text)
    sequence_no: Mapped[int] = mapped_column(SmallInteger)
    chamber: Mapped[str] = mapped_column(String(16))
    created_date_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_fragment_id: Mapped[Optional[str]] = mapped_column(String)

    amendment: Mapped[BillAmendment] = relationship("BillAmendment", back_populates="actions")

    bill: Mapped[Bill] = relationship(
        "Bill",
        primaryjoin=lambda: and_(
            Bill.bill_print_no == BillAmendmentAction.bill_print_no,
            Bill.bill_session_year == BillAmendmentAction.bill_session_year,
        ),
        viewonly=True,
    )


class BillAmendmentPublishStatus(Base):
    __tablename__ = "bill_amendment_publish_status"
    __table_args__ = (
        PrimaryKeyConstraint("bill_print_no", "bill_session_year", "bill_amend_version"),
        ForeignKeyConstraint(
            ["bill_print_no", "bill_session_year", "bill_amend_version"],
            [
                "master.bill_amendment.bill_print_no",
                "master.bill_amendment.bill_session_year",
                "master.bill_amendment.bill_amend_version",
            ],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        {"schema": "master"},
    )

    bill_print_no: Mapped[str] = mapped_column(String)
    bill_session_year: Mapped[int] = mapped_column(SmallInteger)
    bill_amend_version: Mapped[str] = mapped_column(String(1))
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    effect_date_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    override: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_date_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_fragment_id: Mapped[Optional[str]] = mapped_column(String)

    amendment: Mapped[BillAmendment] = relationship("BillAmendment", back_populates="publish_statuses")


class BillSponsor(Base):
    __tablename__ = "bill_sponsor"
    __table_args__ = (
        PrimaryKeyConstraint("bill_print_no", "bill_session_year"),
        ForeignKeyConstraint(
            ["bill_print_no", "bill_session_year"],
            ["master.bill.bill_print_no", "master.bill.bill_session_year"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["session_member_id"],
            ["public.session_member.id"],
            onupdate="CASCADE",
            ondelete="SET NULL",
        ),
        {"schema": "master"},
    )

    bill_print_no: Mapped[str] = mapped_column(String)
    bill_session_year: Mapped[int] = mapped_column(SmallInteger)
    session_member_id: Mapped[Optional[int]] = mapped_column(Integer)
    budget_bill: Mapped[bool] = mapped_column(Boolean, default=False)
    rules_sponsor: Mapped[bool] = mapped_column(Boolean, default=False)
    created_date_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_fragment_id: Mapped[Optional[str]] = mapped_column(String)

    bill: Mapped[Bill] = relationship("Bill", back_populates="sponsors")
    session_member: Mapped[Optional["SessionMember"]] = relationship("SessionMember", back_populates="sponsored_bills")


VoteTypeEnum = Enum("floor", "committee", name="vote_type", schema="master", create_type=False)
VoteCodeEnum = Enum(
    "aye",
    "nay",
    "exc",
    "abs",
    "abd",
    "ayewr",
    name="vote_code",
    schema="master",
    create_type=False,
)


class BillAmendmentVoteInfo(Base):
    __tablename__ = "bill_amendment_vote_info"
    __table_args__ = (
        PrimaryKeyConstraint("id"),
        ForeignKeyConstraint(
            ["bill_print_no", "bill_session_year", "bill_amend_version"],
            [
                "master.bill_amendment.bill_print_no",
                "master.bill_amendment.bill_session_year",
                "master.bill_amendment.bill_amend_version",
            ],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        {"schema": "master"},
    )

    id: Mapped[int] = mapped_column(Integer)
    bill_print_no: Mapped[str] = mapped_column(String)
    bill_session_year: Mapped[int] = mapped_column(SmallInteger)
    bill_amend_version: Mapped[str] = mapped_column(String(1))
    vote_date: Mapped[datetime] = mapped_column(DateTime)
    sequence_no: Mapped[Optional[int]] = mapped_column(SmallInteger)
    vote_type: Mapped[str] = mapped_column(VoteTypeEnum)
    committee_name: Mapped[Optional[str]] = mapped_column(String)
    committee_chamber: Mapped[Optional[str]] = mapped_column(String(16))
    published_date_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    modified_date_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_date_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_fragment_id: Mapped[Optional[str]] = mapped_column(String)

    amendment: Mapped[BillAmendment] = relationship("BillAmendment", back_populates="votes")
    roll: Mapped[List["BillAmendmentVoteRoll"]] = relationship(
        "BillAmendmentVoteRoll", back_populates="vote", cascade="all, delete-orphan"
    )


class BillAmendmentVoteRoll(Base):
    __tablename__ = "bill_amendment_vote_roll"
    __table_args__ = (
        PrimaryKeyConstraint("vote_id", "session_member_id", "session_year", "vote_code"),
        ForeignKeyConstraint(
            ["vote_id"],
            ["master.bill_amendment_vote_info.id"],
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

    vote_id: Mapped[int] = mapped_column(Integer)
    session_member_id: Mapped[int] = mapped_column(Integer)
    member_short_name: Mapped[str] = mapped_column(String)
    session_year: Mapped[int] = mapped_column(SmallInteger)
    vote_code: Mapped[str] = mapped_column(VoteCodeEnum)
    created_date_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_fragment_id: Mapped[Optional[str]] = mapped_column(String)

    vote: Mapped[BillAmendmentVoteInfo] = relationship("BillAmendmentVoteInfo", back_populates="roll")
    session_member: Mapped["SessionMember"] = relationship("SessionMember", back_populates="bill_votes")


class BillMilestone(Base):
    __tablename__ = "bill_milestone"
    __table_args__ = (
        PrimaryKeyConstraint("bill_print_no", "bill_session_year", "status", "rank"),
        ForeignKeyConstraint(
            ["bill_print_no", "bill_session_year"],
            ["master.bill.bill_print_no", "master.bill.bill_session_year"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        {"schema": "master"},
    )

    bill_print_no: Mapped[str] = mapped_column(String)
    bill_session_year: Mapped[int] = mapped_column(SmallInteger)
    status: Mapped[str] = mapped_column(String)
    rank: Mapped[int] = mapped_column(SmallInteger)
    action_sequence_no: Mapped[int] = mapped_column(SmallInteger)
    date: Mapped[datetime] = mapped_column(Date)
    committee_name: Mapped[Optional[str]] = mapped_column(String)
    committee_chamber: Mapped[Optional[str]] = mapped_column(String(16))
    cal_no: Mapped[Optional[int]] = mapped_column(SmallInteger)
    created_date_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_fragment_id: Mapped[Optional[str]] = mapped_column(String)

    bill: Mapped[Bill] = relationship("Bill", back_populates="milestones")


class BillSponsorAdditional(Base):
    __tablename__ = "bill_sponsor_additional"
    __table_args__ = (
        PrimaryKeyConstraint("bill_print_no", "bill_session_year", "session_member_id"),
        ForeignKeyConstraint(
            ["bill_print_no", "bill_session_year"],
            ["master.bill.bill_print_no", "master.bill.bill_session_year"],
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

    bill_print_no: Mapped[str] = mapped_column(String)
    bill_session_year: Mapped[int] = mapped_column(SmallInteger)
    session_member_id: Mapped[int] = mapped_column(Integer)
    sequence_no: Mapped[Optional[int]] = mapped_column(SmallInteger)
    created_date_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_fragment_id: Mapped[Optional[str]] = mapped_column(String)

    bill: Mapped[Bill] = relationship("Bill", back_populates="additional_sponsors")
    session_member: Mapped["SessionMember"] = relationship("SessionMember", back_populates="additional_sponsored_bills")


class BillAmendmentCosponsor(Base):
    __tablename__ = "bill_amendment_cosponsor"
    __table_args__ = (
        PrimaryKeyConstraint("bill_print_no", "bill_session_year", "bill_amend_version", "session_member_id"),
        ForeignKeyConstraint(
            ["bill_print_no", "bill_session_year", "bill_amend_version"],
            [
                "master.bill_amendment.bill_print_no",
                "master.bill_amendment.bill_session_year",
                "master.bill_amendment.bill_amend_version",
            ],
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

    bill_print_no: Mapped[str] = mapped_column(String)
    bill_session_year: Mapped[int] = mapped_column(SmallInteger)
    bill_amend_version: Mapped[str] = mapped_column(String(1))
    session_member_id: Mapped[int] = mapped_column(Integer)
    sequence_no: Mapped[int] = mapped_column(SmallInteger)
    created_date_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_fragment_id: Mapped[Optional[str]] = mapped_column(String)

    amendment: Mapped[BillAmendment] = relationship("BillAmendment", back_populates="cosponsors")
    session_member: Mapped["SessionMember"] = relationship("SessionMember", back_populates="cosponsored_amendments")


class BillAmendmentMultiSponsor(Base):
    __tablename__ = "bill_amendment_multi_sponsor"
    __table_args__ = (
        PrimaryKeyConstraint("bill_print_no", "bill_session_year", "bill_amend_version", "session_member_id"),
        ForeignKeyConstraint(
            ["bill_print_no", "bill_session_year", "bill_amend_version"],
            [
                "master.bill_amendment.bill_print_no",
                "master.bill_amendment.bill_session_year",
                "master.bill_amendment.bill_amend_version",
            ],
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

    bill_print_no: Mapped[str] = mapped_column(String)
    bill_session_year: Mapped[int] = mapped_column(SmallInteger)
    bill_amend_version: Mapped[str] = mapped_column(String(1))
    session_member_id: Mapped[int] = mapped_column(Integer)
    sequence_no: Mapped[int] = mapped_column(SmallInteger)
    created_date_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_fragment_id: Mapped[Optional[str]] = mapped_column(String)

    amendment: Mapped[BillAmendment] = relationship("BillAmendment", back_populates="multi_sponsors")
    session_member: Mapped["SessionMember"] = relationship("SessionMember", back_populates="multi_sponsored_amendments")


class BillEmbedding(Base):
    __tablename__ = "bill_embeddings"
    __table_args__ = (
        PrimaryKeyConstraint("bill_print_no", "bill_session_year"),
        ForeignKeyConstraint(
            ["bill_print_no", "bill_session_year"],
            ["master.bill.bill_print_no", "master.bill.bill_session_year"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        {"schema": "master"},
    )

    bill_print_no: Mapped[str] = mapped_column(String)
    bill_session_year: Mapped[int] = mapped_column(SmallInteger)
    embedding: Mapped[Optional[List[float]]] = mapped_column(PGVector(1536))
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    bill: Mapped[Bill] = relationship("Bill", back_populates="embeddings")
