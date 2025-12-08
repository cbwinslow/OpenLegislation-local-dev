package gov.nysenate.openleg.processors.federal.bill;

import gov.nysenate.openleg.legislation.SessionYear;
import gov.nysenate.openleg.legislation.bill.*;
import gov.nysenate.openleg.legislation.committee.Chamber;
import gov.nysenate.openleg.processors.ParseError;
import gov.nysenate.openleg.processors.bill.LegDataFragment;
import gov.nysenate.openleg.processors.bill.LegDataFragmentType;
import gov.nysenate.openleg.processors.bill.AbstractBillProcessor;
import gov.nysenate.openleg.processors.log.DataProcessUnit;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.SAXException;

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

    @Override
    public LegDataFragmentType getSupportedType() {
        return LegDataFragmentType.BILL;
    }

    @Override
    public void process(LegDataFragment fragment) {
        logger.info("Processing federal bill: {}", fragment.getFragmentId());
        DataProcessUnit unit = createProcessUnit(fragment);
        try {
            Document doc = xmlHelper.parse(fragment.getText());
            Element root = doc.getDocumentElement();

            // Extract bill metadata from XML using DOM
            int congress = parseIntOrDefault(getElementText(root, "congress"), 0);
            String billType = getElementText(root, "billType");
            String billNumber = getElementText(root, "billNumber");
            String title = getElementText(root, "title");

            if (congress == 0 || billNumber.isEmpty()) {
                throw new ParseError("Missing required bill metadata in: " + fragment.getFragmentId());
            }

            // Convert congress to session year
            int sessionYear = Bill.congressToSessionYear(congress);
            SessionYear session = SessionYear.of(sessionYear);

            // Build bill ID
            String printNo = billType.toUpperCase() + billNumber;
            BaseBillId baseBillId = new BaseBillId(printNo, session);
            Bill bill = getOrCreateBaseBill(baseBillId, fragment);

            // Set title
            if (!title.isEmpty()) {
                bill.setTitle(title);
            }

            // Parse actions if present
            List<BillAction> actions = parseActions(root, baseBillId);
            if (!actions.isEmpty()) {
                bill.setActions(actions);
            }

            // Parse text if present
            BillAmendment amendment = bill.getAmendment(Version.ORIGINAL);
            String textContent = getElementText(root, "text");
            if (!textContent.isEmpty()) {
                BillText billText = new BillText(textContent);
                amendment.setBillText(billText);
            }

            // Set federal-specific metadata
            bill.setFederalCongress(congress);
            bill.setFederalSource("govinfo");
            
            bill.setModifiedDateTime(fragment.getPublishedDateTime());
            billIngestCache.set(bill.getBaseBillId(), bill, fragment);
            
            logger.info("Processed federal bill: {}", baseBillId);
        } catch (IOException | SAXException e) {
            unit.addException("XML federal bill parsing error", e);
            throw new ParseError("Error while parsing federal bill XML: " + fragment.getFragmentId(), e);
        } finally {
            postDataUnitEvent(unit);
            checkIngestCache();
        }
    }

    /**
     * Parse bill actions from XML.
     */
    private List<BillAction> parseActions(Element root, BaseBillId baseBillId) {
        List<BillAction> actions = new ArrayList<>();
        NodeList actionNodes = root.getElementsByTagName("action");
        
        for (int i = 0; i < actionNodes.getLength(); i++) {
            Node actionNode = actionNodes.item(i);
            if (actionNode.getNodeType() == Node.ELEMENT_NODE) {
                Element actionEl = (Element) actionNode;
                String dateStr = getElementText(actionEl, "actionDate");
                String text = getElementText(actionEl, "text");
                String chamberStr = getElementText(actionEl, "actionCode");
                
                if (!dateStr.isEmpty() && !text.isEmpty()) {
                    try {
                        LocalDate date = LocalDate.parse(dateStr, DATE_FORMAT);
                        Chamber chamber = chamberStr.startsWith("H") ? Chamber.ASSEMBLY : Chamber.SENATE;
                        BillId billId = new BillId(baseBillId, Version.ORIGINAL);
                        BillAction action = new BillAction(date, text, chamber, i + 1, billId, "UNKNOWN");
                        actions.add(action);
                    } catch (Exception e) {
                        logger.warn("Could not parse action: {}", text, e);
                    }
                }
            }
        }
        return actions;
    }

    /**
     * Get text content of first matching element.
     */
    private String getElementText(Element parent, String tagName) {
        NodeList nodes = parent.getElementsByTagName(tagName);
        if (nodes.getLength() > 0) {
            return nodes.item(0).getTextContent().trim();
        }
        return "";
    }

    /**
     * Parse integer or return default value.
     */
    private int parseIntOrDefault(String value, int defaultValue) {
        if (value == null || value.isEmpty()) {
            return defaultValue;
        }
        try {
            return Integer.parseInt(value.trim());
        } catch (NumberFormatException e) {
            return defaultValue;
        }
    }
}
