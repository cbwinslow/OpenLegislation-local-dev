import unittest
import datetime
from models.bill import Bill, BillId, BaseBillId, BillAction, BillSponsor, BillStatus, ApprovalId, ApprovalMessage, VetoId, VetoMessage, ProgramInfo, BillVoteId, BillVote, TextDiff, BillText, BillAmendment, BillAmendNotFoundEx
from models.session import SessionYear
from models.enums import BillType, Version, Chamber, BillStatusType, VetoType, BillVoteType, BillVoteCode, TextDiffType, BillTextFormat
from models.person import Person, PersonName
from models.member import Member, SessionMember
from models.committee import CommitteeId, CommitteeVersionId
from models.attendance import SenateVoteAttendance

class TestBillId(unittest.TestCase):

    def test_creation_from_full_print_no(self):
        bill_id = BillId(print_no="S1234A", session=2023)
        self.assertEqual(bill_id.base_print_no, "S1234")
        self.assertEqual(bill_id.session.year, 2023)
        self.assertEqual(bill_id.version, Version.A)

    def test_creation_from_base_print_no(self):
        bill_id = BillId(base_print_no="A5678", session=2022, version="B")
        self.assertEqual(bill_id.base_print_no, "A5678")
        self.assertEqual(bill_id.session.year, 2021) # Session year calculation
        self.assertEqual(bill_id.version, Version.B)

    def test_creation_with_no_version(self):
        bill_id = BillId(print_no="R9", session=2023)
        self.assertEqual(bill_id.base_print_no, "R9")
        self.assertEqual(bill_id.version, Version.ORIGINAL)

    def test_validation(self):
        with self.assertRaises(ValueError):
            BillId(print_no="Z1234", session=2023) # Invalid bill type
        with self.assertRaises(ValueError):
            BillId(print_no="S123456", session=2023) # Invalid number length in regex
        with self.assertRaises(ValueError):
            BillId(base_print_no="S123A", session=2023, version="B") # Version in base_print_no
        with self.assertRaises(ValueError):
            BillId(print_no="", session=2023)

    def test_properties(self):
        bill_id = BillId(print_no="J42C", session=2023)
        self.assertEqual(bill_id.print_no, "J42C")
        self.assertEqual(bill_id.bill_type, BillType.J)
        self.assertEqual(bill_id.chamber, Chamber.SENATE)
        self.assertEqual(bill_id.number, 42)

    def test_string_representations(self):
        bill_id = BillId(print_no="S1", session=2023)
        self.assertEqual(str(bill_id), "S1-2023")
        self.assertEqual(bill_id.padded_print_number, "S00001")
        self.assertEqual(bill_id.padded_bill_id_string, "S00001-2023")

    def test_comparison_and_equality(self):
        b1 = BillId(print_no="S123A", session=2023)
        b2 = BillId(base_print_no="S123", session=2023, version="A")
        b3 = BillId(print_no="S123B", session=2023)
        b4 = BillId(print_no="S123A", session=2021)
        b5 = BillId(print_no="A123A", session=2023)

        self.assertEqual(b1, b2)
        self.assertNotEqual(b1, b3)
        self.assertLess(b1, b3)
        self.assertGreater(b3, b1)
        self.assertLess(b4, b1)
        self.assertLess(b5, b1)

    def test_base_equality(self):
        b1 = BillId(print_no="S123A", session=2023)
        b2 = BillId(print_no="S123B", session=2023)
        b3 = BillId(print_no="S123A", session=2021)

        self.assertTrue(b1.equals_base(b2))
        self.assertFalse(b1.equals_base(b3))
        self.assertEqual(b1.hash_base(), b2.hash_base())
        self.assertNotEqual(b1.hash_base(), b3.hash_base())

