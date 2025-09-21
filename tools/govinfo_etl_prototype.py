"""Prototype ETL: parse a govinfo bill XML (string) into Pydantic model and print SQL INSERTs.

This is a prototype for quick iteration; not intended for production. It uses the Pydantic models under `tools/govinfo_pydantic_models.py`.
"""
from lxml import etree
from tools.govinfo_pydantic_models import GovInfoBill, GovInfoSponsor, GovInfoAction, GovInfoBillText
from datetime import datetime


def parse_govinfo_bill(xml_text: str) -> GovInfoBill:
    root = etree.fromstring(xml_text.encode('utf-8'))
    # Representative example parsing — real XPath may differ
    bill_num = root.findtext('.//billNumber') or root.findtext('.//legislativeIdentifier') or 'UNKNOWN'
    congress_text = root.findtext('.//congress') or root.get('congress')
    congress = int(congress_text) if congress_text and congress_text.isdigit() else 119
    title = root.findtext('.//officialTitle') or root.findtext('.//title') or ''
    introduced = root.findtext('.//introducedDate')
    introduced_dt = datetime.fromisoformat(introduced) if introduced else None

    sponsor_name = root.findtext('.//sponsor/name') or root.findtext('.//sponsor')
    sponsor = GovInfoSponsor(name=sponsor_name) if sponsor_name else None

    # Actions
    actions = []
    for a in root.findall('.//actions/action'):
        date_text = a.findtext('date')
        dt = datetime.fromisoformat(date_text) if date_text else None
        desc = a.findtext('text') or (a.text or '').strip()
        actions.append(GovInfoAction(date=dt or datetime.now(), description=desc))

    # Texts
    texts = []
    for t in root.findall('.//textVersions/textVersion'):
        vid = t.findtext('versionId') or 'v'
        fmt = t.findtext('format') or 'html'
        content = t.findtext('content') or t.findtext('href') or ''
        texts.append(GovInfoBillText(version_id=vid, html=content if fmt=='html' else None, plain_text=content if fmt!='html' else None))

    model = GovInfoBill(congress=congress, bill_number=bill_num, title=title, introduced_date=introduced_dt, sponsor=sponsor, actions=actions, texts=texts)
    return model


if __name__ == '__main__':
    sample = '<bill><congress>119</congress><billNumber>H.R.1</billNumber><officialTitle>Example Bill</officialTitle><sponsor><name>Rep. Example</name></sponsor></bill>'
    b = parse_govinfo_bill(sample)
    print(b.json(indent=2))
