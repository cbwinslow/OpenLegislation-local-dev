package gov.nysenate.openleg.legislation.bill.govinfo;

import java.time.LocalDate;
import java.util.List;
import java.util.Objects;

/**
 * Represents a federal bill from GovInfo documents.
 * Parsed from XML <bill> elements.
 * Includes sponsors and cosponsors with dedup linkage to federal members.
 */
public class GovInfoBill {
    private String congressNumber;
    private String sessionNumber;
    private String billNumber;
    private String billType; // e.g., "hr", "s"
    private GovInfoBillSponsor sponsor;
    private List<GovInfoBillCosponsor> cosponsors;
    private List<GovInfoBillAction> actions;
    private GovInfoBillText text;
    private List<GovInfoBillCommittee> committees;
    private List<GovInfoDocRef> docRefs;

    /**
 * Creates a new GovInfoBill with all fields unset.
 */
    public GovInfoBill() {}

    /**
     * Create a GovInfoBill populated with identifying fields and a sponsor.
     *
     * @param congressNumber the congress number (e.g., "117")
     * @param sessionNumber  the session number within the congress
     * @param billNumber     the bill number without prefix (e.g., "1234")
     * @param billType       the bill type prefix (e.g., "hr" or "s")
     * @param sponsor        the parsed sponsor information for the bill
     */
    public GovInfoBill(String congressNumber, String sessionNumber, String billNumber, String billType,
                       GovInfoBillSponsor sponsor) {
        this.congressNumber = congressNumber;
        this.sessionNumber = sessionNumber;
        this.billNumber = billNumber;
        this.billType = billType;
        this.sponsor = sponsor;
    }

    /**
 * Congress number identifying the Congress session for this bill.
 *
 * @return the congress number, or {@code null} if not set
 */
    public String getCongressNumber() { return congressNumber; }
    /**
 * Sets the congress number that identifies the bill.
 *
 * @param congressNumber the congress number (e.g., "116")
 */
public void setCongressNumber(String congressNumber) { this.congressNumber = congressNumber; }

    /**
 * Gets the congressional session number associated with this bill.
 *
 * @return the session number for the bill's Congress
 */
public String getSessionNumber() { return sessionNumber; }
    /**
 * Sets the congressional session number associated with this bill.
 *
 * @param sessionNumber the session number to assign
 */
public void setSessionNumber(String sessionNumber) { this.sessionNumber = sessionNumber; }

    /**
 * Retrieve the bill number used to identify the bill within a congressional session.
 *
 * @return the bill number string (e.g., "hr1234", "s567"), or {@code null} if not set
 */
public String getBillNumber() { return billNumber; }
    /**
 * Set the bill's assigned number within its session.
 *
 * @param billNumber the bill identifier (for example, "1234")
 */
public void setBillNumber(String billNumber) { this.billNumber = billNumber; }

    /**
 * Retrieves the bill type code such as "hr" or "s".
 *
 * @return the bill type code (e.g., "hr", "s"), or null if not set
 */
public String getBillType() { return billType; }
    /**
 * Sets the bill type code for this bill (for example, "hr" for House bills or "s" for Senate bills).
 *
 * @param billType the bill type code (e.g., "hr", "s")
 */
public void setBillType(String billType) { this.billType = billType; }

    /**
 * The bill's sponsor.
 *
 * @return the sponsor, or {@code null} if not set
 */
public GovInfoBillSponsor getSponsor() { return sponsor; }
    /**
 * Set the bill's primary sponsor.
 *
 * @param sponsor the primary sponsor for this bill, or `null` to clear the sponsor
 */
public void setSponsor(GovInfoBillSponsor sponsor) { this.sponsor = sponsor; }

