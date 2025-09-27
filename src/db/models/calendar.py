from __future__ import annotations

from datetime import datetime, date
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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class Calendar(Base):
    __tablename__ = "calendar"
    __table_args__ = {"schema": "master"}

    calendar_no: Mapped[int] = mapped_column(Integer, primary_key=True)
    calendar_year: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    modified_date_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    published_date_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_date_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_fragment_id: Mapped[Optional[str]] = mapped_column(String)

    active_lists: Mapped[List["CalendarActiveList"]] = relationship(
        "CalendarActiveList", back_populates="calendar", cascade="all, delete-orphan"
    )
    supplements: Mapped[List["CalendarSupplemental"]] = relationship(
        "CalendarSupplemental", back_populates="calendar", cascade="all, delete-orphan"
    )


class CalendarActiveList(Base):
    __tablename__ = "calendar_active_list"
    __table_args__ = (
        PrimaryKeyConstraint("id"),
        ForeignKeyConstraint(
            ["calendar_no", "calendar_year"],
            ["master.calendar.calendar_no", "master.calendar.calendar_year"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        {"schema": "master"},
    )

    id: Mapped[int] = mapped_column(Integer)
    sequence_no: Mapped[Optional[int]] = mapped_column(SmallInteger)
    calendar_no: Mapped[int] = mapped_column(Integer)
    calendar_year: Mapped[int] = mapped_column(SmallInteger)
    calendar_date: Mapped[Optional[date]] = mapped_column(Date)
    release_date_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    modified_date_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    published_date_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_date_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_fragment_id: Mapped[Optional[str]] = mapped_column(String)

    calendar: Mapped[Calendar] = relationship("Calendar", back_populates="active_lists")
    entries: Mapped[List["CalendarActiveListEntry"]] = relationship(
        "CalendarActiveListEntry", back_populates="active_list", cascade="all, delete-orphan"
    )


class CalendarActiveListEntry(Base):
    __tablename__ = "calendar_active_list_entry"
    __table_args__ = (
        PrimaryKeyConstraint("calendar_active_list_id", "bill_calendar_no"),
        ForeignKeyConstraint(
            ["calendar_active_list_id"],
            ["master.calendar_active_list.id"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        {"schema": "master"},
    )

    calendar_active_list_id: Mapped[int] = mapped_column(Integer)
    bill_calendar_no: Mapped[int] = mapped_column(Integer)
    bill_print_no: Mapped[Optional[str]] = mapped_column(String)
    bill_amend_version: Mapped[Optional[str]] = mapped_column(String(1))
    bill_session_year: Mapped[Optional[int]] = mapped_column(SmallInteger)
    created_date_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_fragment_id: Mapped[Optional[str]] = mapped_column(String)

    active_list: Mapped[CalendarActiveList] = relationship("CalendarActiveList", back_populates="entries")


class CalendarSupplemental(Base):
    __tablename__ = "calendar_supplemental"
    __table_args__ = (
        PrimaryKeyConstraint("id"),
        ForeignKeyConstraint(
            ["calendar_no", "calendar_year"],
            ["master.calendar.calendar_no", "master.calendar.calendar_year"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        {"schema": "master"},
    )

    id: Mapped[int] = mapped_column(Integer)
    calendar_no: Mapped[int] = mapped_column(Integer)
    calendar_year: Mapped[int] = mapped_column(SmallInteger)
    sup_version: Mapped[str] = mapped_column(String)
    release_date_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    modified_date_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    published_date_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_date_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_fragment_id: Mapped[Optional[str]] = mapped_column(String)

    calendar: Mapped[Calendar] = relationship("Calendar", back_populates="supplements")
    entries: Mapped[List["CalendarSupplementalEntry"]] = relationship(
        "CalendarSupplementalEntry", back_populates="supplement", cascade="all, delete-orphan"
    )


class CalendarSupplementalEntry(Base):
    __tablename__ = "calendar_supplemental_entry"
    __table_args__ = (
        PrimaryKeyConstraint("id"),
        ForeignKeyConstraint(
            ["calendar_sup_id"],
            ["master.calendar_supplemental.id"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        {"schema": "master"},
    )

    id: Mapped[int] = mapped_column(Integer)
    calendar_sup_id: Mapped[int] = mapped_column(Integer)
    section_code: Mapped[Optional[int]] = mapped_column(SmallInteger)
    bill_calendar_no: Mapped[Optional[int]] = mapped_column(Integer)
    bill_print_no: Mapped[Optional[str]] = mapped_column(String)
    bill_amend_version: Mapped[Optional[str]] = mapped_column(String(1))
    bill_session_year: Mapped[Optional[int]] = mapped_column(SmallInteger)
    sub_bill_print_no: Mapped[Optional[str]] = mapped_column(String)
    sub_bill_amend_version: Mapped[Optional[str]] = mapped_column(String(1))
    sub_bill_session_year: Mapped[Optional[int]] = mapped_column(SmallInteger)
    high: Mapped[Optional[bool]] = mapped_column(Boolean)
    created_date_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_fragment_id: Mapped[Optional[str]] = mapped_column(String)

    supplement: Mapped[CalendarSupplemental] = relationship(
        "CalendarSupplemental", back_populates="entries"
    )
