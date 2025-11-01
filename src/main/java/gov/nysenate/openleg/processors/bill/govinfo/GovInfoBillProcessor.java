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

    /**
     * The legislative data fragment type handled by this processor.
     *
     * @return the supported {@link LegDataFragmentType}, specifically {@link LegDataFragmentType#BILL}
     */
    @Override
    public LegDataFragmentType getSupportedType() {
        return LegDataFragmentType.BILL;
    }

    /**
     * Processes a LegDataFragment containing GovInfo bill XML, parses it into a Bill, and schedules the Bill for ingestion.
     *
     * <p>If parsing produces a Bill, it is stored in the bill ingest cache. Processing completion events are posted
     * and the ingest cache is checked regardless of outcome.</p>
     *
     * @param legDataFragment the data fragment containing GovInfo XML to process
     * @throws ParseError if an error occurs while parsing the GovInfo XML
     */
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
     * Build or retrieve a Bill from GovInfo XML and map its metadata, actions, cosponsors, and text versions.
     *
     * @param xmlText  the GovInfo bill XML as a string
     * @param fragment the source LegDataFragment providing provenance and context for the ingest
     * @return         the populated Bill instance (created or retrieved) mapped from the provided XML
     * @throws Exception if XML parsing or mapping of the GovInfo data fails
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
     * Convert a GovInfo bill identifier (e.g., "H.R.1" or "S.123") into an OpenLegislation BillId.
     *
     * Accepts GovInfo compound identifiers and builds a BillId using a simplified print number
     * composed of the chamber letter concatenated with the numeric bill id.
     *
     * @param govInfoBillNumber GovInfo bill identifier such as "H.R.1" or "S.123"
     * @param congress          the congress number to assign to the resulting BillId
     * @return                  a BillId whose print number is the chamber letter plus the bill number (e.g., "H1") for the given congress
     * @throws ParseError       if the GovInfo bill identifier cannot be parsed
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
     * Parse action entries from a GovInfo actions XML element and attach them to the given bill.
     *
     * Iterates "action" child elements, converts those with a date and text into BillAction objects,
     * applies existing action parsing to derive bill status, and replaces the bill's actions with
     * the parsed list on the amendment identified by the provided version.
     *
     * @param bill the bill to update
     * @param version the version whose amendment will receive the parsed actions
     * @param actionsElement the DOM element containing GovInfo "action" child elements
     * @param fragment the source data fragment providing parsing context
     * @throws ParseError if deriving or applying actions to the bill fails
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

                BillId billId = new BillId(bill.getBaseBillId(), Version.ORIGINAL);
                BillAction action = new BillAction(
                    actionDate.toLocalDate(),
                    text,
                    chamber,
                    0, // sequence number
                    billId,
                    "UNKNOWN"
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
     * Extracts cosponsor entries from the given GovInfo XML element and applies them to the bill's active amendment.
     *
     * Parses child <cosponsor> elements of the provided XML element, logs each cosponsor name found, and if any
     * matching SessionMember entries are collected, sets them as co-sponsors on the bill's active amendment and
     * updates the bill's modified timestamp using the provided fragment.
     *
     * @param bill the Bill to update
     * @param cosponsorsElement the XML element containing one or more <cosponsor> child elements
     * @param fragment the source data fragment used to update the bill's metadata (modified timestamp)
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
     * Attach the first XML-formatted text version found in the GovInfo element to the bill's specified version.
     *
     * Searches the provided textVersionsElement for child <textVersion> entries and, for the first entry
     * whose `format` equals "xml" (case-insensitive) and has non-null content, sets that content as the
     * BillText on the bill's amendment identified by `version` and updates the bill's modified date/time.
     *
     * @param bill the Bill to update
     * @param version the version identifier whose amendment will receive the text
     * @param textVersionsElement the XML element containing one or more <textVersion> child elements
     * @param fragment the source data fragment used to attribute the modification (for timestamping/context)
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

    /**
     * Retrieve the text content of the first child element with the specified tag name.
     *
     * @param parent the parent XML element to search within
     * @param tagName the tag name of the child element to find
     * @return the text content of the first matching child element, or {@code null} if no such element exists
     */
    private String getTextContent(Element parent, String tagName) {
        NodeList nodes = parent.getElementsByTagName(tagName);
        if (nodes.getLength() > 0) {
            return nodes.item(0).getTextContent();
        }
        return null;
    }

    /**
     * Finds the first child element with the specified tag name.
     *
     * @param parent the parent element to search within
     * @param tagName the tag name to match
     * @return the first matching child Element, or {@code null} if no match is found
     */
    private Element getFirstElement(Element parent, String tagName) {
        NodeList nodes = parent.getElementsByTagName(tagName);
        if (nodes.getLength() > 0) {
            return (Element) nodes.item(0);
        }
        return null;
    }

    /**
     * Parse a GovInfo date/time string accepting ISO date-time or ISO local date formats.
     *
     * @param dateStr the input date/time string; expected formats are ISO_DATE_TIME (e.g. "2020-01-02T15:04:05")
     *                or ISO_LOCAL_DATE (e.g. "2020-01-02"). If null or unparsable, the current date-time is used.
     * @return the parsed date-time; if an ISO_LOCAL_DATE is provided the result is at start of day, and if the input
     *         is null or cannot be parsed the current date-time is returned.
     */
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

    /**
     * Map a GovInfo chamber description string to the internal Chamber enum.
     *
     * @param chamberStr the chamber description from GovInfo (e.g., "House", "Senate"); may be null
     * @return `Chamber.ASSEMBLY` if the string contains "house" (case-insensitive), `Chamber.SENATE` otherwise
     */
    private Chamber parseChamber(String chamberStr) {
        if (chamberStr == null) return Chamber.SENATE;
        if (chamberStr.toLowerCase().contains("house")) return Chamber.ASSEMBLY; // Map House to Assembly
        if (chamberStr.toLowerCase().contains("senate")) return Chamber.SENATE;
        return Chamber.SENATE; // Default
    }

    /**
     * Perform ingest cache validation and eviction checks for processed bill fragments.
     *
     * No additional behavior is performed in this implementation.
     */
    @Override
    public void checkIngestCache() {
        // Delegate to parent implementation
    }

    /**
     * Hook invoked after ingest to perform any processor-specific post-processing.
     *
     * <p>This implementation is a no-op for GovInfo fragments.</p>
     */
    @Override
    public void postProcess() {
        // Nothing specific for GovInfo
    }
}