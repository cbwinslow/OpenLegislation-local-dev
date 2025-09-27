from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, date
from typing import Optional
import logging

from sqlalchemy.orm import Session

from db.models.bill import (
    Bill,
    BillAmendment,
    BillAmendmentAction,
    BillAmendmentVoteInfo,
    BillAmendmentVoteRoll,
    BillMilestone,
)
from db.models.agenda import (
    Agenda,
    AgendaInfoAddendum,
    AgendaInfoCommittee,
    AgendaInfoCommitteeItem,
    AgendaVoteAddendum,
    AgendaVoteCommittee,
    AgendaVoteCommitteeAttend,
    AgendaVoteCommitteeVote,
)
from db.models.calendar import (
    Calendar,
    CalendarActiveList,
    CalendarActiveListEntry,
    CalendarSupplemental,
    CalendarSupplementalEntry,
)
from db.models.member import Person, Member, SessionMember
from db.models.raw import GovInfoRawPayload
from db.models.bill import BillEmbedding

from tools.embeddings.embedder import EmbeddingService
from tools.storage.minio_client import archive_json_payload

from .models import (
    GovInfoBillRecord,
    GovInfoAction,
    GovInfoAgendaRecord,
    GovInfoAgendaAddendum,
    GovInfoAgendaCommittee,
    GovInfoAgendaCommitteeItem,
    GovInfoAgendaVoteAddendum,
    GovInfoAgendaVoteCommittee,
    GovInfoAgendaVoteAttendance,
    GovInfoAgendaVoteDecision,
    GovInfoCalendarRecord,
    GovInfoCalendarActiveList,
    GovInfoCalendarEntry,
    GovInfoCalendarSupplemental,
    GovInfoMemberRecord,
    GovInfoMemberSession,
    GovInfoVoteRecord,
    GovInfoVoteRollEntry,
    GovInfoBillStatusRecord,
    GovInfoBillMilestone,
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

    payload = _normalize_payload(asdict(record))
    _store_raw_payload(session, "govinfo_bills", record.bill_print_no, payload)
    _maybe_archive("govinfo-bills", f"{record.bill_print_no}-{record.session_year}.json", payload)
    _maybe_embed_bill(session, bill, record)
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

    session.query(AgendaVoteAddendum).filter_by(
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

    for vote_addendum in record.vote_addenda:
        vote_addendum_row = AgendaVoteAddendum(
            agenda_no=record.agenda_no,
            year=record.year,
            addendum_id=vote_addendum.addendum_id,
            modified_date_time=vote_addendum.modified_date_time,
            published_date_time=vote_addendum.published_date_time,
            created_date_time=datetime.utcnow(),
        )
        session.add(vote_addendum_row)
        session.flush()

        for committee in vote_addendum.committees:
            committee_row = AgendaVoteCommittee(
                agenda_no=record.agenda_no,
                year=record.year,
                addendum_id=vote_addendum.addendum_id,
                committee_name=committee.committee_name,
                committee_chamber=_normalize_chamber(committee.committee_chamber) or "senate",
                chair=committee.chair,
                meeting_date_time=committee.meeting_date_time,
                created_date_time=datetime.utcnow(),
            )
            session.add(committee_row)
            session.flush()

            for attendee in committee.attendance:
                session.add(
                    AgendaVoteCommitteeAttend(
                        vote_committee_id=committee_row.id,
                        session_member_id=attendee.session_member_id,
                        session_year=attendee.session_year,
                        lbdc_short_name=attendee.lbdc_short_name,
                        rank=attendee.rank,
                        party=attendee.party,
                        attend_status=attendee.attend_status,
                        created_date_time=datetime.utcnow(),
                    )
                )

            for decision in committee.votes:
                session.add(
                    AgendaVoteCommitteeVote(
                        vote_committee_id=committee_row.id,
                        vote_action=decision.vote_action,
                        vote_info_id=decision.vote_info_id,
                        refer_committee_name=decision.refer_committee_name,
                        refer_committee_chamber=_normalize_chamber(decision.refer_committee_chamber),
                        with_amendment=decision.with_amendment,
                        created_date_time=datetime.utcnow(),
                    )
                )

    payload = _normalize_payload(asdict(record))
    _store_raw_payload(
        session,
        "govinfo_agendas",
        f"{record.agenda_no}-{record.year}",
        payload,
    )
    _maybe_archive(
        "govinfo-agendas",
        f"{record.agenda_no}-{record.year}.json",
        payload,
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

    payload = _normalize_payload(asdict(record))
    _store_raw_payload(
        session,
        "govinfo_calendars",
        f"{record.calendar_no}-{record.calendar_year}",
        payload,
    )
    _maybe_archive(
        "govinfo-calendars",
        f"{record.calendar_no}-{record.calendar_year}.json",
        payload,
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


def persist_member_record(session: Session, record: GovInfoMemberRecord) -> SessionMember:
    session_member = _persist_member_core(session, record)
    payload = _normalize_payload(asdict(record))
    _store_raw_payload(session, "member_data", f"{record.member_id}", payload)
    _maybe_archive("member-data", f"{record.member_id}.json", payload)
    return session_member


def persist_vote_record(session: Session, record: GovInfoVoteRecord) -> BillAmendmentVoteInfo:
    vote = BillAmendmentVoteInfo(
        bill_print_no=record.bill_print_no,
        bill_session_year=record.bill_session_year,
        bill_amend_version=record.bill_amend_version or "",
        vote_date=record.vote_date,
        sequence_no=record.sequence_no,
        vote_type=record.vote_type,
        committee_name=record.committee_name,
        committee_chamber=_normalize_chamber(record.committee_chamber),
        created_date_time=datetime.utcnow(),
    )
    session.add(vote)
    session.flush()

    session.query(BillAmendmentVoteRoll).filter_by(vote_id=vote.id).delete(synchronize_session=False)
    for roll_entry in record.roll:
        session.add(
            BillAmendmentVoteRoll(
                vote_id=vote.id,
                session_member_id=roll_entry.session_member_id,
                member_short_name=roll_entry.member_short_name,
                session_year=roll_entry.session_year,
                vote_code=roll_entry.vote_code.lower(),
                created_date_time=datetime.utcnow(),
            )
        )

    payload = _normalize_payload(asdict(record))
    _store_raw_payload(
        session,
        "bill_votes",
        f"{record.bill_print_no}-{record.vote_date.isoformat()}",
        payload,
    )
    _maybe_archive(
        "bill-votes",
        f"{record.bill_print_no}-{record.vote_date.isoformat()}.json",
        payload,
    )
    return vote


def persist_bill_status_record(session: Session, record: GovInfoBillStatusRecord) -> None:
    session.query(BillMilestone).filter_by(
        bill_print_no=record.bill_print_no,
        bill_session_year=record.bill_session_year,
    ).delete(synchronize_session=False)

    for milestone in record.milestones:
        session.add(
            BillMilestone(
                bill_print_no=record.bill_print_no,
                bill_session_year=record.bill_session_year,
                status=milestone.status,
                rank=milestone.rank,
                action_sequence_no=milestone.action_sequence_no,
                date=milestone.date.date(),
                committee_name=milestone.committee_name,
                committee_chamber=_normalize_chamber(milestone.committee_chamber),
                cal_no=milestone.cal_no,
                created_date_time=datetime.utcnow(),
            )
        )

    payload = _normalize_payload(asdict(record))
    _store_raw_payload(
        session,
        "bill_status",
        f"{record.bill_print_no}-{record.bill_session_year}",
        payload,
    )
    _maybe_archive(
        "bill-status",
        f"{record.bill_print_no}-{record.bill_session_year}.json",
        payload,
    )


def _store_raw_payload(
    session: Session,
    ingestion_type: str,
    record_id: str,
    payload: dict,
    source_path: Optional[str] = None,
) -> None:
    existing = (
        session.query(GovInfoRawPayload)
        .filter_by(ingestion_type=ingestion_type, record_id=record_id)
        .one_or_none()
    )
    if existing:
        existing.payload = payload
        existing.source_path = source_path
        existing.created_at = datetime.utcnow()
        session.add(existing)
    else:
        session.add(
            GovInfoRawPayload(
                ingestion_type=ingestion_type,
                record_id=record_id,
                payload=payload,
                source_path=source_path,
            )
        )


def _maybe_archive(bucket: str, key: str, payload: dict) -> None:
    try:
        archive_json_payload(bucket, key, payload)
    except Exception:  # pragma: no cover - archival is best-effort
        logging.getLogger(__name__).debug("Archive skipped for %s/%s", bucket, key)


def _maybe_embed_bill(session: Session, bill: Bill, record: GovInfoBillRecord) -> None:
    service = EmbeddingService.instance()
    if service is None:
        return
    text = record.summary or record.title or ""
    if not text.strip():
        return
    vector = service.embed([text])[0]
    metadata = {
        "title": record.title,
        "short_title": record.short_title,
        "session_year": record.session_year,
    }
    embedding = session.get(BillEmbedding, (bill.bill_print_no, bill.bill_session_year))
    if embedding is None:
        embedding = BillEmbedding(
            bill_print_no=bill.bill_print_no,
            bill_session_year=bill.bill_session_year,
        )
    embedding.embedding = vector
    embedding.metadata = metadata
    embedding.updated_at = datetime.utcnow()
    session.add(embedding)


def _persist_member_core(session: Session, record: GovInfoMemberRecord) -> SessionMember:
    person = session.get(Person, record.person_id)
    if person is None:
        person = Person(id=record.person_id)
    person.full_name = record.full_name
    person.first_name = record.first_name or person.first_name
    person.last_name = record.last_name or person.last_name
    person.email = record.email or person.email
    session.add(person)

    member = session.get(Member, record.member_id)
    if member is None:
        member = Member(id=record.member_id, person_id=record.person_id)
    member.person_id = record.person_id
    member.chamber = record.chamber
    member.incumbent = record.incumbent
    member.full_name = member.full_name or record.full_name
    session.add(member)

    last_session_member: Optional[SessionMember] = None
    for assignment in record.sessions:
        session_member = (
            session.query(SessionMember)
            .filter_by(member_id=record.member_id, session_year=assignment.session_year)
            .one_or_none()
        )
        if session_member is None:
            session_member = SessionMember(
                member_id=record.member_id,
                session_year=assignment.session_year,
                lbdc_short_name=assignment.lbdc_short_name,
            )
        session_member.lbdc_short_name = assignment.lbdc_short_name
        session_member.district_code = assignment.district_code
        session_member.alternate = assignment.alternate
        session.add(session_member)
        last_session_member = session_member

    if last_session_member is None:
        raise ValueError("Member record must include at least one session assignment")

    return last_session_member
