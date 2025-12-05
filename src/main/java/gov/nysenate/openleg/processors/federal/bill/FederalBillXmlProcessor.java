package gov.nysenate.openleg.processors.federal.bill;

import gov.nysenate.openleg.common.util.XmlHelper;
import gov.nysenate.openleg.legislation.SessionYear;
import gov.nysenate.openleg.legislation.bill.*;
import gov.nysenate.openleg.legislation.committee.Chamber;
import gov.nysenate.openleg.processors.ParseError;
import gov.nysenate.openleg.processors.bill.AbstractBillProcessor;
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
 * Parses XML to Bill model using DOM parsing (consistent with other OpenLegislation processors).
 */
@Service
public class FederalBillXmlProcessor extends AbstractBillProcessor {

    private static final Logger logger = LoggerFactory.getLogger(FederalBillXmlProcessor.class);

    private static final DateTimeFormatter DATE_FORMAT = DateTimeFormatter.ofPattern("yyyy-MM-dd");

    @Autowired
    public FederalBillXmlProcessor(XmlHelper xmlHelper) {
        this.xmlHelper = xmlHelper;
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
            if (bill != null) {
                billIngestCache.set(bill.getBaseBillId(), bill, fragment);
            }
            logger.info("Processed federal bill: {}", fragment.getFragmentId());
        } catch (IOException | SAXException | XPathExpressionException e) {
            unit.addException("Federal bill XML parsing error", e);
            throw new ParseError("Failed to process federal bill XML: " + fragment.getFragmentId(), e);
        } finally {
            postDataUnitEvent(unit);
            checkIngestCache();
        }
    }

    /**
     * Maps a parsed XML Document to a Bill object using DOM-based XPath queries.
     */
    private Bill mapToBill(Document doc, LegDataFragment fragment) throws XPathExpressionException {
        Node billNode = xmlHelper.getNode("//bill", doc);
        if (billNode == null) {
            billNode = doc.getDocumentElement();
        }

        // Extract congress number - try numeric first, fallback to parsing text
        int congress = extractCongressNumber(billNode);
        int sessionYear = congressToSessionYear(congress);
        SessionYear session = SessionYear.of(sessionYear);

        // Extract bill type and number
        String billType = xmlHelper.getString("//billType", billNode);
        if (billType == null || billType.isEmpty()) {
            billType = xmlHelper.getString("@type", billNode);
        }
        String billNumber = xmlHelper.getString("//billNumber", billNode);
        if (billNumber == null || billNumber.isEmpty()) {
            // Try legis-num element for USLM format
            String legisNum = xmlHelper.getString("//legis-num", billNode);
            if (legisNum != null && !legisNum.isEmpty()) {
                billNumber = extractBillNumberFromLegisNum(legisNum);
            }
        }

        if (billNumber == null || billNumber.isEmpty()) {
            throw new ParseError("Unable to extract bill number from federal XML");
        }

        // Determine chamber from bill type
        Chamber chamber = determineChamber(billType);

        // Create base bill ID
        String printNo = normalizePrintNo(billType, billNumber);
        BaseBillId baseBillId = new BaseBillId(printNo, session);
        Bill bill = getOrCreateBaseBill(baseBillId, fragment);

        // Set title
        String title = xmlHelper.getString("//title[@type='official']", billNode);
        if (title == null || title.isEmpty()) {
            title = xmlHelper.getString("//officialTitle", billNode);
        }
        if (title != null && !title.isEmpty()) {
            setTitle(bill, title, fragment);
        }

        // Set summary if available
        String summary = xmlHelper.getString("//summary/text", billNode);
        if (summary != null && !summary.isEmpty()) {
            setSummary(bill, summary, fragment);
        }

        // Parse actions
        parseActionsFromXml(bill, baseBillId.withVersion(Version.ORIGINAL), billNode, fragment);

        // Parse text content
        parseBillText(bill, billNode, fragment);

        // Ensure bill is published
        ensureBaseBillIsPublished(bill, fragment, "govinfo");

        return bill;
    }

    /**
     * Extracts congress number from XML, handling both numeric and text formats.
     */
    private int extractCongressNumber(Node billNode) throws XPathExpressionException {
        String congressStr = xmlHelper.getString("//congress", billNode);
        if (congressStr != null && !congressStr.isEmpty()) {
            // Try parsing as integer first
            try {
                return Integer.parseInt(congressStr.trim());
            } catch (NumberFormatException e) {
                // Try extracting number from text like "One Hundred Nineteenth Congress"
                return parseCongressFromText(congressStr);
            }
        }
        // Default to current congress if not found
        return 118;
    }

    /**
     * Parses congress number from text format (e.g., "One Hundred Nineteenth Congress").
     */
    private int parseCongressFromText(String text) {
        // Simple extraction - look for ordinal number pattern
        if (text.toLowerCase().contains("nineteenth")) {
            if (text.toLowerCase().contains("one hundred")) {
                return 119;
            }
        } else if (text.toLowerCase().contains("eighteenth")) {
            if (text.toLowerCase().contains("one hundred")) {
                return 118;
            }
        }
        // Fallback: try to find any number in the string
        String digits = text.replaceAll("[^0-9]", "");
        if (!digits.isEmpty()) {
            try {
                return Integer.parseInt(digits);
            } catch (NumberFormatException e) {
                // Ignore
            }
        }
        return 118; // Default fallback
    }

    /**
     * Extracts bill number from legis-num format (e.g., "H.R. 1234").
     */
    private String extractBillNumberFromLegisNum(String legisNum) {
        // Remove common prefixes and extract number
        String cleaned = legisNum.replaceAll("[^0-9]", "");
        return cleaned.isEmpty() ? null : cleaned;
    }

    /**
     * Determines chamber from bill type string.
     */
    private Chamber determineChamber(String billType) {
        if (billType == null) {
            return Chamber.SENATE;
        }
        String type = billType.toUpperCase();
        if (type.startsWith("H") || type.contains("HOUSE")) {
            return Chamber.ASSEMBLY; // Use ASSEMBLY for House in OpenLegislation
        }
        return Chamber.SENATE;
    }

    /**
     * Normalizes bill type and number to OpenLegislation print number format.
     */
    private String normalizePrintNo(String billType, String billNumber) {
        String prefix = "S";
        if (billType != null) {
            String type = billType.toUpperCase();
            if (type.startsWith("H") || type.equals("HR")) {
                prefix = "A"; // Assembly for House bills
            }
        }
        return prefix + billNumber;
    }

    /**
     * Parses bill actions from XML and applies them to the bill.
     */
    private void parseActionsFromXml(Bill bill, BillId billId, Node billNode, LegDataFragment fragment)
            throws XPathExpressionException {
        NodeList actionNodes = xmlHelper.getNodeList("//actions/action | //actions/item", billNode);
        if (actionNodes == null || actionNodes.getLength() == 0) {
            return;
        }

        List<BillAction> actions = new ArrayList<>();
        for (int i = 0; i < actionNodes.getLength(); i++) {
            Node actionNode = actionNodes.item(i);
            String dateStr = xmlHelper.getString("actionDate | date", actionNode);
            String text = xmlHelper.getString("text | description", actionNode);
            String chamberStr = xmlHelper.getString("actionCode | type", actionNode);

            if (dateStr != null && !dateStr.isEmpty() && text != null && !text.isEmpty()) {
                LocalDate actionDate = parseActionDate(dateStr);
                Chamber actionChamber = parseChamber(chamberStr);
                BillAction action = new BillAction(
                        actionDate,
                        text.trim(),
                        actionChamber,
                        i + 1,
                        billId,
                        "govinfo"
                );
                actions.add(action);
            }
        }

        if (!actions.isEmpty()) {
            bill.setActions(actions);
        }
    }

    /**
     * Parses bill text content and applies it to the bill amendment.
     */
    private void parseBillText(Bill bill, Node billNode, LegDataFragment fragment)
            throws XPathExpressionException {
        String textContent = xmlHelper.getString("//text | //body", billNode);
        if (textContent != null && !textContent.isEmpty()) {
            BillAmendment amendment = bill.getAmendment(Version.ORIGINAL);
            BillText billText = new BillText(textContent);
            amendment.setBillText(billText);
        }
    }

    /**
     * Parses action date from string format.
     */
    private LocalDate parseActionDate(String dateStr) {
        try {
            return LocalDate.parse(dateStr.trim(), DATE_FORMAT);
        } catch (Exception e) {
            // Try alternative formats
            try {
                return LocalDate.parse(dateStr.trim(), DateTimeFormatter.ISO_LOCAL_DATE);
            } catch (Exception e2) {
                logger.warn("Unable to parse action date: {}", dateStr);
                return LocalDate.now();
            }
        }
    }

    /**
     * Parses chamber from string.
     */
    private Chamber parseChamber(String chamberStr) {
        if (chamberStr == null) {
            return Chamber.SENATE;
        }
        String upper = chamberStr.toUpperCase();
        if (upper.contains("HOUSE") || upper.startsWith("H")) {
            return Chamber.ASSEMBLY;
        }
        return Chamber.SENATE;
    }

    /**
     * Converts congress number to session year.
     * Congress 1 started in 1789. Each congress lasts 2 years.
     */
    private int congressToSessionYear(int congress) {
        return 1789 + (congress - 1) * 2;
    }
}