    /**
 * Retrieve the list of cosponsors parsed from the GovInfo bill.
 *
 * @return the list of {@link GovInfoBillCosponsor} objects representing cosponsors, or {@code null} if not set
 */
public List<GovInfoBillCosponsor> getCosponsors() { return cosponsors; }
    /**
     * Sets the bill's cosponsors and attempts to resolve each cosponsor's personId via a deduplication lookup.
     *
     * If the provided list is null, any existing cosponsors are cleared. When non-null, each cosponsor element
     * may have its `personId` populated by the linkage process.
     *
     * @param cosponsors list of GovInfoBillCosponsor parsed from GovInfo; may be null to clear cosponsors
     */
    public void setCosponsors(List<GovInfoBillCosponsor> cosponsors) { 
        this.cosponsors = cosponsors; 
        if (cosponsors != null) {
            // Link personIds via dedup lookup (in processor/DAO)
            for (GovInfoBillCosponsor cosponsor : cosponsors) {
                // TODO: Call DAO to set cosponsor.personId based on matchKey
            }
        }
    }

    /**
 * Retrieve the list of GovInfo-parsed actions associated with this bill.
 *
 * @return the list of bill actions, or null if not set
 */
public List<GovInfoBillAction> getActions() { return actions; }
    /**
 * Sets the list of actions associated with this bill.
 *
 * @param actions the actions for the bill, or null if none
 */
public void setActions(List<GovInfoBillAction> actions) { this.actions = actions; }

    /**
 * Gets the bill's primary text content.
 *
 * @return the bill text object, or {@code null} if none is set
 */
public GovInfoBillText getText() { return text; }
    /**
 * Set the bill text information parsed from GovInfo documents.
 *
 * @param text the GovInfoBillText containing the bill's text and related metadata, or {@code null} if none is available
 */
public void setText(GovInfoBillText text) { this.text = text; }

    /**
 * Provides the committees referenced by this bill.
 *
 * @return the list of committees for the bill, or {@code null} if none have been set
 */
public List<GovInfoBillCommittee> getCommittees() { return committees; }
    /**
 * Assigns the list of committees associated with this bill.
 *
 * @param committees the committees for this bill, or {@code null} to clear the existing list
 */
public void setCommittees(List<GovInfoBillCommittee> committees) { this.committees = committees; }

    /**
 * Retrieves the GovInfo document references associated with this bill.
 *
 * @return the list of GovInfo document references, or {@code null} if none are set
 */
public List<GovInfoDocRef> getDocRefs() { return docRefs; }
    /**
 * Set the document references associated with this bill.
 *
 * @param docRefs the list of document references for the bill, or {@code null} to clear them
 */
public void setDocRefs(List<GovInfoDocRef> docRefs) { this.docRefs = docRefs; }

    /**
     * Determines whether this GovInfoBill represents the same bill as another object.
     *
     * Compares congressNumber, sessionNumber, billNumber, billType, sponsor, and cosponsors for equality.
     *
     * @param o the object to compare with
     * @return {@code true} if {@code o} is a GovInfoBill whose congressNumber, sessionNumber, billNumber, billType, sponsor, and cosponsors are equal to this instance, {@code false} otherwise
     */
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        GovInfoBill that = (GovInfoBill) o;
        return Objects.equals(congressNumber, that.congressNumber) &&
               Objects.equals(sessionNumber, that.sessionNumber) &&
               Objects.equals(billNumber, that.billNumber) &&
               Objects.equals(billType, that.billType) &&
               Objects.equals(sponsor, that.sponsor) &&
               Objects.equals(cosponsors, that.cosponsors);
    }

    /**
     * Computes a hash code for this GovInfoBill instance.
     *
     * The hash is derived from the bill's identifying fields and sponsors.
     *
     * @return the hash code value computed from congressNumber, sessionNumber, billNumber, billType, sponsor, and cosponsors
     */
    @Override
    public int hashCode() {
        return Objects.hash(congressNumber, sessionNumber, billNumber, billType, sponsor, cosponsors);
    }

    /**
     * Provides a concise string representation of the bill including identifying fields, sponsor, and cosponsor count.
     *
     * @return a string containing congressNumber, sessionNumber, billNumber, billType, sponsor, and the number of cosponsors
     */
    @Override
    public String toString() {
        return "GovInfoBill{" +
                "congressNumber='" + congressNumber + '\'' +
                ", sessionNumber='" + sessionNumber + '\'' +
                ", billNumber='" + billNumber + '\'' +
                ", billType='" + billType + '\'' +
                ", sponsor=" + sponsor +
                ", cosponsors.size=" + (cosponsors != null ? cosponsors.size() : 0) +
                '}';
    }
}