package gov.nysenate.openleg.processors.federal.bill;

import gov.nysenate.openleg.legislation.SessionYear;
import gov.nysenate.openleg.legislation.bill.*;
import gov.nysenate.openleg.legislation.committee.Chamber;
import gov.nysenate.openleg.legislation.member.Member;
import gov.nysenate.openleg.legislation.member.Person;
import gov.nysenate.openleg.legislation.member.PersonName;
import gov.nysenate.openleg.legislation.member.SessionMember;
import gov.nysenate.openleg.processors.ParseError;
import gov.nysenate.openleg.processors.bill.LegDataFragment;
import gov.nysenate.openleg.processors.bill.LegDataFragmentType;
import gov.nysenate.openleg.processors.bill.AbstractBillProcessor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
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

/**
 * Processor for federal bill XML from congress.gov/govinfo.
 * Parses XML to Bill model using DOM parsing.
 */
@Service
public class FederalBillXmlProcessor extends AbstractBillProcessor {

    private static final Logger logger = LoggerFactory.getLogger(FederalBillXmlProcessor.class);

    private static final DateTimeFormatter DATE_FORMAT = DateTimeFormatter.ofPattern("yyyy-MM-dd");

    /** Placeholder ID for federal members/persons not yet in the database */
    private static final int PLACEHOLDER_ID = 0;

    private final DocumentBuilder documentBuilder;

    public FederalBillXmlProcessor() throws ParserConfigurationException {
        this.documentBuilder = DocumentBuilderFactory.newInstance().newDocumentBuilder();
    }

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
            Bill bill = mapToBill(doc, federalFile);
            // TODO: Implement persistence - federal bill processing not yet complete
            logger.info("Processed federal bill: {}", federalFile.getFileName());
        } catch (Exception e) {
            logger.error("Error processing federal bill XML: {}", federalFile.getFileName(), e);
            throw new ParseError("Failed to process federal bill XML: " + federalFile.getFileName(), e);
        }
    }

    Document parseXml(File xmlFile) throws SAXException, IOException {
        return documentBuilder.parse(xmlFile);
    }

    private Bill mapToBill(Document doc, FederalBillXmlFile sourceFile) {
        Element root = doc.getDocumentElement();
        
        // Extract legislation ID
        NodeList legIdNodes = root.getElementsByTagName("legislation-id");
        if (legIdNodes.getLength() == 0) {
            throw new ParseError("Missing legislation-id element in federal bill XML");
        }
        Element legIdElement = (Element) legIdNodes.item(0);
        int congress = Integer.parseInt(getElementText(legIdElement, "congress"));
        String type = getElementText(legIdElement, "type");
        String number = getElementText(legIdElement, "number");
        
        // Map federal chambers to NY state chambers (HOUSE->ASSEMBLY, SENATE->SENATE)
        Chamber chamber = type.startsWith("H") ? Chamber.ASSEMBLY : Chamber.SENATE;
        int sessionYear = congressToSessionYear(congress);
        SessionYear session = SessionYear.of(sessionYear);
        BaseBillId baseBillId = new BaseBillId(number, session);

        Bill bill = new Bill(baseBillId);
        
        // Extract title
        String title = getElementText(root, "official-title");
        if (title != null) {
            bill.setTitle(title);
        }

        // Extract sponsor (simplified - create placeholder member)
        NodeList sponsorNodes = root.getElementsByTagName("sponsor");
        if (sponsorNodes.getLength() > 0) {
            Element sponsorElement = (Element) sponsorNodes.item(0);
            String name = getElementText(sponsorElement, "full-name");
            if (name != null) {
                // Create placeholder Person and Member 
                // PersonName: (fullName, prefix, firstName, middleName, lastName, suffix)
                PersonName personName = new PersonName(name, "", name, "", "", "");
                Person person = new Person(PLACEHOLDER_ID, personName, null, null);
                Member member = new Member(person, PLACEHOLDER_ID, chamber, false);
                SessionMember sessionMember = new SessionMember(PLACEHOLDER_ID, member, "FEDERAL_SPONSOR", session, null, false);
                BillSponsor sponsor = new BillSponsor(sessionMember);
                bill.setSponsor(sponsor);
            }
        }

        // Extract actions
        List<BillAction> actions = new ArrayList<>();
        NodeList actionNodes = root.getElementsByTagName("action");
        for (int i = 0; i < actionNodes.getLength(); i++) {
            Element actionElement = (Element) actionNodes.item(i);
            String dateStr = getElementText(actionElement, "date");
            if (dateStr != null) {
                LocalDate date = LocalDate.parse(dateStr, DATE_FORMAT);
                String chamberStr = getElementText(actionElement, "chamber");
                // Map HOUSE to ASSEMBLY for actions
                Chamber actionChamber = "HOUSE".equals(chamberStr) ? Chamber.ASSEMBLY : Chamber.SENATE;
                String text = getElementText(actionElement, "text");
                BillId billId = new BillId(baseBillId, Version.ORIGINAL);
                BillAction action = new BillAction(date, text, actionChamber, i, billId, "UNKNOWN");
                actions.add(action);
            }
        }
        bill.setActions(actions);

        // Extract text and add to amendment
        BillAmendment amendment = bill.getAmendment(Version.ORIGINAL);
        StringBuilder textBuilder = new StringBuilder();
        NodeList textNodes = root.getElementsByTagName("text");
        for (int i = 0; i < textNodes.getLength(); i++) {
            Element textElement = (Element) textNodes.item(i);
            String content = textElement.getTextContent();
            if (content != null) {
                textBuilder.append(content).append("\n");
            }
        }
        BillText billText = new BillText(textBuilder.toString());
        amendment.setBillText(billText);

        bill.setPublishedDateTime(sourceFile.getPublishedDateTime());
        bill.setFederalCongress(congress);
        bill.setFederalSource("govinfo");
        return bill;
    }

    private String getElementText(Element parent, String tagName) {
        NodeList nodes = parent.getElementsByTagName(tagName);
        if (nodes.getLength() > 0) {
            return nodes.item(0).getTextContent();
        }
        return null;
    }

    private int congressToSessionYear(int congress) {
        return 1789 + (congress - 1) * 2; // Starting year of congress, e.g., 119th = 2025
    }
}