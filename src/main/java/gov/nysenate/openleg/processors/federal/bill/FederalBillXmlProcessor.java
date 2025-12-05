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

    private final DocumentBuilderFactory documentBuilderFactory;

    public FederalBillXmlProcessor() {
        this.documentBuilderFactory = DocumentBuilderFactory.newInstance();
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
            Document doc = parseXmlFile(xmlFile);
            Bill bill = mapToBill(doc, federalFile);
            // Persistence logic would go here
            logger.info("Processed federal bill: {}", federalFile.getFileName());
        } catch (Exception e) {
            logger.error("Error processing federal bill XML: {}", federalFile.getFileName(), e);
            throw new ParseError("Failed to process federal bill XML: " + federalFile.getFileName(), e);
        }
    }

    /**
     * Parse XML file into a DOM Document.
     */
    private Document parseXmlFile(File xmlFile) throws ParserConfigurationException, SAXException, IOException {
        DocumentBuilder builder = documentBuilderFactory.newDocumentBuilder();
        return builder.parse(xmlFile);
    }

    /**
     * Map parsed XML Document to Bill model.
     */
    private Bill mapToBill(Document doc, FederalBillXmlFile sourceFile) {
        Element root = doc.getDocumentElement();
        
        int congress = sourceFile.getCongress();
        String billType = sourceFile.getBillType();
        String billNumber = sourceFile.getBillNumber();
        
        // Determine chamber from bill type
        Chamber chamber = billType.startsWith("H") ? Chamber.ASSEMBLY : Chamber.SENATE;
        
        // Convert congress number to session year
        int sessionYear = congressToSessionYear(congress);
        SessionYear session = SessionYear.of(sessionYear);
        
        // Create base bill ID
        String printNo = billType + billNumber;
        BaseBillId baseBillId = new BaseBillId(printNo, session);
        Bill bill = new Bill(baseBillId);
        
        // Extract title
        String title = getElementText(root, "title");
        if (title == null || title.isEmpty()) {
            title = getElementText(root, "official-title");
        }
        bill.setTitle(title != null ? title : "");
        
        // Extract actions
        List<BillAction> actions = parseActions(root, baseBillId);
        bill.setActions(actions);
        
        // Extract text content
        String textContent = extractTextContent(root);
        BillAmendment amendment = bill.getAmendment(Version.ORIGINAL);
        if (amendment != null && !textContent.isEmpty()) {
            BillText billText = new BillText(textContent);
            amendment.setBillText(billText);
        }
        
        // Set federal-specific fields
        bill.setFederalCongress(congress);
        bill.setFederalSource("govinfo");
        
        return bill;
    }
    
    /**
     * Parse bill actions from XML.
     */
    private List<BillAction> parseActions(Element root, BaseBillId baseBillId) {
        List<BillAction> actions = new ArrayList<>();
        NodeList actionNodes = root.getElementsByTagName("action");
        
        for (int i = 0; i < actionNodes.getLength(); i++) {
            Element actionElement = (Element) actionNodes.item(i);
            
            String dateStr = getElementText(actionElement, "actionDate");
            String text = getElementText(actionElement, "text");
            String chamberStr = getElementText(actionElement, "actionCode");
            
            if (dateStr != null && text != null) {
                try {
                    LocalDate date = LocalDate.parse(dateStr, DATE_FORMAT);
                    Chamber actionChamber = chamberStr != null && chamberStr.startsWith("H") 
                            ? Chamber.ASSEMBLY : Chamber.SENATE;
                    BillId billId = new BillId(baseBillId, Version.ORIGINAL);
                    BillAction action = new BillAction(date, text, actionChamber, i + 1, billId, "UNKNOWN");
                    actions.add(action);
                } catch (Exception e) {
                    logger.warn("Could not parse action: {}", text, e);
                }
            }
        }
        
        return actions;
    }
    
    /**
     * Extract text content from bill XML.
     */
    private String extractTextContent(Element root) {
        StringBuilder textBuilder = new StringBuilder();
        
        // Try to get text from various possible elements
        NodeList textNodes = root.getElementsByTagName("text");
        for (int i = 0; i < textNodes.getLength(); i++) {
            String content = textNodes.item(i).getTextContent();
            if (content != null && !content.trim().isEmpty()) {
                textBuilder.append(content.trim()).append("\n");
            }
        }
        
        return textBuilder.toString().trim();
    }
    
    /**
     * Get text content of first matching child element.
     */
    private String getElementText(Element parent, String tagName) {
        NodeList nodes = parent.getElementsByTagName(tagName);
        if (nodes.getLength() > 0) {
            return nodes.item(0).getTextContent();
        }
        return "";
    }

    /**
     * Convert congress number to session year.
     * e.g., 119th Congress = 2025
     */
    private int congressToSessionYear(int congress) {
        return 1789 + (congress - 1) * 2;
    }
}
