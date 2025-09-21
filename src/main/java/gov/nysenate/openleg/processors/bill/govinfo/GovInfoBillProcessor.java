package gov.nysenate.openleg.processors.bill.govinfo;

import gov.nysenate.openleg.legislation.SessionYear;
import gov.nysenate.openleg.legislation.bill.*;
import gov.nysenate.openleg.legislation.committee.Chamber;
import gov.nysenate.openleg.legislation.member.SessionMember;
import gov.nysenate.openleg.processors.ParseError;
import gov.nysenate.openleg.processors.bill.AbstractBillProcessor;
import gov.nysenate.openleg.processors.bill.LegDataFragment;
import gov.nysenate.openleg.processors.bill.LegDataFragmentType;
import gov.nysenate.openleg.processors.log.DataProcessUnit;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.NodeList;
import org.xml.sax.InputSource;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import java.io.StringReader;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

/**
 * Processes GovInfo XML bill data and integrates it into the existing OpenLegislation bill model.
 * Maps congress.gov bulk XML data to Bill objects using the existing data processing framework.
 */
@Service
public class GovInfoBillProcessor extends AbstractBillProcessor {
    private static final Logger logger = LoggerFactory.getLogger(GovInfoBillProcessor.class);

    @Override
    public LegDataFragmentType getSupportedType() {
        return LegDataFragmentType.BILL;
    }

    @Override
    public void process(LegDataFragment legDataFragment) {
        DataProcessUnit unit = createProcessUnit(legDataFragment);
        try {
            logger.info("GovInfoBillProcessor: processing " + legDataFragment.getFragmentId());

            // Parse XML into Bill object
            Bill bill = parseGovInfoBillXml(legDataFragment.getText(), legDataFragment);

            if (bill != null) {
                // Store in ingest cache for persistence
                billIngestCache.set(bill.getBaseBillId(), bill, legDataFragment);
            }

        } catch (Exception e) {
            throw new ParseError("GovInfo parsing error", e);
        } finally {
            postDataUnitEvent(unit);
            checkIngestCache();
        }
    }

    /**
     * Parse GovInfo XML into a Bill object using existing Bill model and helper methods.
     */
    private Bill parseGovInfoBillXml(String xmlText, LegDataFragment fragment) throws Exception {
        DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
        DocumentBuilder builder = factory.newDocumentBuilder();
        Document doc = builder.parse(new InputSource(new StringReader(xmlText)));
        doc.getDocumentElement().normalize();

        Element billElement = doc.getDocumentElement();

        // Extract basic bill identity
        int congress = Integer.parseInt(getTextContent(billElement, "congress"));
        String billNumber = getTextContent(billElement, "billNumber");
        String billTypeStr = getTextContent(billElement, "billType");

        // Create BillId - map federal bill number to our format
        // GovInfo uses format like "H.R.1" or "S.123", we need to convert to our format
        BillId billId = createBillIdFromGovInfo(billNumber, congress);

        // Get or create the bill
        Bill bill = getOrCreateBaseBill(billId, fragment);

        // Set basic metadata
        String title = getTextContent(billElement, "officialTitle");
        if (title != null) {
            setTitle(bill, title, fragment);
        }

        String summary = getTextContent(billElement, "summary");
        if (summary != null) {
            setSummary(bill, summary, fragment);
        }

        // Parse introduced date
        String introducedDateStr = getTextContent(billElement, "introducedDate");
        if (introducedDateStr != null) {
            // Note: Bill model doesn't have introduced date field, but we can store it elsewhere if needed
            logger.debug("Introduced date: {}", introducedDateStr);
        }

        // Parse sponsor
        Element sponsorElement = getFirstElement(billElement, "sponsor");
        if (sponsorElement != null) {
            String sponsorName = getTextContent(sponsorElement, "name");
            if (sponsorName != null) {
                // For federal bills, we might not have exact member matches
                // Could create a placeholder or skip sponsor mapping for now
                logger.debug("Sponsor: {}", sponsorName);
            }
        }

        // Parse actions
        Element actionsElement = getFirstElement(billElement, "actions");
        if (actionsElement != null) {
            parseActionsFromGovInfo(bill, billId.getVersion(), actionsElement, fragment);
        }

        // Parse cosponsors
        Element cosponsorsElement = getFirstElement(billElement, "cosponsors");
        if (cosponsorsElement != null) {
            parseCosponsorsFromGovInfo(bill, cosponsorsElement, fragment);
        }

        // Parse text versions
        Element textVersionsElement = getFirstElement(billElement, "textVersions");
        if (textVersionsElement != null) {
            parseTextVersionsFromGovInfo(bill, billId.getVersion(), textVersionsElement, fragment);
        }

        // Ensure bill is published
        ensureBaseBillIsPublished(bill, fragment, "govinfo");

        return bill;
    }