class TestBaseBillId(unittest.TestCase):
    def test_creation_forces_base_version(self):
        # Even if a version is in the print_no, it should be ignored and set to ORIGINAL
        base_bill_id = BaseBillId(print_no="S1234A", session=2023)
        self.assertEqual(base_bill_id.base_print_no, "S1234")
        self.assertEqual(base_bill_id.session.year, 2023)
        self.assertEqual(base_bill_id.version, Version.ORIGINAL)

    def test_creation_from_base_print_no(self):
        # Providing a version should be ignored
        base_bill_id = BaseBillId(base_print_no="A5678", session=2022, version="B")
        self.assertEqual(base_bill_id.base_print_no, "A5678")
        self.assertEqual(base_bill_id.session.year, 2021)
        self.assertEqual(base_bill_id.version, Version.ORIGINAL)

    def test_of_method(self):
        bill_id = BillId(print_no="S123A", session=2023)
        base_bill_id = BaseBillId.of(bill_id)
        self.assertIsInstance(base_bill_id, BaseBillId)
        self.assertEqual(base_bill_id.base_print_no, "S123")
        self.assertEqual(base_bill_id.session.year, 2023)
        self.assertEqual(base_bill_id.version, Version.ORIGINAL)

    def test_with_version_method(self):
        base_bill_id = BaseBillId(print_no="S1234", session=2023)
        versioned_bill_id = base_bill_id.with_version(Version.C)
        self.assertIsInstance(versioned_bill_id, BillId)
        self.assertNotIsInstance(versioned_bill_id, BaseBillId)
        self.assertEqual(versioned_bill_id.base_print_no, "S1234")
        self.assertEqual(versioned_bill_id.session.year, 2023)
        self.assertEqual(versioned_bill_id.version, Version.C)

    def test_string_representation(self):
        base_bill_id = BaseBillId(print_no="S1234A", session=2023)
        # The version should be empty in the string representation for ORIGINAL
        self.assertEqual(str(base_bill_id), "S1234-2023")

class TestBillAction(unittest.TestCase):
    def setUp(self):
        self.bill_id1 = BillId(print_no="S1A", session=2023)
        self.bill_id2 = BillId(print_no="S1B", session=2023)
        self.bill_id3 = BillId(print_no="S2A", session=2023)
        self.date1 = datetime.date(2023, 1, 10)
        self.date2 = datetime.date(2023, 1, 11)

    def test_creation(self):
        action = BillAction(
            bill_id=self.bill_id1,
            date=self.date1,
            chamber=Chamber.SENATE,
            sequence_no=10,
            text="REFERRED TO RULES",
            action_type="COMMITTEE"
        )
        self.assertEqual(action.sequence_no, 10)
        self.assertEqual(action.text, "REFERRED TO RULES")
        self.assertEqual(action.chamber, Chamber.SENATE)
        self.assertEqual(str(action), "2023-01-10 (SENATE) REFERRED TO RULES")

    def test_equality(self):
        # Equal actions (different bill version, same base)
        action1 = BillAction(bill_id=self.bill_id1, date=self.date1, chamber=Chamber.SENATE, sequence_no=1, text="text", action_type="t")
        action2 = BillAction(bill_id=self.bill_id2, date=self.date1, chamber=Chamber.SENATE, sequence_no=1, text="TEXT", action_type="t")
        self.assertEqual(action1, action2)
        self.assertEqual(hash(action1), hash(action2))

        # Different actions
        action3 = BillAction(bill_id=self.bill_id3, date=self.date1, chamber=Chamber.SENATE, sequence_no=1, text="text", action_type="t")
        action4 = BillAction(bill_id=self.bill_id1, date=self.date2, chamber=Chamber.SENATE, sequence_no=1, text="text", action_type="t")
        action5 = BillAction(bill_id=self.bill_id1, date=self.date1, chamber=Chamber.ASSEMBLY, sequence_no=1, text="text", action_type="t")
        action6 = BillAction(bill_id=self.bill_id1, date=self.date1, chamber=Chamber.SENATE, sequence_no=2, text="text", action_type="t")
        action7 = BillAction(bill_id=self.bill_id1, date=self.date1, chamber=Chamber.SENATE, sequence_no=1, text="other text", action_type="t")

        self.assertNotEqual(action1, action3) # Different bill
        self.assertNotEqual(action1, action4) # Different date
        self.assertNotEqual(action1, action5) # Different chamber
        self.assertNotEqual(action1, action6) # Different sequence
        self.assertNotEqual(action1, action7) # Different text

    def test_comparison(self):
        action1 = BillAction(bill_id=self.bill_id1, date=self.date1, chamber=Chamber.SENATE, sequence_no=1, text="a", action_type="t")
        action2 = BillAction(bill_id=self.bill_id1, date=self.date1, chamber=Chamber.SENATE, sequence_no=10, text="b", action_type="t")
        action3 = BillAction(bill_id=self.bill_id1, date=self.date1, chamber=Chamber.SENATE, sequence_no=5, text="c", action_type="t")

        actions = [action1, action2, action3]
        actions.sort()

        self.assertEqual(actions[0].sequence_no, 1)
        self.assertEqual(actions[1].sequence_no, 5)
        self.assertEqual(actions[2].sequence_no, 10)

