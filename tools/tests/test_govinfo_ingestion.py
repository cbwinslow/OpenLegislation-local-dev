import datetime
import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db.base import Base
from db.models import (
    Bill,
    BillAmendment,
    BillAmendmentAction,
    BillAmendmentVoteInfo,
    BillAmendmentVoteRoll,
    BillMilestone,
    Agenda,
    AgendaInfoAddendum,
    AgendaInfoCommittee,
    AgendaInfoCommitteeItem,
    AgendaVoteAddendum,
    AgendaVoteCommittee,
    AgendaVoteCommitteeAttend,
    AgendaVoteCommitteeVote,
    Calendar,
    CalendarActiveList,
    CalendarActiveListEntry,
)
from db.models.member import Person, Member, SessionMember
from db.models.raw import GovInfoRawPayload

from tools.govinfo_bill_ingestion import GovInfoBillIngestor
from tools.member_data_ingestion import MemberDataIngestor
from tools.bill_vote_ingestion import BillVoteIngestor
from tools.bill_status_ingestion import BillStatusIngestor
from tools.govinfo.models import (
    GovInfoAction,
    GovInfoBillRecord,
    GovInfoSponsor,
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
)
from tools.govinfo.persistence import (
    persist_bill_record,
    persist_agenda_record,
    persist_calendar_record,
    persist_member_record,
    persist_vote_record,
    persist_bill_status_record,
)


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_persist_bill_record(session):
    record = GovInfoBillRecord(
        bill_print_no="S123",
        session_year=118,
        bill_type="S",
        title="Sample Bill",
        short_title="Short",
        summary="Summary",
        sponsor=GovInfoSponsor(name="Doe", party="D", state="NY"),
        actions=[
            GovInfoAction(
                description="Introduced",
                action_code="INTRO",
                action_date=datetime.datetime(2023, 1, 3),
            )
        ],
    )

    persist_bill_record(session, record)
    session.commit()

    bill = session.get(Bill, ("S123", 118))
    assert bill is not None
    assert bill.title == "Sample Bill"
    assert bill.sponsor_party == "D"

    actions = session.query(BillAmendmentAction).filter_by(bill_print_no="S123").all()
    assert len(actions) == 1
    assert actions[0].text == "Introduced"
    assert session.query(GovInfoRawPayload).filter_by(ingestion_type="govinfo_bills").count() == 1


def test_persist_agenda_record(session):
    # Seed session member used by vote attendance
    person = Person(id=1, full_name="John Doe")
    session.add(person)
    member = Member(id=1, person_id=1, chamber="senate", incumbent=True)
    session.add(member)
    session_member = SessionMember(
        id=1,
        member_id=1,
        lbdc_short_name="DOE",
        session_year=2024,
        district_code=1,
        alternate=False,
    )
    session.add(session_member)
    session.commit()

    record = GovInfoAgendaRecord(
        agenda_no=1,
        year=2024,
        info_addenda=[
            GovInfoAgendaAddendum(
                addendum_id="A",
                committees=[
                    GovInfoAgendaCommittee(
                        committee_name="Rules",
                        committee_chamber="senate",
                        meeting_date_time=datetime.datetime(2024, 3, 1, 10),
                        items=[
                            GovInfoAgendaCommitteeItem(
                                bill_print_no="S123",
                                session_year=118,
                                amendment="",
                            )
                        ],
                    )
                ],
            )
        ],
        vote_addenda=[
            GovInfoAgendaVoteAddendum(
                addendum_id="A",
                committees=[
                    GovInfoAgendaVoteCommittee(
                        committee_name="Rules",
                        committee_chamber="senate",
                        attendance=[
                            GovInfoAgendaVoteAttendance(
                                session_member_id=1,
                                session_year=2024,
                                lbdc_short_name="DOE",
                                rank=1,
                                party="D",
                                attend_status="present",
                            )
                        ],
                        votes=[
                            GovInfoAgendaVoteDecision(
                                vote_action="AYE",
                                with_amendment=False,
                            )
                        ],
                    )
                ],
            )
        ],
    )

    persist_agenda_record(session, record)
    session.commit()

    agenda = session.get(Agenda, (1, 2024))
    assert agenda is not None
    assert agenda.info_addenda[0].committees[0].committee_name == "Rules"
    assert agenda.vote_addenda[0].committees[0].attendance[0].lbdc_short_name == "DOE"
    assert session.query(GovInfoRawPayload).filter_by(ingestion_type="govinfo_agendas").count() == 1


def test_bill_ingestor_discovery_patterns(tmp_path):
    bills_dir = tmp_path / "bills"
    nested_dir = bills_dir / "nested"
    nested_dir.mkdir(parents=True)

    file_main = bills_dir / "BILLS-118hr1ih.xml"
    file_nested = nested_dir / "BILLSTATUS-118hr1ih.xml"
    file_extra = tmp_path / "extra.xml"

    file_main.write_text("<xml />", encoding="utf-8")
    file_nested.write_text("<xml />", encoding="utf-8")
    file_extra.write_text("<xml />", encoding="utf-8")

    ingestor = GovInfoBillIngestor(
        xml_dir=[str(bills_dir)],
        patterns=["BILLS-*.xml"],
        files=[str(file_extra)],
        recursive=False,
    )
    records = ingestor.discover_records()
    paths = {Path(r["metadata"]["xml_file"]).name for r in records}
    assert "BILLS-118hr1ih.xml" in paths
    assert "BILLSTATUS-118hr1ih.xml" not in paths
    assert "extra.xml" in paths

    ingestor_recursive = GovInfoBillIngestor(
        xml_dir=[str(bills_dir)],
        patterns=["*.xml"],
        recursive=True,
    )
    recursive_paths = {Path(r["metadata"]["xml_file"]).name for r in ingestor_recursive.discover_records()}
    assert {"BILLS-118hr1ih.xml", "BILLSTATUS-118hr1ih.xml"}.issubset(recursive_paths)


