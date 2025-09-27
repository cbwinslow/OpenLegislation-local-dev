import unittest
from models.agenda import AgendaId, CommitteeAgendaId
from models.committee import CommitteeId
from models.enums import Chamber

class TestAgendaId(unittest.TestCase):
    def test_creation_and_str(self):
        agenda_id = AgendaId(year=2023, number=1)
        self.assertEqual(agenda_id.year, 2023)
        self.assertEqual(agenda_id.number, 1)
        self.assertEqual(str(agenda_id), "2023-1")

    def test_equality_and_hashing(self):
        id1 = AgendaId(year=2023, number=1)
        id2 = AgendaId(year=2023, number=1)
        id3_diff_num = AgendaId(year=2023, number=2)
        id4_diff_year = AgendaId(year=2022, number=1)

        self.assertEqual(id1, id2)
        self.assertEqual(hash(id1), hash(id2))
        self.assertNotEqual(id1, id3_diff_num)
        self.assertNotEqual(id1, id4_diff_year)

    def test_comparison(self):
        id1 = AgendaId(year=2023, number=10)
        id2 = AgendaId(year=2023, number=20)
        id3 = AgendaId(year=2022, number=100)

        self.assertLess(id1, id2)
        self.assertGreater(id1, id3)

        agendas = [id1, id2, id3]
        agendas.sort()
        self.assertEqual(agendas, [id3, id1, id2])

class TestCommitteeAgendaId(unittest.TestCase):
    def setUp(self):
        self.agenda_id1 = AgendaId(year=2023, number=1)
        self.agenda_id2 = AgendaId(year=2023, number=2)
        self.committee_id1 = CommitteeId(chamber=Chamber.SENATE, name="Finance")
        self.committee_id2 = CommitteeId(chamber=Chamber.SENATE, name="Rules")

    def test_creation_and_str(self):
        ca_id = CommitteeAgendaId(agenda_id=self.agenda_id1, committee_id=self.committee_id1)
        self.assertEqual(ca_id.agenda_id, self.agenda_id1)
        self.assertEqual(ca_id.committee_id, self.committee_id1)
        self.assertEqual(str(ca_id), "2023-1-SENATE-Finance")

    def test_equality_and_hashing(self):
        id1 = CommitteeAgendaId(agenda_id=self.agenda_id1, committee_id=self.committee_id1)
        id2 = CommitteeAgendaId(agenda_id=self.agenda_id1, committee_id=self.committee_id1)
        id3_diff_agenda = CommitteeAgendaId(agenda_id=self.agenda_id2, committee_id=self.committee_id1)
        id4_diff_committee = CommitteeAgendaId(agenda_id=self.agenda_id1, committee_id=self.committee_id2)

        self.assertEqual(id1, id2)
        self.assertEqual(hash(id1), hash(id2))
        self.assertNotEqual(id1, id3_diff_agenda)
        self.assertNotEqual(id1, id4_diff_committee)

    def test_comparison(self):
        id1 = CommitteeAgendaId(agenda_id=self.agenda_id1, committee_id=self.committee_id2) # Rules
        id2 = CommitteeAgendaId(agenda_id=self.agenda_id1, committee_id=self.committee_id1) # Finance
        id3 = CommitteeAgendaId(agenda_id=self.agenda_id2, committee_id=self.committee_id1) # Agenda 2

        # Finance < Rules, so id2 < id1
        self.assertLess(id2, id1)
        # Agenda 1 < Agenda 2, so id1 < id3
        self.assertLess(id1, id3)

        items = [id1, id3, id2]
        items.sort()
        self.assertEqual(items, [id2, id1, id3])

if __name__ == '__main__':
    unittest.main()