class TestBillSponsor(unittest.TestCase):
    def setUp(self):
        name = PersonName(full_name="John D. Doe", most_recent_chamber=Chamber.SENATE, first_name="John", middle_name="D.", last_name="Doe", suffix="")
        person = Person(person_id=1, name=name, email="jdoe@nysenate.gov", img_name="")
        member = Member(person=person, member_id=101, chamber=Chamber.SENATE, incumbent=True)
        session_year = SessionYear(year=2023)
        self.session_member = SessionMember(
            session_member_id=1001,
            member=member,
            lbdc_short_name="DOE",
            session_year=session_year,
            district_code=25,
            alternate=False
        )

    def test_member_sponsor(self):
        sponsor = BillSponsor(member=self.session_member)
        self.assertTrue(sponsor.has_member)
        self.assertEqual(str(sponsor), "DOE")

    def test_rules_sponsor(self):
        sponsor = BillSponsor(rules=True)
        self.assertFalse(sponsor.has_member)
        self.assertEqual(str(sponsor), "RULES")

    def test_budget_sponsor(self):
        sponsor = BillSponsor(budget=True)
        self.assertFalse(sponsor.has_member)
        self.assertEqual(str(sponsor), "BUDGET BILL")

    def test_redistricting_sponsor(self):
        sponsor = BillSponsor(redistricting=True)
        self.assertFalse(sponsor.has_member)
        self.assertEqual(str(sponsor), "REDISTRICTING")

    def test_rules_with_member_sponsor(self):
        sponsor = BillSponsor(rules=True, member=self.session_member)
        self.assertTrue(sponsor.has_member)
        self.assertEqual(str(sponsor), "RULES (DOE)")

class TestBillStatus(unittest.TestCase):
    def setUp(self):
        self.date = datetime.date(2023, 5, 15)
        self.committee_id = CommitteeId(chamber=Chamber.SENATE, name="Finance")

    def test_basic_status(self):
        status = BillStatus(status_type=BillStatusType.IN_SENATE_COMM, action_date=self.date)
        self.assertEqual(status.status_type, BillStatusType.IN_SENATE_COMM)
        self.assertEqual(status.action_date, self.date)
        self.assertEqual(str(status), "In Senate Committee (2023-05-15)")

    def test_status_with_committee(self):
        status = BillStatus(
            status_type=BillStatusType.IN_SENATE_COMM,
            action_date=self.date,
            committee_id=self.committee_id
        )
        self.assertEqual(str(status), "In Senate Committee (2023-05-15) SENATE-Finance")

    def test_status_with_calendar(self):
        status = BillStatus(
            status_type=BillStatusType.SENATE_FLOOR,
            action_date=self.date,
            calendar_no=123
        )
        self.assertEqual(str(status), "Senate Floor Calendar (2023-05-15) Cal No: 123")

    def test_status_with_committee_and_calendar(self):
        status = BillStatus(
            status_type=BillStatusType.SENATE_FLOOR,
            action_date=self.date,
            committee_id=self.committee_id,
            calendar_no=456
        )
        self.assertEqual(str(status), "Senate Floor Calendar (2023-05-15) SENATE-Finance Cal No: 456")

