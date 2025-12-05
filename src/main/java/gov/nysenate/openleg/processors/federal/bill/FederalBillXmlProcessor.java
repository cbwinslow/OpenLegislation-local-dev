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
            Document doc = parseXmlDocument(xmlFile);
            Bill bill = mapToBill(doc, federalFile);
            // Note: Persistence would be handled by a DAO in a complete implementation
            logger.info("Processed federal bill: {}", federalFile.getFileName());
        } catch (Exception e) {
            logger.error("Error processing federal bill XML: {}", federalFile.getFileName(), e);
            throw new ParseError("Failed to process federal bill XML: " + federalFile.getFileName(), e);
        }
    }

    /**
     * Parse the XML file into a DOM Document.
     */
    Document parseXmlDocument(File xmlFile) throws ParserConfigurationException, SAXException, IOException {
        DocumentBuilder builder = documentBuilderFactory.newDocumentBuilder();
        return builder.parse(xmlFile);
    }

    /**
     * Map the DOM Document to a Bill model.
     */
    Bill mapToBill(Document doc, FederalBillXmlFile sourceFile) {
        Element root = doc.getDocumentElement();
        
        int congress = sourceFile.getCongress();
        String billType = sourceFile.getBillType();
        String billNumber = sourceFile.getBillNumber();
        
        // Convert congress number to session year (e.g., 119th Congress = 2025)
        int sessionYear = congressToSessionYear(congress);
        SessionYear session = SessionYear.of(sessionYear);
        
        // Create the bill ID
        String printNo = billType + billNumber;
        BaseBillId baseBillId = new BaseBillId(printNo, session);
        Bill bill = new Bill(baseBillId);
        
        // Parse title
        String title = getElementText(root, "title");
        if (title != null && !title.isEmpty()) {
            bill.setTitle(title);
        }
        
        // Parse summary
        String summary = getElementText(root, "summary");
        if (summary != null && !summary.isEmpty()) {
            bill.setSummary(summary);
        }
        
        // Set federal-specific fields
        bill.setFederalCongress(congress);
        bill.setFederalSource("govinfo");
        
        return bill;
    }

    private String getElementText(Element parent, String tagName) {
        NodeList nodes = parent.getElementsByTagName(tagName);
        if (nodes.getLength() > 0) {
            return nodes.item(0).getTextContent();
        }
        return "";
    }

    private int congressToSessionYear(int congress) {
        // 1st Congress started in 1789; each congress is 2 years
        return 1789 + (congress - 1) * 2;
    }
}
