package gov.nysenate.openleg.processors.federal.bill;

import gov.nysenate.openleg.common.util.XmlHelper;
import gov.nysenate.openleg.legislation.SessionYear;
import gov.nysenate.openleg.legislation.bill.*;
import gov.nysenate.openleg.legislation.committee.Chamber;
import gov.nysenate.openleg.processors.AbstractLegDataProcessor;
import gov.nysenate.openleg.processors.ParseError;
import gov.nysenate.openleg.processors.bill.LegDataFragment;
import gov.nysenate.openleg.processors.bill.LegDataFragmentType;
import gov.nysenate.openleg.processors.log.DataProcessUnit;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.w3c.dom.Document;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.SAXException;

import javax.xml.xpath.XPathExpressionException;
import java.io.IOException;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

/**
 * Processor for federal bill XML from congress.gov/govinfo.
 * Parses XML to Bill model using DOM parsing with XmlHelper.
 */
@Service
public class FederalBillXmlProcessor extends AbstractLegDataProcessor {

    private static final Logger logger = LoggerFactory.getLogger(FederalBillXmlProcessor.class);

    private static final DateTimeFormatter DATE_FORMAT = DateTimeFormatter.ofPattern("yyyy-MM-dd");

    @Autowired
    public FederalBillXmlProcessor(XmlHelper xmlHelper) {
        this.xmlHelper = xmlHelper;
    }

    public FederalBillXmlProcessor() {
        // Default constructor for testing
    }

    @Override
    public LegDataFragmentType getSupportedType() {
        return LegDataFragmentType.BILL;
    }

    @Override
    public void process(LegDataFragment fragment) {
        logger.info("Processing federal bill fragment: {}", fragment.getFragmentId());
        DataProcessUnit unit = createProcessUnit(fragment);

        try {
            Document doc = xmlHelper.parse(fragment.getText());
            Bill bill = mapToBill(doc, fragment);
            billIngestCache.set(bill.getBaseBillId(), bill, fragment);
            logger.info("Processed federal bill: {}", bill.getBaseBillId());
        } catch (IOException | SAXException | XPathExpressionException e) {
            unit.addException("Error parsing federal bill XML", e);
            throw new ParseError("Failed to process federal bill XML: " + fragment.getFragmentId(), e);
        } finally {
            postDataUnitEvent(unit);
            checkIngestCache();
        }
    }

    /**
     * Maps a parsed XML Document to a Bill object using DOM/XPath parsing.
     */
    private Bill mapToBill(Document doc, LegDataFragment fragment)
            throws XPathExpressionException {

        // Extract bill metadata
        Node billNode = xmlHelper.getNode("//bill", doc);
        if (billNode == null) {
            billNode = xmlHelper.getNode("//billStatus", doc);
        }
        if (billNode == null) {
            throw new ParseError("Cannot find bill or billStatus element in XML");
        }

        // Parse congress number
        int congress = parseCongressNumber(billNode, doc);

        // Parse bill type and number
        String billType = parseBillType(billNode, doc);
        String billNumber = parseBillNumber(billNode, doc);

        // Derive chamber from bill type
        Chamber chamber = deriveChamber(billType);

        // Convert congress to session year
        int sessionYear = congressToSessionYear(congress);
        SessionYear session = SessionYear.of(sessionYear);

        // Create bill ID using print number format (e.g., "HR1234" or "S567")
        String printNo = billType.toUpperCase() + billNumber;
        BaseBillId baseBillId = new BaseBillId(printNo, session);

        // Get or create the bill
        Bill bill = getOrCreateBaseBill(baseBillId, fragment);

        // Set title
        String title = parseTitle(billNode, doc);
        if (title != null && !title.isEmpty()) {
            bill.setTitle(title);
        }

        // Parse and set actions
        List<BillAction> actions = parseActions(billNode, doc, baseBillId, chamber);
        if (!actions.isEmpty()) {
            bill.setActions(actions);
        }

        // Parse and set bill text
        String text = parseText(billNode, doc);
        if (text != null && !text.isEmpty()) {
            BillAmendment amendment = bill.getAmendment(Version.ORIGINAL);
            BillText billText = new BillText(text);
            amendment.setBillText(billText);
        }

        // Set federal-specific fields
        bill.setFederalCongress(congress);
        bill.setFederalSource("govinfo");
        bill.setModifiedDateTime(fragment.getPublishedDateTime());

        return bill;
    }

