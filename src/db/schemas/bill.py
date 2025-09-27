from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel


class PersonSchema(BaseModel):
    id: int
    full_name: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]

    class Config:
        orm_mode = True


class MemberSchema(BaseModel):
    id: int
    chamber: str
    incumbent: bool
    full_name: Optional[str]
    person: Optional[PersonSchema]

    class Config:
        orm_mode = True


class SessionMemberSchema(BaseModel):
    id: int
    member_id: int
    lbdc_short_name: str
    session_year: int
    district_code: Optional[int]
    alternate: bool
    member: Optional[MemberSchema]

    class Config:
        orm_mode = True


class BillAmendmentActionSchema(BaseModel):
    bill_print_no: str
    bill_session_year: int
    bill_amend_version: str
    sequence_no: int
    effect_date: Optional[date]
    text: Optional[str]
    chamber: Optional[str]
    created_date_time: datetime

    class Config:
        orm_mode = True


class BillAmendmentPublishStatusSchema(BaseModel):
    bill_print_no: str
    bill_session_year: int
    bill_amend_version: str
    published: bool
    effect_date_time: datetime
    override: bool
    notes: Optional[str]

    class Config:
        orm_mode = True


class BillAmendmentSchema(BaseModel):
    bill_print_no: str
    bill_session_year: int
    bill_amend_version: str
    sponsor_memo: Optional[str]
    act_clause: Optional[str]
    full_text: Optional[str]
    full_text_html: Optional[str]
    stricken: bool
    uni_bill: bool
    law_code: Optional[str]
    law_section: Optional[str]
    created_date_time: datetime
    actions: List[BillAmendmentActionSchema] = []
    publish_statuses: List[BillAmendmentPublishStatusSchema] = []
    cosponsors: List["BillAmendmentCosponsorSchema"] = []
    multi_sponsors: List["BillAmendmentMultiSponsorSchema"] = []

    class Config:
        orm_mode = True


class BillSponsorSchema(BaseModel):
    bill_print_no: str
    bill_session_year: int
    session_member_id: Optional[int]
    budget_bill: bool
    rules_sponsor: bool
    session_member: Optional[SessionMemberSchema]

    class Config:
        orm_mode = True


class BillSponsorAdditionalSchema(BaseModel):
    bill_print_no: str
    bill_session_year: int
    session_member_id: int
    sequence_no: Optional[int]
    session_member: SessionMemberSchema

    class Config:
        orm_mode = True


class BillAmendmentCosponsorSchema(BaseModel):
    bill_print_no: str
    bill_session_year: int
    bill_amend_version: str
    session_member_id: int
    sequence_no: int
    session_member: SessionMemberSchema

    class Config:
        orm_mode = True


class BillAmendmentMultiSponsorSchema(BaseModel):
    bill_print_no: str
    bill_session_year: int
    bill_amend_version: str
    session_member_id: int
    sequence_no: int
    session_member: SessionMemberSchema

    class Config:
        orm_mode = True


class BillSchema(BaseModel):
    bill_print_no: str
    bill_session_year: int
    title: Optional[str]
    summary: Optional[str]
    active_version: str
    active_year: Optional[int]
    status: Optional[str]
    status_date: Optional[date]
    committee_name: Optional[str]
    committee_chamber: Optional[str]
    blurb: Optional[str]
    amendments: List[BillAmendmentSchema] = []
    sponsors: List[BillSponsorSchema] = []
    additional_sponsors: List[BillSponsorAdditionalSchema] = []

    class Config:
        orm_mode = True


BillAmendmentSchema.update_forward_refs(
    BillAmendmentCosponsorSchema=BillAmendmentCosponsorSchema,
    BillAmendmentMultiSponsorSchema=BillAmendmentMultiSponsorSchema,
)

BillSchema.update_forward_refs(
    BillAmendmentSchema=BillAmendmentSchema,
    BillSponsorAdditionalSchema=BillSponsorAdditionalSchema,
)