class TestApprovalId(unittest.TestCase):
    def test_creation_and_str(self):
        approval_id = ApprovalId(year=2023, approval_number=42)
        self.assertEqual(approval_id.year, 2023)
        self.assertEqual(approval_id.approval_number, 42)
        self.assertEqual(str(approval_id), "2023-42")

    def test_equality_and_hashing(self):
        id1 = ApprovalId(year=2023, approval_number=42)
        id2 = ApprovalId(year=2023, approval_number=42)
        id3_diff_num = ApprovalId(year=2023, approval_number=43)
        id4_diff_year = ApprovalId(year=2022, approval_number=42)

        self.assertEqual(id1, id2)
        self.assertEqual(hash(id1), hash(id2))
        self.assertNotEqual(id1, id3_diff_num)
        self.assertNotEqual(id1, id4_diff_year)

    def test_comparison(self):
        id1 = ApprovalId(year=2023, approval_number=10)
        id2 = ApprovalId(year=2023, approval_number=20)
        id3 = ApprovalId(year=2022, approval_number=100)

        self.assertLess(id1, id2)
        self.assertGreater(id1, id3)

        approvals = [id1, id2, id3]
        approvals.sort()
        self.assertEqual(approvals, [id3, id1, id2])

class TestApprovalMessage(unittest.TestCase):
    def setUp(self):
        self.bill_id = BillId(print_no="S1234", session=2023)

    def test_creation_and_properties(self):
        msg = ApprovalMessage(
            year=2023,
            bill_id=self.bill_id,
            approval_number=5,
            memo_text="This is an important bill.",
            chapter=101,
            signer="Governor"
        )
        self.assertEqual(msg.year, 2023)
        self.assertEqual(msg.approval_number, 5)
        self.assertEqual(msg.signer, "Governor")

        # Test the approval_id property
        approval_id = msg.approval_id
        self.assertIsInstance(approval_id, ApprovalId)
        self.assertEqual(approval_id.year, 2023)
        self.assertEqual(approval_id.approval_number, 5)

    def test_comparison(self):
        msg1 = ApprovalMessage(year=2023, bill_id=self.bill_id, approval_number=10, chapter=1)
        msg2 = ApprovalMessage(year=2023, bill_id=self.bill_id, approval_number=20, chapter=2)
        msg3 = ApprovalMessage(year=2022, bill_id=self.bill_id, approval_number=100, chapter=3)

        self.assertLess(msg1, msg2)
        self.assertGreater(msg1, msg3)

        messages = [msg1, msg2, msg3]
        messages.sort()
        self.assertEqual(messages, [msg3, msg1, msg2])

class TestVetoId(unittest.TestCase):
    def test_creation_and_str(self):
        veto_id = VetoId(year=2023, veto_number=15)
        self.assertEqual(veto_id.year, 2023)
        self.assertEqual(veto_id.veto_number, 15)
        self.assertEqual(str(veto_id), "2023-15")

    def test_equality_and_hashing(self):
        id1 = VetoId(year=2023, veto_number=15)
        id2 = VetoId(year=2023, veto_number=15)
        id3_diff_num = VetoId(year=2023, veto_number=16)
        id4_diff_year = VetoId(year=2022, veto_number=15)

        self.assertEqual(id1, id2)
        self.assertEqual(hash(id1), hash(id2))
        self.assertNotEqual(id1, id3_diff_num)
        self.assertNotEqual(id1, id4_diff_year)

    def test_comparison(self):
        id1 = VetoId(year=2023, veto_number=10)
        id2 = VetoId(year=2023, veto_number=20)
        id3 = VetoId(year=2022, veto_number=100)

        self.assertLess(id1, id2)
        self.assertGreater(id1, id3)

        vetoes = [id1, id2, id3]
        vetoes.sort()
        self.assertEqual(vetoes, [id3, id1, id2])

