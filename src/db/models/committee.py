from __future__ import annotations

from datetime import datetime, time
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKeyConstraint,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
    Time,
)
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

ChamberEnum = Enum(
    "assembly",
    "senate",
    name="chamber",
    schema="public",
    create_type=False,
)

CommitteeMemberTitle = Enum(
    "chair_person",
    "vice_chair",
    "member",
    name="committee_member_title",
    schema="public",
    create_type=False,
)


class Committee(Base):
    __tablename__ = "committee"
    __table_args__ = {"schema": "master"}

    name: Mapped[str] = mapped_column(CITEXT, primary_key=True)
    chamber: Mapped[str] = mapped_column(ChamberEnum, primary_key=True)
    id: Mapped[int] = mapped_column(Integer, index=True)
    current_version: Mapped[datetime] = mapped_column(DateTime, default=datetime.min)
    current_session: Mapped[int] = mapped_column(Integer, default=0)
    full_name: Mapped[Optional[str]] = mapped_column(Text)

    versions: Mapped[List["CommitteeVersion"]] = relationship(
        "CommitteeVersion", back_populates="committee", cascade="all, delete-orphan"
    )
    members: Mapped[List["CommitteeMember"]] = relationship(
        "CommitteeMember", back_populates="committee", cascade="all, delete-orphan"
    )


class CommitteeVersion(Base):
    __tablename__ = "committee_version"
    __table_args__ = (
        PrimaryKeyConstraint("id"),
        ForeignKeyConstraint(
            ["committee_name", "chamber"],
            ["master.committee.name", "master.committee.chamber"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        {"schema": "master"},
    )

    id: Mapped[int] = mapped_column(Integer)
    location: Mapped[Optional[str]] = mapped_column(Text)
    meetday: Mapped[Optional[str]] = mapped_column(Text)
    meetaltweek: Mapped[bool] = mapped_column(Boolean, default=False)
    meetaltweektext: Mapped[Optional[str]] = mapped_column(Text)
    meettime: Mapped[Optional[time]] = mapped_column(Time)
    session_year: Mapped[int] = mapped_column(Integer)
    created: Mapped[datetime] = mapped_column(DateTime)
    reformed: Mapped[datetime] = mapped_column(DateTime, default=datetime.max)
    committee_name: Mapped[str] = mapped_column(CITEXT)
    chamber: Mapped[str] = mapped_column(ChamberEnum)
    last_fragment_id: Mapped[Optional[str]] = mapped_column(String)

    committee: Mapped[Committee] = relationship("Committee", back_populates="versions")
    members: Mapped[List["CommitteeMember"]] = relationship(
        "CommitteeMember", back_populates="version", cascade="all, delete-orphan"
    )


class CommitteeMember(Base):
    __tablename__ = "committee_member"
    __table_args__ = (
        PrimaryKeyConstraint("id"),
        ForeignKeyConstraint(
            ["chamber", "committee_name"],
            ["master.committee.chamber", "master.committee.name"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["chamber", "committee_name", "session_year", "version_created"],
            [
                "master.committee_version.chamber",
                "master.committee_version.committee_name",
                "master.committee_version.session_year",
                "master.committee_version.created",
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

    id: Mapped[int] = mapped_column(Integer)
    majority: Mapped[bool] = mapped_column(Boolean, default=True)
    sequence_no: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(CommitteeMemberTitle, default="member")
    committee_name: Mapped[str] = mapped_column(CITEXT)
    version_created: Mapped[datetime] = mapped_column(DateTime)
    session_year: Mapped[int] = mapped_column(Integer)
    session_member_id: Mapped[int] = mapped_column(Integer)
    chamber: Mapped[str] = mapped_column(ChamberEnum)

    committee: Mapped[Committee] = relationship("Committee", back_populates="members")
    version: Mapped[CommitteeVersion] = relationship("CommitteeVersion", back_populates="members")
    session_member: Mapped["SessionMember"] = relationship("SessionMember", back_populates="committee_assignments")


from .member import SessionMember  # noqa: E402  pylint: disable=wrong-import-position
