package gov.nysenate.openleg.processors.federal.bill;

import gov.nysenate.openleg.common.util.XmlHelper;
import gov.nysenate.openleg.legislation.SessionYear;
import gov.nysenate.openleg.legislation.bill.*;
import gov.nysenate.openleg.legislation.committee.Chamber;
import gov.nysenate.openleg.processors.ParseError;
import gov.nysenate.openleg.processors.bill.LegDataFragment;
import gov.nysenate.openleg.processors.bill.LegDataFragmentType;
import gov.nysenate.openleg.processors.bill.AbstractBillProcessor;
import gov.nysenate.openleg.legislation.member.Member;
import gov.nysenate.openleg.legislation.member.Person;
import gov.nysenate.openleg.legislation.member.SessionMember;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.SAXException;

import javax.xml.xpath.XPathExpressionException;
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
@Service
public class FederalBillXmlProcessor extends AbstractBillProcessor {

    private static final Logger logger = LoggerFactory.getLogger(FederalBillXmlProcessor.class);

    private static final DateTimeFormatter DATE_FORMAT = DateTimeFormatter.ofPattern("yyyy-MM-dd");

    private final XmlHelper xmlHelper;

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
        FederalBillXmlFile federalFile = (FederalBillXmlFile) fragment.getParentLegDataFile();
        File xmlFile = federalFile.getFile();
        try {
            Document doc = xmlHelper.parse(xmlFile);
            Bill bill = mapToBill(doc, federalFile, fragment);
            // Persist bill using ingest cache
            billIngestCache.set(bill.getBaseBillId(), bill, fragment);
            logger.info("Processed federal bill: {}", federalFile.getFileName());
        } catch (IOException | SAXException | XPathExpressionException e) {
            logger.error("Error processing federal bill XML: {}", federalFile.getFileName(), e);
            throw new ParseError("Failed to process federal bill XML: " + federalFile.getFileName(), e);
        }
    }

    private Bill mapToBill(Document doc, FederalBillXmlFile sourceFile, LegDataFragment fragment) throws XPathExpressionException {
        // Parse legislation ID
        Node legIdNode = xmlHelper.getNode("//legislationId", doc);
        int congress = xmlHelper.getInteger("congress", legIdNode);
        String type = xmlHelper.getString("type", legIdNode);
        String number = xmlHelper.getString("number", legIdNode);
        
        int sessionYear = congressToSessionYear(congress);
        SessionYear session = SessionYear.of(sessionYear);
        BaseBillId baseBillId = new BaseBillId(number, session);
        BillId billId = new BillId(baseBillId, Version.ORIGINAL);

        // Get or create the bill
        Bill bill = getOrCreateBaseBill(billId, fragment);
        BillAmendment amendment = bill.getAmendment(Version.ORIGINAL);
        
        // Parse title
        String title = xmlHelper.getString("//officialTitle", doc);
        setTitle(bill, title, fragment);

        // Parse sponsors
        // TODO: Map federal sponsors properly using bioguide IDs
        BillSponsor sponsor = new BillSponsor();
        sponsor.setMember(null); // Placeholder - federal sponsor mapping not yet implemented
        bill.setSponsor(sponsor);

        // Parse actions
        List<BillAction> actions = new ArrayList<>();
        NodeList actionNodes = xmlHelper.getNodeList("//actions/action", doc);
        for (int i = 0; i < actionNodes.getLength(); i++) {
            Node actionNode = actionNodes.item(i);
            String dateStr = xmlHelper.getString("date", actionNode);
            LocalDate date = LocalDate.parse(dateStr, DATE_FORMAT);
            String actionChamberStr = xmlHelper.getString("chamber", actionNode);
            // Map federal chambers to OpenLeg chambers (HOUSE and SENATE both map to SENATE for now)
            Chamber actionChamber = "ASSEMBLY".equalsIgnoreCase(actionChamberStr) ? Chamber.ASSEMBLY : Chamber.SENATE;
            String text = xmlHelper.getString("text", actionNode);
            BillId actionBillId = new BillId(baseBillId, Version.ORIGINAL);
            BillAction action = new BillAction(date, text, actionChamber, 0, actionBillId, "UNKNOWN");
            actions.add(action);
        }
        bill.setActions(actions);

        // Parse text
        StringBuilder textBuilder = new StringBuilder();
        NodeList textNodes = xmlHelper.getNodeList("//texts/text", doc);
        for (int i = 0; i < textNodes.getLength(); i++) {
            Node textNode = textNodes.item(i);
            textBuilder.append(textNode.getTextContent()).append("\n");
        }
        BillText billText = new BillText(textBuilder.toString());
        amendment.setBillText(billText);

        setModifiedDateTime(bill, fragment);
        bill.setFederalCongress(congress);
        bill.setFederalSource("govinfo");
        return bill;
    }

    private int congressToSessionYear(int congress) {
        return 1789 + (congress - 1) * 2; // Starting year of congress, e.g., 119th = 2025
    }
}