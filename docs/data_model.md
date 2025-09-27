# OpenLegislation Data Model

## Core Entities

### Bill
Primary legislative document entity containing:
- **Identity**: BaseBillId (printNo, sessionYear, version)
- **Metadata**: title, summary, sponsor, status
- **Content**: amendments, actions, texts, committees
- **Lifecycle**: introduced date, milestones, chapter info

**Relationships**:
- 1:N with BillAmendment
- 1:N with BillAction
- 1:N with BillSponsor (additional)
- 1:N with CommitteeVersionId
- 1:N with BillVote

### BillAmendment
Represents a specific version of a bill:
- **Identity**: BillId (extends BaseBillId with version)
- **Content**: fullText, memo, lawCode
- **Status**: publishStatus, sameAs references

**Relationships**:
- N:1 with Bill
- 1:N with BillText
- 1:N with BillAction
- 1:N with BillAmendmentCosponsor

### BillAction
Records legislative actions taken on bills:
- **Identity**: sequenceNo, billId, date
- **Content**: text, chamber
- **Metadata**: timestamp, fragmentId

### BillSponsor
Represents bill sponsorship:
- **Member**: SessionMember reference
- **Type**: rules, budget, or individual member
- **Additional**: multi-sponsor information

## Supporting Entities

### SessionMember
Legislator information for a specific session:
- **Identity**: memberId, sessionYear
- **Person**: name, district, party
- **Role**: chamber, position

### Committee
Committee information:
- **Identity**: name, chamber, sessionYear
- **Members**: chair, members with titles
- **Versions**: historical changes

### BillVote
Roll call vote information:
- **Identity**: BillVoteId (billId, date, sequenceNo)
- **Details**: voteType, committeeName
- **Results**: member votes, totals

## Data Flow

### Ingestion Process
1. **Source Files** → SOBI XML, GovInfo XML
2. **Parsing** → Specialized processors (BillSobiProcessor, GovInfoBillProcessor)
3. **Validation** → Data integrity checks
4. **Storage** → Master tables with change logging
5. **Indexing** → Full-text search, API optimization

### Key Relationships
```
Bill (1) ──── (N) BillAmendment
   │
   ├── (N) BillAction
   ├── (N) BillSponsor
   ├── (N) CommitteeVersionId
   └── (N) BillVote

BillAmendment (1) ──── (N) BillText
SessionMember (1) ──── (N) BillVote
Committee (1) ──── (N) CommitteeMember
```

## Congress.gov Integration Data Model

### GovInfo XML Structure
```xml
<bill>
  <congress>119</congress>
  <billNumber>H.R.1</billNumber>
  <officialTitle>...</officialTitle>
  <sponsor>
    <name>Rep. Example</name>
    <party>D</party>
    <state>NY</state>
  </sponsor>
  <cosponsors>
    <cosponsor>...</cosponsor>
  </cosponsors>
  <actions>
    <action>...</action>
  </actions>
  <textVersions>
    <textVersion>...</textVersion>
  </textVersions>
</bill>
```

### Mapping to OpenLegislation
- **GovInfo Bill** → **Bill** (federal jurisdiction)
- **GovInfo Actions** → **BillAction** (federal chamber)
- **GovInfo Sponsors** → **BillSponsor** (federal members)
- **GovInfo Texts** → **BillText** (federal versions)

### Staging Tables
For safe integration, use govinfo_* staging tables:
- `govinfo_bill` - Raw federal bill metadata
- `govinfo_bill_action` - Federal legislative actions
- `govinfo_bill_cosponsor` - Federal cosponsors
- `govinfo_bill_text` - Federal bill text versions

### Deduplication Strategy
1. **Staging**: Load into govinfo_* tables
2. **Matching**: Compare with existing master data
3. **Merging**: Update or insert into master tables
4. **Linking**: Create jurisdiction-aware relationships

## Data Quality Considerations

### Validation Rules
- Bill numbers must follow jurisdiction patterns
- Dates must be within valid session ranges
- Member references must exist
- Text content must be well-formed

### Integrity Constraints
- Foreign keys to sessions and members
- Unique constraints on bill identities
- Check constraints on enumerated values
- Not null constraints on required fields

### Change Tracking
- All master table changes logged via triggers
- Fragment IDs link changes to source files
- Published timestamps for temporal queries
- Audit trail for compliance
