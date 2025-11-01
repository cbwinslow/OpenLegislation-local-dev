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
        FederalBillXmlFile federalFile = (FederalBillXmlFile) fragment.getParentLegDataFile();
        File xmlFile = federalFile.getFile();
        try {
            Document doc = parseXml(xmlFile);
            // TODO: Implement full federal bill processing when infrastructure is ready
            // Bill bill = mapToBill(doc, federalFile);
            // super.saveLegData(bill);
            logger.info("Processed federal bill XML (stub): {}", federalFile.getFileName());
        } catch (Exception e) {
            logger.error("Error processing federal bill XML: {}", federalFile.getFileName(), e);
            throw new ParseError("Failed to process federal bill XML: " + federalFile.getFileName(), e);
        }
    }

    private Document parseXml(File xmlFile) throws ParserConfigurationException, SAXException, IOException {
        DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
        factory.setNamespaceAware(true);
        DocumentBuilder builder = factory.newDocumentBuilder();
        return builder.parse(xmlFile);
    }

    /* TODO: Implement when federal bill infrastructure is ready
    private Bill mapToBill(Document doc, FederalBillXmlFile sourceFile) {
        Element root = doc.getDocumentElement();
        
        // Parse legislation ID
        Element legIdElement = (Element) root.getElementsByTagName("legislation-id").item(0);
        int congress = Integer.parseInt(getElementText(legIdElement, "congress"));
        String type = getElementText(legIdElement, "type");
        String number = getElementText(legIdElement, "number");
        Chamber chamber = type.startsWith("H") ? Chamber.HOUSE : Chamber.SENATE;
        BillType billType = BillType.fromString(type.toUpperCase());
        int sessionYear = congressToSessionYear(congress);
        SessionYear session = SessionYear.of(sessionYear);
        BaseBillId baseBillId = new BaseBillId(number, session);

        Bill bill = new Bill(baseBillId);
        
        // Parse title
        NodeList titleNodes = root.getElementsByTagName("official-title");
        if (titleNodes.getLength() > 0) {
            bill.setTitle(titleNodes.item(0).getTextContent());
        }

        // Parse sponsors
        List<BillSponsor> sponsors = new ArrayList<>();
        NodeList sponsorNodes = root.getElementsByTagName("sponsor");
        for (int i = 0; i < sponsorNodes.getLength(); i++) {
            Element sponsorElem = (Element) sponsorNodes.item(i);
            String fullName = getElementText(sponsorElem, "full-name");
            String party = getElementText(sponsorElem, "party");
            // Create placeholder member (would need bioguide lookup in production)
            Member member = new Member("Federal", fullName, "", null);
            SessionMember sessionMember = new SessionMember(0, member, "SPONSOR", session, null, true);
            BillSponsor sponsor = new BillSponsor(sessionMember);
            sponsors.add(sponsor);
        }
        bill.sponsors = sponsors;

        // Parse actions
        List<BillAction> actions = new ArrayList<>();
        NodeList actionNodes = root.getElementsByTagName("action");
        for (int i = 0; i < actionNodes.getLength(); i++) {
            Element actionElem = (Element) actionNodes.item(i);
            String dateStr = getElementText(actionElem, "date");
            String actionChamberStr = getElementText(actionElem, "chamber");
            String text = getElementText(actionElem, "text");
            
            if (dateStr != null && !dateStr.isEmpty()) {
                LocalDate date = LocalDate.parse(dateStr, DATE_FORMAT);
                Chamber actionChamber = "HOUSE".equals(actionChamberStr) ? Chamber.HOUSE : Chamber.SENATE;
                BillId billId = new BillId(baseBillId, Version.ORIGINAL);
                BillAction action = new BillAction(date, text, actionChamber, i, billId, "UNKNOWN");
                actions.add(action);
            }
        }
        bill.actions = actions;

        // Parse text
        BillText billText = new BillText();
        StringBuilder textBuilder = new StringBuilder();
        NodeList textNodes = root.getElementsByTagName("text");
        for (int i = 0; i < textNodes.getLength(); i++) {
            Element textElem = (Element) textNodes.item(i);
            String content = textElem.getTextContent();
            if (content != null) {
                textBuilder.append(content).append("\n");
            }
        }
        billText.setText(PLAIN, textBuilder.toString());
        bill.setText(billText);

        bill.setOllaDate(sourceFile.getPublishedDateTime());
        bill.setFederalCongress(congress);
        bill.setFederalSource("govinfo");
        return bill;
    }

    private int congressToSessionYear(int congress) {
        return 1789 + (congress - 1) * 2; // Starting year of congress, e.g., 119th = 2025
    }
    */

    private String getElementText(Element parent, String tagName) {
        NodeList nodes = parent.getElementsByTagName(tagName);
        if (nodes.getLength() > 0) {
            return nodes.item(0).getTextContent();
        }
        return "";
    }
}