import unittest
import datetime
from models.committee import CommitteeId, CommitteeSessionId, CommitteeVersionId
from models.enums import Chamber
from models.session import SessionYear

class TestCommitteeId(unittest.TestCase):
    def test_creation_and_str(self):
        committee_id = CommitteeId(chamber=Chamber.SENATE, name="Rules")
        self.assertEqual(committee_id.chamber, Chamber.SENATE)
        self.assertEqual(committee_id.name, "Rules")
        self.assertEqual(str(committee_id), "SENATE-Rules")

    def test_equality_and_hashing(self):
        # Test case-insensitive equality
        id1 = CommitteeId(chamber=Chamber.ASSEMBLY, name="Health")
        id2 = CommitteeId(chamber=Chamber.ASSEMBLY, name="HEALTH")
        id3 = CommitteeId(chamber=Chamber.ASSEMBLY, name="health")
        self.assertEqual(id1, id2)
        self.assertEqual(id1, id3)
        self.assertEqual(hash(id1), hash(id2))
        self.assertEqual(hash(id1), hash(id3))

        # Test inequality
        id4_diff_name = CommitteeId(chamber=Chamber.ASSEMBLY, name="Education")
        id5_diff_chamber = CommitteeId(chamber=Chamber.SENATE, name="Health")
        self.assertNotEqual(id1, id4_diff_name)
        self.assertNotEqual(id1, id5_diff_chamber)

    def test_comparison(self):
        c1 = CommitteeId(chamber=Chamber.ASSEMBLY, name="Banks")
        c2 = CommitteeId(chamber=Chamber.ASSEMBLY, name="Codes")
        c3 = CommitteeId(chamber=Chamber.SENATE, name="Agriculture")
        c4 = CommitteeId(chamber=Chamber.SENATE, name="banks") # same as c1 but different chamber

        self.assertLess(c1, c2) # Alphabetical name comparison
        self.assertLess(c1, c3) # ASSEMBLY comes before SENATE
        self.assertLess(c3, c4) # Agriculture comes before banks in Senate

        committees = [c3, c2, c4, c1]
        committees.sort()

        self.assertEqual(committees, [c1, c2, c3, c4])

class TestCommitteeHierarchy(unittest.TestCase):
    def setUp(self):
        self.c_id = CommitteeId(chamber=Chamber.SENATE, name="Rules")

        self.cs_id1 = CommitteeSessionId(chamber=Chamber.SENATE, name="Rules", session=SessionYear(year=2023))
        self.cs_id2 = CommitteeSessionId(chamber=Chamber.SENATE, name="Rules", session=SessionYear(year=2021))

        self.date1 = datetime.datetime(2023, 1, 10, 12, 0, 0)
        self.date2 = datetime.datetime(2023, 1, 11, 12, 0, 0)
        self.cv_id1 = CommitteeVersionId(chamber=Chamber.SENATE, name="Rules", session=SessionYear(year=2023), reference_date=self.date1)
        self.cv_id2 = CommitteeVersionId(chamber=Chamber.SENATE, name="Rules", session=SessionYear(year=2023), reference_date=self.date2)

    def test_committee_session_id(self):
        self.assertEqual(self.cs_id1.name, "Rules")
        self.assertEqual(self.cs_id1.session.year, 2023)
        self.assertEqual(str(self.cs_id1), "SENATE-Rules-2023")
        self.assertEqual(self.cs_id1, CommitteeSessionId(chamber=Chamber.SENATE, name="rules", session=SessionYear(year=2023)))
        self.assertNotEqual(self.cs_id1, self.cs_id2)
        self.assertLess(self.cs_id2, self.cs_id1)

    def test_committee_version_id(self):
        self.assertEqual(self.cv_id1.name, "Rules")
        self.assertEqual(self.cv_id1.session.year, 2023)
        self.assertEqual(self.cv_id1.reference_date, self.date1)
        self.assertEqual(str(self.cv_id1), f"SENATE-Rules-2023-{self.date1}")
        self.assertNotEqual(self.cv_id1, self.cv_id2)
        self.assertLess(self.cv_id1, self.cv_id2)

    def test_hierarchy_comparison(self):
        # A more specific ID is "greater than" a less specific one if the common parts are equal
        self.assertGreater(self.cs_id1, self.c_id)
        self.assertLess(self.c_id, self.cs_id1)
        self.assertGreater(self.cv_id1, self.cs_id1)
        self.assertLess(self.cs_id1, self.cv_id1)

        # Test sorting
        items = [self.cv_id2, self.c_id, self.cs_id1, self.cv_id1, self.cs_id2]
        items.sort()
        self.assertEqual(items, [self.c_id, self.cs_id2, self.cs_id1, self.cv_id1, self.cv_id2])

if __name__ == '__main__':
    unittest.main()