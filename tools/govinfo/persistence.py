from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from db.models.bill import (
    Bill,
    BillAmendment,
    BillAmendmentAction,
)
from db.models.agenda import (
    Agenda,
    AgendaInfoAddendum,
    AgendaInfoCommittee,
    AgendaInfoCommitteeItem,
)
from db.models.calendar import (
    Calendar,
    CalendarActiveList,
    CalendarActiveListEntry,
    CalendarSupplemental,
    CalendarSupplementalEntry,
)

from .models import (
    GovInfoBillRecord,
    GovInfoAction,
    GovInfoAgendaRecord,
    GovInfoAgendaAddendum,
    GovInfoAgendaCommittee,
    GovInfoAgendaCommitteeItem,
    GovInfoCalendarRecord,
    GovInfoCalendarActiveList,
    GovInfoCalendarEntry,
    GovInfoCalendarSupplemental,
)


def persist_bill_record(session: Session, record: GovInfoBillRecord) -> Bill:
    bill = session.get(Bill, (record.bill_print_no, record.session_year))
    if bill is None:
        bill = Bill(
            bill_print_no=record.bill_print_no,
            bill_session_year=record.session_year,
        )

    bill.title = record.title or bill.title
    bill.summary = record.summary or bill.summary
    bill.short_title = record.short_title or bill.short_title
    bill.bill_type = record.bill_type or bill.bill_type
    bill.congress = record.congress or bill.congress
    bill.data_source = record.data_source or bill.data_source
    bill.sponsor_party = record.sponsor.party if record.sponsor else bill.sponsor_party
    bill.sponsor_state = record.sponsor.state if record.sponsor else bill.sponsor_state
    bill.modified_date_time = datetime.utcnow()
    bill.active_version = record.active_version or bill.active_version

    session.add(bill)
    session.flush()

    amendment = (
        session.query(BillAmendment)
        .filter_by(
            bill_print_no=record.bill_print_no,
            bill_session_year=record.session_year,
            bill_amend_version=record.active_version or "",
        )
        .one_or_none()
    )
    if amendment is None:
        amendment = BillAmendment(
            bill_print_no=record.bill_print_no,
            bill_session_year=record.session_year,
            bill_amend_version=record.active_version or "",
        )
    session.add(amendment)
    session.flush()

    session.query(BillAmendmentAction).filter_by(
        bill_print_no=record.bill_print_no,
        bill_session_year=record.session_year,
        bill_amend_version=record.active_version or "",
    ).delete(synchronize_session=False)

    for idx, action in enumerate(record.actions, start=1):
        session.add(
            BillAmendmentAction(
                bill_print_no=record.bill_print_no,
                bill_session_year=record.session_year,
                bill_amend_version=record.active_version or "",
                sequence_no=idx,
                effect_date=_safe_date(action),
                text=action.description,
                chamber=_normalize_chamber(action.chamber),
                created_date_time=datetime.utcnow(),
                last_fragment_id=None,
            )
        )

    return bill


def persist_agenda_record(session: Session, record: GovInfoAgendaRecord) -> Agenda:
    agenda = session.get(Agenda, (record.agenda_no, record.year))
    if agenda is None:
        agenda = Agenda(agenda_no=record.agenda_no, year=record.year)

    agenda.published_date_time = agenda.published_date_time or record.published_date_time
    agenda.modified_date_time = record.modified_date_time or agenda.modified_date_time
    session.add(agenda)
    session.flush()

    session.query(AgendaInfoAddendum).filter_by(
        agenda_no=record.agenda_no,
        year=record.year,
    ).delete(synchronize_session=False)

    for addendum in record.info_addenda:
        addendum_row = AgendaInfoAddendum(
            agenda_no=record.agenda_no,
            year=record.year,
            addendum_id=addendum.addendum_id,
            modified_date_time=addendum.modified_date_time,
            published_date_time=addendum.published_date_time,
            week_of=addendum.week_of.date() if addendum.week_of else None,
            created_date_time=datetime.utcnow(),
        )
        session.add(addendum_row)
        session.flush()

        for committee in addendum.committees:
            committee_row = AgendaInfoCommittee(
                agenda_no=record.agenda_no,
                year=record.year,
                addendum_id=addendum.addendum_id,
                committee_name=committee.committee_name,
                committee_chamber=_normalize_chamber(committee.committee_chamber) or "senate",
                chair=committee.chair,
                location=committee.location,
                meeting_date_time=committee.meeting_date_time,
                notes=committee.notes,
                created_date_time=datetime.utcnow(),
            )
            session.add(committee_row)
            session.flush()

            for item in committee.items:
                session.add(
                    AgendaInfoCommitteeItem(
                        info_committee_id=committee_row.id,
                        bill_print_no=item.bill_print_no,
                        bill_session_year=item.session_year,
                        bill_amend_version=item.amendment or "",
                        message=item.message,
                        created_date_time=datetime.utcnow(),
                    )
                )

    return agenda


