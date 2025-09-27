import unittest
from models.person import Person, PersonName
from models.member import Member, SessionMember
from models.session import SessionYear
from models.enums import Chamber

class TestPersonAndMember(unittest.TestCase):
    def setUp(self):
        self.name1 = PersonName(
            full_name="John D. Doe",
            most_recent_chamber=Chamber.SENATE,
            first_name="John",
            middle_name="D.",
            last_name="Doe",
            suffix=""
        )
        self.name2 = PersonName(
            full_name="Jane A. Smith",
            most_recent_chamber=Chamber.ASSEMBLY,
            first_name="Jane",
            middle_name="A.",
            last_name="Smith",
            suffix=""
        )
        self.person1 = Person(person_id=1, name=self.name1, email="jdoe@nysenate.gov", img_name="")
        self.person2 = Person(person_id=2, name=self.name2, email="jsmith@nyassembly.gov", img_name="jane_smith.jpg")
        self.member1 = Member(person=self.person1, member_id=101, chamber=Chamber.SENATE, incumbent=True)
        self.member2 = Member(person=self.person2, member_id=102, chamber=Chamber.ASSEMBLY, incumbent=True)

    def test_person_name(self):
        self.assertEqual(self.name1.prefix, "Senator")
        self.assertEqual(self.name2.prefix, "Assembly Member")
        self.assertLess(self.name1, self.name2) # Doe < Smith

    def test_person(self):
        self.assertEqual(self.person1.person_id, 1)
        self.assertEqual(self.person1.img_name, "no_image.jpg") # Default value
        self.assertEqual(self.person2.img_name, "jane_smith.jpg")
        self.assertEqual(self.person1.suggested_image_file_name, "1_John_Doe.jpg")
        self.assertLess(self.person1, self.person2)

    def test_member(self):
        self.assertEqual(self.member1.member_id, 101)
        self.assertEqual(self.member1.chamber, Chamber.SENATE)
        self.assertTrue(self.member1.incumbent)
        self.assertEqual(self.member1.person, self.person1)

    def test_session_member(self):
        session_year = SessionYear(year=2023)
        sm1 = SessionMember(
            session_member_id=1001,
            member=self.member1,
            lbdc_short_name="DOE",
            session_year=session_year,
            district_code=25,
            alternate=False
        )
        self.assertEqual(str(sm1), "DOE (year: 2023, id: 101)")

        # Test equality
        sm2_same = SessionMember(session_member_id=1002, member=self.member1, lbdc_short_name="DOE", session_year=session_year, district_code=25, alternate=False)
        self.assertEqual(sm1, sm2_same)
        self.assertEqual(hash(sm1), hash(sm2_same))

        # Test equality with alternate flag
        sm3_alt = SessionMember(session_member_id=1003, member=self.member1, lbdc_short_name="DOEJD", session_year=session_year, district_code=25, alternate=True)
        self.assertEqual(sm1, sm3_alt) # Should be equal because one is an alternate
        self.assertEqual(hash(sm1), hash(sm3_alt)) # Hash should still be the same

        # Test inequality
        sm4_diff_member = SessionMember(session_member_id=1004, member=self.member2, lbdc_short_name="DOE", session_year=session_year, district_code=25, alternate=False)
        self.assertNotEqual(sm1, sm4_diff_member)

        sm5_diff_name_not_alt = SessionMember(session_member_id=1005, member=self.member1, lbdc_short_name="OTHER", session_year=session_year, district_code=25, alternate=False)
        self.assertNotEqual(sm1, sm5_diff_name_not_alt) # Not equal if names differ and neither is alternate

        # Test comparison
        sm6_later_year = SessionMember(session_member_id=1006, member=self.member1, lbdc_short_name="DOE", session_year=SessionYear(year=2025), district_code=25, alternate=False)
        self.assertLess(sm1, sm6_later_year)
        self.assertLess(sm3_alt, sm1) # Alternate comes before non-alternate

if __name__ == '__main__':
    unittest.main()