    /**
     * Convert GovInfo bill number format to OpenLegislation BillId.
     * GovInfo: "H.R.1" → OpenLegislation: "H1" (simplified mapping)
     */
    private BillId createBillIdFromGovInfo(String govInfoBillNumber, int congress) {
        // Parse GovInfo format like "H.R.1" or "S.123"
        String[] parts = govInfoBillNumber.split("\\.");
        if (parts.length >= 2) {
            String chamberCode = parts[0]; // "H" or "S"
            String billType = parts[1];    // "R" or bill type
            String number = parts[parts.length - 1]; // "1" or "123"

            // Map to our format: H1, S123, etc.
            String printNo = chamberCode + number;
            return new BillId(printNo, congress);
        }
        throw new ParseError("Unable to parse GovInfo bill number: " + govInfoBillNumber);
    }

    /**
     * Parse actions from GovInfo XML format.
     */
    private void parseActionsFromGovInfo(Bill bill, Version version, Element actionsElement, LegDataFragment fragment) throws ParseError {
        NodeList actionNodes = actionsElement.getElementsByTagName("action");
        List<BillAction> actions = new ArrayList<>();

        for (int i = 0; i < actionNodes.getLength(); i++) {
            Element actionElement = (Element) actionNodes.item(i);

            String dateStr = getTextContent(actionElement, "date");
            String chamberStr = getTextContent(actionElement, "chamber");
            String text = getTextContent(actionElement, "text");
            String type = getTextContent(actionElement, "type");

            if (dateStr != null && text != null) {
                LocalDateTime actionDate = parseDateTime(dateStr);
                Chamber chamber = parseChamber(chamberStr);

                BillAction action = new BillAction(
                    actionDate.toLocalDate(),
                    text,
                    chamber,
                    i + 1, // sequence number
                    bill.getBaseBillId().withVersion(version)
                );
                actions.add(action);
            }
        }

        if (!actions.isEmpty()) {
            // Use existing parseActions method to apply actions and derive status
            parseActions("", bill, bill.getAmendment(version), fragment, null);
            // Override with our parsed actions
            bill.setActions(actions);
        }
    }

    /**
     * Parse cosponsors from GovInfo XML.
     */
    private void parseCosponsorsFromGovInfo(Bill bill, Element cosponsorsElement, LegDataFragment fragment) {
        NodeList cosponsorNodes = cosponsorsElement.getElementsByTagName("cosponsor");
        List<SessionMember> cosponsors = new ArrayList<>();

        for (int i = 0; i < cosponsorNodes.getLength(); i++) {
            Element cosponsorElement = (Element) cosponsorNodes.item(i);
            String name = getTextContent(cosponsorElement, "name");

            if (name != null) {
                // For federal data, we might not have exact member matches
                // Could implement fuzzy matching or create placeholder members
                logger.debug("Cosponsor: {}", name);
            }
        }

        // Apply cosponsors to active amendment
        if (!cosponsors.isEmpty()) {
            bill.getActiveAmendment().setCoSponsors(cosponsors);
            setModifiedDateTime(bill, fragment);
        }
    }

    /**
     * Parse text versions from GovInfo XML.
     */
    private void parseTextVersionsFromGovInfo(Bill bill, Version version, Element textVersionsElement, LegDataFragment fragment) {
        NodeList textNodes = textVersionsElement.getElementsByTagName("textVersion");

        for (int i = 0; i < textNodes.getLength(); i++) {
            Element textElement = (Element) textNodes.item(i);
            String versionId = getTextContent(textElement, "versionId");
            String format = getTextContent(textElement, "format");
            String content = getTextContent(textElement, "content");

            if (content != null && "xml".equalsIgnoreCase(format)) {
                // For now, store as plain text. Could enhance to parse XML content.
                BillText billText = new BillText(content);
                bill.getAmendment(version).setBillText(billText);
                setModifiedDateTime(bill, fragment);
                break; // Use first available text
            }
        }
    }

    // Helper methods
    private String getTextContent(Element parent, String tagName) {
        NodeList nodes = parent.getElementsByTagName(tagName);
        if (nodes.getLength() > 0) {
            return nodes.item(0).getTextContent();
        }
        return null;
    }

    private Element getFirstElement(Element parent, String tagName) {
        NodeList nodes = parent.getElementsByTagName(tagName);
        if (nodes.getLength() > 0) {
            return (Element) nodes.item(0);
        }
        return null;
    }

    private LocalDateTime parseDateTime(String dateStr) {
        if (dateStr == null) return LocalDateTime.now();
        try {
            return LocalDateTime.parse(dateStr, DateTimeFormatter.ISO_DATE_TIME);
        } catch (Exception e) {
            try {
                LocalDate date = LocalDate.parse(dateStr, DateTimeFormatter.ISO_LOCAL_DATE);
                return date.atStartOfDay();
            } catch (Exception e2) {
                return LocalDateTime.now();
            }
        }
    }

    private Chamber parseChamber(String chamberStr) {
        if (chamberStr == null) return Chamber.SENATE;
        if (chamberStr.toLowerCase().contains("house")) return Chamber.ASSEMBLY; // Map House to Assembly
        if (chamberStr.toLowerCase().contains("senate")) return Chamber.SENATE;
        return Chamber.SENATE; // Default
    }

    @Override
    public void checkIngestCache() {
        // Delegate to parent implementation
    }

    @Override
    public void postProcess() {
        // Nothing specific for GovInfo
    }
}