def persist_calendar_record(session: Session, record: GovInfoCalendarRecord) -> Calendar:
    calendar = session.get(Calendar, (record.calendar_no, record.calendar_year))
    if calendar is None:
        calendar = Calendar(
            calendar_no=record.calendar_no,
            calendar_year=record.calendar_year,
        )

    calendar.published_date_time = calendar.published_date_time or record.published_date_time
    calendar.modified_date_time = record.modified_date_time or calendar.modified_date_time
    session.add(calendar)
    session.flush()

    session.query(CalendarActiveList).filter_by(
        calendar_no=record.calendar_no,
        calendar_year=record.calendar_year,
    ).delete(synchronize_session=False)

    session.query(CalendarSupplemental).filter_by(
        calendar_no=record.calendar_no,
        calendar_year=record.calendar_year,
    ).delete(synchronize_session=False)

    for active_list in record.active_lists:
        active_row = CalendarActiveList(
            id=None,
            sequence_no=active_list.sequence_no,
            calendar_no=record.calendar_no,
            calendar_year=record.calendar_year,
            calendar_date=active_list.calendar_date.date() if active_list.calendar_date else None,
            release_date_time=active_list.release_date_time,
            notes=active_list.notes,
            created_date_time=datetime.utcnow(),
        )
        session.add(active_row)
        session.flush()

        for entry in active_list.entries:
            session.add(
                CalendarActiveListEntry(
                    calendar_active_list_id=active_row.id,
                    bill_calendar_no=entry.bill_calendar_no,
                    bill_print_no=entry.bill_print_no,
                    bill_session_year=entry.bill_session_year,
                    bill_amend_version=entry.bill_amend_version or "",
                    created_date_time=datetime.utcnow(),
                )
            )

    for supplemental in record.supplements:
        supplement_row = CalendarSupplemental(
            id=None,
            calendar_no=record.calendar_no,
            calendar_year=record.calendar_year,
            sup_version=supplemental.sup_version,
            release_date_time=supplemental.release_date_time,
            notes=supplemental.notes,
            created_date_time=datetime.utcnow(),
        )
        session.add(supplement_row)
        session.flush()

        for entry in supplemental.entries:
            session.add(
                CalendarSupplementalEntry(
                    id=None,
                    calendar_sup_id=supplement_row.id,
                    section_code=None,
                    bill_calendar_no=entry.bill_calendar_no,
                    bill_print_no=entry.bill_print_no,
                    bill_session_year=entry.bill_session_year,
                    bill_amend_version=entry.bill_amend_version or "",
                    sub_bill_print_no=None,
                    sub_bill_amend_version="",
                    sub_bill_session_year=None,
                    high=entry.high,
                    created_date_time=datetime.utcnow(),
                )
            )

    return calendar


def _safe_date(action: GovInfoAction):
    if action.action_date is None:
        return None
    return action.action_date.date()


def _normalize_chamber(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized == "house":
        return "assembly"
    if normalized in {"senate", "assembly", "joint"}:
        return normalized
    return normalized or None
