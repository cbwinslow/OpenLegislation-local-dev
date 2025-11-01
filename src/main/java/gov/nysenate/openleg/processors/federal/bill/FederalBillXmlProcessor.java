package gov.nysenate.openleg.processors.federal.bill;

import gov.nysenate.openleg.legislation.bill.*;
import gov.nysenate.openleg.legislation.committee.Chamber;
import gov.nysenate.openleg.processors.ParseError;
import gov.nysenate.openleg.processors.bill.LegDataFragment;
import gov.nysenate.openleg.processors.bill.LegDataFragmentType;
import gov.nysenate.openleg.processors.bill.AbstractBillProcessor;
import gov.nysenate.openleg.processors.log.DataProcessUnit;
import gov.nysenate.openleg.legislation.member.Member;
import gov.nysenate.openleg.legislation.member.SessionMember;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
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
        logger.info("Processing federal bill fragment: {}", fragment.getFragmentId());
        DataProcessUnit unit = createProcessUnit(fragment);
        try {
            final Document doc = xmlHelper.parse(fragment.getText());
            final Node billNode = xmlHelper.getNode("bill", doc);
            
            FederalBillXmlFile federalFile = (FederalBillXmlFile) fragment.getSourceFile();
            Bill bill = mapToBill(doc, billNode, federalFile);
            
            // Cache the bill using the base class infrastructure
            billIngestCache.set(bill.getBaseBillId(), bill, fragment);
            
            logger.info("Processed federal bill: {}", federalFile.getFileName());
        } catch (IOException | SAXException | XPathExpressionException e) {
            unit.addException("XML Federal Bill parsing error", e);
            throw new ParseError("Error parsing federal bill XML", e);
        } finally {
            postDataUnitEvent(unit);
            checkIngestCache();
        }
    }

    private Bill mapToBill(Document doc, Node billNode, FederalBillXmlFile sourceFile) throws XPathExpressionException {
        // Extract legislation ID info
        Node legIdNode = xmlHelper.getNode("legislationId", billNode);
        int congress = xmlHelper.getInteger("congress", legIdNode);
        String type = xmlHelper.getString("type", legIdNode);
        String number = xmlHelper.getString("number", legIdNode);
        
        // Determine chamber and bill type
        Chamber chamber = type.startsWith("H") ? Chamber.HOUSE : Chamber.SENATE;
        BillType billType = BillType.fromString(type.toUpperCase());
        int sessionYear = congressToSessionYear(congress);
        SessionYear session = SessionYear.of(sessionYear);
        BaseBillId baseBillId = new BaseBillId(number, session);

        Bill bill = getOrCreateBaseBill(new BillId(baseBillId, Version.ORIGINAL), sourceFile);
        
        // Set title
        String title = xmlHelper.getString("officialTitle", billNode);
        if (title != null && !title.isEmpty()) {
            bill.setTitle(title);
        }

        // Process sponsors
        NodeList sponsorNodes = xmlHelper.getNodeList("sponsors/sponsor", billNode);
        List<BillSponsor> sponsors = new ArrayList<>();
        for (int i = 0; i < sponsorNodes.getLength(); i++) {
            Node sponsorNode = sponsorNodes.item(i);
            String fullName = xmlHelper.getString("fullName", sponsorNode);
            String party = xmlHelper.getString("party", sponsorNode);
            // Create placeholder member - in production, would look up from member database
            Member member = new Member("Federal", fullName, fullName, null);
            SessionMember sessionMember = new SessionMember(0, member, "SPONSOR", session, null, true);
            BillSponsor sponsor = new BillSponsor(sessionMember);
            sponsors.add(sponsor);
        }
        bill.sponsors = sponsors;

        // Process actions
        NodeList actionNodes = xmlHelper.getNodeList("actions/action", billNode);
        List<BillAction> actions = new ArrayList<>();
        for (int i = 0; i < actionNodes.getLength(); i++) {
            Node actionNode = actionNodes.item(i);
            String dateStr = xmlHelper.getString("date", actionNode);
            LocalDate date = LocalDate.parse(dateStr, DATE_FORMAT);
            String actionChamberStr = xmlHelper.getString("chamber", actionNode);
            Chamber actionChamber = "HOUSE".equalsIgnoreCase(actionChamberStr) ? Chamber.HOUSE : Chamber.SENATE;
            String text = xmlHelper.getString("text", actionNode);
            BillId billId = new BillId(baseBillId, Version.ORIGINAL);
            BillAction action = new BillAction(date, text, actionChamber, i, billId, "UNKNOWN");
            actions.add(action);
        }
        bill.actions = actions;

        // Process text
        NodeList textNodes = xmlHelper.getNodeList("texts/text", billNode);
        BillText billText = new BillText();
        StringBuilder textBuilder = new StringBuilder();
        for (int i = 0; i < textNodes.getLength(); i++) {
            Node textNode = textNodes.item(i);
            String content = textNode.getTextContent();
            textBuilder.append(content).append("\n");
        }
        billText.setText(PLAIN, textBuilder.toString());
        bill.setText(billText);

        // Set federal-specific fields
        bill.setModifiedDateTime(sourceFile.getPublishedDateTime());
        bill.setFederalCongress(congress);
        bill.setFederalSource("govinfo");
        
        return bill;
    }

    private int congressToSessionYear(int congress) {
        return 1789 + (congress - 1) * 2; // Starting year of congress, e.g., 119th = 2025
    }
}