class TestVetoMessage(unittest.TestCase):
    def setUp(self):
        self.bill_id = BaseBillId(print_no="S1234", session=2023)

    def test_creation_and_properties(self):
        msg = VetoMessage(
            year=2023,
            bill_id=self.bill_id,
            veto_number=12,
            memo_text="This is a veto.",
            veto_type=VetoType.STANDARD,
            chapter=0,
            bill_page=0,
            line_start=0,
            line_end=0,
            signer="Governor"
        )
        self.assertEqual(msg.year, 2023)
        self.assertEqual(msg.veto_number, 12)
        self.assertEqual(msg.signer, "Governor")

        # Test the veto_id property
        veto_id = msg.veto_id
        self.assertIsInstance(veto_id, VetoId)
        self.assertEqual(veto_id.year, 2023)
        self.assertEqual(veto_id.veto_number, 12)

    def test_comparison(self):
        msg1 = VetoMessage(year=2023, bill_id=self.bill_id, veto_number=10, veto_type=VetoType.STANDARD, chapter=0, bill_page=0, line_start=0, line_end=0)
        msg2 = VetoMessage(year=2023, bill_id=self.bill_id, veto_number=20, veto_type=VetoType.STANDARD, chapter=0, bill_page=0, line_start=0, line_end=0)
        msg3 = VetoMessage(year=2022, bill_id=self.bill_id, veto_number=100, veto_type=VetoType.STANDARD, chapter=0, bill_page=0, line_start=0, line_end=0)

        self.assertLess(msg1, msg2)
        self.assertGreater(msg1, msg3)

        messages = [msg1, msg2, msg3]
        messages.sort()
        self.assertEqual(messages, [msg3, msg1, msg2])

class TestProgramInfo(unittest.TestCase):
    def test_creation(self):
        info = ProgramInfo(info="Test Program", number=123)
        self.assertEqual(info.info, "Test Program")
        self.assertEqual(info.number, 123)

class TestBillVoteId(unittest.TestCase):
    def setUp(self):
        self.bill_id = BillId(print_no="S1234", session=2023)
        self.committee_id = CommitteeId(chamber=Chamber.SENATE, name="Finance")
        self.date = datetime.date(2023, 6, 1)

    def test_creation_and_equality(self):
        id1 = BillVoteId(
            bill_id=self.bill_id,
            vote_date=self.date,
            vote_type=BillVoteType.COMMITTEE,
            sequence_no=1,
            committee_id=self.committee_id
        )
        id2 = BillVoteId(
            bill_id=self.bill_id,
            vote_date=self.date,
            vote_type=BillVoteType.COMMITTEE,
            sequence_no=1,
            committee_id=self.committee_id
        )
        self.assertEqual(id1, id2)
        self.assertEqual(hash(id1), hash(id2))

    def test_comparison_logic(self):
        # Committee vote should come before a same-day floor vote
        committee_vote_id = BillVoteId(bill_id=self.bill_id, vote_date=self.date, vote_type=BillVoteType.COMMITTEE, sequence_no=1, committee_id=self.committee_id)
        floor_vote_id = BillVoteId(bill_id=self.bill_id, vote_date=self.date, vote_type=BillVoteType.FLOOR, sequence_no=2, committee_id=None)
        self.assertLess(committee_vote_id, floor_vote_id)

        # Test sorting with a more complex list
        vote1 = committee_vote_id
        vote2 = floor_vote_id
        vote3_earlier_date = BillVoteId(bill_id=self.bill_id, vote_date=self.date - datetime.timedelta(days=1), vote_type=BillVoteType.COMMITTEE, sequence_no=3, committee_id=self.committee_id)
        vote4_different_bill = BillVoteId(bill_id=BillId(print_no="S1235", session=2023), vote_date=self.date, vote_type=BillVoteType.FLOOR, sequence_no=1, committee_id=None)
        vote5_same_day_earlier_seq = BillVoteId(bill_id=self.bill_id, vote_date=self.date, vote_type=BillVoteType.COMMITTEE, sequence_no=0, committee_id=self.committee_id)

        votes = [vote1, vote2, vote3_earlier_date, vote4_different_bill, vote5_same_day_earlier_seq]
        votes.sort()

        expected_order = [
            vote3_earlier_date,         # Earliest date
            vote5_same_day_earlier_seq, # Same date, earliest sequence
            vote1,                      # Same date, next sequence
            vote2,                      # Same date, floor vote (None committee) comes after committee vote
            vote4_different_bill        # Different bill, sorts last
        ]
        self.assertEqual(votes, expected_order)

