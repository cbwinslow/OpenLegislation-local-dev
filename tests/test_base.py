import unittest
import datetime
from models.base import BaseLegislativeContent
from models.session import SessionYear

class TestBaseLegislativeContent(unittest.TestCase):

    def test_base_content_creation(self):
        now = datetime.datetime.now()
        content = BaseLegislativeContent(
            year=2023,
            modified_date_time=now,
            published_date_time=now
        )
        self.assertEqual(content.year, 2023)
        self.assertIsNotNone(content.session)
        self.assertEqual(content.session.year, 2023)
        self.assertEqual(content.modified_date_time, now)
        self.assertEqual(content.published_date_time, now)

    def test_base_content_session_calculation(self):
        content = BaseLegislativeContent(year=2022)
        self.assertEqual(content.year, 2022)
        self.assertIsNotNone(content.session)
        self.assertEqual(content.session.year, 2021)

    def test_is_published(self):
        content_published = BaseLegislativeContent(
            year=2023,
            published_date_time=datetime.datetime.now()
        )
        self.assertTrue(content_published.is_published)

        content_unpublished = BaseLegislativeContent(year=2023)
        self.assertFalse(content_unpublished.is_published)

    def test_subclassing(self):
        class SubContent(BaseLegislativeContent):
            extra_field: str

        sub_content = SubContent(year=2023, extra_field="test")
        self.assertEqual(sub_content.year, 2023)
        self.assertEqual(sub_content.session.year, 2023)
        self.assertEqual(sub_content.extra_field, "test")


if __name__ == '__main__':
    unittest.main()