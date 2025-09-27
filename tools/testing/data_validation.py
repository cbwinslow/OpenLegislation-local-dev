# tools/testing/data_validation.py
"""
Data Validation and Consistency Checking Script

This script performs comprehensive validation checks on the migrated Python models
and database to ensure data integrity and consistency.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models.bill import Bill, BillId
from models.agenda import Agenda, AgendaId
from models.committee import Committee, CommitteeId
from models.member import Member
from models.calendar import Calendar, CalendarId
from models.law_info import LawInfo
from models.transcript import Transcript
from models.spotcheck_report import SpotcheckReport
from src.db.config import get_database_config
from src.db.session import get_db_session

class DataValidator:
    """Comprehensive data validation system"""

    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.engine = create_engine(db_config['url'])
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.validation_results = {
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'errors': []
        }

    def run_all_validations(self) -> Dict[str, Any]:
        """Run all validation checks"""
        print("🔍 Starting comprehensive data validation...")

        # Basic connectivity
        self._validate_database_connection()

        # Model validations
        self._validate_bill_data()
        self._validate_agenda_data()
        self._validate_committee_data()
        self._validate_member_data()
        self._validate_calendar_data()
        self._validate_law_data()
        self._validate_transcript_data()
        self._validate_spotcheck_data()

        # Cross-reference validations
        self._validate_cross_references()

        # Data integrity checks
        self._validate_data_integrity()

        return self.validation_results

    def _validate_database_connection(self):
        """Test database connection"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            self.validation_results['passed'] += 1
            print("✅ Database connection successful")
        except Exception as e:
            self._log_error("Database connection failed", str(e))

    def _validate_bill_data(self):
        """Validate Bill model data"""
        try:
            with self.SessionLocal() as session:
                bills = session.query(Bill).limit(100).all()

                for bill in bills:
                    # Validate required fields
                    if not bill.title:
                        self._log_error("Bill validation", f"Bill {bill.bill_id} missing title")

                    if not bill.status:
                        self._log_error("Bill validation", f"Bill {bill.bill_id} missing status")

                    # Validate relationships
                    if hasattr(bill, 'sponsors') and bill.sponsors:
                        for sponsor in bill.sponsors:
                            if not sponsor.member_id:
                                self._log_warning("Bill validation", f"Bill {bill.bill_id} has sponsor with missing member_id")

                self.validation_results['passed'] += 1
                print(f"✅ Bill data validation completed ({len(bills)} bills checked)")

        except Exception as e:
            self._log_error("Bill validation failed", str(e))

    def _validate_agenda_data(self):
        """Validate Agenda model data"""
        try:
            with self.SessionLocal() as session:
                agendas = session.query(Agenda).limit(50).all()

                for agenda in agendas:
                    if agenda.total_bills_considered < 0:
                        self._log_error("Agenda validation", f"Agenda {agenda.agenda_id} has negative bill count")

                    if agenda.published_date_time and agenda.published_date_time > datetime.now():
                        self._log_warning("Agenda validation", f"Agenda {agenda.agenda_id} has future publish date")

                self.validation_results['passed'] += 1
                print(f"✅ Agenda data validation completed ({len(agendas)} agendas checked)")

        except Exception as e:
            self._log_error("Agenda validation failed", str(e))

    def _validate_committee_data(self):
        """Validate Committee model data"""
        try:
            with self.SessionLocal() as session:
                committees = session.query(Committee).limit(50).all()

                for committee in committees:
                    if not committee.chair:
                        self._log_warning("Committee validation", f"Committee {committee.committee_id} missing chair")

                    if not committee.location:
                        self._log_warning("Committee validation", f"Committee {committee.committee_id} missing location")

                self.validation_results['passed'] += 1
                print(f"✅ Committee data validation completed ({len(committees)} committees checked)")

        except Exception as e:
            self._log_error("Committee validation failed", str(e))

    def _validate_member_data(self):
        """Validate Member model data"""
        try:
            with self.SessionLocal() as session:
                members = session.query(Member).limit(100).all()

                for member in members:
                    if not member.person.full_name:
                        self._log_error("Member validation", f"Member {member.member_id} missing full name")

                    if not member.chamber:
                        self._log_error("Member validation", f"Member {member.member_id} missing chamber")

                    if not member.district_code:
                        self._log_warning("Member validation", f"Member {member.member_id} missing district code")

                self.validation_results['passed'] += 1
                print(f"✅ Member data validation completed ({len(members)} members checked)")

        except Exception as e:
            self._log_error("Member validation failed", str(e))

    def _validate_calendar_data(self):
        """Validate Calendar model data"""
        try:
            with self.SessionLocal() as session:
                calendars = session.query(Calendar).limit(20).all()

                for calendar in calendars:
                    if calendar.published_date_time and calendar.published_date_time > datetime.now():
                        self._log_warning("Calendar validation", f"Calendar {calendar.calendar_id} has future publish date")

                self.validation_results['passed'] += 1
                print(f"✅ Calendar data validation completed ({len(calendars)} calendars checked)")

        except Exception as e:
            self._log_error("Calendar validation failed", str(e))

    def _validate_law_data(self):
        """Validate Law model data"""
        try:
            with self.SessionLocal() as session:
                laws = session.query(LawInfo).limit(50).all()

                for law in laws:
                    if not law.title:
                        self._log_error("Law validation", f"Law {law.law_doc_id} missing title")

                    if law.active_date and law.active_date > datetime.now():
                        self._log_warning("Law validation", f"Law {law.law_doc_id} has future active date")

                self.validation_results['passed'] += 1
                print(f"✅ Law data validation completed ({len(laws)} laws checked)")

        except Exception as e:
            self._log_error("Law validation failed", str(e))

    def _validate_transcript_data(self):
        """Validate Transcript model data"""
        try:
            with self.SessionLocal() as session:
                transcripts = session.query(Transcript).limit(20).all()

                for transcript in transcripts:
                    if not transcript.text:
                        self._log_error("Transcript validation", f"Transcript {transcript.transcript_id} missing text")

                    if transcript.transcript_id.date > datetime.now().date():
                        self._log_warning("Transcript validation", f"Transcript {transcript.transcript_id} has future date")

                self.validation_results['passed'] += 1
                print(f"✅ Transcript data validation completed ({len(transcripts)} transcripts checked)")

        except Exception as e:
            self._log_error("Transcript validation failed", str(e))

    def _validate_spotcheck_data(self):
        """Validate Spotcheck model data"""
        try:
            with self.SessionLocal() as session:
                reports = session.query(SpotcheckReport).limit(20).all()

                for report in reports:
                    if not report.data_source:
                        self._log_error("Spotcheck validation", f"Report {report.report_id} missing data source")

                self.validation_results['passed'] += 1
                print(f"✅ Spotcheck data validation completed ({len(reports)} reports checked)")

        except Exception as e:
            self._log_error("Spotcheck validation failed", str(e))

    def _validate_cross_references(self):
        """Validate cross-references between models"""
        try:
            with self.SessionLocal() as session:
                # Check bill sponsors reference valid members
                bills_with_sponsors = session.query(Bill).filter(Bill.sponsors.isnot(None)).limit(10).all()

                for bill in bills_with_sponsors:
                    if hasattr(bill, 'sponsors') and bill.sponsors:
                        for sponsor in bill.sponsors:
                            member_exists = session.query(Member).filter(
                                Member.member_id == sponsor.member_id
                            ).first()
                            if not member_exists:
                                self._log_warning("Cross-reference validation",
                                                f"Bill {bill.bill_id} references non-existent member {sponsor.member_id}")

                self.validation_results['passed'] += 1
                print("✅ Cross-reference validation completed")

        except Exception as e:
            self._log_error("Cross-reference validation failed", str(e))

    def _validate_data_integrity(self):
        """Validate data integrity constraints"""
        try:
            with self.SessionLocal() as session:
                # Check for duplicate IDs
                bill_ids = session.query(BillId).all()
                unique_bill_ids = set(str(bid) for bid in bill_ids)

                if len(bill_ids) != len(unique_bill_ids):
                    self._log_error("Data integrity", "Duplicate BillIds found")

                # Check date consistency
                future_bills = session.query(Bill).filter(
                    Bill.created_date > datetime.now()
                ).count()

                if future_bills > 0:
                    self._log_warning("Data integrity", f"{future_bills} bills have future creation dates")

                self.validation_results['passed'] += 1
                print("✅ Data integrity validation completed")

        except Exception as e:
            self._log_error("Data integrity validation failed", str(e))

    def _log_error(self, check: str, message: str):
        """Log validation error"""
        self.validation_results['errors'].append({
            'check': check,
            'type': 'error',
            'message': message
        })
        self.validation_results['failed'] += 1
        print(f"❌ {check}: {message}")

    def _log_warning(self, check: str, message: str):
        """Log validation warning"""
        self.validation_results['errors'].append({
            'check': check,
            'type': 'warning',
            'message': message
        })
        self.validation_results['warnings'] += 1
        print(f"⚠️  {check}: {message}")

def main():
    """Main validation function"""
    print("🚀 OpenLegislation Data Validation Script")
    print("=" * 50)

    # Get database configuration
    try:
        db_config = get_database_config()
    except Exception as e:
        print(f"❌ Failed to get database config: {e}")
        return 1

    # Run validations
    validator = DataValidator(db_config)
    results = validator.run_all_validations()

    # Print summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"⚠️  Warnings: {results['warnings']}")

    if results['errors']:
        print("\n📋 DETAILED ERRORS:")
        for error in results['errors']:
            print(f"  {error['type'].upper()}: {error['check']} - {error['message']}")

    # Return exit code
    if results['failed'] > 0:
        print("\n❌ Validation FAILED - check errors above")
        return 1
    else:
        print("\n✅ Validation PASSED")
        return 0

if __name__ == "__main__":
    sys.exit(main())