class TestBillVote(unittest.TestCase):
    def setUp(self):
        self.bill_id = BillId(print_no="S5000", session=2023)
        self.vote_date = datetime.date(2023, 4, 1)

        name1 = PersonName(full_name="John D. Doe", most_recent_chamber=Chamber.SENATE, first_name="John", middle_name="D.", last_name="Doe", suffix="")
        person1 = Person(person_id=1, name=name1, email="jdoe@nysenate.gov", img_name="")
        member1 = Member(person=person1, member_id=101, chamber=Chamber.SENATE, incumbent=True)
        self.sm1 = SessionMember(session_member_id=1001, member=member1, lbdc_short_name="DOE", session_year=SessionYear(year=2023), district_code=25, alternate=False)

        name2 = PersonName(full_name="Jane A. Smith", most_recent_chamber=Chamber.SENATE, first_name="Jane", middle_name="A.", last_name="Smith", suffix="")
        person2 = Person(person_id=2, name=name2, email="jsmith@nysenate.gov", img_name="")
        member2 = Member(person=person2, member_id=102, chamber=Chamber.SENATE, incumbent=True)
        self.sm2 = SessionMember(session_member_id=1002, member=member2, lbdc_short_name="SMITH", session_year=SessionYear(year=2023), district_code=26, alternate=False)

    def test_creation_and_vote_id(self):
        vote = BillVote(
            bill_id=self.bill_id,
            vote_date=self.vote_date,
            vote_type=BillVoteType.FLOOR,
            sequence_no=1
        )
        self.assertEqual(vote.year, 2023)
        self.assertEqual(vote.session.year, 2023)

        vote_id = vote.vote_id
        self.assertIsInstance(vote_id, BillVoteId)
        self.assertEqual(vote_id.bill_id, self.bill_id)
        self.assertEqual(vote_id.vote_date, self.vote_date)

    def test_creation_from_vote_id(self):
        vote_id = BillVoteId(bill_id=self.bill_id, vote_date=self.vote_date, vote_type=BillVoteType.FLOOR, sequence_no=1)
        vote = BillVote(vote_id=vote_id)
        self.assertEqual(vote.vote_id, vote_id)
        self.assertEqual(vote.year, 2023)

    def test_vote_management(self):
        vote = BillVote(bill_id=self.bill_id, vote_date=self.vote_date, vote_type=BillVoteType.FLOOR)
        vote.add_member_vote(BillVoteCode.AYE, self.sm1)
        vote.add_member_vote(BillVoteCode.NAY, self.sm2)

        self.assertEqual(vote.count(), 2)
        ayes = vote.get_members_by_vote(BillVoteCode.AYE)
        self.assertIn(self.sm1, ayes)
        self.assertEqual(len(ayes), 1)

        counts = vote.get_vote_counts()
        self.assertEqual(counts.get(BillVoteCode.AYE), 1)
        self.assertEqual(counts.get(BillVoteCode.NAY), 1)
        self.assertIsNone(counts.get(BillVoteCode.EXC))

    def test_equality(self):
        v1 = BillVote(bill_id=self.bill_id, vote_date=self.vote_date, vote_type=BillVoteType.FLOOR)
        v1.add_member_vote(BillVoteCode.AYE, self.sm1)

        v2 = BillVote(bill_id=self.bill_id, vote_date=self.vote_date, vote_type=BillVoteType.FLOOR)
        v2.add_member_vote(BillVoteCode.AYE, self.sm1)

        self.assertEqual(v1, v2)
        self.assertEqual(hash(v1), hash(v2))

        v3 = BillVote(bill_id=self.bill_id, vote_date=self.vote_date, vote_type=BillVoteType.FLOOR)
        v3.add_member_vote(BillVoteCode.NAY, self.sm1)
        self.assertNotEqual(v1, v3)

