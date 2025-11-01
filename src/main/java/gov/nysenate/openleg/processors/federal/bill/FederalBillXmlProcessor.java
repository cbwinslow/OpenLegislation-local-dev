package gov.nysenate.openleg.processors.federal.bill;

import gov.nysenate.openleg.legislation.bill.*;
import gov.nysenate.openleg.legislation.committee.Chamber;
import gov.nysenate.openleg.processors.ParseError;
import gov.nysenate.openleg.processors.bill.LegDataFragment;
import gov.nysenate.openleg.processors.bill.LegDataFragmentType;
import gov.nysenate.openleg.processors.bill.AbstractBillProcessor;
import gov.nysenate.openleg.legislation.member.Member;
import gov.nysenate.openleg.legislation.member.SessionMember;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.NodeList;
import org.xml.sax.SAXException;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import java.io.File;
import java.io.IOException;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

import static gov.nysenate.openleg.legislation.bill.BillTextFormat.PLAIN;

/**
 * Processor for federal bill XML from congress.gov/govinfo.
 * Parses XML to Bill model using DOM parsing.
 */
public class FederalBillXmlProcessor extends AbstractBillProcessor {

    private static final Logger logger = LoggerFactory.getLogger(FederalBillXmlProcessor.class);

    private static final DateTimeFormatter DATE_FORMAT = DateTimeFormatter.ofPattern("yyyy-MM-dd");

    @Override
    public LegDataFragmentType getSupportedType() {
        return LegDataFragmentType.BILL;
    }

    @Override
    public void process(LegDataFragment fragment) {
        FederalBillXmlFile federalFile = (FederalBillXmlFile) fragment.getSourceFile();
        File xmlFile = federalFile.getFile();
        try {
            Document doc = parseXml(xmlFile);
            Bill bill = mapToBill(doc, federalFile);
            // Persistence via base class or DAO
            super.saveLegData(bill);
            logger.info("Processed federal bill: {}", federalFile.getFileName());
        } catch (Exception e) {
            logger.error("Error processing federal bill XML: {}", federalFile.getFileName(), e);
            throw new ParseError("Failed to process federal bill XML: " + federalFile.getFileName(), e);
        }
    }

    Document parseXml(File xmlFile) throws Exception {
        DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
        DocumentBuilder builder = factory.newDocumentBuilder();
        return builder.parse(xmlFile);
    }

    Bill mapToBill(Document doc, FederalBillXmlFile sourceFile) {
        Element root = doc.getDocumentElement();
        
        // Extract congress number and bill type from XML
        int congress = Integer.parseInt(getElementTextContent(root, "congress"));
        String type = getElementTextContent(root, "type");
        String number = getElementTextContent(root, "number");
        
        Chamber chamber = type.startsWith("H") ? Chamber.HOUSE : Chamber.SENATE;
        BillType billType = BillType.fromString(type.toUpperCase());
        int sessionYear = congressToSessionYear(congress);
        SessionYear session = SessionYear.of(sessionYear);
        BaseBillId baseBillId = new BaseBillId(number, session);

        Bill bill = new Bill(baseBillId);
        bill.setTitle(getElementTextContent(root, "title"));

        // Sponsors
        List<BillSponsor> sponsors = new ArrayList<>();
        NodeList sponsorNodes = root.getElementsByTagName("sponsor");
        for (int i = 0; i < sponsorNodes.getLength(); i++) {
            Element sponsorEl = (Element) sponsorNodes.item(i);
            String name = getElementTextContent(sponsorEl, "fullName");
            String party = getElementTextContent(sponsorEl, "party");
            Member member = new Member("Federal Sponsor", "Doe", "John", null); // Map from bioguide if available
            SessionMember sessionMember = new SessionMember(0, member, "SPONSOR", session, null, true);
            BillSponsor sponsor = new BillSponsor(sessionMember);
            sponsors.add(sponsor);
        }
        bill.sponsors = sponsors;

        // Actions
        List<BillAction> actions = new ArrayList<>();
        NodeList actionNodes = root.getElementsByTagName("action");
        for (int i = 0; i < actionNodes.getLength(); i++) {
            Element actionEl = (Element) actionNodes.item(i);
            String dateStr = getElementTextContent(actionEl, "date");
            if (dateStr != null && !dateStr.isEmpty()) {
                LocalDate date = LocalDate.parse(dateStr, DATE_FORMAT);
                Chamber actionChamber = "HOUSE".equals(getElementTextContent(actionEl, "chamber")) ? Chamber.HOUSE : Chamber.SENATE;
                String text = getElementTextContent(actionEl, "text");
                BillId billId = new BillId(baseBillId, Version.ORIGINAL);
                BillAction action = new BillAction(date, text, actionChamber, i, billId, "UNKNOWN");
                actions.add(action);
            }
        }
        bill.actions = actions;

        // Text
        BillText billText = new BillText();
        StringBuilder textBuilder = new StringBuilder();
        NodeList textNodes = root.getElementsByTagName("text");
        for (int i = 0; i < textNodes.getLength(); i++) {
            Element textEl = (Element) textNodes.item(i);
            textBuilder.append(textEl.getTextContent()).append("\n");
        }
        billText.setText(PLAIN, textBuilder.toString());
        bill.setText(billText);

        bill.setOllaDate(sourceFile.getPublishedDateTime());
        bill.setFederalCongress(congress);
        bill.setFederalSource("govinfo");
        return bill;
    }
    
    private String getElementTextContent(Element parent, String tagName) {
        NodeList nodeList = parent.getElementsByTagName(tagName);
        if (nodeList.getLength() > 0) {
            return nodeList.item(0).getTextContent();
        }
        return null;
    }

    private int congressToSessionYear(int congress) {
        return 1789 + (congress - 1) * 2; // Starting year of congress, e.g., 119th = 2025
    }
}