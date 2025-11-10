"""SQLAlchemy table metadata for normalized ingestion tables."""
from __future__ import annotations

from sqlalchemy import JSON, Column, Date, DateTime, Integer, MetaData, String, Table, UniqueConstraint

metadata = MetaData(schema="public")

openstates_bills = Table(
    "openstates_bills",
    metadata,
    Column("id", String, primary_key=True),
    Column("identifier", String, nullable=False),
    Column("legislative_session", String, nullable=False),
    Column("title", String, nullable=False),
    Column("classification", JSON, nullable=False),
    Column("subject", JSON, nullable=False),
    Column("first_action_date", Date),
    Column("last_action_date", Date),
    Column("created_at", DateTime),
    Column("updated_at", DateTime),
    Column("primary_sponsor", String),
    Column("source_updated", DateTime),
    Column("retrieved_at", DateTime, nullable=False),
    Column("raw_payload", JSON),
    UniqueConstraint("identifier", "legislative_session", name="uq_openstates_bill_session"),
)

openstates_people = Table(
    "openstates_people",
    metadata,
    Column("id", String, primary_key=True),
    Column("name", String, nullable=False),
    Column("given_name", String),
    Column("family_name", String),
    Column("party", String),
    Column("chamber", String),
    Column("state", String),
    Column("district", String),
    Column("email", String),
    Column("retrieved_at", DateTime, nullable=False),
    Column("raw_payload", JSON),
)

openstates_votes = Table(
    "openstates_votes",
    metadata,
    Column("id", String, primary_key=True),
    Column("bill_id", String, nullable=False),
    Column("organization", String),
    Column("motion_text", String),
    Column("motion_classification", JSON, nullable=False),
    Column("result", String),
    Column("start_date", DateTime),
    Column("counts", JSON, nullable=False),
    Column("retrieved_at", DateTime, nullable=False),
    Column("raw_payload", JSON),
)

congress_bills = Table(
    "congress_bills",
    metadata,
    Column("bill_id", String, primary_key=True),
    Column("congress", String, nullable=False),
    Column("bill_type", String, nullable=False),
    Column("bill_number", String, nullable=False),
    Column("title", String),
    Column("sponsor_bioguide_id", String),
    Column("introduced_date", Date),
    Column("latest_action_date", Date),
    Column("latest_action_text", String),
    Column("subjects", JSON, nullable=False),
    Column("source_updated", DateTime),
    Column("retrieved_at", DateTime, nullable=False),
    Column("raw_payload", JSON),
)

congress_members = Table(
    "congress_members",
    metadata,
    Column("bioguide_id", String, primary_key=True),
    Column("first_name", String, nullable=False),
    Column("last_name", String, nullable=False),
    Column("party", String),
    Column("chamber", String),
    Column("state", String),
    Column("district", String),
    Column("start_date", Date),
    Column("end_date", Date),
    Column("source_updated", DateTime),
    Column("retrieved_at", DateTime, nullable=False),
    Column("raw_payload", JSON),
)

congress_votes = Table(
    "congress_votes",
    metadata,
    Column("id", String, primary_key=True),
    Column("chamber", String, nullable=False),
    Column("congress", String, nullable=False),
    Column("session", String),
    Column("roll_call", String, nullable=False),
    Column("vote_date", DateTime, nullable=False),
    Column("question", String),
    Column("description", String),
    Column("result", String),
    Column("yeas", Integer, nullable=False),
    Column("nays", Integer, nullable=False),
    Column("present", Integer, nullable=False),
    Column("not_voting", Integer, nullable=False),
    Column("retrieved_at", DateTime, nullable=False),
    Column("raw_payload", JSON),
    UniqueConstraint("chamber", "congress", "session", "roll_call", name="uq_congress_vote"),
)

govinfo_packages = Table(
    "govinfo_packages",
    metadata,
    Column("package_id", String, primary_key=True),
    Column("title", String),
    Column("collection_code", String),
    Column("summary", String),
    Column("congress", String),
    Column("download", String),
    Column("last_modified", DateTime),
    Column("retrieved_at", DateTime, nullable=False),
    Column("raw_payload", JSON),
)

govinfo_downloads = Table(
    "govinfo_downloads",
    metadata,
    Column("package_id", String, nullable=False),
    Column("format", String, nullable=False),
    Column("url", String, nullable=False),
    Column("size", Integer),
    Column("retrieved_at", DateTime, nullable=False),
    Column("raw_payload", JSON),
    UniqueConstraint("package_id", "format", name="uq_govinfo_download"),
)

openleg_bills = Table(
    "openleg_bills",
    metadata,
    Column("print_no", String, primary_key=True),
    Column("session", String, nullable=False),
    Column("title", String),
    Column("sponsor_member_id", Integer),
    Column("summary", String),
    Column("law_section", String),
    Column("last_status", String),
    Column("last_status_date", Date),
    Column("committee_name", String),
    Column("cosponsors", JSON, nullable=False),
    Column("source_updated", DateTime),
    Column("retrieved_at", DateTime, nullable=False),
    Column("raw_payload", JSON),
)

openleg_agendas = Table(
    "openleg_agendas",
    metadata,
    Column("agenda_id", String, primary_key=True),
    Column("meeting_date", Date),
    Column("committee_name", String),
    Column("location", String),
    Column("notes", String),
    Column("bills", JSON, nullable=False),
    Column("published_at", DateTime),
    Column("retrieved_at", DateTime, nullable=False),
    Column("raw_payload", JSON),
)