class TestTextDiff(unittest.TestCase):
    def test_plain_format(self):
        diff_added = TextDiff(diff_type=TextDiffType.ADDED, raw_text="new text")
        self.assertEqual(diff_added.plain_format_text, "NEW TEXT")

        diff_removed = TextDiff(diff_type=TextDiffType.REMOVED, raw_text="old text")
        self.assertEqual(diff_removed.plain_format_text, "old text")

        diff_unchanged = TextDiff(diff_type=TextDiffType.UNCHANGED, raw_text="same text")
        self.assertEqual(diff_unchanged.plain_format_text, "same text")

    def test_html_format(self):
        diff = TextDiff(diff_type=TextDiffType.ADDED, raw_text="new text")
        self.assertEqual(diff.html_format_text, "<b><u>new text</u></b>")

        diff_header = TextDiff(diff_type=TextDiffType.HEADER, raw_text="Header")
        self.assertEqual(diff_header.html_format_text, "<font size=5><b>Header</b></font>")

    def test_template_format(self):
        diff_added = TextDiff(diff_type=TextDiffType.ADDED, raw_text="new text")
        self.assertEqual(diff_added.template_format_text, '<span class="ol-changed ol-added">new text</span>')

        diff_unchanged = TextDiff(diff_type=TextDiffType.UNCHANGED, raw_text="same text")
        self.assertEqual(diff_unchanged.template_format_text, "same text") # No span if no css classes

class TestBillText(unittest.TestCase):
    def setUp(self):
        self.diffs = [
            TextDiff(diff_type=TextDiffType.UNCHANGED, raw_text="This is "),
            TextDiff(diff_type=TextDiffType.ADDED, raw_text="new"),
            TextDiff(diff_type=TextDiffType.UNCHANGED, raw_text=" text."),
        ]
        self.sobi_text = "This is some SOBI text."

    def test_from_sobi_plain_text(self):
        bill_text = BillText(sobi_plain_text=self.sobi_text)
        # format_html_extracted_bill_text is called, which might alter the text.
        # Here we just check that the plain text is returned.
        self.assertIn(self.sobi_text, bill_text.get_full_text(BillTextFormat.PLAIN))
        # HTML and TEMPLATE should be empty if only SOBI text is provided
        self.assertEqual(bill_text.get_full_text(BillTextFormat.HTML), "")
        self.assertEqual(bill_text.get_full_text(BillTextFormat.TEMPLATE), "")

    def test_from_diffs_plain(self):
        bill_text = BillText(diffs=self.diffs)
        # ADDED text becomes uppercase in plain format
        self.assertIn("This is NEW text.", bill_text.get_full_text(BillTextFormat.PLAIN))

    def test_from_diffs_html(self):
        bill_text = BillText(diffs=self.diffs)
        html = bill_text.get_full_text(BillTextFormat.HTML)
        self.assertIn(BillText.HTML_STYLE, html)
        self.assertIn("<pre>", html)
        self.assertIn("This is ", html)
        self.assertIn("<b><u>new</u></b>", html)
        self.assertIn(" text.", html)
        self.assertIn("</pre>", html)

    def test_from_diffs_template(self):
        bill_text = BillText(diffs=self.diffs)
        template = bill_text.get_full_text(BillTextFormat.TEMPLATE)
        self.assertIn('<pre class="ol-bill-text">', template)
        self.assertIn("This is ", template)
        self.assertIn('<span class="ol-changed ol-added">new</span>', template)
        self.assertIn(" text.", template)
        self.assertIn("</pre>", template)

