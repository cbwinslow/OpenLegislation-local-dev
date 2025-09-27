import unittest
from unittest.mock import patch, MagicMock
import os
import requests
from processors.govinfo_processor import GovInfoApiProcessor
from models.bill import Bill

class TestGovInfoApiProcessor(unittest.TestCase):

    def setUp(self):
        self.api_key = "TEST_KEY"
        self.processor = GovInfoApiProcessor(api_key=self.api_key)
        self.mock_successful_response = {
            "granules": [
                {
                    "packageId": "BILLS-118hr1enr",
                    "title": "H.R. 1 (ENR) - For the People Act of 2023",
                    "metadata": {
                        "sponsors": [
                            {
                                "name": "SARBANES, JOHN P.",
                                "firstName": "John",
                                "lastName": "Sarbanes",
                                "party": "D",
                                "state": "MD"
                            }
                        ],
                        "actions": [
                            {
                                "date": "2023-03-03T05:00:00Z",
                                "chamber": "House",
                                "text": "Introduced in House"
                            }
                        ]
                    }
                }
            ]
        }

    @patch('requests.get')
    def test_process_bills_success(self, mock_get):
        # Configure the mock to return a successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_successful_response
        mock_get.return_value = mock_response

        bills = self.processor.process_bills(congress=118, limit=1)

        # Verify that requests.get was called correctly
        expected_url = f"{self.processor.base_url}/collections/BILLS/granules?offset=0&pageSize=1&congress=118&api_key={self.api_key}"
        mock_get.assert_called_once_with(expected_url, timeout=60)

        # Verify that we got one bill back
        self.assertEqual(len(bills), 1)

        # Verify the content of the bill
        bill = bills[0]
        self.assertIsInstance(bill, Bill)
        self.assertEqual(bill.base_bill_id.base_print_no, "A1")
        self.assertEqual(bill.title, "H.R. 1 (ENR) - For the People Act of 2023")
        self.assertEqual(bill.federal_congress, 118)
        self.assertEqual(len(bill.actions), 1)
        self.assertEqual(bill.actions[0].text, "Introduced in House")
        self.assertIsNotNone(bill.sponsor)
        self.assertEqual(bill.sponsor.member.lbdc_short_name, "SARBANES, JOHN P.")

    @patch('requests.get')
    def test_process_bills_api_error_and_retry(self, mock_get):
        # Configure the mock to simulate a failure, then success
        mock_failure_response = MagicMock()
        mock_failure_response.raise_for_status.side_effect = requests.exceptions.RequestException("API Error")

        mock_success_response = MagicMock()
        mock_success_response.status_code = 200
        mock_success_response.json.return_value = self.mock_successful_response

        mock_get.side_effect = [mock_failure_response, mock_success_response]

        with patch('time.sleep', return_value=None) as mock_sleep: # Mock time.sleep to speed up test
            bills = self.processor.process_bills(congress=118, limit=1)

            # Verify that requests.get was called twice (initial + 1 retry)
            self.assertEqual(mock_get.call_count, 2)
            # Verify that sleep was called once
            mock_sleep.assert_called_once()
            # Verify that we still got the bill
            self.assertEqual(len(bills), 1)

if __name__ == '__main__':
    unittest.main()