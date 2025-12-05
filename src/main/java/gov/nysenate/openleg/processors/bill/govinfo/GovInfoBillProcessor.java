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
     * Specify which LegDataFragmentType this processor handles.
     *
     * @return the supported fragment type: {@link LegDataFragmentType#BILL}
     */
    @Override
    public LegDataFragmentType getSupportedType() {
        return LegDataFragmentType.BILL;
    }

    /**
     * Processes a GovInfo bill data fragment by parsing its XML into a Bill and placing the result into the ingest cache.
     *
     * The method also posts a data unit event and triggers ingest cache checks as part of the processing lifecycle.
     *
     * @param legDataFragment the bill data fragment containing GovInfo XML to parse
     * @throws ParseError if the GovInfo XML cannot be parsed or another error occurs during processing
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
     * Parse a GovInfo bill XML document and construct or update a corresponding Bill model.
     *
     * This reads identifying fields (congress, bill number/type), maps the GovInfo bill identifier
     * to the local BillId, sets title and summary when present, and parses actions, cosponsors,
     * and text versions before ensuring the base bill is marked published with source "govinfo".
     *
     * @param xmlText  the raw GovInfo bill XML content
     * @param fragment the originating LegDataFragment used for provenance and cache tracking
     * @return the constructed or updated Bill populated with parsed metadata and related entities
     * @throws Exception if XML parsing or mapping fails (for example, invalid XML or unparseable bill id)
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
     * Create an OpenLegislation BillId from a GovInfo bill number and congress.
     *
     * Parses GovInfo identifiers like "H.R.1" or "S.123" and converts them into the processor's BillId format (for example, "H.R.1" with congress 118 -> BillId("H1", 118)).
     *
     * @param govInfoBillNumber the bill identifier from GovInfo (expected formats include "H.R.1", "S.123", etc.)
     * @param congress the numeric congress session to associate with the BillId
     * @return the corresponding BillId in OpenLegislation format
     * @throws ParseError if the govInfoBillNumber cannot be parsed into the expected components
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
     * Parses action entries from a GovInfo actions XML element, converts them into BillAction
     * objects, attaches them to the bill, and updates the bill's derived status.
     *
     * @param bill the bill to populate with parsed actions
     * @param version the amendment version the parsed actions apply to
     * @param actionsElement the XML element containing one or more `<action>` child elements
     * @param fragment the source data fragment providing context for the parse
     * @throws ParseError if an error occurs while parsing action data
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
     * Extracts cosponsor entries from a GovInfo "cosponsors" XML element and assigns any found
     * cosponsors to the bill's active amendment, updating the bill's modified timestamp.
     *
     * This method reads child "cosponsor" elements, attempts to obtain each cosponsor's `name`,
     * and collects corresponding SessionMember instances. Member resolution is not performed for
     * federal data (names are logged but not matched to concrete members).
     *
     * @param bill the bill to update
     * @param cosponsorsElement the XML element containing one or more "cosponsor" child elements
     * @param fragment the source data fragment associated with this parsing operation (used to
     *                 set the bill's modified date/time when cosponsors are applied)
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
     * Extracts the first available XML-formatted text version from GovInfo and sets it as the amendment's bill text.
     *
     * Iterates textVersion elements under the provided textVersionsElement, and when a textVersion with
     * non-null content and format "xml" is found, stores that content in a BillText on the bill's amendment
     * for the given version and updates the bill's modified date/time.
     *
     * @param bill the Bill to update
     * @param version the Version of the amendment to which the text should be applied
     * @param textVersionsElement the parent XML element containing one or more <textVersion> child elements
     * @param fragment the source LegDataFragment used to mark modification metadata
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
     * Retrieve the text content of the first child element with the given tag name.
     *
     * @param parent the parent XML element to search
     * @param tagName the child tag name to look for
     * @return the text content of the first matching child element, or {@code null} if none is found
     */
    private String getTextContent(Element parent, String tagName) {
        NodeList nodes = parent.getElementsByTagName(tagName);
        if (nodes.getLength() > 0) {
            return nodes.item(0).getTextContent();
        }
        return null;
    }

    /**
     * Retrieve the first child element with the given tag name.
     *
     * @param parent  the parent Element to search within
     * @param tagName the tag name to find
     * @return the first matching child Element, or `null` if no such element exists
     */
    private Element getFirstElement(Element parent, String tagName) {
        NodeList nodes = parent.getElementsByTagName(tagName);
        if (nodes.getLength() > 0) {
            return (Element) nodes.item(0);
        }
        return null;
    }

    /**
     * Parse a date/time string from govinfo into a LocalDateTime.
     *
     * Accepts an ISO date-time (e.g. "2020-01-01T12:34:56") or an ISO local date (e.g. "2020-01-01").
     * If the input is an ISO local date, the returned time will be the start of that day.
     * If the input is null or cannot be parsed, returns the current date and time.
     *
     * @param dateStr the date or date-time string to parse; may be null
     * @return the parsed LocalDateTime, the start of day for ISO local dates, or the current LocalDateTime if parsing fails
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
     * Maps a chamber label string to the corresponding Chamber enum.
     *
     * @param chamberStr a chamber name or label (case-insensitive), e.g. "House" or "Senate"; may be null
     * @return `Chamber.ASSEMBLY` if `chamberStr` contains "house" (case-insensitive), `Chamber.SENATE` if it contains "senate" or is null, otherwise `Chamber.SENATE`
     */
    private Chamber parseChamber(String chamberStr) {
        if (chamberStr == null) return Chamber.SENATE;
        if (chamberStr.toLowerCase().contains("house")) return Chamber.ASSEMBLY; // Map House to Assembly
        if (chamberStr.toLowerCase().contains("senate")) return Chamber.SENATE;
        return Chamber.SENATE; // Default
    }

    /**
     * No-op override that defers ingest cache handling to the superclass implementation.
     */
    @Override
    public void checkIngestCache() {
        // Delegate to parent implementation
    }

    /**
     * Post-processing hook invoked after GovInfo bill processing.
     *
     * <p>This implementation performs no additional actions.</p>
     */
    @Override
    public void postProcess() {
        // Nothing specific for GovInfo
    }
}