class TestBillAmendment(unittest.TestCase):
    def setUp(self):
        self.base_bill_id = BaseBillId(print_no="S1234", session=2023)
        self.amendment = BillAmendment(base_bill_id=self.base_bill_id, version=Version.A)
        name = PersonName(full_name="John D. Doe", most_recent_chamber=Chamber.SENATE, first_name="John", middle_name="D.", last_name="Doe", suffix="")
        person = Person(person_id=1, name=name, email="jdoe@nysenate.gov", img_name="")
        member = Member(person=person, member_id=101, chamber=Chamber.SENATE, incumbent=True)
        session_year = SessionYear(year=2023)
        self.session_member = SessionMember(
            session_member_id=1001,
            member=member,
            lbdc_short_name="DOE",
            session_year=session_year,
            district_code=25,
            alternate=False
        )

    def test_creation_and_properties(self):
        self.assertEqual(self.amendment.version, Version.A)
        self.assertEqual(self.amendment.bill_id.print_no, "S1234A")
        self.assertEqual(self.amendment.bill_type, BillType.S)
        self.assertFalse(self.amendment.is_resolution)

    def test_co_sponsors_mutability(self):
        self.amendment.co_sponsors.append(self.session_member)
        self.assertEqual(len(self.amendment.co_sponsors), 1)
        self.assertEqual(self.amendment.co_sponsors[0].lbdc_short_name, "DOE")

    def test_vote_management(self):
        vote_id = BillVoteId(bill_id=self.amendment.bill_id, vote_date=datetime.date.today(), vote_type=BillVoteType.FLOOR, sequence_no=1)
        vote = BillVote(vote_id=vote_id)
        vote.add_member_vote(BillVoteCode.AYE, self.session_member)

        self.amendment.update_vote(vote)

        self.assertEqual(len(self.amendment.votes_map), 1)
        self.assertEqual(len(self.amendment.votes_list), 1)
        self.assertEqual(self.amendment.votes_list[0].get_vote_counts().get(BillVoteCode.AYE), 1)

    def test_related_laws_json(self):
        self.amendment.related_laws_json = '{"PENAL LAW": ["120.05", "125.25"]}'
        laws_map = self.amendment.related_laws_map
        self.assertIn("PENAL LAW", laws_map)
        self.assertIn("120.05", laws_map["PENAL LAW"])

class TestBill(unittest.TestCase):
    def setUp(self):
        self.base_bill_id = BaseBillId(print_no="S1234", session=2023)
        self.bill = Bill(base_bill_id=self.base_bill_id, title="A bill about something important")

    def test_creation_and_properties(self):
        self.assertEqual(self.bill.base_bill_id, self.base_bill_id)
        self.assertEqual(self.bill.year, 2023)
        self.assertEqual(self.bill.session.year, 2023)
        self.assertEqual(self.bill.title, "A bill about something important")

    def test_amendment_management(self):
        # By default, a Bill should not have any amendments
        self.assertEqual(len(self.bill.amendment_map), 0)
        with self.assertRaises(BillAmendNotFoundEx):
            self.bill.get_amendment(Version.ORIGINAL)

        # Add an amendment
        orig_amendment = BillAmendment(base_bill_id=self.base_bill_id, version=Version.ORIGINAL)
        self.bill.add_amendment(orig_amendment)
        self.assertEqual(len(self.bill.amendment_map), 1)
        self.assertEqual(self.bill.get_amendment(Version.ORIGINAL), orig_amendment)

        # Test active_amendment property
        self.assertEqual(self.bill.active_amendment, orig_amendment)

        # Add another amendment and change active version
        a_amendment = BillAmendment(base_bill_id=self.base_bill_id, version=Version.A)
        self.bill.add_amendment(a_amendment)
        self.bill.active_version = Version.A
        self.assertEqual(self.bill.active_amendment, a_amendment)

        amendment_list = self.bill.amendment_list
        self.assertIn(orig_amendment, amendment_list)
        self.assertIn(a_amendment, amendment_list)

    def test_comparison(self):
        bill2 = Bill(base_bill_id=BaseBillId(print_no="S1235", session=2023))
        self.assertLess(self.bill, bill2)

if __name__ == '__main__':
    unittest.main()