def test_member_ingestor_discovery(tmp_path):
    members_dir = tmp_path / "members"
    members_dir.mkdir()
    file_a = members_dir / "MEMBERS-001.json"
    file_b = members_dir / "custom.json"
    file_a.write_text("[]", encoding="utf-8")
    file_b.write_text("[]", encoding="utf-8")

    ingestor = MemberDataIngestor(json_dir=[str(members_dir)], patterns=["MEMBERS-*.json"], files=[str(file_b)])
    paths = {Path(r["path"]).name for r in ingestor.discover_records()}
    assert {"MEMBERS-001.json", "custom.json"} == paths


def test_vote_ingestor_discovery(tmp_path):
    vote_dir = tmp_path / "votes"
    nested = vote_dir / "nested"
    nested.mkdir(parents=True)
    (vote_dir / "VOTES-001.json").write_text("[]", encoding="utf-8")
    (nested / "VOTES-002.json").write_text("[]", encoding="utf-8")

    ingestor = BillVoteIngestor(json_dir=[str(vote_dir)], recursive=True)
    discovered = {Path(r["path"]).name for r in ingestor.discover_records()}
    assert {"VOTES-001.json", "VOTES-002.json"} == discovered


def test_status_ingestor_discovery(tmp_path):
    status_dir = tmp_path / "status"
    status_dir.mkdir()
    file_path = status_dir / "STATUS-2024-S300.json"
    file_path.write_text("[]", encoding="utf-8")

    ingestor = BillStatusIngestor(json_dir=[str(status_dir)])
    records = ingestor.discover_records()
    assert records[0]["path"].endswith("STATUS-2024-S300.json")


def test_persist_member_record(session):
    record = GovInfoMemberRecord(
        person_id=1,
        full_name="Jane Doe",
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        member_id=1001,
        chamber="senate",
        sessions=[
            GovInfoMemberSession(session_year=2024, lbdc_short_name="DOE")
        ],
    )

    session_member = persist_member_record(session, record)
    session.commit()

    assert session_member.session_year == 2024
    assert session.query(SessionMember).count() == 1
    assert session.query(Member).filter_by(id=1001).one().chamber == "senate"
    assert session.query(GovInfoRawPayload).filter_by(ingestion_type="member_data").count() == 1


def test_persist_vote_record(session):
    # Seed bill/amendment and session member
    bill = Bill(bill_print_no="S200", bill_session_year=118)
    session.add(bill)
    amendment = BillAmendment(
        bill_print_no="S200",
        bill_session_year=118,
        bill_amend_version="",
    )
    session.add(amendment)
    person = Person(id=2, full_name="Alex Smith")
    session.add(person)
    member = Member(id=2002, person_id=2, chamber="senate")
    session.add(member)
    session_member = SessionMember(
        id=3003,
        member_id=2002,
        lbdc_short_name="SMITH",
        session_year=2024,
    )
    session.add(session_member)
    session.commit()

    vote_record = GovInfoVoteRecord(
        bill_print_no="S200",
        bill_session_year=118,
        bill_amend_version="",
        vote_date=datetime.datetime(2024, 3, 10, 12, 0),
        vote_type="floor",
        roll=[
            GovInfoVoteRollEntry(
                session_member_id=3003,
                session_year=2024,
                member_short_name="SMITH",
                vote_code="aye",
            )
        ],
    )

    vote = persist_vote_record(session, vote_record)
    session.commit()

    stored_vote = session.get(BillAmendmentVoteInfo, vote.id)
    assert stored_vote is not None
    assert stored_vote.vote_type == "floor"
    assert session.query(BillAmendmentVoteRoll).filter_by(vote_id=vote.id).count() == 1
    assert session.query(GovInfoRawPayload).filter_by(ingestion_type="bill_votes").count() == 1


def test_persist_bill_status_record(session):
    bill = Bill(bill_print_no="S300", bill_session_year=119)
    session.add(bill)
    session.commit()

    record = GovInfoBillStatusRecord(
        bill_print_no="S300",
        bill_session_year=119,
        milestones=[
            GovInfoBillMilestone(
                status="Introduced",
                rank=1,
                action_sequence_no=1,
                date=datetime.datetime(2024, 1, 1),
            )
        ],
    )

    persist_bill_status_record(session, record)
    session.commit()

    milestones = session.query(BillMilestone).filter_by(bill_print_no="S300").all()
    assert len(milestones) == 1
    assert milestones[0].status == "Introduced"
    assert session.query(GovInfoRawPayload).filter_by(ingestion_type="bill_status").count() == 1


def test_persist_calendar_record(session):
    record = GovInfoCalendarRecord(
        calendar_no=10,
        calendar_year=2024,
        active_lists=[
            GovInfoCalendarActiveList(
                sequence_no=1,
                calendar_date=datetime.datetime(2024, 5, 1),
                release_date_time=datetime.datetime(2024, 4, 25, 9),
                notes="Active list",
                entries=[
                    GovInfoCalendarEntry(
                        bill_calendar_no=1,
                        bill_print_no="S123",
                        bill_session_year=118,
                    )
                ],
            )
        ],
    )

    persist_calendar_record(session, record)
    session.commit()

    calendar = session.get(Calendar, (10, 2024))
    assert calendar is not None
    assert calendar.active_lists[0].entries[0].bill_print_no == "S123"