    private int parseCongressNumber(Node billNode, Document doc) throws XPathExpressionException {
        // Try different XPath expressions for congress number
        String congressStr = xmlHelper.getString("congress", billNode);
        if (congressStr == null || congressStr.isEmpty()) {
            congressStr = xmlHelper.getString("//congress", doc);
        }
        if (congressStr == null || congressStr.isEmpty()) {
            congressStr = xmlHelper.getString("@congress", billNode);
        }
        if (congressStr == null || congressStr.isEmpty()) {
            throw new ParseError("Cannot find congress number in federal bill XML");
        }
        return Integer.parseInt(congressStr.trim());
    }

    private String parseBillType(Node billNode, Document doc) throws XPathExpressionException {
        String type = xmlHelper.getString("type", billNode);
        if (type == null || type.isEmpty()) {
            type = xmlHelper.getString("//type", doc);
        }
        if (type == null || type.isEmpty()) {
            type = xmlHelper.getString("@type", billNode);
        }
        return type != null ? type.trim().toUpperCase() : "HR";
    }

    private String parseBillNumber(Node billNode, Document doc) throws XPathExpressionException {
        String number = xmlHelper.getString("number", billNode);
        if (number == null || number.isEmpty()) {
            number = xmlHelper.getString("//number", doc);
        }
        if (number == null || number.isEmpty()) {
            number = xmlHelper.getString("@number", billNode);
        }
        return number != null ? number.trim() : "0";
    }

    private String parseTitle(Node billNode, Document doc) throws XPathExpressionException {
        String title = xmlHelper.getString("title", billNode);
        if (title == null || title.isEmpty()) {
            title = xmlHelper.getString("//title[@type='official']", doc);
        }
        if (title == null || title.isEmpty()) {
            title = xmlHelper.getString("//title", doc);
        }
        return title != null ? title.trim() : "";
    }

    private String parseText(Node billNode, Document doc) throws XPathExpressionException {
        String text = xmlHelper.getString("//legis-body", doc);
        if (text == null || text.isEmpty()) {
            text = xmlHelper.getString("//text", doc);
        }
        return text != null ? text.trim() : "";
    }

    private List<BillAction> parseActions(Node billNode, Document doc, BaseBillId baseBillId, Chamber chamber)
            throws XPathExpressionException {
        List<BillAction> actions = new ArrayList<>();
        NodeList actionNodes = xmlHelper.getNodeList("//action | //actions/action", doc);

        if (actionNodes != null) {
            for (int i = 0; i < actionNodes.getLength(); i++) {
                Node actionNode = actionNodes.item(i);
                BillAction action = parseAction(actionNode, baseBillId, chamber, i + 1);
                if (action != null) {
                    actions.add(action);
                }
            }
        }
        return actions;
    }

    private BillAction parseAction(Node actionNode, BaseBillId baseBillId, Chamber chamber, int sequenceNo)
            throws XPathExpressionException {
        String dateStr = xmlHelper.getString("actionDate", actionNode);
        if (dateStr == null || dateStr.isEmpty()) {
            dateStr = xmlHelper.getString("@actionDate", actionNode);
        }
        if (dateStr == null || dateStr.isEmpty()) {
            dateStr = xmlHelper.getString("date", actionNode);
        }

        String text = xmlHelper.getString("text", actionNode);
        if (text == null || text.isEmpty()) {
            text = actionNode.getTextContent();
        }

        if (dateStr == null || dateStr.isEmpty() || text == null || text.isEmpty()) {
            return null;
        }

        LocalDate date;
        try {
            date = LocalDate.parse(dateStr.trim(), DATE_FORMAT);
        } catch (Exception e) {
            logger.warn("Could not parse action date: {}", dateStr);
            return null;
        }

        BillId billId = new BillId(baseBillId, Version.ORIGINAL);
        return new BillAction(date, text.trim(), chamber, sequenceNo, billId, "UNKNOWN");
    }

    private Chamber deriveChamber(String billType) {
        if (billType == null) {
            return Chamber.SENATE;
        }
        String type = billType.toUpperCase();
        if (type.startsWith("H") || type.equals("HR") || type.equals("HRES") ||
                type.equals("HCONRES") || type.equals("HJRES")) {
            return Chamber.ASSEMBLY; // Federal House maps to Assembly
        }
        return Chamber.SENATE;
    }

    private int congressToSessionYear(int congress) {
        // Congress 1 started in 1789
        // Each congress is 2 years
        return 1789 + (congress - 1) * 2;
    }
}
