# GovInfo API Mapping to Java Classes & SQL Tables

## Process
1. API Call (RestTemplate): GET /v1/search?collection=BILLS&api_key={key}.
2. JSON Parse (Jackson): Unmarshal to GovInfoResponse (wrapper).
3. Map to Models: GovInfoBillResponse → Bill (setters for title, sponsors).
4. Persist (JPA): BillDao.save(bill) → bill table (e.g., title VARCHAR, sponsors @OneToMany to bill_sponsor).
5. Index (ES): ElasticSearchService.index(bill).

## Collections & Mappings
- **BILLS**: JSON {"results": [{"title": "HR 1", "sponsors": [{"name": "Rep X"}], "actions": [{"text": "Introduced"}]}]} → Bill (billNo="HR1", session=congress, sponsors=BillSponsor, actions=BillAction). SQL: bill (title, congress_number), bill_sponsor, bill_action.
- **BILLSTATUS**: {"status": {"actions": [...]}} → BillAction (append to Bill). SQL: bill_action (text, date).
- **FR**: {"notice": {"title": "Rule", "agency": "DOE"}} → LawDocument (lawId="FR-2025-123", sponsor.orgName="DOE"). SQL: law_document (title, metadata JSONB).
- **CFR**: {"title": {"parts": [{"sections": [{"text": "Reg text"}]}]}} → Law (title/part/section). SQL: law (title VARCHAR, sections JSONB).
- **CREC**: {"record": {"date": "2025-09-25", "debates": "Text"}} → Transcript (date, content). SQL: transcript (date DATE, content TEXT).
- **PLAW/USCODE**: {"law": {"sections": [...]}} → LawDocument. SQL: law_document (sections JSONB).
- **Other (e.g., HEARINGS)**: {"hearing": {"title": "Hearing", "witnesses": [...]}} → New Hearing model. SQL: Extend bill or new hearing table.

## Java Classes
- GovInfoResponse (wrapper): @JsonIgnoreProperties, fields like List<GovInfoBill>.
- Processor: GovInfoApiProcessor (above) unmarshals, maps to Bill/LawDocument.
- SQL: JPA @Table maps (e.g., @Column(name="govinfo_pkg_id") private String pkgId; → transcript.govinfo_pkg_id).

Test: mvn test (add unit for mapping).
