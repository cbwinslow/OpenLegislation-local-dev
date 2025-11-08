#!/usr/bin/env python3
"""
SQLAlchemy Models for OpenLegislation Database

This module defines SQLAlchemy ORM models that exactly match the existing PostgreSQL database schema.
These models are used for database operations in the ingestion processes.

Author: OpenLegislation Team
Date: 2025-11-08
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, Date, DateTime, Float, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func, text
import uuid

Base = declarative_base()


# ===========================================
# TELEMETRY AND AUDIT MODELS
# ===========================================

class TelemetryEvent(Base):
    """Telemetry events table"""
    __tablename__ = 'telemetry_events'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(100), nullable=False)
    event_data = Column(JSONB)
    source = Column(String(100))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PerformanceMetric(Base):
    """Performance metrics table"""
    __tablename__ = 'performance_metrics'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    function_name = Column(String(200), nullable=False)
    execution_time = Column(Float(precision=4))
    success = Column(Boolean, default=True)
    metadata_json = Column(JSONB)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class FeatureFlag(Base):
    """Feature flags table"""
    __tablename__ = 'feature_flags'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flag_name = Column(String(100), unique=True, nullable=False)
    enabled = Column(Boolean, default=False)
    metadata_json = Column(JSONB)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JobQueue(Base):
    """Job queue table"""
    __tablename__ = 'job_queue'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type = Column(String(100), nullable=False)
    job_data = Column(JSONB)
    priority = Column(Integer, default=1)
    status = Column(String(50), default='pending')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)


# ===========================================
# LEGISLATIVE DATA MODELS (EXACTLY MATCHING SCHEMA)
# ===========================================

class Bill(Base):
    """Bills table - exactly matching database_schema.sql"""
    __tablename__ = 'bills'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_print_no = Column(String(20), nullable=False)
    bill_session_year = Column(Integer, nullable=False)
    title = Column(Text)
    summary = Column(Text)
    active_version = Column(String(50))
    data_source = Column(String(50), default='federal')
    congress = Column(Integer)
    bill_type = Column(String(10))
    sponsor_party = Column(String(20))
    sponsor_state = Column(String(10))
    status = Column(String(100))
    status_date = Column(Date)
    short_title = Column(Text)
    ldblurb = Column(Text)
    federal_congress = Column(Integer)
    federal_source = Column(String(100))
    session_year = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('bill_print_no', 'bill_session_year', name='uq_bill_print_no_session'),
    )


class BillSponsor(Base):
    """Bill sponsors table - exactly matching database_schema.sql"""
    __tablename__ = 'bill_sponsors'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_print_no = Column(String(20), nullable=False)
    bill_session_year = Column(Integer, nullable=False)
    session_member_id = Column(UUID(as_uuid=True))
    budget_bill = Column(Boolean, default=False)
    rules_sponsor = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('bill_print_no', 'bill_session_year', 'session_member_id', name='uq_bill_sponsor'),
    )


class BillAction(Base):
    """Bill actions table - exactly matching database_schema.sql"""
    __tablename__ = 'bill_actions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_print_no = Column(String(20), nullable=False)
    bill_session_year = Column(Integer, nullable=False)
    bill_amend_version = Column(String(50))
    effect_date = Column(Date)
    text = Column(Text)
    sequence_no = Column(Integer)
    chamber = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('bill_print_no', 'bill_session_year', 'bill_amend_version', 'sequence_no', name='uq_bill_action'),
    )


class Committee(Base):
    """Committees table - exactly matching database_schema.sql"""
    __tablename__ = 'committees'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    chamber = Column(String(20), nullable=False)
    committee_id = Column(String(50))
    current_session = Column(Integer)
    full_name = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('name', 'chamber', name='uq_committee_name_chamber'),
    )


class CommitteeMember(Base):
    """Committee members table - exactly matching database_schema.sql"""
    __tablename__ = 'committee_members'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    majority = Column(Boolean, default=False)
    sequence_no = Column(Integer)
    title = Column(String(100))
    committee_name = Column(String(200), nullable=False)
    version_created = Column(DateTime(timezone=True), server_default=func.now())
    session_year = Column(Integer)
    session_member_id = Column(UUID(as_uuid=True))
    chamber = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FederalMember(Base):
    """Federal members table - matching congress.gov API structure"""
    __tablename__ = 'federal_members'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bioguide_id = Column(String(10), unique=True)  # congress.gov: bioguideId
    first_name = Column(String(100))
    last_name = Column(String(100))
    full_name = Column(Text)  # congress.gov: name
    party = Column(String(20))  # congress.gov: party
    state = Column(String(10))  # congress.gov: state
    district = Column(String(10))  # congress.gov: district
    chamber = Column(String(20))  # congress.gov: chamber
    active = Column(Boolean, default=True)
    congress = Column(Integer)
    # Additional congress.gov fields
    date_of_birth = Column(Date)  # congress.gov: biography.dateOfBirth
    place_of_birth = Column(String(100))  # congress.gov: biography.placeOfBirth
    education = Column(JSONB)  # congress.gov: biography.education
    profession = Column(JSONB)  # congress.gov: biography.profession
    contact_website = Column(String(255))  # congress.gov: contactWebsite
    office_address = Column(JSONB)  # congress.gov: office
    terms = Column(JSONB)  # congress.gov: terms array
    committees = Column(JSONB)  # congress.gov: committees array
    last_updated = Column(DateTime(timezone=True))  # congress.gov: lastUpdated
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class RawPayload(Base):
    """Raw payload storage table - exactly matching database_schema.sql"""
    __tablename__ = 'raw_payloads'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ingestion_type = Column(String(50), nullable=False)
    record_id = Column(String(100), nullable=False)
    payload = Column(JSONB)
    processed_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('ingestion_type', 'record_id', name='uq_raw_payload'),
    )


# ===========================================
# MISSING LEGISLATIVE DATA MODELS
# ===========================================

class BillAmendment(Base):
    """Bill amendments table - represents specific versions of bills"""
    __tablename__ = 'bill_amendments'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_print_no = Column(String(20), nullable=False)
    bill_session_year = Column(Integer, nullable=False)
    bill_amend_version = Column(String(10), nullable=False)
    sponsor_memo = Column(Text)
    full_text = Column(Text)
    law_code = Column(Text)
    publish_status = Column(String(50))
    same_as = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('bill_print_no', 'bill_session_year', 'bill_amend_version', name='uq_bill_amendment'),
    )


class BillText(Base):
    """Bill text versions table"""
    __tablename__ = 'bill_texts'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_print_no = Column(String(20), nullable=False)
    bill_session_year = Column(Integer, nullable=False)
    bill_amend_version = Column(String(10), nullable=False)
    text_format = Column(String(16))  # 'html', 'plain', 'xml'
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('bill_print_no', 'bill_session_year', 'bill_amend_version', name='uq_bill_text'),
    )


class BillAmendmentCosponsor(Base):
    """Bill amendment cosponsors table"""
    __tablename__ = 'bill_amendment_cosponsors'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_print_no = Column(String(20), nullable=False)
    bill_session_year = Column(Integer, nullable=False)
    bill_amend_version = Column(String(10), nullable=False)
    session_member_id = Column(UUID(as_uuid=True))
    is_lead_cosponsor = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('bill_print_no', 'bill_session_year', 'bill_amend_version', 'session_member_id', name='uq_bill_amendment_cosponsor'),
    )


class SessionMember(Base):
    """Session members table - legislators for specific sessions"""
    __tablename__ = 'session_members'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    member_id = Column(String(50), nullable=False)
    session_year = Column(Integer, nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    full_name = Column(Text)
    party = Column(String(20))
    state = Column(String(10))
    district = Column(String(10))
    chamber = Column(String(20))
    position = Column(String(50))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('member_id', 'session_year', name='uq_session_member'),
    )


class BillVote(Base):
    """Bill vote information table"""
    __tablename__ = 'bill_votes'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_print_no = Column(String(20), nullable=False)
    bill_session_year = Column(Integer, nullable=False)
    vote_date = Column(Date, nullable=False)
    sequence_no = Column(Integer, nullable=False)
    vote_type = Column(String(50))
    committee_name = Column(String(200))
    committee_chamber = Column(String(20))
    ayes = Column(Integer, default=0)
    nays = Column(Integer, default=0)
    absent = Column(Integer, default=0)
    excused = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('bill_print_no', 'bill_session_year', 'vote_date', 'sequence_no', name='uq_bill_vote'),
    )


class CommitteeVersionId(Base):
    """Committee version IDs table"""
    __tablename__ = 'committee_version_ids'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_print_no = Column(String(20), nullable=False)
    bill_session_year = Column(Integer, nullable=False)
    committee_name = Column(String(200), nullable=False)
    chamber = Column(String(20), nullable=False)
    version_created = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ===========================================
# GOVINFO STAGING TABLES
# ===========================================

class GovInfoBill(Base):
    """GovInfo bill staging table"""
    __tablename__ = 'govinfo_bills'

    id = Column(Integer, primary_key=True, autoincrement=True)
    congress = Column(Integer, nullable=False)
    bill_number = Column(String(64), nullable=False)
    bill_type = Column(String(8))
    title = Column(Text)
    introduced_date = Column(DateTime(timezone=True))
    sponsor_name = Column(String(255))
    sponsor_party = Column(String(8))
    sponsor_state = Column(String(8))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('congress', 'bill_number', name='uq_govinfo_bill'),
    )


class GovInfoBillText(Base):
    """GovInfo bill text staging table"""
    __tablename__ = 'govinfo_bill_texts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    govinfo_bill_id = Column(Integer, ForeignKey('govinfo_bills.id', ondelete='CASCADE'), nullable=False)
    version_id = Column(String(128), nullable=False)
    text_format = Column(String(16))  # 'html' or 'plain'
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class GovInfoBillAction(Base):
    """GovInfo bill action staging table"""
    __tablename__ = 'govinfo_bill_actions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    govinfo_bill_id = Column(Integer, ForeignKey('govinfo_bills.id', ondelete='CASCADE'), nullable=False)
    action_date = Column(DateTime(timezone=True))
    chamber = Column(String(16))
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class GovInfoBillCosponsor(Base):
    """GovInfo bill cosponsor staging table"""
    __tablename__ = 'govinfo_bill_cosponsors'

    id = Column(Integer, primary_key=True, autoincrement=True)
    govinfo_bill_id = Column(Integer, ForeignKey('govinfo_bills.id', ondelete='CASCADE'), nullable=False)
    cosponsor_name = Column(String(255))
    cosponsor_party = Column(String(8))
    cosponsor_state = Column(String(8))
    is_lead_cosponsor = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class GovInfoBillCommittee(Base):
    """GovInfo bill committee staging table"""
    __tablename__ = 'govinfo_bill_committees'

    id = Column(Integer, primary_key=True, autoincrement=True)
    govinfo_bill_id = Column(Integer, ForeignKey('govinfo_bills.id', ondelete='CASCADE'), nullable=False)
    committee_name = Column(String(200))
    committee_chamber = Column(String(20))
    subcommittee_name = Column(String(200))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class GovInfoBillSubject(Base):
    """GovInfo bill subject staging table"""
    __tablename__ = 'govinfo_bill_subjects'

    id = Column(Integer, primary_key=True, autoincrement=True)
    govinfo_bill_id = Column(Integer, ForeignKey('govinfo_bills.id', ondelete='CASCADE'), nullable=False)
    subject = Column(String(200))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class GovInfoDocRefs(Base):
    """GovInfo document references staging table"""
    __tablename__ = 'govinfo_doc_refs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    govinfo_bill_id = Column(Integer, ForeignKey('govinfo_bills.id', ondelete='CASCADE'), nullable=False)
    ref_type = Column(String(50))
    ref_value = Column(String(200))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ===========================================
# OPENSTATES API MODELS
# ===========================================

class OpenStatesBill(Base):
    """OpenStates bill staging table"""
    __tablename__ = 'openstates_bills'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    state = Column(String(2), nullable=False)  # Two-letter state code
    session = Column(String(50), nullable=False)  # Legislative session
    bill_id = Column(String(50), nullable=False)  # OpenStates bill identifier
    title = Column(Text)
    classification = Column(JSONB)  # Array of bill types
    subject = Column(JSONB)  # Array of subjects
    abstract = Column(Text)
    first_action_date = Column(Date)
    latest_action_date = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('state', 'session', 'bill_id', name='uq_openstates_bill'),
    )


class OpenStatesBillAction(Base):
    """OpenStates bill actions staging table"""
    __tablename__ = 'openstates_bill_actions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    openstates_bill_id = Column(UUID(as_uuid=True), ForeignKey('openstates_bills.id', ondelete='CASCADE'), nullable=False)
    date = Column(Date, nullable=False)
    description = Column(Text)
    chamber = Column(String(20))
    classification = Column(JSONB)  # Array of action types
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class OpenStatesLegislator(Base):
    """OpenStates legislator staging table"""
    __tablename__ = 'openstates_legislators'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    state = Column(String(2), nullable=False)
    legislator_id = Column(String(50), nullable=False)  # OpenStates legislator ID
    name = Column(String(255))
    party = Column(String(20))
    chamber = Column(String(20))
    district = Column(String(50))
    email = Column(String(255))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('state', 'legislator_id', name='uq_openstates_legislator'),
    )


class OpenStatesCommittee(Base):
    """OpenStates committee staging table"""
    __tablename__ = 'openstates_committees'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    state = Column(String(2), nullable=False)
    committee_id = Column(String(50), nullable=False)
    name = Column(String(255))
    chamber = Column(String(20))
    parent_id = Column(String(50))  # Parent committee ID
    members = Column(JSONB)  # Array of member objects
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('state', 'committee_id', name='uq_openstates_committee'),
    )


# ===========================================
# OPENLEGISLATURE (NY STATE LBDC) MODELS
# ===========================================

class NYBill(Base):
    """NY State Legislature bill staging table"""
    __tablename__ = 'ny_bills'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    print_no = Column(String(20), nullable=False)
    session_year = Column(Integer, nullable=False)
    title = Column(Text)
    summary = Column(Text)
    sponsor = Column(String(255))
    co_sponsors = Column(JSONB)  # Array of co-sponsor names
    status = Column(String(100))
    committee = Column(String(255))
    law_code = Column(String(50))
    law_section = Column(String(100))
    full_text_url = Column(String(500))
    amendment_text_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('print_no', 'session_year', name='uq_ny_bill'),
    )


class NYBillAction(Base):
    """NY State Legislature bill actions staging table"""
    __tablename__ = 'ny_bill_actions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ny_bill_id = Column(UUID(as_uuid=True), ForeignKey('ny_bills.id', ondelete='CASCADE'), nullable=False)
    date = Column(Date)
    text = Column(Text)
    chamber = Column(String(20))
    sequence_no = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class NYMember(Base):
    """NY State Legislature member staging table"""
    __tablename__ = 'ny_members'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    member_id = Column(String(50), nullable=False)
    session_year = Column(Integer, nullable=False)
    full_name = Column(String(255))
    first_name = Column(String(100))
    last_name = Column(String(100))
    party = Column(String(20))
    chamber = Column(String(20))
    district = Column(String(10))
    email = Column(String(255))
    active = Column(Boolean, default=True)
    committees = Column(JSONB)  # Array of committee memberships
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('member_id', 'session_year', name='uq_ny_member'),
    )


class NYCommittee(Base):
    """NY State Legislature committee staging table"""
    __tablename__ = 'ny_committees'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    committee_name = Column(String(255), nullable=False)
    chamber = Column(String(20), nullable=False)
    session_year = Column(Integer, nullable=False)
    chair = Column(String(255))
    members = Column(JSONB)  # Array of member names
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('committee_name', 'chamber', 'session_year', name='uq_ny_committee'),
    )


# ===========================================
# UTILITY FUNCTIONS
# ===========================================

def get_engine(database_url: str = None):
    """Get SQLAlchemy engine"""
    if database_url is None:
        from database_connection import get_connection_string
        database_url = get_connection_string()

    return create_engine(database_url)


def get_session(engine=None):
    """Get SQLAlchemy session"""
    if engine is None:
        engine = get_engine()

    Session = sessionmaker(bind=engine)
    return Session()


def create_tables(engine=None):
    """Create all tables"""
    if engine is None:
        engine = get_engine()

    Base.metadata.create_all(engine)


def drop_tables(engine=None):
    """Drop all tables"""
    if engine is None:
        engine = get_engine()

    Base.metadata.drop_all(engine)


# ===========================================
# CONVENIENCE FUNCTIONS FOR INGESTION
# ===========================================

def upsert_bill(session, bill_data: dict):
    """Upsert a bill record using ON CONFLICT"""
    from sqlalchemy.dialects.postgresql import insert

    stmt = insert(Bill).values(**bill_data)
    stmt = stmt.on_conflict_do_update(
        constraint='uq_bill_print_no_session',
        set_={k: v for k, v in bill_data.items() if k not in ['bill_print_no', 'bill_session_year']}
    )
    result = session.execute(stmt)
    return result


def upsert_bill_sponsor(session, sponsor_data: dict):
    """Upsert a bill sponsor record"""
    from sqlalchemy.dialects.postgresql import insert

    stmt = insert(BillSponsor).values(**sponsor_data)
    stmt = stmt.on_conflict_do_nothing()  # Skip if already exists
    result = session.execute(stmt)
    return result


def upsert_bill_action(session, action_data: dict):
    """Upsert a bill action record"""
    from sqlalchemy.dialects.postgresql import insert

    stmt = insert(BillAction).values(**action_data)
    stmt = stmt.on_conflict_do_nothing()  # Skip if already exists
    result = session.execute(stmt)
    return result


def upsert_committee(session, committee_data: dict):
    """Upsert a committee record"""
    from sqlalchemy.dialects.postgresql import insert

    stmt = insert(Committee).values(**committee_data)
    stmt = stmt.on_conflict_do_update(
        constraint='uq_committee_name_chamber',
        set_={k: v for k, v in committee_data.items() if k not in ['name', 'chamber']}
    )
    result = session.execute(stmt)
    return result


def upsert_committee_member(session, member_data: dict):
    """Upsert a committee member record"""
    from sqlalchemy.dialects.postgresql import insert

    stmt = insert(CommitteeMember).values(**member_data)
    stmt = stmt.on_conflict_do_nothing()  # Skip if already exists
    result = session.execute(stmt)
    return result


def upsert_federal_member(session, member_data: dict):
    """Upsert a federal member record"""
    from sqlalchemy.dialects.postgresql import insert

    stmt = insert(FederalMember).values(**member_data)
    stmt = stmt.on_conflict_do_update(
        index_elements=['bioguide_id'],  # Unique constraint on bioguide_id
        set_={k: v for k, v in member_data.items() if k != 'bioguide_id'}
    )
    result = session.execute(stmt)
    return result


def store_raw_payload(session, ingestion_type: str, record_id: str, payload: dict):
    """Store raw payload for debugging"""
    from sqlalchemy.dialects.postgresql import insert

    raw_data = {
        'ingestion_type': ingestion_type,
        'record_id': record_id,
        'payload': payload
    }

    stmt = insert(RawPayload).values(**raw_data)
    stmt = stmt.on_conflict_do_update(
        constraint='uq_raw_payload',
        set_={'payload': payload, 'processed_at': func.now()}
    )
    result = session.execute(stmt)
    return result


# ===========================================
# GOVINFO STAGING TABLE UPSERTS
# ===========================================

def upsert_govinfo_bill(session, bill_data: dict):
    """Upsert GovInfo bill record"""
    from sqlalchemy.dialects.postgresql import insert

    stmt = insert(GovInfoBill).values(**bill_data)
    stmt = stmt.on_conflict_do_update(
        constraint='uq_govinfo_bill',
        set_={k: v for k, v in bill_data.items() if k not in ['congress', 'bill_number']}
    )
    result = session.execute(stmt)
    return result


def upsert_govinfo_bill_action(session, action_data: dict):
    """Upsert GovInfo bill action record"""
    from sqlalchemy.dialects.postgresql import insert

    stmt = insert(GovInfoBillAction).values(**action_data)
    stmt = stmt.on_conflict_do_nothing()  # Skip if already exists
    result = session.execute(stmt)
    return result


def upsert_govinfo_bill_cosponsor(session, cosponsor_data: dict):
    """Upsert GovInfo bill cosponsor record"""
    from sqlalchemy.dialects.postgresql import insert

    stmt = insert(GovInfoBillCosponsor).values(**cosponsor_data)
    stmt = stmt.on_conflict_do_nothing()  # Skip if already exists
    result = session.execute(stmt)
    return result


# ===========================================
# OPENSTATES API UPSERTS
# ===========================================

def upsert_openstates_bill(session, bill_data: dict):
    """Upsert OpenStates bill record"""
    from sqlalchemy.dialects.postgresql import insert

    stmt = insert(OpenStatesBill).values(**bill_data)
    stmt = stmt.on_conflict_do_update(
        constraint='uq_openstates_bill',
        set_={k: v for k, v in bill_data.items() if k not in ['state', 'session', 'bill_id']}
    )
    result = session.execute(stmt)
    return result


def upsert_openstates_legislator(session, legislator_data: dict):
    """Upsert OpenStates legislator record"""
    from sqlalchemy.dialects.postgresql import insert

    stmt = insert(OpenStatesLegislator).values(**legislator_data)
    stmt = stmt.on_conflict_do_update(
        constraint='uq_openstates_legislator',
        set_={k: v for k, v in legislator_data.items() if k not in ['state', 'legislator_id']}
    )
    result = session.execute(stmt)
    return result


def upsert_openstates_committee(session, committee_data: dict):
    """Upsert OpenStates committee record"""
    from sqlalchemy.dialects.postgresql import insert

    stmt = insert(OpenStatesCommittee).values(**committee_data)
    stmt = stmt.on_conflict_do_update(
        constraint='uq_openstates_committee',
        set_={k: v for k, v in committee_data.items() if k not in ['state', 'committee_id']}
    )
    result = session.execute(stmt)
    return result


# ===========================================
# OPENLEGISLATURE (NY STATE) UPSERTS
# ===========================================

def upsert_ny_bill(session, bill_data: dict):
    """Upsert NY State bill record"""
    from sqlalchemy.dialects.postgresql import insert

    stmt = insert(NYBill).values(**bill_data)
    stmt = stmt.on_conflict_do_update(
        constraint='uq_ny_bill',
        set_={k: v for k, v in bill_data.items() if k not in ['print_no', 'session_year']}
    )
    result = session.execute(stmt)
    return result


def upsert_ny_member(session, member_data: dict):
    """Upsert NY State member record"""
    from sqlalchemy.dialects.postgresql import insert

    stmt = insert(NYMember).values(**member_data)
    stmt = stmt.on_conflict_do_update(
        constraint='uq_ny_member',
        set_={k: v for k, v in member_data.items() if k not in ['member_id', 'session_year']}
    )
    result = session.execute(stmt)
    return result


def upsert_ny_committee(session, committee_data: dict):
    """Upsert NY State committee record"""
    from sqlalchemy.dialects.postgresql import insert

    stmt = insert(NYCommittee).values(**committee_data)
    stmt = stmt.on_conflict_do_update(
        constraint='uq_ny_committee',
        set_={k: v for k, v in committee_data.items() if k not in ['committee_name', 'chamber', 'session_year']}
    )
    result = session.execute(stmt)
    return result


# ===========================================
# ADDITIONAL LEGISLATIVE UPSERTS
# ===========================================

def upsert_bill_amendment(session, amendment_data: dict):
    """Upsert bill amendment record"""
    from sqlalchemy.dialects.postgresql import insert

    stmt = insert(BillAmendment).values(**amendment_data)
    stmt = stmt.on_conflict_do_update(
        constraint='uq_bill_amendment',
        set_={k: v for k, v in amendment_data.items() if k not in ['bill_print_no', 'bill_session_year', 'bill_amend_version']}
    )
    result = session.execute(stmt)
    return result


def upsert_bill_text(session, text_data: dict):
    """Upsert bill text record"""
    from sqlalchemy.dialects.postgresql import insert

    stmt = insert(BillText).values(**text_data)
    stmt = stmt.on_conflict_do_update(
        constraint='uq_bill_text',
        set_={k: v for k, v in text_data.items() if k not in ['bill_print_no', 'bill_session_year', 'bill_amend_version']}
    )
    result = session.execute(stmt)
    return result


def upsert_session_member(session, member_data: dict):
    """Upsert session member record"""
    from sqlalchemy.dialects.postgresql import insert

    stmt = insert(SessionMember).values(**member_data)
    stmt = stmt.on_conflict_do_update(
        constraint='uq_session_member',
        set_={k: v for k, v in member_data.items() if k not in ['member_id', 'session_year']}
    )
    result = session.execute(stmt)
    return result


def upsert_bill_vote(session, vote_data: dict):
    """Upsert bill vote record"""
    from sqlalchemy.dialects.postgresql import insert

    stmt = insert(BillVote).values(**vote_data)
    stmt = stmt.on_conflict_do_update(
        constraint='uq_bill_vote',
        set_={k: v for k, v in vote_data.items() if k not in ['bill_print_no', 'bill_session_year', 'vote_date', 'sequence_no']}
    )
    result = session.execute(stmt)
    return result


# ===========================================
# TESTING AND UTILITIES
# ===========================================

if __name__ == '__main__':
    # Test database connection and table creation
    print("Testing OpenLegislation Database Models")
    print("=" * 45)

    try:
        engine = get_engine()
        print("✅ Database engine created")

        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")

        # Create tables
        create_tables(engine)
        print("✅ Tables created successfully")

        # Test session
        session = get_session(engine)
        print("✅ Database session created")

        # Test basic query
        bill_count = session.query(Bill).count()
        print(f"✅ Bills table accessible (count: {bill_count})")

        session.close()
        print("✅ Database session closed")

        print("\n🎉 Database models test completed successfully!")

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
