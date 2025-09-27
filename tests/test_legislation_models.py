import unittest
import datetime
from models.enums import CacheType
from models.publish_status import PublishStatus
from models.session import SessionYear

from models.enums import CalendarSectionType, CalendarType, Version, VetoType, TextDiffType, BillVoteType, BillVoteCode, BillUpdateField, SobiLineType, BillTextType, BillTextFormat, BillStatusType, BillType, Chamber


class TestLegislationModels(unittest.TestCase):

    def test_cache_type_enum(self):
        self.assertEqual(CacheType.AGENDA.value, "AGENDA")
        self.assertEqual(CacheType.BILL.value, "BILL")
        self.assertEqual(CacheType.LAW.value, "LAW")
        self.assertEqual(len(CacheType), 10)

    def test_chamber_enum(self):
        self.assertEqual(Chamber.SENATE.value, 'S')
        self.assertEqual(Chamber.ASSEMBLY.abbreviation, 'A')
        self.assertEqual(Chamber.SENATE.as_sql_enum(), 'senate')
        self.assertEqual(Chamber.ASSEMBLY.opposite(), Chamber.SENATE)
        self.assertEqual(Chamber.get_value("SENATE"), Chamber.SENATE)

    def test_bill_type_enum(self):
        self.assertEqual(BillType.S.chamber, Chamber.SENATE)
        self.assertEqual(BillType.S.bill_name, "Senate")
        self.assertFalse(BillType.S.is_resolution)
        self.assertTrue(BillType.J.is_resolution)
        self.assertEqual(BillType.A.chamber, Chamber.ASSEMBLY)

    def test_bill_status_type_enum(self):
        self.assertEqual(BillStatusType.INTRODUCED.value, "Introduced")
        self.assertEqual(BillStatusType.IN_ASSEMBLY_COMM.desc, "In Assembly Committee")
        self.assertEqual(len(BillStatusType), 15)

    def test_bill_text_format_enum(self):
        self.assertEqual(BillTextFormat.PLAIN.value, "PLAIN")
        self.assertEqual(BillTextFormat.HTML.value, "HTML")
        self.assertEqual(len(BillTextFormat), 3)

    def test_sobi_line_type_enum(self):
        self.assertEqual(SobiLineType.BILL_INFO.type_code, '1')
        self.assertEqual(SobiLineType.from_code('A'), SobiLineType.ACT_CLAUSE)
        self.assertIsNone(SobiLineType.from_code('X'))
        self.assertEqual(len(SobiLineType), 17)

    def test_bill_text_type_enum(self):
        self.assertEqual(BillTextType.BILL.sobi_line_type, SobiLineType.TEXT)
        self.assertEqual(BillTextType.BILL.type_string, "BTXT")
        self.assertEqual(BillTextType.from_sobi_line_type(SobiLineType.SPONSOR_MEMO), BillTextType.SPONSOR_MEMO)
        self.assertIsNone(BillTextType.from_sobi_line_type(SobiLineType.LAW))

    def test_bill_update_field_enum(self):
        self.assertEqual(BillUpdateField.PUBLISHED_BILL.value, "PUBLISHED_BILL")
        self.assertEqual(BillUpdateField.VOTE.value, "VOTE")
        self.assertEqual(len(BillUpdateField), 17)

    def test_bill_vote_code_enum(self):
        self.assertEqual(BillVoteCode.AYE.alternate_string, "YES")
        self.assertEqual(BillVoteCode.from_string("AYE"), BillVoteCode.AYE)
        self.assertEqual(BillVoteCode.from_string("YES"), BillVoteCode.AYE)
        self.assertEqual(BillVoteCode.from_string("  excused  "), BillVoteCode.EXC)
        with self.assertRaises(ValueError):
            BillVoteCode.from_string("INVALID")
        self.assertEqual(len(BillVoteCode), 6)

    def test_bill_vote_type_enum(self):
        self.assertEqual(BillVoteType.COMMITTEE.code, 1)
        self.assertEqual(BillVoteType.from_string("  floor  "), BillVoteType.FLOOR)
        self.assertEqual(BillVoteType.from_code(1), BillVoteType.COMMITTEE)
        with self.assertRaises(ValueError):
            BillVoteType.from_string(None)
        with self.assertRaises(KeyError):
            BillVoteType.from_string("OTHER")
        with self.assertRaises(ValueError):
            BillVoteType.from_code(99)
        self.assertEqual(len(BillVoteType), 2)

    def test_text_diff_type_enum(self):
        self.assertEqual(TextDiffType.UNCHANGED.type, 0)
        self.assertEqual(TextDiffType.ADDED.type, 1)
        self.assertEqual(TextDiffType.REMOVED.type, -1)
        self.assertEqual(TextDiffType.ADDED.template_css_class, ["ol-changed", "ol-added"])
        self.assertEqual(TextDiffType.REMOVED.html_opening_tags, "<b><s>")
        self.assertEqual(TextDiffType.PAGE_BREAK.html_closing_tags, "")
        self.assertEqual(len(TextDiffType), 6)

    def test_veto_type_enum(self):
        self.assertEqual(VetoType.STANDARD.value, "STANDARD")
        self.assertEqual(VetoType.LINE_ITEM.value, "LINE_ITEM")
        self.assertEqual(len(VetoType), 2)

    def test_version_enum(self):
        self.assertEqual(str(Version.ORIGINAL), "")
        self.assertEqual(str(Version.A), "A")
        self.assertEqual(Version.of(None), Version.ORIGINAL)
        self.assertEqual(Version.of(""), Version.ORIGINAL)
        self.assertEqual(Version.of("DEFAULT"), Version.ORIGINAL)
        self.assertEqual(Version.of(" b "), Version.B)
        with self.assertRaises(KeyError):
            Version.of("invalid")

        before_c = Version.before(Version.C)
        self.assertIn(Version.ORIGINAL, before_c)
        self.assertIn(Version.A, before_c)
        self.assertIn(Version.B, before_c)
        self.assertNotIn(Version.C, before_c)

        after_y = Version.after(Version.Y)
        self.assertIn(Version.Z, after_y)
        self.assertNotIn(Version.Y, after_y)

        self.assertEqual(len(Version), 27)

    def test_publish_status_creation(self):
        now = datetime.datetime.now()
        ps = PublishStatus(published=True, effect_date_time=now, override=True, notes="Test note")
        self.assertTrue(ps.published)
        self.assertEqual(ps.effect_date_time, now)
        self.assertTrue(ps.override)
        self.assertEqual(ps.notes, "Test note")
        self.assertIn("(Override) Published", str(ps))

    def test_publish_status_defaults(self):
        now = datetime.datetime.now()
        ps = PublishStatus(effect_date_time=now)
        self.assertFalse(ps.published)
        self.assertFalse(ps.override)
        self.assertEqual(ps.notes, "")
        self.assertIn("Unpublished", str(ps))

    def test_publish_status_comparison(self):
        time1 = datetime.datetime(2023, 1, 1)
        time2 = datetime.datetime(2023, 1, 2)
        ps1 = PublishStatus(effect_date_time=time1)
        ps2 = PublishStatus(effect_date_time=time2)
        ps3 = PublishStatus(effect_date_time=time1, override=True)
        ps4 = PublishStatus(effect_date_time=time1, published=True)

        self.assertLess(ps1, ps2)
        self.assertGreater(ps2, ps1)
        self.assertLess(ps1, ps3) # non-override comes before override
        self.assertLess(ps1, ps4) # unpublished comes before published

    def test_session_year_validation(self):
        sy_odd = SessionYear(year=2023)
        self.assertEqual(sy_odd.year, 2023)

        sy_even = SessionYear(year=2022)
        self.assertEqual(sy_even.year, 2021)

        with self.assertRaises(ValueError):
            SessionYear(year=0)
        with self.assertRaises(ValueError):
            SessionYear(year=-1)

    def test_session_year_methods(self):
        sy = SessionYear(year=2023)
        self.assertEqual(sy.previous_session_year().year, 2021)
        self.assertEqual(sy.next_session_year().year, 2025)
        self.assertEqual(str(sy), "2023")

    def test_session_year_current(self):
        current_year = datetime.date.today().year
        expected_session_year = current_year if current_year % 2 != 0 else current_year - 1
        sy_current = SessionYear.current()
        self.assertEqual(sy_current.year, expected_session_year)

    def test_calendar_type_enum(self):
        self.assertEqual(CalendarType.ACTIVE_LIST.value, "ACTIVE_LIST")
        self.assertEqual(CalendarType.FLOOR_CALENDAR.value, "FLOOR_CALENDAR")
        self.assertEqual(len(CalendarType), 3)

    def test_calendar_section_type_enum(self):
        self.assertEqual(CalendarSectionType.RESOLUTIONS.code, 100)
        self.assertEqual(CalendarSectionType.THIRD_READING.lrs_representation, "BILLS ON THIRD READING")

        self.assertEqual(CalendarSectionType.from_code(200), CalendarSectionType.ORDER_OF_THE_SECOND_REPORT)
        with self.assertRaises(ValueError):
            CalendarSectionType.from_code(999)

        self.assertEqual(CalendarSectionType.from_lrs_representation("BILLS STARRED ON THIRD READING"), CalendarSectionType.STARRED_ON_THIRD_READING)
        with self.assertRaises(ValueError):
            CalendarSectionType.from_lrs_representation("INVALID")

        self.assertEqual(len(CalendarSectionType), 7)

if __name__ == '__main__':
    unittest.main()