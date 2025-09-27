import unittest
import re
from models import bill_text_utils

class TestBillTextUtils(unittest.TestCase):

    def test_format_html_extracted_bill_text_senate(self):
        senate_header = """
   STATE OF NEW YORK
________________________________________________________________________

                                  IN SENATE

                                (PREFILED)
                             January 4, 2023
                                ________

Introduced by Sen. KENNEDY -- read twice and ordered printed, and when
  printed to be committed to the Committee on Rules

AN ACT to amend the executive law, in relation to enacting the "challenge
  protection act"
"""
        result = bill_text_utils.format_html_extracted_bill_text(senate_header)
        lines = result.split('\n')

        # Check for key centered text, ignoring exact whitespace padding
        self.assertIn("S T A T E   O F   N E W   Y O R K", lines[1])
        self.assertTrue(lines[1].strip() == "S T A T E   O F   N E W   Y O R K")
        self.assertIn("I N  S E N A T E", lines[4])
        self.assertTrue(lines[4].strip() == "I N  S E N A T E")

    def test_format_html_extracted_bill_text_assembly(self):
        assembly_header = """
   STATE OF NEW YORK
________________________________________________________________________

                                 IN ASSEMBLY

                             January 9, 2023
                                ________

Introduced by M. of A. LUPARDO, BARRETT, BENDETT, BRABENEC, BUTTENSCHON,
  CLARK,  DeSTEFANO,  DICKENS,  DURSO,  FORREST, FRIEND, GALLAHAN, GAND-
  OLFO, HAWLEY, JENSEN, K. BROWN, LEMONDES, LUNSFORD, MANKTELOW,  McDO-
  NOUGH,  MILLER,  J. M. GIGLIO, O'DONNELL, PALMESANO, REILLY, ROZIC, L.
  ROSENTHAL, SIMON, SIMPSON, SLATER, STECK, STERN, TAGUE, THIELE,  WALSH,
  ZINERMAN,  GUNTHER,  JACOBSON,  ANGELINO,  BEEPHAN, BLUMENCRANTZ -- Multi-
  Sponsored by -- M. of A. SAYEGH -- read once and referred to the Commit-
  tee on Agriculture

AN ACT to amend the agriculture and markets law, in relation to creating
  the farm preservation and viability act
"""
        result = bill_text_utils.format_html_extracted_bill_text(assembly_header)
        lines = result.split('\n')
        self.assertIn("S T A T E   O F   N E W   Y O R K", lines[1])
        self.assertTrue(lines[1].strip() == "S T A T E   O F   N E W   Y O R K")
        self.assertIn("I N  A S S E M B L Y", lines[4])
        self.assertTrue(lines[4].strip() == "I N  A S S E M B L Y")


    def test_convert_html_to_plain_text(self):
        html = """
<pre>
  <span class="ol-bold">
    <u>
      NEW YORK STATE
    </u>
  </span>
  <p class="brk"></p>
  regular text
</pre>
"""
        expected = "NEW YORK STATE\nregular text"
        actual = bill_text_utils.convert_html_to_plain_text(html)
        # Normalize whitespace to handle minor differences between parsers
        actual_normalized = re.sub(r'\\s+', ' ', actual).strip()
        expected_normalized = re.sub(r'\\s+', ' ', expected).strip()
        self.assertEqual(actual_normalized, expected_normalized)

if __name__ == '__main__':
    unittest.main()