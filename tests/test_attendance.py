import unittest
import datetime
from models.attendance import SenateVoteAttendance
from models.member import Member, SessionMember
from models.person import Person, PersonName
from models.session import SessionYear
from models.enums import Chamber

class TestSenateVoteAttendance(unittest.TestCase):
    def setUp(self):
        self.name = PersonName(
            full_name="John D. Doe",
            most_recent_chamber=Chamber.SENATE,
            first_name="John",
            middle_name="D.",
            last_name="Doe",
            suffix=""
        )
        self.person = Person(person_id=1, name=self.name, email="jdoe@nysenate.gov", img_name="")
        self.member = Member(person=self.person, member_id=101, chamber=Chamber.SENATE, incumbent=True)
        self.session_year = SessionYear(year=2023)
        self.session_member = SessionMember(
            session_member_id=1001,
            member=self.member,
            lbdc_short_name="DOE",
            session_year=self.session_year,
            district_code=25,
            alternate=False
        )

    def test_creation_empty(self):
        attendance = SenateVoteAttendance(year=2023)
        self.assertEqual(attendance.year, 2023)
        self.assertEqual(attendance.remote_members, [])

    def test_creation_with_members(self):
        attendance = SenateVoteAttendance(year=2023, remote_members=[self.session_member])
        self.assertEqual(len(attendance.remote_members), 1)
        self.assertEqual(attendance.remote_members[0], self.session_member)

if __name__ == '__main__':
    unittest.main()