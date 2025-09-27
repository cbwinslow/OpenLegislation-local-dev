import requests
import time
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from models.bill import Bill, BillId, BaseBillId, BillSponsor, BillAction
from models.enums import Chamber
from models.session import SessionYear
from models.member import SessionMember, Member
from models.person import Person, PersonName

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GovInfoApiProcessor:
    def __init__(self, api_key: str, db_session: Any = None):
        self.api_key = api_key
        self.db_session = db_session
        self.base_url = "https://api.govinfo.gov"

    def congress_to_session_year(self, congress: int) -> int:
        return 1789 + (congress - 1) * 2

    def map_bill_from_json(self, hit: Dict[str, Any], congress: int) -> Optional[Bill]:
        try:
            package_id = hit.get("packageId")
            if not package_id:
                logging.warning("Skipping hit with no packageId")
                return None

            # e.g., BILLS-118hr1enr
            bill_no_match = re.match(r"BILLS-\d+(hr|s|sres|hres|sjres|hjres|hconres|sconres)(\d+)", package_id)
            if not bill_no_match:
                logging.warning(f"Could not parse bill number from packageId: {package_id}")
                return None

            bill_type_prefix = bill_no_match.group(1).upper()
            bill_number = bill_no_match.group(2)

            # This mapping is an approximation. A real implementation would need a more robust way
            # to map govinfo prefixes to the internal BillType enum.
            bill_type_map = {
                "HR": "A", "S": "S", "SRES": "R", "HRES": "E",
                "SJRES": "J", "HJRES": "J", "HCONRES": "C", "SCONRES": "B"
            }

            bill_prefix = bill_type_map.get(bill_type_prefix)
            if not bill_prefix:
                logging.warning(f"Unrecognized bill type prefix: {bill_type_prefix}")
                return None

            base_print_no = f"{bill_prefix}{bill_number}"
            session_year = self.congress_to_session_year(congress)

            base_bill_id = BaseBillId(print_no=base_print_no, session=session_year)

            bill = Bill(
                base_bill_id=base_bill_id,
                title=hit.get("title", ""),
                federal_congress=congress,
                federal_source="GovInfo API"
            )

            metadata = hit.get("metadata", {})

            # Sponsors
            sponsors = []
            for sponsor_data in metadata.get("sponsors", []):
                # This is a simplified mapping. A real implementation would need to
                # look up or create Person/Member/SessionMember objects.
                sponsor = BillSponsor(
                    member=SessionMember(
                        session_member_id=0, # Placeholder
                        member=Member(
                            person=Person(
                                person_id=0, # Placeholder
                                name=PersonName(
                                    full_name=sponsor_data.get("name", ""),
                                    first_name=sponsor_data.get("firstName", ""),
                                    last_name=sponsor_data.get("lastName", ""),
                                    middle_name="", suffix="", prefix=""
                                ),
                                email="", img_name=""
                            ),
                            member_id=0, # Placeholder
                            chamber=Chamber.SENATE if bill_prefix in ["S", "R", "B", "J"] else Chamber.ASSEMBLY,
                            incumbent=True
                        ),
                        lbdc_short_name=sponsor_data.get("name", ""),
                        session_year=SessionYear(year=session_year),
                        district_code=0, # Placeholder
                        alternate=False
                    )
                )
                sponsors.append(sponsor)

            if sponsors:
                bill.sponsor = sponsors[0]
                bill.additional_sponsors = sponsors[1:]

            # Actions
            actions = []
            for action_data in metadata.get("actions", []):
                chamber_str = action_data.get("chamber", "SENATE").upper()
                chamber = Chamber.ASSEMBLY if chamber_str == "HOUSE" else Chamber[chamber_str]
                action = BillAction(
                    bill_id=bill.base_bill_id,
                    date=datetime.strptime(action_data.get("date"), "%Y-%m-%dT%H:%M:%SZ").date(),
                    chamber=chamber,
                    text=action_data.get("text", ""),
                    action_type=action_data.get("type", "action")
                )
                actions.append(action)
            bill.actions = actions

            return bill

        except Exception as e:
            logging.error(f"Error mapping bill from JSON: {hit.get('packageId')}", exc_info=e)
            return None

    def process_bills(self, congress: int, limit: int = 50) -> List[Bill]:
        logging.info(f"Starting ingestion of bills for congress: {congress}")
        url = f"{self.base_url}/collections/BILLS/granules?offset=0&pageSize={limit}&congress={congress}&api_key={self.api_key}"

        bills: List[Bill] = []
        max_retries = 3

        for attempt in range(max_retries):
            try:
                logging.debug(f"Fetching from URL: {url}")
                response = requests.get(url, timeout=60)
                response.raise_for_status()

                data = response.json()
                if "message" in data and "API rate limit exceeded" in data["message"]:
                     raise requests.exceptions.RequestException(f"API rate limit exceeded: {data['message']}")

                results = data.get("granules", [])
                processed_count = 0
                for hit in results:
                    bill = self.map_bill_from_json(hit, congress)
                    if bill:
                        bills.append(bill)
                        processed_count += 1
                        logging.debug(f"Mapped bill: {bill.base_bill_id}")

                logging.info(f"Successfully processed {processed_count} bills for congress {congress}")
                break

            except requests.exceptions.RequestException as e:
                logging.warning(f"Attempt {attempt + 1} failed for congress {congress}: {e}")
                if attempt + 1 >= max_retries:
                    logging.error(f"Max retries exceeded for congress {congress}", exc_info=e)
                    raise
                time.sleep(2 ** attempt)

        logging.info(f"Ingestion completed for congress {congress}: {len(bills)} bills ingested")
        return bills

if __name__ == '__main__':
    import os
    api_key = os.environ.get("GOVINFO_API_KEY")
    if not api_key:
        logging.warning("GOVINFO_API_KEY environment variable not set. Cannot run live test.")
    else:
        processor = GovInfoApiProcessor(api_key)
        processor.process_bills(congress=118, limit=5)