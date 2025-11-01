package gov.nysenate.openleg.processors.federal.bill;

import gov.nysenate.openleg.legislation.SessionYear;
import gov.nysenate.openleg.legislation.bill.*;
import gov.nysenate.openleg.legislation.committee.Chamber;
import gov.nysenate.openleg.processors.ParseError;
import gov.nysenate.openleg.processors.bill.LegDataFragment;
import gov.nysenate.openleg.processors.bill.LegDataFragmentType;
import gov.nysenate.openleg.processors.bill.AbstractBillProcessor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.SAXException;

import javax.xml.xpath.XPathExpressionException;
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
        try {
            Document doc = xmlHelper.parse(federalFile.getFile());
            Bill bill = mapToBill(doc, federalFile, fragment);
            // Persistence via base class cache
            billIngestCache.set(bill.getBaseBillId(), bill, fragment);
            logger.info("Processed federal bill: {}", federalFile.getFileName());
        } catch (IOException | SAXException | XPathExpressionException e) {
            logger.error("Error processing federal bill XML: {}", federalFile.getFileName(), e);
            throw new ParseError("Failed to process federal bill XML: " + federalFile.getFileName(), e);
        } finally {
            checkIngestCache();
        }
    }

    private Bill mapToBill(Document doc, FederalBillXmlFile sourceFile, LegDataFragment fragment) 
            throws XPathExpressionException {
        // Parse bill node
        Node billNode = xmlHelper.getNode("//bill", doc);
        if (billNode == null) {
            throw new ParseError("No bill element found in XML");
        }

        // Extract legislation ID
        Node legIdNode = xmlHelper.getNode("legislation-id", billNode);
        int congress = xmlHelper.getInteger("congress", legIdNode);
        String type = xmlHelper.getString("type", legIdNode).trim().toUpperCase();
        String number = xmlHelper.getString("number", legIdNode).trim();

        // Determine chamber and create bill ID
        Chamber chamber = type.startsWith("H") ? Chamber.HOUSE : Chamber.SENATE;
        int sessionYear = congressToSessionYear(congress);
        SessionYear session = SessionYear.of(sessionYear);
        BaseBillId baseBillId = new BaseBillId(type + number, session);

        Bill bill = getOrCreateBaseBill(new BillId(baseBillId, Version.ORIGINAL), fragment);
        
        // Set title
        String title = xmlHelper.getString("official-title", billNode);
        if (title != null && !title.isEmpty()) {
            setTitle(bill, title, fragment);
        }

        // Parse sponsors
        NodeList sponsorNodes = xmlHelper.getNodeList("sponsor", billNode);
        if (sponsorNodes.getLength() > 0) {
            Element sponsorElement = (Element) sponsorNodes.item(0);
            String fullName = xmlHelper.getString("full-name", sponsorElement);
            if (fullName != null && !fullName.isEmpty()) {
                handlePrimaryMemberParsing(bill, fullName, session);
            }
        }

        // Parse actions
        NodeList actionNodes = xmlHelper.getNodeList("actions/action", billNode);
        List<BillAction> actions = new ArrayList<>();
        for (int i = 0; i < actionNodes.getLength(); i++) {
            Element actionElement = (Element) actionNodes.item(i);
            String dateStr = xmlHelper.getString("date", actionElement);
            String chamberStr = xmlHelper.getString("chamber", actionElement);
            String text = xmlHelper.getString("text", actionElement);
            
            if (dateStr != null && !dateStr.isEmpty()) {
                LocalDate date = LocalDate.parse(dateStr, DATE_FORMAT);
                Chamber actionChamber = "HOUSE".equalsIgnoreCase(chamberStr) ? Chamber.HOUSE : Chamber.SENATE;
                BillId billId = new BillId(baseBillId, Version.ORIGINAL);
                BillAction action = new BillAction(date, text, actionChamber, i, billId, "FEDERAL");
                actions.add(action);
            }
        }
        if (!actions.isEmpty()) {
            bill.setActions(actions);
        }

        // Parse text
        Node textNode = xmlHelper.getNode("text", billNode);
        if (textNode != null) {
            String textContent = textNode.getTextContent();
            if (textContent != null && !textContent.isEmpty()) {
                BillAmendment amendment = bill.getAmendment(Version.ORIGINAL);
                amendment.setFullText(PLAIN, textContent.trim());
            }
        }

        // Set federal metadata
        bill.setModifiedDateTime(sourceFile.getPublishedDateTime());
        bill.setFederalCongress(congress);
        bill.setFederalSource("govinfo");
        
        return bill;
    }

    private int congressToSessionYear(int congress) {
        return 1789 + (congress - 1) * 2; // Starting year of congress, e.g., 119th = 2025
    }
}